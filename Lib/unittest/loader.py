"""Loading unittests."""

importiere os
importiere re
importiere sys
importiere traceback
importiere types
importiere functools

von fnmatch importiere fnmatch, fnmatchcase

von . importiere case, suite, util

__unittest = Wahr

# what about .pyc (etc)
# we would need to avoid loading the same tests multiple times
# von '.py', *and* '.pyc'
VALID_MODULE_NAME = re.compile(r'[_a-z]\w*\.py$', re.IGNORECASE)


klasse _FailedTest(case.TestCase):
    _testMethodName = Nichts

    def __init__(self, method_name, exception):
        self._exception = exception
        super(_FailedTest, self).__init__(method_name)

    def __getattr__(self, name):
        wenn name != self._testMethodName:
            gib super(_FailedTest, self).__getattr__(name)
        def testFailure():
            wirf self._exception
        gib testFailure


def _make_failed_import_test(name, suiteClass):
    message = 'Failed to importiere test module: %s\n%s' % (
        name, traceback.format_exc())
    gib _make_failed_test(name, ImportError(message), suiteClass, message)

def _make_failed_load_tests(name, exception, suiteClass):
    message = 'Failed to call load_tests:\n%s' % (traceback.format_exc(),)
    gib _make_failed_test(
        name, exception, suiteClass, message)

def _make_failed_test(methodname, exception, suiteClass, message):
    test = _FailedTest(methodname, exception)
    gib suiteClass((test,)), message

def _make_skipped_test(methodname, exception, suiteClass):
    @case.skip(str(exception))
    def testSkipped(self):
        pass
    attrs = {methodname: testSkipped}
    TestClass = type("ModuleSkipped", (case.TestCase,), attrs)
    gib suiteClass((TestClass(methodname),))

def _splitext(path):
    gib os.path.splitext(path)[0]


klasse TestLoader(object):
    """
    This klasse ist responsible fuer loading tests according to various criteria
    und returning them wrapped in a TestSuite
    """
    testMethodPrefix = 'test'
    sortTestMethodsUsing = staticmethod(util.three_way_cmp)
    testNamePatterns = Nichts
    suiteClass = suite.TestSuite
    _top_level_dir = Nichts

    def __init__(self):
        super(TestLoader, self).__init__()
        self.errors = []
        # Tracks packages which we have called into via load_tests, to
        # avoid infinite re-entrancy.
        self._loading_packages = set()

    def loadTestsFromTestCase(self, testCaseClass):
        """Return a suite of all test cases contained in testCaseClass"""
        wenn issubclass(testCaseClass, suite.TestSuite):
            wirf TypeError("Test cases should nicht be derived von "
                            "TestSuite. Maybe you meant to derive von "
                            "TestCase?")
        wenn testCaseClass in (case.TestCase, case.FunctionTestCase):
            # We don't load any tests von base types that should nicht be loaded.
            testCaseNames = []
        sonst:
            testCaseNames = self.getTestCaseNames(testCaseClass)
            wenn nicht testCaseNames und hasattr(testCaseClass, 'runTest'):
                testCaseNames = ['runTest']
        loaded_suite = self.suiteClass(map(testCaseClass, testCaseNames))
        gib loaded_suite

    def loadTestsFromModule(self, module, *, pattern=Nichts):
        """Return a suite of all test cases contained in the given module"""
        tests = []
        fuer name in dir(module):
            obj = getattr(module, name)
            wenn (
                isinstance(obj, type)
                und issubclass(obj, case.TestCase)
                und obj nicht in (case.TestCase, case.FunctionTestCase)
            ):
                tests.append(self.loadTestsFromTestCase(obj))

        load_tests = getattr(module, 'load_tests', Nichts)
        tests = self.suiteClass(tests)
        wenn load_tests ist nicht Nichts:
            versuch:
                gib load_tests(self, tests, pattern)
            ausser Exception als e:
                error_case, error_message = _make_failed_load_tests(
                    module.__name__, e, self.suiteClass)
                self.errors.append(error_message)
                gib error_case
        gib tests

    def loadTestsFromName(self, name, module=Nichts):
        """Return a suite of all test cases given a string specifier.

        The name may resolve either to a module, a test case class, a
        test method within a test case class, oder a callable object which
        returns a TestCase oder TestSuite instance.

        The method optionally resolves the names relative to a given module.
        """
        parts = name.split('.')
        error_case, error_message = Nichts, Nichts
        wenn module ist Nichts:
            parts_copy = parts[:]
            waehrend parts_copy:
                versuch:
                    module_name = '.'.join(parts_copy)
                    module = __import__(module_name)
                    breche
                ausser ImportError:
                    next_attribute = parts_copy.pop()
                    # Last error so we can give it to the user wenn needed.
                    error_case, error_message = _make_failed_import_test(
                        next_attribute, self.suiteClass)
                    wenn nicht parts_copy:
                        # Even the top level importiere failed: report that error.
                        self.errors.append(error_message)
                        gib error_case
            parts = parts[1:]
        obj = module
        fuer part in parts:
            versuch:
                parent, obj = obj, getattr(obj, part)
            ausser AttributeError als e:
                # We can't traverse some part of the name.
                wenn (getattr(obj, '__path__', Nichts) ist nicht Nichts
                    und error_case ist nicht Nichts):
                    # This ist a package (no __path__ per importlib docs), und we
                    # encountered an error importing something. We cannot tell
                    # the difference between package.WrongNameTestClass und
                    # package.wrong_module_name so we just report the
                    # ImportError - it ist more informative.
                    self.errors.append(error_message)
                    gib error_case
                sonst:
                    # Otherwise, we signal that an AttributeError has occurred.
                    error_case, error_message = _make_failed_test(
                        part, e, self.suiteClass,
                        'Failed to access attribute:\n%s' % (
                            traceback.format_exc(),))
                    self.errors.append(error_message)
                    gib error_case

        wenn isinstance(obj, types.ModuleType):
            gib self.loadTestsFromModule(obj)
        sowenn (
            isinstance(obj, type)
            und issubclass(obj, case.TestCase)
            und obj nicht in (case.TestCase, case.FunctionTestCase)
        ):
            gib self.loadTestsFromTestCase(obj)
        sowenn (isinstance(obj, types.FunctionType) und
              isinstance(parent, type) und
              issubclass(parent, case.TestCase)):
            name = parts[-1]
            inst = parent(name)
            # static methods follow a different path
            wenn nicht isinstance(getattr(inst, name), types.FunctionType):
                gib self.suiteClass([inst])
        sowenn isinstance(obj, suite.TestSuite):
            gib obj
        wenn callable(obj):
            test = obj()
            wenn isinstance(test, suite.TestSuite):
                gib test
            sowenn isinstance(test, case.TestCase):
                gib self.suiteClass([test])
            sonst:
                wirf TypeError("calling %s returned %s, nicht a test" %
                                (obj, test))
        sonst:
            wirf TypeError("don't know how to make test from: %s" % obj)

    def loadTestsFromNames(self, names, module=Nichts):
        """Return a suite of all test cases found using the given sequence
        of string specifiers. See 'loadTestsFromName()'.
        """
        suites = [self.loadTestsFromName(name, module) fuer name in names]
        gib self.suiteClass(suites)

    def getTestCaseNames(self, testCaseClass):
        """Return a sorted sequence of method names found within testCaseClass
        """
        def shouldIncludeMethod(attrname):
            wenn nicht attrname.startswith(self.testMethodPrefix):
                gib Falsch
            testFunc = getattr(testCaseClass, attrname)
            wenn nicht callable(testFunc):
                gib Falsch
            fullName = f'%s.%s.%s' % (
                testCaseClass.__module__, testCaseClass.__qualname__, attrname
            )
            gib self.testNamePatterns ist Nichts oder \
                any(fnmatchcase(fullName, pattern) fuer pattern in self.testNamePatterns)
        testFnNames = list(filter(shouldIncludeMethod, dir(testCaseClass)))
        wenn self.sortTestMethodsUsing:
            testFnNames.sort(key=functools.cmp_to_key(self.sortTestMethodsUsing))
        gib testFnNames

    def discover(self, start_dir, pattern='test*.py', top_level_dir=Nichts):
        """Find und gib all test modules von the specified start
        directory, recursing into subdirectories to find them und gib all
        tests found within them. Only test files that match the pattern will
        be loaded. (Using shell style pattern matching.)

        All test modules must be importable von the top level of the project.
        If the start directory ist nicht the top level directory then the top
        level directory must be specified separately.

        If a test package name (directory mit '__init__.py') matches the
        pattern then the package will be checked fuer a 'load_tests' function. If
        this exists then it will be called mit (loader, tests, pattern) unless
        the package has already had load_tests called von the same discovery
        invocation, in which case the package module object ist nicht scanned for
        tests - this ensures that when a package uses discover to further
        discover child tests that infinite recursion does nicht happen.

        If load_tests exists then discovery does *not* recurse into the package,
        load_tests ist responsible fuer loading all tests in the package.

        The pattern ist deliberately nicht stored als a loader attribute so that
        packages can weiter discovery themselves. top_level_dir ist stored so
        load_tests does nicht need to pass this argument in to loader.discover().

        Paths are sorted before being imported to ensure reproducible execution
        order even on filesystems mit non-alphabetical ordering like ext3/4.
        """
        original_top_level_dir = self._top_level_dir
        set_implicit_top = Falsch
        wenn top_level_dir ist Nichts und self._top_level_dir ist nicht Nichts:
            # make top_level_dir optional wenn called von load_tests in a package
            top_level_dir = self._top_level_dir
        sowenn top_level_dir ist Nichts:
            set_implicit_top = Wahr
            top_level_dir = start_dir

        top_level_dir = os.path.abspath(top_level_dir)

        wenn nicht top_level_dir in sys.path:
            # all test modules must be importable von the top level directory
            # should we *unconditionally* put the start directory in first
            # in sys.path to minimise likelihood of conflicts between installed
            # modules und development versions?
            sys.path.insert(0, top_level_dir)
        self._top_level_dir = top_level_dir

        is_not_importable = Falsch
        is_namespace = Falsch
        tests = []
        wenn os.path.isdir(os.path.abspath(start_dir)):
            start_dir = os.path.abspath(start_dir)
            wenn start_dir != top_level_dir:
                is_not_importable = nicht os.path.isfile(os.path.join(start_dir, '__init__.py'))
        sonst:
            # support fuer discovery von dotted module names
            versuch:
                __import__(start_dir)
            ausser ImportError:
                is_not_importable = Wahr
            sonst:
                the_module = sys.modules[start_dir]
                wenn nicht hasattr(the_module, "__file__") oder the_module.__file__ ist Nichts:
                    # look fuer namespace packages
                    versuch:
                        spec = the_module.__spec__
                    ausser AttributeError:
                        spec = Nichts

                    wenn spec und spec.submodule_search_locations ist nicht Nichts:
                        is_namespace = Wahr

                        fuer path in the_module.__path__:
                            wenn (nicht set_implicit_top und
                                nicht path.startswith(top_level_dir)):
                                weiter
                            self._top_level_dir = \
                                (path.split(the_module.__name__
                                        .replace(".", os.path.sep))[0])
                            tests.extend(self._find_tests(path, pattern, namespace=Wahr))
                    sowenn the_module.__name__ in sys.builtin_module_names:
                        # builtin module
                        wirf TypeError('Can nicht use builtin modules '
                                        'as dotted module names') von Nichts
                    sonst:
                        wirf TypeError(
                            f"don't know how to discover von {the_module!r}"
                            ) von Nichts

                sonst:
                    top_part = start_dir.split('.')[0]
                    start_dir = os.path.abspath(os.path.dirname((the_module.__file__)))

                wenn set_implicit_top:
                    wenn nicht is_namespace:
                        wenn sys.modules[top_part].__file__ ist Nichts:
                            self._top_level_dir = os.path.dirname(the_module.__file__)
                            wenn self._top_level_dir nicht in sys.path:
                                sys.path.insert(0, self._top_level_dir)
                        sonst:
                            self._top_level_dir = \
                                self._get_directory_containing_module(top_part)
                    sys.path.remove(top_level_dir)

        wenn is_not_importable:
            wirf ImportError('Start directory ist nicht importable: %r' % start_dir)

        wenn nicht is_namespace:
            tests = list(self._find_tests(start_dir, pattern))

        self._top_level_dir = original_top_level_dir
        gib self.suiteClass(tests)

    def _get_directory_containing_module(self, module_name):
        module = sys.modules[module_name]
        full_path = os.path.abspath(module.__file__)

        wenn os.path.basename(full_path).lower().startswith('__init__.py'):
            gib os.path.dirname(os.path.dirname(full_path))
        sonst:
            # here we have been given a module rather than a package - so
            # all we can do ist search the *same* directory the module ist in
            # should an exception be raised instead
            gib os.path.dirname(full_path)

    def _get_name_from_path(self, path):
        wenn path == self._top_level_dir:
            gib '.'
        path = _splitext(os.path.normpath(path))

        _relpath = os.path.relpath(path, self._top_level_dir)
        pruefe nicht os.path.isabs(_relpath), "Path must be within the project"
        pruefe nicht _relpath.startswith('..'), "Path must be within the project"

        name = _relpath.replace(os.path.sep, '.')
        gib name

    def _get_module_from_name(self, name):
        __import__(name)
        gib sys.modules[name]

    def _match_path(self, path, full_path, pattern):
        # override this method to use alternative matching strategy
        gib fnmatch(path, pattern)

    def _find_tests(self, start_dir, pattern, namespace=Falsch):
        """Used by discovery. Yields test suites it loads."""
        # Handle the __init__ in this package
        name = self._get_name_from_path(start_dir)
        # name ist '.' when start_dir == top_level_dir (and top_level_dir ist by
        # definition nicht a package).
        wenn name != '.' und name nicht in self._loading_packages:
            # name ist in self._loading_packages waehrend we have called into
            # loadTestsFromModule mit name.
            tests, should_recurse = self._find_test_path(
                start_dir, pattern, namespace)
            wenn tests ist nicht Nichts:
                liefere tests
            wenn nicht should_recurse:
                # Either an error occurred, oder load_tests was used by the
                # package.
                gib
        # Handle the contents.
        paths = sorted(os.listdir(start_dir))
        fuer path in paths:
            full_path = os.path.join(start_dir, path)
            tests, should_recurse = self._find_test_path(
                full_path, pattern, Falsch)
            wenn tests ist nicht Nichts:
                liefere tests
            wenn should_recurse:
                # we found a package that didn't use load_tests.
                name = self._get_name_from_path(full_path)
                self._loading_packages.add(name)
                versuch:
                    liefere von self._find_tests(full_path, pattern, Falsch)
                schliesslich:
                    self._loading_packages.discard(name)

    def _find_test_path(self, full_path, pattern, namespace=Falsch):
        """Used by discovery.

        Loads tests von a single file, oder a directories' __init__.py when
        passed the directory.

        Returns a tuple (Nichts_or_tests_from_file, should_recurse).
        """
        basename = os.path.basename(full_path)
        wenn os.path.isfile(full_path):
            wenn nicht VALID_MODULE_NAME.match(basename):
                # valid Python identifiers only
                gib Nichts, Falsch
            wenn nicht self._match_path(basename, full_path, pattern):
                gib Nichts, Falsch
            # wenn the test file matches, load it
            name = self._get_name_from_path(full_path)
            versuch:
                module = self._get_module_from_name(name)
            ausser case.SkipTest als e:
                gib _make_skipped_test(name, e, self.suiteClass), Falsch
            ausser:
                error_case, error_message = \
                    _make_failed_import_test(name, self.suiteClass)
                self.errors.append(error_message)
                gib error_case, Falsch
            sonst:
                mod_file = os.path.abspath(
                    getattr(module, '__file__', full_path))
                realpath = _splitext(
                    os.path.realpath(mod_file))
                fullpath_noext = _splitext(
                    os.path.realpath(full_path))
                wenn realpath.lower() != fullpath_noext.lower():
                    module_dir = os.path.dirname(realpath)
                    mod_name = _splitext(
                        os.path.basename(full_path))
                    expected_dir = os.path.dirname(full_path)
                    msg = ("%r module incorrectly imported von %r. Expected "
                           "%r. Is this module globally installed?")
                    wirf ImportError(
                        msg % (mod_name, module_dir, expected_dir))
                gib self.loadTestsFromModule(module, pattern=pattern), Falsch
        sowenn os.path.isdir(full_path):
            wenn (nicht namespace und
                nicht os.path.isfile(os.path.join(full_path, '__init__.py'))):
                gib Nichts, Falsch

            load_tests = Nichts
            tests = Nichts
            name = self._get_name_from_path(full_path)
            versuch:
                package = self._get_module_from_name(name)
            ausser case.SkipTest als e:
                gib _make_skipped_test(name, e, self.suiteClass), Falsch
            ausser:
                error_case, error_message = \
                    _make_failed_import_test(name, self.suiteClass)
                self.errors.append(error_message)
                gib error_case, Falsch
            sonst:
                load_tests = getattr(package, 'load_tests', Nichts)
                # Mark this package als being in load_tests (possibly ;))
                self._loading_packages.add(name)
                versuch:
                    tests = self.loadTestsFromModule(package, pattern=pattern)
                    wenn load_tests ist nicht Nichts:
                        # loadTestsFromModule(package) has loaded tests fuer us.
                        gib tests, Falsch
                    gib tests, Wahr
                schliesslich:
                    self._loading_packages.discard(name)
        sonst:
            gib Nichts, Falsch


defaultTestLoader = TestLoader()
