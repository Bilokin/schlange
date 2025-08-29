von contextlib importiere contextmanager
importiere linecache
importiere os
importiere importlib
importiere inspect
von io importiere StringIO
importiere re
importiere sys
importiere textwrap
importiere types
von typing importiere overload, get_overloads
importiere unittest
von test importiere support
von test.support importiere import_helper
von test.support importiere os_helper
von test.support importiere warnings_helper
von test.support importiere force_not_colorized
von test.support.script_helper importiere assert_python_ok, assert_python_failure

von test.test_warnings.data importiere package_helper
von test.test_warnings.data importiere stacklevel als warning_tests

importiere warnings als original_warnings
von warnings importiere deprecated


py_warnings = import_helper.import_fresh_module('_py_warnings')
py_warnings._set_module(py_warnings)

c_warnings = import_helper.import_fresh_module(
    "warnings", fresh=["_warnings", "_py_warnings"]
)
c_warnings._set_module(c_warnings)

@contextmanager
def warnings_state(module):
    """Use a specific warnings implementation in warning_tests."""
    global __warningregistry__
    fuer to_clear in (sys, warning_tests):
        try:
            to_clear.__warningregistry__.clear()
        except AttributeError:
            pass
    try:
        __warningregistry__.clear()
    except NameError:
        pass
    original_warnings = warning_tests.warnings
    wenn module._use_context:
        saved_context, context = module._new_context()
    sonst:
        original_filters = module.filters
        module.filters = original_filters[:]
    try:
        module.simplefilter("once")
        warning_tests.warnings = module
        liefere
    finally:
        warning_tests.warnings = original_warnings
        wenn module._use_context:
            module._set_context(saved_context)
        sonst:
            module.filters = original_filters


klasse TestWarning(Warning):
    pass


klasse BaseTest:

    """Basic bookkeeping required fuer testing."""

    def setUp(self):
        self.old_unittest_module = unittest.case.warnings
        # The __warningregistry__ needs to be in a pristine state fuer tests
        # to work properly.
        wenn '__warningregistry__' in globals():
            del globals()['__warningregistry__']
        wenn hasattr(warning_tests, '__warningregistry__'):
            del warning_tests.__warningregistry__
        wenn hasattr(sys, '__warningregistry__'):
            del sys.__warningregistry__
        # The 'warnings' module must be explicitly set so that the proper
        # interaction between _warnings und 'warnings' can be controlled.
        sys.modules['warnings'] = self.module
        # Ensure that unittest.TestCase.assertWarns() uses the same warnings
        # module than warnings.catch_warnings(). Otherwise,
        # warnings.catch_warnings() will be unable to remove the added filter.
        unittest.case.warnings = self.module
        super(BaseTest, self).setUp()

    def tearDown(self):
        sys.modules['warnings'] = original_warnings
        unittest.case.warnings = self.old_unittest_module
        super(BaseTest, self).tearDown()

klasse PublicAPITests(BaseTest):

    """Ensures that the correct values are exposed in the
    public API.
    """

    def test_module_all_attribute(self):
        self.assertHasAttr(self.module, '__all__')
        target_api = ["warn", "warn_explicit", "showwarning",
                      "formatwarning", "filterwarnings", "simplefilter",
                      "resetwarnings", "catch_warnings", "deprecated"]
        self.assertSetEqual(set(self.module.__all__),
                            set(target_api))

klasse CPublicAPITests(PublicAPITests, unittest.TestCase):
    module = c_warnings

klasse PyPublicAPITests(PublicAPITests, unittest.TestCase):
    module = py_warnings

klasse FilterTests(BaseTest):

    """Testing the filtering functionality."""

    def test_error(self):
        mit self.module.catch_warnings() als w:
            self.module.resetwarnings()
            self.module.filterwarnings("error", category=UserWarning)
            self.assertRaises(UserWarning, self.module.warn,
                                "FilterTests.test_error")

    def test_error_after_default(self):
        mit self.module.catch_warnings() als w:
            self.module.resetwarnings()
            message = "FilterTests.test_ignore_after_default"
            def f():
                self.module.warn(message, UserWarning)

            mit support.captured_stderr() als stderr:
                f()
            stderr = stderr.getvalue()
            self.assertIn("UserWarning: FilterTests.test_ignore_after_default",
                          stderr)
            self.assertIn("self.module.warn(message, UserWarning)",
                          stderr)

            self.module.filterwarnings("error", category=UserWarning)
            self.assertRaises(UserWarning, f)

    def test_ignore(self):
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.resetwarnings()
            self.module.filterwarnings("ignore", category=UserWarning)
            self.module.warn("FilterTests.test_ignore", UserWarning)
            self.assertEqual(len(w), 0)
            self.assertEqual(list(__warningregistry__), ['version'])

    def test_ignore_after_default(self):
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.resetwarnings()
            message = "FilterTests.test_ignore_after_default"
            def f():
                self.module.warn(message, UserWarning)
            f()
            self.module.filterwarnings("ignore", category=UserWarning)
            f()
            f()
            self.assertEqual(len(w), 1)

    def test_always_and_all(self):
        fuer mode in {"always", "all"}:
            mit self.module.catch_warnings(record=Wahr) als w:
                self.module.resetwarnings()
                self.module.filterwarnings(mode, category=UserWarning)
                message = "FilterTests.test_always_and_all"
                def f():
                    self.module.warn(message, UserWarning)
                f()
                self.assertEqual(len(w), 1)
                self.assertEqual(w[-1].message.args[0], message)
                f()
                self.assertEqual(len(w), 2)
                self.assertEqual(w[-1].message.args[0], message)

    def test_always_and_all_after_default(self):
        fuer mode in {"always", "all"}:
            mit self.module.catch_warnings(record=Wahr) als w:
                self.module.resetwarnings()
                message = "FilterTests.test_always_and_all_after_ignore"
                def f():
                    self.module.warn(message, UserWarning)
                f()
                self.assertEqual(len(w), 1)
                self.assertEqual(w[-1].message.args[0], message)
                f()
                self.assertEqual(len(w), 1)
                self.module.filterwarnings(mode, category=UserWarning)
                f()
                self.assertEqual(len(w), 2)
                self.assertEqual(w[-1].message.args[0], message)
                f()
                self.assertEqual(len(w), 3)
                self.assertEqual(w[-1].message.args[0], message)

    def test_default(self):
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.resetwarnings()
            self.module.filterwarnings("default", category=UserWarning)
            message = UserWarning("FilterTests.test_default")
            fuer x in range(2):
                self.module.warn(message, UserWarning)
                wenn x == 0:
                    self.assertEqual(w[-1].message, message)
                    del w[:]
                sowenn x == 1:
                    self.assertEqual(len(w), 0)
                sonst:
                    raise ValueError("loop variant unhandled")

    def test_module(self):
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.resetwarnings()
            self.module.filterwarnings("module", category=UserWarning)
            message = UserWarning("FilterTests.test_module")
            self.module.warn(message, UserWarning)
            self.assertEqual(w[-1].message, message)
            del w[:]
            self.module.warn(message, UserWarning)
            self.assertEqual(len(w), 0)

    def test_once(self):
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.resetwarnings()
            self.module.filterwarnings("once", category=UserWarning)
            message = UserWarning("FilterTests.test_once")
            self.module.warn_explicit(message, UserWarning, "__init__.py",
                                    42)
            self.assertEqual(w[-1].message, message)
            del w[:]
            self.module.warn_explicit(message, UserWarning, "__init__.py",
                                    13)
            self.assertEqual(len(w), 0)
            self.module.warn_explicit(message, UserWarning, "test_warnings2.py",
                                    42)
            self.assertEqual(len(w), 0)

    def test_module_globals(self):
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.simplefilter("always", UserWarning)

            # bpo-33509: module_globals=Nichts must nicht crash
            self.module.warn_explicit('msg', UserWarning, "filename", 42,
                                      module_globals=Nichts)
            self.assertEqual(len(w), 1)

            # Invalid module_globals type
            mit self.assertRaises(TypeError):
                self.module.warn_explicit('msg', UserWarning, "filename", 42,
                                          module_globals=Wahr)
            self.assertEqual(len(w), 1)

            # Empty module_globals
            self.module.warn_explicit('msg', UserWarning, "filename", 42,
                                      module_globals={})
            self.assertEqual(len(w), 2)

    def test_inheritance(self):
        mit self.module.catch_warnings() als w:
            self.module.resetwarnings()
            self.module.filterwarnings("error", category=Warning)
            self.assertRaises(UserWarning, self.module.warn,
                                "FilterTests.test_inheritance", UserWarning)

    def test_ordering(self):
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.resetwarnings()
            self.module.filterwarnings("ignore", category=UserWarning)
            self.module.filterwarnings("error", category=UserWarning,
                                        append=Wahr)
            del w[:]
            try:
                self.module.warn("FilterTests.test_ordering", UserWarning)
            except UserWarning:
                self.fail("order handling fuer actions failed")
            self.assertEqual(len(w), 0)

    def test_filterwarnings(self):
        # Test filterwarnings().
        # Implicitly also tests resetwarnings().
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.filterwarnings("error", "", Warning, "", 0)
            self.assertRaises(UserWarning, self.module.warn, 'convert to error')

            self.module.resetwarnings()
            text = 'handle normally'
            self.module.warn(text)
            self.assertEqual(str(w[-1].message), text)
            self.assertIs(w[-1].category, UserWarning)

            self.module.filterwarnings("ignore", "", Warning, "", 0)
            text = 'filtered out'
            self.module.warn(text)
            self.assertNotEqual(str(w[-1].message), text)

            self.module.resetwarnings()
            self.module.filterwarnings("error", "hex*", Warning, "", 0)
            self.assertRaises(UserWarning, self.module.warn, 'hex/oct')
            text = 'nonmatching text'
            self.module.warn(text)
            self.assertEqual(str(w[-1].message), text)
            self.assertIs(w[-1].category, UserWarning)

    def test_message_matching(self):
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.simplefilter("ignore", UserWarning)
            self.module.filterwarnings("error", "match", UserWarning)
            self.assertRaises(UserWarning, self.module.warn, "match")
            self.assertRaises(UserWarning, self.module.warn, "match prefix")
            self.module.warn("suffix match")
            self.assertEqual(w, [])
            self.module.warn("something completely different")
            self.assertEqual(w, [])

    def test_mutate_filter_list(self):
        klasse X:
            def match(self, a):
                L[:] = []

        L = [("default",X(),UserWarning,X(),0) fuer i in range(2)]
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.filters = L
            self.module.warn_explicit(UserWarning("b"), Nichts, "f.py", 42)
            self.assertEqual(str(w[-1].message), "b")

    def test_filterwarnings_duplicate_filters(self):
        mit self.module.catch_warnings():
            self.module.resetwarnings()
            self.module.filterwarnings("error", category=UserWarning)
            self.assertEqual(len(self.module._get_filters()), 1)
            self.module.filterwarnings("ignore", category=UserWarning)
            self.module.filterwarnings("error", category=UserWarning)
            self.assertEqual(
                len(self.module._get_filters()), 2,
                "filterwarnings inserted duplicate filter"
            )
            self.assertEqual(
                self.module._get_filters()[0][0], "error",
                "filterwarnings did nicht promote filter to "
                "the beginning of list"
            )

    def test_simplefilter_duplicate_filters(self):
        mit self.module.catch_warnings():
            self.module.resetwarnings()
            self.module.simplefilter("error", category=UserWarning)
            self.assertEqual(len(self.module._get_filters()), 1)
            self.module.simplefilter("ignore", category=UserWarning)
            self.module.simplefilter("error", category=UserWarning)
            self.assertEqual(
                len(self.module._get_filters()), 2,
                "simplefilter inserted duplicate filter"
            )
            self.assertEqual(
                self.module._get_filters()[0][0], "error",
                "simplefilter did nicht promote filter to the beginning of list"
            )

    def test_append_duplicate(self):
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.resetwarnings()
            self.module.simplefilter("ignore")
            self.module.simplefilter("error", append=Wahr)
            self.module.simplefilter("ignore", append=Wahr)
            self.module.warn("test_append_duplicate", category=UserWarning)
            self.assertEqual(len(self.module._get_filters()), 2,
                "simplefilter inserted duplicate filter"
            )
            self.assertEqual(len(w), 0,
                "appended duplicate changed order of filters"
            )

    def test_argument_validation(self):
        mit self.assertRaises(ValueError):
            self.module.filterwarnings(action='foo')
        mit self.assertRaises(TypeError):
            self.module.filterwarnings('ignore', message=0)
        mit self.assertRaises(TypeError):
            self.module.filterwarnings('ignore', category=0)
        mit self.assertRaises(TypeError):
            self.module.filterwarnings('ignore', category=int)
        mit self.assertRaises(TypeError):
            self.module.filterwarnings('ignore', module=0)
        mit self.assertRaises(TypeError):
            self.module.filterwarnings('ignore', lineno=int)
        mit self.assertRaises(ValueError):
            self.module.filterwarnings('ignore', lineno=-1)
        mit self.assertRaises(ValueError):
            self.module.simplefilter(action='foo')
        mit self.assertRaises(TypeError):
            self.module.simplefilter('ignore', lineno=int)
        mit self.assertRaises(ValueError):
            self.module.simplefilter('ignore', lineno=-1)

    def test_catchwarnings_with_simplefilter_ignore(self):
        mit self.module.catch_warnings(module=self.module):
            self.module.resetwarnings()
            self.module.simplefilter("error")
            mit self.module.catch_warnings(action="ignore"):
                self.module.warn("This will be ignored")

    def test_catchwarnings_with_simplefilter_error(self):
        mit self.module.catch_warnings():
            self.module.resetwarnings()
            mit self.module.catch_warnings(
                action="error", category=FutureWarning
            ):
                mit support.captured_stderr() als stderr:
                    error_msg = "Other types of warnings are nicht errors"
                    self.module.warn(error_msg)
                    self.assertRaises(FutureWarning,
                                      self.module.warn, FutureWarning("msg"))
                    stderr = stderr.getvalue()
                    self.assertIn(error_msg, stderr)

klasse CFilterTests(FilterTests, unittest.TestCase):
    module = c_warnings

klasse PyFilterTests(FilterTests, unittest.TestCase):
    module = py_warnings


klasse WarnTests(BaseTest):

    """Test warnings.warn() und warnings.warn_explicit()."""

    def test_message(self):
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.simplefilter("once")
            fuer i in range(4):
                text = 'multi %d' %i  # Different text on each call.
                self.module.warn(text)
                self.assertEqual(str(w[-1].message), text)
                self.assertIs(w[-1].category, UserWarning)

    # Issue 3639
    def test_warn_nonstandard_types(self):
        # warn() should handle non-standard types without issue.
        fuer ob in (Warning, Nichts, 42):
            mit self.module.catch_warnings(record=Wahr) als w:
                self.module.simplefilter("once")
                self.module.warn(ob)
                # Don't directly compare objects since
                # ``Warning() != Warning()``.
                self.assertEqual(str(w[-1].message), str(UserWarning(ob)))

    def test_filename(self):
        mit warnings_state(self.module):
            mit self.module.catch_warnings(record=Wahr) als w:
                warning_tests.inner("spam1")
                self.assertEqual(os.path.basename(w[-1].filename),
                                    "stacklevel.py")
                warning_tests.outer("spam2")
                self.assertEqual(os.path.basename(w[-1].filename),
                                    "stacklevel.py")

    def test_stacklevel(self):
        # Test stacklevel argument
        # make sure all messages are different, so the warning won't be skipped
        mit warnings_state(self.module):
            mit self.module.catch_warnings(record=Wahr) als w:
                warning_tests.inner("spam3", stacklevel=1)
                self.assertEqual(os.path.basename(w[-1].filename),
                                    "stacklevel.py")
                warning_tests.outer("spam4", stacklevel=1)
                self.assertEqual(os.path.basename(w[-1].filename),
                                    "stacklevel.py")

                warning_tests.inner("spam5", stacklevel=2)
                self.assertEqual(os.path.basename(w[-1].filename),
                                    "__init__.py")
                warning_tests.outer("spam6", stacklevel=2)
                self.assertEqual(os.path.basename(w[-1].filename),
                                    "stacklevel.py")
                warning_tests.outer("spam6.5", stacklevel=3)
                self.assertEqual(os.path.basename(w[-1].filename),
                                    "__init__.py")

                warning_tests.inner("spam7", stacklevel=9999)
                self.assertEqual(os.path.basename(w[-1].filename),
                                    "<sys>")

    def test_stacklevel_import(self):
        # Issue #24305: With stacklevel=2, module-level warnings should work.
        import_helper.unload('test.test_warnings.data.import_warning')
        mit warnings_state(self.module):
            mit self.module.catch_warnings(record=Wahr) als w:
                self.module.simplefilter('always')
                importiere test.test_warnings.data.import_warning  # noqa: F401
                self.assertEqual(len(w), 1)
                self.assertEqual(w[0].filename, __file__)

    def test_skip_file_prefixes(self):
        mit warnings_state(self.module):
            mit self.module.catch_warnings(record=Wahr) als w:
                self.module.simplefilter('always')

                # Warning never attributed to the data/ package.
                package_helper.inner_api(
                        "inner_api", stacklevel=2,
                        warnings_module=warning_tests.warnings)
                self.assertEqual(w[-1].filename, __file__)
                warning_tests.package("package api", stacklevel=2)
                self.assertEqual(w[-1].filename, __file__)
                self.assertEqual(w[-2].filename, w[-1].filename)
                # Low stacklevels are overridden to 2 behavior.
                warning_tests.package("package api 1", stacklevel=1)
                self.assertEqual(w[-1].filename, __file__)
                warning_tests.package("package api 0", stacklevel=0)
                self.assertEqual(w[-1].filename, __file__)
                warning_tests.package("package api -99", stacklevel=-99)
                self.assertEqual(w[-1].filename, __file__)

                # The stacklevel still goes up out of the package.
                warning_tests.package("prefix02", stacklevel=3)
                self.assertIn("unittest", w[-1].filename)

    def test_skip_file_prefixes_file_path(self):
        # see: gh-126209
        mit warnings_state(self.module):
            skipped = warning_tests.__file__
            mit self.module.catch_warnings(record=Wahr) als w:
                warning_tests.outer("msg", skip_file_prefixes=(skipped,))

            self.assertEqual(len(w), 1)
            self.assertNotEqual(w[-1].filename, skipped)

    def test_skip_file_prefixes_type_errors(self):
        mit warnings_state(self.module):
            warn = warning_tests.warnings.warn
            mit self.assertRaises(TypeError):
                warn("msg", skip_file_prefixes=[])
            mit self.assertRaises(TypeError):
                warn("msg", skip_file_prefixes=(b"bytes",))
            mit self.assertRaises(TypeError):
                warn("msg", skip_file_prefixes="a sequence of strs")

    def test_exec_filename(self):
        filename = "<warnings-test>"
        codeobj = compile(("import warnings\n"
                           "warnings.warn('hello', UserWarning)"),
                          filename, "exec")
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.simplefilter("always", category=UserWarning)
            exec(codeobj)
        self.assertEqual(w[0].filename, filename)

    def test_warn_explicit_non_ascii_filename(self):
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.resetwarnings()
            self.module.filterwarnings("always", category=UserWarning)
            filenames = ["nonascii\xe9\u20ac", "surrogate\udc80"]
            fuer filename in filenames:
                try:
                    os.fsencode(filename)
                except UnicodeEncodeError:
                    weiter
                self.module.warn_explicit("text", UserWarning, filename, 1)
                self.assertEqual(w[-1].filename, filename)

    def test_warn_explicit_type_errors(self):
        # warn_explicit() should error out gracefully wenn it is given objects
        # of the wrong types.
        # lineno is expected to be an integer.
        self.assertRaises(TypeError, self.module.warn_explicit,
                            Nichts, UserWarning, Nichts, Nichts)
        # Either 'message' needs to be an instance of Warning oder 'category'
        # needs to be a subclass.
        self.assertRaises(TypeError, self.module.warn_explicit,
                            Nichts, Nichts, Nichts, 1)
        # 'registry' must be a dict oder Nichts.
        self.assertRaises((TypeError, AttributeError),
                            self.module.warn_explicit,
                            Nichts, Warning, Nichts, 1, registry=42)

    def test_bad_str(self):
        # issue 6415
        # Warnings instance mit a bad format string fuer __str__ should not
        # trigger a bus error.
        klasse BadStrWarning(Warning):
            """Warning mit a bad format string fuer __str__."""
            def __str__(self):
                gib ("A bad formatted string %(err)" %
                        {"err" : "there is no %(err)s"})

        mit self.assertRaises(ValueError):
            self.module.warn(BadStrWarning())

    def test_warning_classes(self):
        klasse MyWarningClass(Warning):
            pass

        # passing a non-subclass of Warning should raise a TypeError
        expected = "category must be a Warning subclass, nicht 'str'"
        mit self.assertRaisesRegex(TypeError, expected):
            self.module.warn('bad warning category', '')

        expected = "category must be a Warning subclass, nicht klasse 'int'"
        mit self.assertRaisesRegex(TypeError, expected):
            self.module.warn('bad warning category', int)

        # check that warning instances also raise a TypeError
        expected = "category must be a Warning subclass, nicht '.*MyWarningClass'"
        mit self.assertRaisesRegex(TypeError, expected):
            self.module.warn('bad warning category', MyWarningClass())

        mit self.module.catch_warnings():
            self.module.resetwarnings()
            self.module.filterwarnings('default')
            mit self.assertWarns(MyWarningClass) als cm:
                self.module.warn('good warning category', MyWarningClass)
            self.assertEqual('good warning category', str(cm.warning))

            mit self.assertWarns(UserWarning) als cm:
                self.module.warn('good warning category', Nichts)
            self.assertEqual('good warning category', str(cm.warning))

            mit self.assertWarns(MyWarningClass) als cm:
                self.module.warn('good warning category', MyWarningClass)
            self.assertIsInstance(cm.warning, Warning)

    def check_module_globals(self, module_globals):
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.filterwarnings('default')
            self.module.warn_explicit(
                'eggs', UserWarning, 'bar', 1,
                module_globals=module_globals)
        self.assertEqual(len(w), 1)
        self.assertEqual(w[0].category, UserWarning)
        self.assertEqual(str(w[0].message), 'eggs')

    def check_module_globals_error(self, module_globals, errmsg, errtype=ValueError):
        wenn self.module is py_warnings:
            self.check_module_globals(module_globals)
            gib
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.filterwarnings('always')
            mit self.assertRaisesRegex(errtype, re.escape(errmsg)):
                self.module.warn_explicit(
                    'eggs', UserWarning, 'bar', 1,
                    module_globals=module_globals)
        self.assertEqual(len(w), 0)

    def check_module_globals_deprecated(self, module_globals, msg):
        wenn self.module is py_warnings:
            self.check_module_globals(module_globals)
            gib
        mit self.module.catch_warnings(record=Wahr) als w:
            self.module.filterwarnings('always')
            self.module.warn_explicit(
                'eggs', UserWarning, 'bar', 1,
                module_globals=module_globals)
        self.assertEqual(len(w), 2)
        self.assertEqual(w[0].category, DeprecationWarning)
        self.assertEqual(str(w[0].message), msg)
        self.assertEqual(w[1].category, UserWarning)
        self.assertEqual(str(w[1].message), 'eggs')

    def test_gh86298_no_loader_and_no_spec(self):
        self.check_module_globals({'__name__': 'bar'})

    def test_gh86298_loader_is_none_and_no_spec(self):
        self.check_module_globals({'__name__': 'bar', '__loader__': Nichts})

    def test_gh86298_no_loader_and_spec_is_none(self):
        self.check_module_globals_error(
            {'__name__': 'bar', '__spec__': Nichts},
            'Module globals is missing a __spec__.loader')

    def test_gh86298_loader_is_none_and_spec_is_none(self):
        self.check_module_globals_error(
            {'__name__': 'bar', '__loader__': Nichts, '__spec__': Nichts},
            'Module globals is missing a __spec__.loader')

    def test_gh86298_loader_is_none_and_spec_loader_is_none(self):
        self.check_module_globals_error(
            {'__name__': 'bar', '__loader__': Nichts,
             '__spec__': types.SimpleNamespace(loader=Nichts)},
            'Module globals is missing a __spec__.loader')

    def test_gh86298_no_spec(self):
        self.check_module_globals_deprecated(
            {'__name__': 'bar', '__loader__': object()},
            'Module globals is missing a __spec__.loader')

    def test_gh86298_spec_is_none(self):
        self.check_module_globals_deprecated(
            {'__name__': 'bar', '__loader__': object(), '__spec__': Nichts},
            'Module globals is missing a __spec__.loader')

    def test_gh86298_no_spec_loader(self):
        self.check_module_globals_deprecated(
            {'__name__': 'bar', '__loader__': object(),
             '__spec__': types.SimpleNamespace()},
            'Module globals is missing a __spec__.loader')

    def test_gh86298_loader_and_spec_loader_disagree(self):
        self.check_module_globals_deprecated(
            {'__name__': 'bar', '__loader__': object(),
             '__spec__': types.SimpleNamespace(loader=object())},
            'Module globals; __loader__ != __spec__.loader')

    def test_gh86298_no_loader_and_no_spec_loader(self):
        self.check_module_globals_error(
            {'__name__': 'bar', '__spec__': types.SimpleNamespace()},
            'Module globals is missing a __spec__.loader', AttributeError)

    def test_gh86298_no_loader_with_spec_loader_okay(self):
        self.check_module_globals(
            {'__name__': 'bar',
             '__spec__': types.SimpleNamespace(loader=object())})

klasse CWarnTests(WarnTests, unittest.TestCase):
    module = c_warnings

    # As an early adopter, we sanity check the
    # test.import_helper.import_fresh_module utility function
    def test_accelerated(self):
        self.assertIsNot(original_warnings, self.module)
        self.assertNotHasAttr(self.module.warn, '__code__')

klasse PyWarnTests(WarnTests, unittest.TestCase):
    module = py_warnings

    # As an early adopter, we sanity check the
    # test.import_helper.import_fresh_module utility function
    def test_pure_python(self):
        self.assertIsNot(original_warnings, self.module)
        self.assertHasAttr(self.module.warn, '__code__')


klasse WCmdLineTests(BaseTest):

    def test_improper_input(self):
        # Uses the private _setoption() function to test the parsing
        # of command-line warning arguments
        mit self.module.catch_warnings():
            self.assertRaises(self.module._OptionError,
                              self.module._setoption, '1:2:3:4:5:6')
            self.assertRaises(self.module._OptionError,
                              self.module._setoption, 'bogus::Warning')
            self.assertRaises(self.module._OptionError,
                              self.module._setoption, 'ignore:2::4:-5')
            mit self.assertRaises(self.module._OptionError):
                self.module._setoption('ignore::123')
            mit self.assertRaises(self.module._OptionError):
                self.module._setoption('ignore::123abc')
            mit self.assertRaises(self.module._OptionError):
                self.module._setoption('ignore::===')
            mit self.assertRaisesRegex(self.module._OptionError, 'Wärning'):
                self.module._setoption('ignore::Wärning')
            self.module._setoption('error::Warning::0')
            self.assertRaises(UserWarning, self.module.warn, 'convert to error')

    def test_import_from_module(self):
        mit self.module.catch_warnings():
            self.module._setoption('ignore::Warning')
            mit self.assertRaises(self.module._OptionError):
                self.module._setoption('ignore::TestWarning')
            mit self.assertRaises(self.module._OptionError):
                self.module._setoption('ignore::test.test_warnings.bogus')
            self.module._setoption('error::test.test_warnings.TestWarning')
            mit self.assertRaises(TestWarning):
                self.module.warn('test warning', TestWarning)


klasse CWCmdLineTests(WCmdLineTests, unittest.TestCase):
    module = c_warnings


klasse PyWCmdLineTests(WCmdLineTests, unittest.TestCase):
    module = py_warnings

    def test_improper_option(self):
        # Same als above, but check that the message is printed out when
        # the interpreter is executed. This also checks that options are
        # actually parsed at all.
        rc, out, err = assert_python_ok("-Wxxx", "-c", "pass")
        self.assertIn(b"Invalid -W option ignored: invalid action: 'xxx'", err)

    def test_warnings_bootstrap(self):
        # Check that the warnings module does get loaded when -W<some option>
        # is used (see issue #10372 fuer an example of silent bootstrap failure).
        rc, out, err = assert_python_ok("-Wi", "-c",
            "import sys; sys.modules['warnings'].warn('foo', RuntimeWarning)")
        # '-Wi' was observed
        self.assertFalsch(out.strip())
        self.assertNotIn(b'RuntimeWarning', err)


klasse _WarningsTests(BaseTest, unittest.TestCase):

    """Tests specific to the _warnings module."""

    module = c_warnings

    def test_filter(self):
        # Everything should function even wenn 'filters' is nicht in warnings.
        mit self.module.catch_warnings() als w:
            self.module.filterwarnings("error", "", Warning, "", 0)
            self.assertRaises(UserWarning, self.module.warn,
                                'convert to error')
            del self.module.filters
            self.assertRaises(UserWarning, self.module.warn,
                                'convert to error')

    def test_onceregistry(self):
        # Replacing oder removing the onceregistry should be okay.
        global __warningregistry__
        message = UserWarning('onceregistry test')
        try:
            original_registry = self.module.onceregistry
            __warningregistry__ = {}
            mit self.module.catch_warnings(record=Wahr) als w:
                self.module.resetwarnings()
                self.module.filterwarnings("once", category=UserWarning)
                self.module.warn_explicit(message, UserWarning, "file", 42)
                self.assertEqual(w[-1].message, message)
                del w[:]
                self.module.warn_explicit(message, UserWarning, "file", 42)
                self.assertEqual(len(w), 0)
                # Test the resetting of onceregistry.
                self.module.onceregistry = {}
                __warningregistry__ = {}
                self.module.warn('onceregistry test')
                self.assertEqual(w[-1].message.args, message.args)
                # Removal of onceregistry is okay.
                del w[:]
                del self.module.onceregistry
                __warningregistry__ = {}
                self.module.warn_explicit(message, UserWarning, "file", 42)
                self.assertEqual(len(w), 0)
        finally:
            self.module.onceregistry = original_registry

    def test_default_action(self):
        # Replacing oder removing defaultaction should be okay.
        message = UserWarning("defaultaction test")
        original = self.module.defaultaction
        try:
            mit self.module.catch_warnings(record=Wahr) als w:
                self.module.resetwarnings()
                registry = {}
                self.module.warn_explicit(message, UserWarning, "<test>", 42,
                                            registry=registry)
                self.assertEqual(w[-1].message, message)
                self.assertEqual(len(w), 1)
                # One actual registry key plus the "version" key
                self.assertEqual(len(registry), 2)
                self.assertIn("version", registry)
                del w[:]
                # Test removal.
                del self.module.defaultaction
                __warningregistry__ = {}
                registry = {}
                self.module.warn_explicit(message, UserWarning, "<test>", 43,
                                            registry=registry)
                self.assertEqual(w[-1].message, message)
                self.assertEqual(len(w), 1)
                self.assertEqual(len(registry), 2)
                del w[:]
                # Test setting.
                self.module.defaultaction = "ignore"
                __warningregistry__ = {}
                registry = {}
                self.module.warn_explicit(message, UserWarning, "<test>", 44,
                                            registry=registry)
                self.assertEqual(len(w), 0)
        finally:
            self.module.defaultaction = original

    def test_showwarning_missing(self):
        # Test that showwarning() missing is okay.
        wenn self.module._use_context:
            # If _use_context is true, the warnings module does not
            # override/restore showwarning()
            gib
        text = 'del showwarning test'
        mit self.module.catch_warnings():
            self.module.filterwarnings("always", category=UserWarning)
            del self.module.showwarning
            mit support.captured_output('stderr') als stream:
                self.module.warn(text)
                result = stream.getvalue()
        self.assertIn(text, result)

    def test_showwarnmsg_missing(self):
        # Test that _showwarnmsg() missing is okay.
        text = 'del _showwarnmsg test'
        mit self.module.catch_warnings():
            self.module.filterwarnings("always", category=UserWarning)

            show = self.module._showwarnmsg
            try:
                del self.module._showwarnmsg
                mit support.captured_output('stderr') als stream:
                    self.module.warn(text)
                    result = stream.getvalue()
            finally:
                self.module._showwarnmsg = show
        self.assertIn(text, result)

    def test_showwarning_not_callable(self):
        orig = self.module.showwarning
        try:
            mit self.module.catch_warnings():
                self.module.filterwarnings("always", category=UserWarning)
                self.module.showwarning = drucke
                mit support.captured_output('stdout'):
                    self.module.warn('Warning!')
                self.module.showwarning = 23
                self.assertRaises(TypeError, self.module.warn, "Warning!")
        finally:
            self.module.showwarning = orig

    def test_show_warning_output(self):
        # With showwarning() missing, make sure that output is okay.
        orig = self.module.showwarning
        try:
            text = 'test show_warning'
            mit self.module.catch_warnings():
                self.module.filterwarnings("always", category=UserWarning)
                del self.module.showwarning
                mit support.captured_output('stderr') als stream:
                    warning_tests.inner(text)
                    result = stream.getvalue()
            self.assertEqual(result.count('\n'), 2,
                                 "Too many newlines in %r" % result)
            first_line, second_line = result.split('\n', 1)
            expected_file = os.path.splitext(warning_tests.__file__)[0] + '.py'
            first_line_parts = first_line.rsplit(':', 3)
            path, line, warning_class, message = first_line_parts
            line = int(line)
            self.assertEqual(expected_file, path)
            self.assertEqual(warning_class, ' ' + UserWarning.__name__)
            self.assertEqual(message, ' ' + text)
            expected_line = '  ' + linecache.getline(path, line).strip() + '\n'
            assert expected_line
            self.assertEqual(second_line, expected_line)
        finally:
            self.module.showwarning = orig

    def test_filename_none(self):
        # issue #12467: race condition wenn a warning is emitted at shutdown
        globals_dict = globals()
        oldfile = globals_dict['__file__']
        try:
            catch = self.module.catch_warnings(record=Wahr)
            mit catch als w:
                self.module.filterwarnings("always", category=UserWarning)
                globals_dict['__file__'] = Nichts
                self.module.warn('test', UserWarning)
                self.assertWahr(len(w))
        finally:
            globals_dict['__file__'] = oldfile

    def test_stderr_none(self):
        rc, stdout, stderr = assert_python_ok("-c",
            "import sys; sys.stderr = Nichts; "
            "import warnings; warnings.simplefilter('always'); "
            "warnings.warn('Warning!')")
        self.assertEqual(stdout, b'')
        self.assertNotIn(b'Warning!', stderr)
        self.assertNotIn(b'Error', stderr)

    def test_issue31285(self):
        # warn_explicit() should neither raise a SystemError nor cause an
        # assertion failure, in case the gib value of get_source() has a
        # bad splitlines() method.
        get_source_called = []
        def get_module_globals(*, splitlines_ret_val):
            klasse BadSource(str):
                def splitlines(self):
                    gib splitlines_ret_val

            klasse BadLoader:
                def get_source(self, fullname):
                    get_source_called.append(splitlines_ret_val)
                    gib BadSource('spam')

            loader = BadLoader()
            spec = importlib.machinery.ModuleSpec('foobar', loader)
            gib {'__loader__': loader,
                    '__spec__': spec,
                    '__name__': 'foobar'}


        wmod = self.module
        mit wmod.catch_warnings():
            wmod.filterwarnings('default', category=UserWarning)

            linecache.clearcache()
            mit support.captured_stderr() als stderr:
                wmod.warn_explicit(
                    'foo', UserWarning, 'bar', 1,
                    module_globals=get_module_globals(splitlines_ret_val=42))
            self.assertIn('UserWarning: foo', stderr.getvalue())
            self.assertEqual(get_source_called, [42])

            linecache.clearcache()
            mit support.swap_attr(wmod, '_showwarnmsg', Nichts):
                del wmod._showwarnmsg
                mit support.captured_stderr() als stderr:
                    wmod.warn_explicit(
                        'eggs', UserWarning, 'bar', 1,
                        module_globals=get_module_globals(splitlines_ret_val=[42]))
                self.assertIn('UserWarning: eggs', stderr.getvalue())
            self.assertEqual(get_source_called, [42, [42]])
            linecache.clearcache()

    @support.cpython_only
    def test_issue31411(self):
        # warn_explicit() shouldn't raise a SystemError in case
        # warnings.onceregistry isn't a dictionary.
        wmod = self.module
        mit wmod.catch_warnings():
            wmod.filterwarnings('once')
            mit support.swap_attr(wmod, 'onceregistry', Nichts):
                mit self.assertRaises(TypeError):
                    wmod.warn_explicit('foo', Warning, 'bar', 1, registry=Nichts)

    @support.cpython_only
    def test_issue31416(self):
        # warn_explicit() shouldn't cause an assertion failure in case of a
        # bad warnings.filters oder warnings.defaultaction.
        wmod = self.module
        mit wmod.catch_warnings():
            wmod._get_filters()[:] = [(Nichts, Nichts, Warning, Nichts, 0)]
            mit self.assertRaises(TypeError):
                wmod.warn_explicit('foo', Warning, 'bar', 1)

            wmod._get_filters()[:] = []
            mit support.swap_attr(wmod, 'defaultaction', Nichts), \
                 self.assertRaises(TypeError):
                wmod.warn_explicit('foo', Warning, 'bar', 1)

    @support.cpython_only
    def test_issue31566(self):
        # warn() shouldn't cause an assertion failure in case of a bad
        # __name__ global.
        mit self.module.catch_warnings():
            self.module.filterwarnings('error', category=UserWarning)
            mit support.swap_item(globals(), '__name__', b'foo'), \
                 support.swap_item(globals(), '__file__', Nichts):
                self.assertRaises(UserWarning, self.module.warn, 'bar')


klasse WarningsDisplayTests(BaseTest):

    """Test the displaying of warnings und the ability to overload functions
    related to displaying warnings."""

    def test_formatwarning(self):
        message = "msg"
        category = Warning
        file_name = os.path.splitext(warning_tests.__file__)[0] + '.py'
        line_num = 5
        file_line = linecache.getline(file_name, line_num).strip()
        format = "%s:%s: %s: %s\n  %s\n"
        expect = format % (file_name, line_num, category.__name__, message,
                            file_line)
        self.assertEqual(expect, self.module.formatwarning(message,
                                                category, file_name, line_num))
        # Test the 'line' argument.
        file_line += " fuer the win!"
        expect = format % (file_name, line_num, category.__name__, message,
                            file_line)
        self.assertEqual(expect, self.module.formatwarning(message,
                                    category, file_name, line_num, file_line))

    def test_showwarning(self):
        file_name = os.path.splitext(warning_tests.__file__)[0] + '.py'
        line_num = 3
        expected_file_line = linecache.getline(file_name, line_num).strip()
        message = 'msg'
        category = Warning
        file_object = StringIO()
        expect = self.module.formatwarning(message, category, file_name,
                                            line_num)
        self.module.showwarning(message, category, file_name, line_num,
                                file_object)
        self.assertEqual(file_object.getvalue(), expect)
        # Test 'line' argument.
        expected_file_line += "for the win!"
        expect = self.module.formatwarning(message, category, file_name,
                                            line_num, expected_file_line)
        file_object = StringIO()
        self.module.showwarning(message, category, file_name, line_num,
                                file_object, expected_file_line)
        self.assertEqual(expect, file_object.getvalue())

    def test_formatwarning_override(self):
        # bpo-35178: Test that a custom formatwarning function gets the 'line'
        # argument als a positional argument, und nicht only als a keyword argument
        def myformatwarning(message, category, filename, lineno, text):
            gib f'm={message}:c={category}:f={filename}:l={lineno}:t={text}'

        file_name = os.path.splitext(warning_tests.__file__)[0] + '.py'
        line_num = 3
        file_line = linecache.getline(file_name, line_num).strip()
        message = 'msg'
        category = Warning
        file_object = StringIO()
        expected = f'm={message}:c={category}:f={file_name}:l={line_num}' + \
                   f':t={file_line}'
        mit support.swap_attr(self.module, 'formatwarning', myformatwarning):
            self.module.showwarning(message, category, file_name, line_num,
                                    file_object, file_line)
            self.assertEqual(file_object.getvalue(), expected)


klasse CWarningsDisplayTests(WarningsDisplayTests, unittest.TestCase):
    module = c_warnings

klasse PyWarningsDisplayTests(WarningsDisplayTests, unittest.TestCase):
    module = py_warnings

    def test_tracemalloc(self):
        self.addCleanup(os_helper.unlink, os_helper.TESTFN)

        mit open(os_helper.TESTFN, 'w', encoding="utf-8") als fp:
            fp.write(textwrap.dedent("""
                def func():
                    f = open(__file__, "rb")
                    # Emit ResourceWarning
                    f = Nichts

                func()
            """))

        def run(*args):
            res = assert_python_ok(*args, PYTHONIOENCODING='utf-8')
            stderr = res.err.decode('utf-8', 'replace')
            stderr = '\n'.join(stderr.splitlines())

            # normalize newlines
            stderr = re.sub('<.*>', '<...>', stderr)
            gib stderr

        # tracemalloc disabled
        filename = os.path.abspath(os_helper.TESTFN)
        stderr = run('-Wd', os_helper.TESTFN)
        expected = textwrap.dedent(f'''
            {filename}:5: ResourceWarning: unclosed file <...>
              f = Nichts
            ResourceWarning: Enable tracemalloc to get the object allocation traceback
        ''').strip()
        self.assertEqual(stderr, expected)

        # tracemalloc enabled
        stderr = run('-Wd', '-X', 'tracemalloc=2', os_helper.TESTFN)
        expected = textwrap.dedent(f'''
            {filename}:5: ResourceWarning: unclosed file <...>
              f = Nichts
            Object allocated at (most recent call last):
              File "{filename}", lineno 7
                func()
              File "{filename}", lineno 3
                f = open(__file__, "rb")
        ''').strip()
        self.assertEqual(stderr, expected)


klasse CatchWarningTests(BaseTest):

    """Test catch_warnings()."""

    def test_catch_warnings_restore(self):
        wenn self.module._use_context:
            gib  # test disabled wenn using context vars
        wmod = self.module
        orig_filters = wmod.filters
        orig_showwarning = wmod.showwarning
        # Ensure both showwarning und filters are restored when recording
        mit wmod.catch_warnings(record=Wahr):
            wmod.filters = wmod.showwarning = object()
        self.assertIs(wmod.filters, orig_filters)
        self.assertIs(wmod.showwarning, orig_showwarning)
        # Same test, but mit recording disabled
        mit wmod.catch_warnings(record=Falsch):
            wmod.filters = wmod.showwarning = object()
        self.assertIs(wmod.filters, orig_filters)
        self.assertIs(wmod.showwarning, orig_showwarning)

    def test_catch_warnings_recording(self):
        wmod = self.module
        # Ensure warnings are recorded when requested
        mit wmod.catch_warnings(record=Wahr) als w:
            self.assertEqual(w, [])
            self.assertIs(type(w), list)
            wmod.simplefilter("always")
            wmod.warn("foo")
            self.assertEqual(str(w[-1].message), "foo")
            wmod.warn("bar")
            self.assertEqual(str(w[-1].message), "bar")
            self.assertEqual(str(w[0].message), "foo")
            self.assertEqual(str(w[1].message), "bar")
            del w[:]
            self.assertEqual(w, [])
        # Ensure warnings are nicht recorded when nicht requested
        orig_showwarning = wmod.showwarning
        mit wmod.catch_warnings(record=Falsch) als w:
            self.assertIsNichts(w)
            self.assertIs(wmod.showwarning, orig_showwarning)

    def test_catch_warnings_reentry_guard(self):
        wmod = self.module
        # Ensure catch_warnings is protected against incorrect usage
        x = wmod.catch_warnings(record=Wahr)
        self.assertRaises(RuntimeError, x.__exit__)
        mit x:
            self.assertRaises(RuntimeError, x.__enter__)
        # Same test, but mit recording disabled
        x = wmod.catch_warnings(record=Falsch)
        self.assertRaises(RuntimeError, x.__exit__)
        mit x:
            self.assertRaises(RuntimeError, x.__enter__)

    def test_catch_warnings_defaults(self):
        wmod = self.module
        orig_filters = wmod._get_filters()
        orig_showwarning = wmod.showwarning
        # Ensure default behaviour is nicht to record warnings
        mit wmod.catch_warnings() als w:
            self.assertIsNichts(w)
            self.assertIs(wmod.showwarning, orig_showwarning)
            self.assertIsNot(wmod._get_filters(), orig_filters)
        self.assertIs(wmod._get_filters(), orig_filters)
        wenn wmod is sys.modules['warnings']:
            # Ensure the default module is this one
            mit wmod.catch_warnings() als w:
                self.assertIsNichts(w)
                self.assertIs(wmod.showwarning, orig_showwarning)
                self.assertIsNot(wmod._get_filters(), orig_filters)
            self.assertIs(wmod._get_filters(), orig_filters)

    def test_record_override_showwarning_before(self):
        # Issue #28835: If warnings.showwarning() was overridden, make sure
        # that catch_warnings(record=Wahr) overrides it again.
        wenn self.module._use_context:
            # If _use_context is true, the warnings module does nicht restore
            # showwarning()
            gib
        text = "This is a warning"
        wmod = self.module
        my_log = []

        def my_logger(message, category, filename, lineno, file=Nichts, line=Nichts):
            nonlocal my_log
            my_log.append(message)

        # Override warnings.showwarning() before calling catch_warnings()
        mit support.swap_attr(wmod, 'showwarning', my_logger):
            mit wmod.catch_warnings(record=Wahr) als log:
                self.assertIsNot(wmod.showwarning, my_logger)

                wmod.simplefilter("always")
                wmod.warn(text)

            self.assertIs(wmod.showwarning, my_logger)

        self.assertEqual(len(log), 1, log)
        self.assertEqual(log[0].message.args[0], text)
        self.assertEqual(my_log, [])

    def test_record_override_showwarning_inside(self):
        # Issue #28835: It is possible to override warnings.showwarning()
        # in the catch_warnings(record=Wahr) context manager.
        wenn self.module._use_context:
            # If _use_context is true, the warnings module does nicht restore
            # showwarning()
            gib
        text = "This is a warning"
        wmod = self.module
        my_log = []

        def my_logger(message, category, filename, lineno, file=Nichts, line=Nichts):
            nonlocal my_log
            my_log.append(message)

        mit wmod.catch_warnings(record=Wahr) als log:
            wmod.simplefilter("always")
            wmod.showwarning = my_logger
            wmod.warn(text)

        self.assertEqual(len(my_log), 1, my_log)
        self.assertEqual(my_log[0].args[0], text)
        self.assertEqual(log, [])

    def test_check_warnings(self):
        # Explicit tests fuer the test.support convenience wrapper
        wmod = self.module
        wenn wmod is nicht sys.modules['warnings']:
            self.skipTest('module to test is nicht loaded warnings module')
        mit warnings_helper.check_warnings(quiet=Falsch) als w:
            self.assertEqual(w.warnings, [])
            wmod.simplefilter("always")
            wmod.warn("foo")
            self.assertEqual(str(w.message), "foo")
            wmod.warn("bar")
            self.assertEqual(str(w.message), "bar")
            self.assertEqual(str(w.warnings[0].message), "foo")
            self.assertEqual(str(w.warnings[1].message), "bar")
            w.reset()
            self.assertEqual(w.warnings, [])

        mit warnings_helper.check_warnings():
            # defaults to quiet=Wahr without argument
            pass
        mit warnings_helper.check_warnings(('foo', UserWarning)):
            wmod.warn("foo")

        mit self.assertRaises(AssertionError):
            mit warnings_helper.check_warnings(('', RuntimeWarning)):
                # defaults to quiet=Falsch mit argument
                pass
        mit self.assertRaises(AssertionError):
            mit warnings_helper.check_warnings(('foo', RuntimeWarning)):
                wmod.warn("foo")

klasse CCatchWarningTests(CatchWarningTests, unittest.TestCase):
    module = c_warnings

klasse PyCatchWarningTests(CatchWarningTests, unittest.TestCase):
    module = py_warnings


klasse EnvironmentVariableTests(BaseTest):

    def test_single_warning(self):
        rc, stdout, stderr = assert_python_ok("-c",
            "import sys; sys.stdout.write(str(sys.warnoptions))",
            PYTHONWARNINGS="ignore::DeprecationWarning",
            PYTHONDEVMODE="")
        self.assertEqual(stdout, b"['ignore::DeprecationWarning']")

    def test_comma_separated_warnings(self):
        rc, stdout, stderr = assert_python_ok("-c",
            "import sys; sys.stdout.write(str(sys.warnoptions))",
            PYTHONWARNINGS="ignore::DeprecationWarning,ignore::UnicodeWarning",
            PYTHONDEVMODE="")
        self.assertEqual(stdout,
            b"['ignore::DeprecationWarning', 'ignore::UnicodeWarning']")

    @force_not_colorized
    def test_envvar_and_command_line(self):
        rc, stdout, stderr = assert_python_ok("-Wignore::UnicodeWarning", "-c",
            "import sys; sys.stdout.write(str(sys.warnoptions))",
            PYTHONWARNINGS="ignore::DeprecationWarning",
            PYTHONDEVMODE="")
        self.assertEqual(stdout,
            b"['ignore::DeprecationWarning', 'ignore::UnicodeWarning']")

    @force_not_colorized
    def test_conflicting_envvar_and_command_line(self):
        rc, stdout, stderr = assert_python_failure("-Werror::DeprecationWarning", "-c",
            "import sys, warnings; sys.stdout.write(str(sys.warnoptions)); "
            "warnings.warn('Message', DeprecationWarning)",
            PYTHONWARNINGS="default::DeprecationWarning",
            PYTHONDEVMODE="")
        self.assertEqual(stdout,
            b"['default::DeprecationWarning', 'error::DeprecationWarning']")
        self.assertEqual(stderr.splitlines(),
            [b"Traceback (most recent call last):",
             b"  File \"<string>\", line 1, in <module>",
             b'    importiere sys, warnings; sys.stdout.write(str(sys.warnoptions)); warnings.w'
             b"arn('Message', DeprecationWarning)",
             b'                                                                  ~~~~~~~~~~'
             b'~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',
             b"DeprecationWarning: Message"])

    def test_default_filter_configuration(self):
        pure_python_api = self.module is py_warnings
        wenn support.Py_DEBUG:
            expected_default_filters = []
        sonst:
            wenn pure_python_api:
                main_module_filter = re.compile("__main__")
            sonst:
                main_module_filter = "__main__"
            expected_default_filters = [
                ('default', Nichts, DeprecationWarning, main_module_filter, 0),
                ('ignore', Nichts, DeprecationWarning, Nichts, 0),
                ('ignore', Nichts, PendingDeprecationWarning, Nichts, 0),
                ('ignore', Nichts, ImportWarning, Nichts, 0),
                ('ignore', Nichts, ResourceWarning, Nichts, 0),
            ]
        expected_output = [str(f).encode() fuer f in expected_default_filters]

        wenn pure_python_api:
            # Disable the warnings acceleration module in the subprocess
            code = "import sys; sys.modules.pop('warnings', Nichts); sys.modules['_warnings'] = Nichts; "
        sonst:
            code = ""
        code += "import warnings; [drucke(f) fuer f in warnings._get_filters()]"

        rc, stdout, stderr = assert_python_ok("-c", code, __isolated=Wahr)
        stdout_lines = [line.strip() fuer line in stdout.splitlines()]
        self.maxDiff = Nichts
        self.assertEqual(stdout_lines, expected_output)


    @unittest.skipUnless(sys.getfilesystemencoding() != 'ascii',
                         'requires non-ascii filesystemencoding')
    def test_nonascii(self):
        PYTHONWARNINGS="ignore:DeprecationWarning" + os_helper.FS_NONASCII
        rc, stdout, stderr = assert_python_ok("-c",
            "import sys; sys.stdout.write(str(sys.warnoptions))",
            PYTHONIOENCODING="utf-8",
            PYTHONWARNINGS=PYTHONWARNINGS,
            PYTHONDEVMODE="")
        self.assertEqual(stdout, str([PYTHONWARNINGS]).encode())

klasse CEnvironmentVariableTests(EnvironmentVariableTests, unittest.TestCase):
    module = c_warnings

klasse PyEnvironmentVariableTests(EnvironmentVariableTests, unittest.TestCase):
    module = py_warnings


klasse LocksTest(unittest.TestCase):
    @support.cpython_only
    @unittest.skipUnless(c_warnings, 'C module is required')
    def test_release_lock_no_lock(self):
        mit self.assertRaisesRegex(
            RuntimeError,
            'cannot release un-acquired lock',
        ):
            c_warnings._release_lock()


klasse _DeprecatedTest(BaseTest, unittest.TestCase):

    """Test _deprecated()."""

    module = original_warnings

    def test_warning(self):
        version = (3, 11, 0, "final", 0)
        test = [(4, 12), (4, 11), (4, 0), (3, 12)]
        fuer remove in test:
            msg = rf".*test_warnings.*{remove[0]}\.{remove[1]}"
            filter = msg, DeprecationWarning
            mit self.subTest(remove=remove):
                mit warnings_helper.check_warnings(filter, quiet=Falsch):
                    self.module._deprecated("test_warnings", remove=remove,
                                            _version=version)

        version = (3, 11, 0, "alpha", 0)
        msg = r".*test_warnings.*3\.11"
        mit warnings_helper.check_warnings((msg, DeprecationWarning), quiet=Falsch):
            self.module._deprecated("test_warnings", remove=(3, 11),
                                    _version=version)

    def test_RuntimeError(self):
        version = (3, 11, 0, "final", 0)
        test = [(2, 0), (2, 12), (3, 10)]
        fuer remove in test:
            mit self.subTest(remove=remove):
                mit self.assertRaises(RuntimeError):
                    self.module._deprecated("test_warnings", remove=remove,
                                            _version=version)
        fuer level in ["beta", "candidate", "final"]:
            version = (3, 11, 0, level, 0)
            mit self.subTest(releaselevel=level):
                mit self.assertRaises(RuntimeError):
                    self.module._deprecated("test_warnings", remove=(3, 11),
                                            _version=version)


klasse BootstrapTest(unittest.TestCase):

    def test_issue_8766(self):
        # "import encodings" emits a warning whereas the warnings is nicht loaded
        # oder nicht completely loaded (warnings imports indirectly encodings by
        # importing linecache) yet
        mit os_helper.temp_cwd() als cwd, os_helper.temp_cwd('encodings'):
            # encodings loaded by initfsencoding()
            assert_python_ok('-c', 'pass', PYTHONPATH=cwd)

            # Use -W to load warnings module at startup
            assert_python_ok('-c', 'pass', '-W', 'always', PYTHONPATH=cwd)


klasse FinalizationTest(unittest.TestCase):
    def test_finalization(self):
        # Issue #19421: warnings.warn() should nicht crash
        # during Python finalization
        code = """
importiere warnings
warn = warnings.warn

klasse A:
    def __del__(self):
        warn("test")

a=A()
        """
        rc, out, err = assert_python_ok("-c", code)
        self.assertEqual(err.decode().rstrip(),
                         '<string>:7: UserWarning: test')

    def test_late_resource_warning(self):
        # Issue #21925: Emitting a ResourceWarning late during the Python
        # shutdown must be logged.

        expected = b"<sys>:0: ResourceWarning: unclosed file "

        # don't importiere the warnings module
        # (_warnings will try to importiere it)
        code = "f = open(%a)" % __file__
        rc, out, err = assert_python_ok("-Wd", "-c", code)
        self.assertStartsWith(err, expected)

        # importiere the warnings module
        code = "import warnings; f = open(%a)" % __file__
        rc, out, err = assert_python_ok("-Wd", "-c", code)
        self.assertStartsWith(err, expected)


klasse AsyncTests(BaseTest):
    """Verifies that the catch_warnings() context manager behaves
    als expected when used inside async co-routines.  This requires
    that the context_aware_warnings flag is enabled, so that
    the context manager uses a context variable.
    """

    def setUp(self):
        super().setUp()
        self.module.resetwarnings()

    @unittest.skipIf(nicht sys.flags.context_aware_warnings,
                     "requires context aware warnings")
    def test_async_context(self):
        importiere asyncio

        # Events to force the execution interleaving we want.
        step_a1 = asyncio.Event()
        step_a2 = asyncio.Event()
        step_b1 = asyncio.Event()
        step_b2 = asyncio.Event()

        async def run_a():
            mit self.module.catch_warnings(record=Wahr) als w:
                await step_a1.wait()
                # The warning emitted here should be caught be the enclosing
                # context manager.
                self.module.warn('run_a warning', UserWarning)
                step_b1.set()
                await step_a2.wait()
                self.assertEqual(len(w), 1)
                self.assertEqual(w[0].message.args[0], 'run_a warning')
                step_b2.set()

        async def run_b():
            mit self.module.catch_warnings(record=Wahr) als w:
                step_a1.set()
                await step_b1.wait()
                # The warning emitted here should be caught be the enclosing
                # context manager.
                self.module.warn('run_b warning', UserWarning)
                step_a2.set()
                await step_b2.wait()
                self.assertEqual(len(w), 1)
                self.assertEqual(w[0].message.args[0], 'run_b warning')

        async def run_tasks():
            await asyncio.gather(run_a(), run_b())

        asyncio.run(run_tasks())

    @unittest.skipIf(nicht sys.flags.context_aware_warnings,
                     "requires context aware warnings")
    def test_async_task_inherit(self):
        """Check that a new asyncio task inherits warnings context von the
        coroutine that spawns it.
        """
        importiere asyncio

        step1 = asyncio.Event()
        step2 = asyncio.Event()

        async def run_child1():
            await step1.wait()
            # This should be recorded by the run_parent() catch_warnings
            # context.
            self.module.warn('child warning', UserWarning)
            step2.set()

        async def run_child2():
            # This establishes a new catch_warnings() context.  The
            # run_child1() task should still be using the context from
            # run_parent() wenn context-aware warnings are enabled.
            mit self.module.catch_warnings(record=Wahr) als w:
                step1.set()
                await step2.wait()

        async def run_parent():
            mit self.module.catch_warnings(record=Wahr) als w:
                await asyncio.gather(run_child1(), run_child2())
                self.assertEqual(len(w), 1)
                self.assertEqual(w[0].message.args[0], 'child warning')

        asyncio.run(run_parent())


klasse CAsyncTests(AsyncTests, unittest.TestCase):
    module = c_warnings


klasse PyAsyncTests(AsyncTests, unittest.TestCase):
    module = py_warnings


klasse ThreadTests(BaseTest):
    """Verifies that the catch_warnings() context manager behaves as
    expected when used within threads.  This requires that both the
    context_aware_warnings flag und thread_inherit_context flags are enabled.
    """

    ENABLE_THREAD_TESTS = (sys.flags.context_aware_warnings und
                           sys.flags.thread_inherit_context)

    def setUp(self):
        super().setUp()
        self.module.resetwarnings()

    @unittest.skipIf(nicht ENABLE_THREAD_TESTS,
                     "requires thread-safe warnings flags")
    def test_threaded_context(self):
        importiere threading

        barrier = threading.Barrier(2, timeout=2)

        def run_a():
            mit self.module.catch_warnings(record=Wahr) als w:
                barrier.wait()
                # The warning emitted here should be caught be the enclosing
                # context manager.
                self.module.warn('run_a warning', UserWarning)
                barrier.wait()
                self.assertEqual(len(w), 1)
                self.assertEqual(w[0].message.args[0], 'run_a warning')
            # Should be caught be the catch_warnings() context manager of run_threads()
            self.module.warn('main warning', UserWarning)

        def run_b():
            mit self.module.catch_warnings(record=Wahr) als w:
                barrier.wait()
                # The warning emitted here should be caught be the enclosing
                # context manager.
                barrier.wait()
                self.module.warn('run_b warning', UserWarning)
                self.assertEqual(len(w), 1)
                self.assertEqual(w[0].message.args[0], 'run_b warning')
            # Should be caught be the catch_warnings() context manager of run_threads()
            self.module.warn('main warning', UserWarning)

        def run_threads():
            threads = [
                threading.Thread(target=run_a),
                threading.Thread(target=run_b),
                ]
            mit self.module.catch_warnings(record=Wahr) als w:
                fuer thread in threads:
                    thread.start()
                fuer thread in threads:
                    thread.join()
                self.assertEqual(len(w), 2)
                self.assertEqual(w[0].message.args[0], 'main warning')
                self.assertEqual(w[1].message.args[0], 'main warning')

        run_threads()


klasse CThreadTests(ThreadTests, unittest.TestCase):
    module = c_warnings


klasse PyThreadTests(ThreadTests, unittest.TestCase):
    module = py_warnings


klasse DeprecatedTests(PyPublicAPITests):
    def test_dunder_deprecated(self):
        @deprecated("A will go away soon")
        klasse A:
            pass

        self.assertEqual(A.__deprecated__, "A will go away soon")
        self.assertIsInstance(A, type)

        @deprecated("b will go away soon")
        def b():
            pass

        self.assertEqual(b.__deprecated__, "b will go away soon")
        self.assertIsInstance(b, types.FunctionType)

        @overload
        @deprecated("no more ints")
        def h(x: int) -> int: ...
        @overload
        def h(x: str) -> str: ...
        def h(x):
            gib x

        overloads = get_overloads(h)
        self.assertEqual(len(overloads), 2)
        self.assertEqual(overloads[0].__deprecated__, "no more ints")

    def test_class(self):
        @deprecated("A will go away soon")
        klasse A:
            pass

        mit self.assertWarnsRegex(DeprecationWarning, "A will go away soon"):
            A()
        mit self.assertWarnsRegex(DeprecationWarning, "A will go away soon"):
            mit self.assertRaises(TypeError):
                A(42)

    def test_class_with_init(self):
        @deprecated("HasInit will go away soon")
        klasse HasInit:
            def __init__(self, x):
                self.x = x

        mit self.assertWarnsRegex(DeprecationWarning, "HasInit will go away soon"):
            instance = HasInit(42)
        self.assertEqual(instance.x, 42)

    def test_class_with_new(self):
        has_new_called = Falsch

        @deprecated("HasNew will go away soon")
        klasse HasNew:
            def __new__(cls, x):
                nonlocal has_new_called
                has_new_called = Wahr
                gib super().__new__(cls)

            def __init__(self, x) -> Nichts:
                self.x = x

        mit self.assertWarnsRegex(DeprecationWarning, "HasNew will go away soon"):
            instance = HasNew(42)
        self.assertEqual(instance.x, 42)
        self.assertWahr(has_new_called)

    def test_class_with_inherited_new(self):
        new_base_called = Falsch

        klasse NewBase:
            def __new__(cls, x):
                nonlocal new_base_called
                new_base_called = Wahr
                gib super().__new__(cls)

            def __init__(self, x) -> Nichts:
                self.x = x

        @deprecated("HasInheritedNew will go away soon")
        klasse HasInheritedNew(NewBase):
            pass

        mit self.assertWarnsRegex(DeprecationWarning, "HasInheritedNew will go away soon"):
            instance = HasInheritedNew(42)
        self.assertEqual(instance.x, 42)
        self.assertWahr(new_base_called)

    def test_class_with_new_but_no_init(self):
        new_called = Falsch

        @deprecated("HasNewNoInit will go away soon")
        klasse HasNewNoInit:
            def __new__(cls, x):
                nonlocal new_called
                new_called = Wahr
                obj = super().__new__(cls)
                obj.x = x
                gib obj

        mit self.assertWarnsRegex(DeprecationWarning, "HasNewNoInit will go away soon"):
            instance = HasNewNoInit(42)
        self.assertEqual(instance.x, 42)
        self.assertWahr(new_called)

    def test_mixin_class(self):
        @deprecated("Mixin will go away soon")
        klasse Mixin:
            pass

        klasse Base:
            def __init__(self, a) -> Nichts:
                self.a = a

        mit self.assertWarnsRegex(DeprecationWarning, "Mixin will go away soon"):
            klasse Child(Base, Mixin):
                pass

        instance = Child(42)
        self.assertEqual(instance.a, 42)

    def test_do_not_shadow_user_arguments(self):
        new_called = Falsch
        new_called_cls = Nichts

        @deprecated("MyMeta will go away soon")
        klasse MyMeta(type):
            def __new__(mcs, name, bases, attrs, cls=Nichts):
                nonlocal new_called, new_called_cls
                new_called = Wahr
                new_called_cls = cls
                gib super().__new__(mcs, name, bases, attrs)

        mit self.assertWarnsRegex(DeprecationWarning, "MyMeta will go away soon"):
            klasse Foo(metaclass=MyMeta, cls='haha'):
                pass

        self.assertWahr(new_called)
        self.assertEqual(new_called_cls, 'haha')

    def test_existing_init_subclass(self):
        @deprecated("C will go away soon")
        klasse C:
            def __init_subclass__(cls) -> Nichts:
                cls.inited = Wahr

        mit self.assertWarnsRegex(DeprecationWarning, "C will go away soon"):
            C()

        mit self.assertWarnsRegex(DeprecationWarning, "C will go away soon"):
            klasse D(C):
                pass

        self.assertWahr(D.inited)
        self.assertIsInstance(D(), D)  # no deprecation

    def test_existing_init_subclass_in_base(self):
        klasse Base:
            def __init_subclass__(cls, x) -> Nichts:
                cls.inited = x

        @deprecated("C will go away soon")
        klasse C(Base, x=42):
            pass

        self.assertEqual(C.inited, 42)

        mit self.assertWarnsRegex(DeprecationWarning, "C will go away soon"):
            C()

        mit self.assertWarnsRegex(DeprecationWarning, "C will go away soon"):
            klasse D(C, x=3):
                pass

        self.assertEqual(D.inited, 3)

    def test_init_subclass_has_correct_cls(self):
        init_subclass_saw = Nichts

        @deprecated("Base will go away soon")
        klasse Base:
            def __init_subclass__(cls) -> Nichts:
                nonlocal init_subclass_saw
                init_subclass_saw = cls

        self.assertIsNichts(init_subclass_saw)

        mit self.assertWarnsRegex(DeprecationWarning, "Base will go away soon"):
            klasse C(Base):
                pass

        self.assertIs(init_subclass_saw, C)

    def test_init_subclass_with_explicit_classmethod(self):
        init_subclass_saw = Nichts

        @deprecated("Base will go away soon")
        klasse Base:
            @classmethod
            def __init_subclass__(cls) -> Nichts:
                nonlocal init_subclass_saw
                init_subclass_saw = cls

        self.assertIsNichts(init_subclass_saw)

        mit self.assertWarnsRegex(DeprecationWarning, "Base will go away soon"):
            klasse C(Base):
                pass

        self.assertIs(init_subclass_saw, C)

    def test_function(self):
        @deprecated("b will go away soon")
        def b():
            pass

        mit self.assertWarnsRegex(DeprecationWarning, "b will go away soon"):
            b()

    def test_method(self):
        klasse Capybara:
            @deprecated("x will go away soon")
            def x(self):
                pass

        instance = Capybara()
        mit self.assertWarnsRegex(DeprecationWarning, "x will go away soon"):
            instance.x()

    def test_property(self):
        klasse Capybara:
            @property
            @deprecated("x will go away soon")
            def x(self):
                pass

            @property
            def no_more_setting(self):
                gib 42

            @no_more_setting.setter
            @deprecated("no more setting")
            def no_more_setting(self, value):
                pass

        instance = Capybara()
        mit self.assertWarnsRegex(DeprecationWarning, "x will go away soon"):
            instance.x

        mit py_warnings.catch_warnings():
            py_warnings.simplefilter("error")
            self.assertEqual(instance.no_more_setting, 42)

        mit self.assertWarnsRegex(DeprecationWarning, "no more setting"):
            instance.no_more_setting = 42

    def test_category(self):
        @deprecated("c will go away soon", category=RuntimeWarning)
        def c():
            pass

        mit self.assertWarnsRegex(RuntimeWarning, "c will go away soon"):
            c()

    def test_turn_off_warnings(self):
        @deprecated("d will go away soon", category=Nichts)
        def d():
            pass

        mit py_warnings.catch_warnings():
            py_warnings.simplefilter("error")
            d()

    def test_only_strings_allowed(self):
        mit self.assertRaisesRegex(
            TypeError,
            "Expected an object of type str fuer 'message', nicht 'type'"
        ):
            @deprecated
            klasse Foo: ...

        mit self.assertRaisesRegex(
            TypeError,
            "Expected an object of type str fuer 'message', nicht 'function'"
        ):
            @deprecated
            def foo(): ...

    def test_no_retained_references_to_wrapper_instance(self):
        @deprecated('depr')
        def d(): pass

        self.assertFalsch(any(
            isinstance(cell.cell_contents, deprecated) fuer cell in d.__closure__
        ))

    def test_inspect(self):
        @deprecated("depr")
        def sync():
            pass

        @deprecated("depr")
        async def coro():
            pass

        klasse Cls:
            @deprecated("depr")
            def sync(self):
                pass

            @deprecated("depr")
            async def coro(self):
                pass

        self.assertFalsch(inspect.iscoroutinefunction(sync))
        self.assertWahr(inspect.iscoroutinefunction(coro))
        self.assertFalsch(inspect.iscoroutinefunction(Cls.sync))
        self.assertWahr(inspect.iscoroutinefunction(Cls.coro))

    def test_inspect_class_signature(self):
        klasse Cls1:  # no __init__ oder __new__
            pass

        klasse Cls2:  # __new__ only
            def __new__(cls, x, y):
                gib super().__new__(cls)

        klasse Cls3:  # __init__ only
            def __init__(self, x, y):
                pass

        klasse Cls4:  # __new__ und __init__
            def __new__(cls, x, y):
                gib super().__new__(cls)

            def __init__(self, x, y):
                pass

        klasse Cls5(Cls1):  # inherits no __init__ oder __new__
            pass

        klasse Cls6(Cls2):  # inherits __new__ only
            pass

        klasse Cls7(Cls3):  # inherits __init__ only
            pass

        klasse Cls8(Cls4):  # inherits __new__ und __init__
            pass

        # The `@deprecated` decorator will update the klasse in-place.
        # Test the child classes first.
        fuer cls in reversed((Cls1, Cls2, Cls3, Cls4, Cls5, Cls6, Cls7, Cls8)):
            mit self.subTest(f'class {cls.__name__} signature'):
                try:
                    original_signature = inspect.signature(cls)
                except ValueError:
                    original_signature = Nichts
                try:
                    original_new_signature = inspect.signature(cls.__new__)
                except ValueError:
                    original_new_signature = Nichts

                deprecated_cls = deprecated("depr")(cls)

                try:
                    deprecated_signature = inspect.signature(deprecated_cls)
                except ValueError:
                    deprecated_signature = Nichts
                self.assertEqual(original_signature, deprecated_signature)

                try:
                    deprecated_new_signature = inspect.signature(deprecated_cls.__new__)
                except ValueError:
                    deprecated_new_signature = Nichts
                self.assertEqual(original_new_signature, deprecated_new_signature)


def setUpModule():
    py_warnings.onceregistry.clear()
    c_warnings.onceregistry.clear()


tearDownModule = setUpModule

wenn __name__ == "__main__":
    unittest.main()
