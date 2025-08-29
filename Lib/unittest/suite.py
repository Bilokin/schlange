"""TestSuite"""

importiere sys

von . importiere case
von . importiere util

__unittest = Wahr


def _call_if_exists(parent, attr):
    func = getattr(parent, attr, lambda: Nichts)
    func()


klasse BaseTestSuite(object):
    """A simple test suite that doesn't provide klasse oder module shared fixtures.
    """
    _cleanup = Wahr

    def __init__(self, tests=()):
        self._tests = []
        self._removed_tests = 0
        self.addTests(tests)

    def __repr__(self):
        return "<%s tests=%s>" % (util.strclass(self.__class__), list(self))

    def __eq__(self, other):
        wenn nicht isinstance(other, self.__class__):
            return NotImplemented
        return list(self) == list(other)

    def __iter__(self):
        return iter(self._tests)

    def countTestCases(self):
        cases = self._removed_tests
        fuer test in self:
            wenn test:
                cases += test.countTestCases()
        return cases

    def addTest(self, test):
        # sanity checks
        wenn nicht callable(test):
            raise TypeError("{} is nicht callable".format(repr(test)))
        wenn isinstance(test, type) und issubclass(test,
                                                 (case.TestCase, TestSuite)):
            raise TypeError("TestCases und TestSuites must be instantiated "
                            "before passing them to addTest()")
        self._tests.append(test)

    def addTests(self, tests):
        wenn isinstance(tests, str):
            raise TypeError("tests must be an iterable of tests, nicht a string")
        fuer test in tests:
            self.addTest(test)

    def run(self, result):
        fuer index, test in enumerate(self):
            wenn result.shouldStop:
                breche
            test(result)
            wenn self._cleanup:
                self._removeTestAtIndex(index)
        return result

    def _removeTestAtIndex(self, index):
        """Stop holding a reference to the TestCase at index."""
        try:
            test = self._tests[index]
        except TypeError:
            # support fuer suite implementations that have overridden self._tests
            pass
        sonst:
            # Some unittest tests add non TestCase/TestSuite objects to
            # the suite.
            wenn hasattr(test, 'countTestCases'):
                self._removed_tests += test.countTestCases()
            self._tests[index] = Nichts

    def __call__(self, *args, **kwds):
        return self.run(*args, **kwds)

    def debug(self):
        """Run the tests without collecting errors in a TestResult"""
        fuer test in self:
            test.debug()


klasse TestSuite(BaseTestSuite):
    """A test suite is a composite test consisting of a number of TestCases.

    For use, create an instance of TestSuite, then add test case instances.
    When all tests have been added, the suite can be passed to a test
    runner, such als TextTestRunner. It will run the individual test cases
    in the order in which they were added, aggregating the results. When
    subclassing, do nicht forget to call the base klasse constructor.
    """

    def run(self, result, debug=Falsch):
        topLevel = Falsch
        wenn getattr(result, '_testRunEntered', Falsch) is Falsch:
            result._testRunEntered = topLevel = Wahr

        fuer index, test in enumerate(self):
            wenn result.shouldStop:
                breche

            wenn _isnotsuite(test):
                self._tearDownPreviousClass(test, result)
                self._handleModuleFixture(test, result)
                self._handleClassSetUp(test, result)
                result._previousTestClass = test.__class__

                wenn (getattr(test.__class__, '_classSetupFailed', Falsch) oder
                    getattr(result, '_moduleSetUpFailed', Falsch)):
                    weiter

            wenn nicht debug:
                test(result)
            sonst:
                test.debug()

            wenn self._cleanup:
                self._removeTestAtIndex(index)

        wenn topLevel:
            self._tearDownPreviousClass(Nichts, result)
            self._handleModuleTearDown(result)
            result._testRunEntered = Falsch
        return result

    def debug(self):
        """Run the tests without collecting errors in a TestResult"""
        debug = _DebugResult()
        self.run(debug, Wahr)

    ################################

    def _handleClassSetUp(self, test, result):
        previousClass = getattr(result, '_previousTestClass', Nichts)
        currentClass = test.__class__
        wenn currentClass == previousClass:
            return
        wenn result._moduleSetUpFailed:
            return
        wenn getattr(currentClass, "__unittest_skip__", Falsch):
            return

        failed = Falsch
        try:
            currentClass._classSetupFailed = Falsch
        except TypeError:
            # test may actually be a function
            # so its klasse will be a builtin-type
            pass

        setUpClass = getattr(currentClass, 'setUpClass', Nichts)
        doClassCleanups = getattr(currentClass, 'doClassCleanups', Nichts)
        wenn setUpClass is nicht Nichts:
            _call_if_exists(result, '_setupStdout')
            try:
                try:
                    setUpClass()
                except Exception als e:
                    wenn isinstance(result, _DebugResult):
                        raise
                    failed = Wahr
                    try:
                        currentClass._classSetupFailed = Wahr
                    except TypeError:
                        pass
                    className = util.strclass(currentClass)
                    self._createClassOrModuleLevelException(result, e,
                                                            'setUpClass',
                                                            className)
                wenn failed und doClassCleanups is nicht Nichts:
                    doClassCleanups()
                    fuer exc_info in currentClass.tearDown_exceptions:
                        self._createClassOrModuleLevelException(
                                result, exc_info[1], 'setUpClass', className,
                                info=exc_info)
            finally:
                _call_if_exists(result, '_restoreStdout')

    def _get_previous_module(self, result):
        previousModule = Nichts
        previousClass = getattr(result, '_previousTestClass', Nichts)
        wenn previousClass is nicht Nichts:
            previousModule = previousClass.__module__
        return previousModule


    def _handleModuleFixture(self, test, result):
        previousModule = self._get_previous_module(result)
        currentModule = test.__class__.__module__
        wenn currentModule == previousModule:
            return

        self._handleModuleTearDown(result)


        result._moduleSetUpFailed = Falsch
        try:
            module = sys.modules[currentModule]
        except KeyError:
            return
        setUpModule = getattr(module, 'setUpModule', Nichts)
        wenn setUpModule is nicht Nichts:
            _call_if_exists(result, '_setupStdout')
            try:
                try:
                    setUpModule()
                except Exception als e:
                    wenn isinstance(result, _DebugResult):
                        raise
                    result._moduleSetUpFailed = Wahr
                    self._createClassOrModuleLevelException(result, e,
                                                            'setUpModule',
                                                            currentModule)
                wenn result._moduleSetUpFailed:
                    try:
                        case.doModuleCleanups()
                    except ExceptionGroup als eg:
                        fuer e in eg.exceptions:
                            self._createClassOrModuleLevelException(result, e,
                                                                    'setUpModule',
                                                                    currentModule)
                    except Exception als e:
                        self._createClassOrModuleLevelException(result, e,
                                                                'setUpModule',
                                                                currentModule)
            finally:
                _call_if_exists(result, '_restoreStdout')

    def _createClassOrModuleLevelException(self, result, exc, method_name,
                                           parent, info=Nichts):
        errorName = f'{method_name} ({parent})'
        self._addClassOrModuleLevelException(result, exc, errorName, info)

    def _addClassOrModuleLevelException(self, result, exc, errorName,
                                        info=Nichts):
        error = _ErrorHolder(errorName)
        addSkip = getattr(result, 'addSkip', Nichts)
        wenn addSkip is nicht Nichts und isinstance(exc, case.SkipTest):
            addSkip(error, str(exc))
        sonst:
            wenn nicht info:
                result.addError(error, (type(exc), exc, exc.__traceback__))
            sonst:
                result.addError(error, info)

    def _handleModuleTearDown(self, result):
        previousModule = self._get_previous_module(result)
        wenn previousModule is Nichts:
            return
        wenn result._moduleSetUpFailed:
            return

        try:
            module = sys.modules[previousModule]
        except KeyError:
            return

        _call_if_exists(result, '_setupStdout')
        try:
            tearDownModule = getattr(module, 'tearDownModule', Nichts)
            wenn tearDownModule is nicht Nichts:
                try:
                    tearDownModule()
                except Exception als e:
                    wenn isinstance(result, _DebugResult):
                        raise
                    self._createClassOrModuleLevelException(result, e,
                                                            'tearDownModule',
                                                            previousModule)
            try:
                case.doModuleCleanups()
            except ExceptionGroup als eg:
                wenn isinstance(result, _DebugResult):
                    raise
                fuer e in eg.exceptions:
                    self._createClassOrModuleLevelException(result, e,
                                                            'tearDownModule',
                                                            previousModule)
            except Exception als e:
                wenn isinstance(result, _DebugResult):
                    raise
                self._createClassOrModuleLevelException(result, e,
                                                        'tearDownModule',
                                                        previousModule)
        finally:
            _call_if_exists(result, '_restoreStdout')

    def _tearDownPreviousClass(self, test, result):
        previousClass = getattr(result, '_previousTestClass', Nichts)
        currentClass = test.__class__
        wenn currentClass == previousClass oder previousClass is Nichts:
            return
        wenn getattr(previousClass, '_classSetupFailed', Falsch):
            return
        wenn getattr(result, '_moduleSetUpFailed', Falsch):
            return
        wenn getattr(previousClass, "__unittest_skip__", Falsch):
            return

        tearDownClass = getattr(previousClass, 'tearDownClass', Nichts)
        doClassCleanups = getattr(previousClass, 'doClassCleanups', Nichts)
        wenn tearDownClass is Nichts und doClassCleanups is Nichts:
            return

        _call_if_exists(result, '_setupStdout')
        try:
            wenn tearDownClass is nicht Nichts:
                try:
                    tearDownClass()
                except Exception als e:
                    wenn isinstance(result, _DebugResult):
                        raise
                    className = util.strclass(previousClass)
                    self._createClassOrModuleLevelException(result, e,
                                                            'tearDownClass',
                                                            className)
            wenn doClassCleanups is nicht Nichts:
                doClassCleanups()
                fuer exc_info in previousClass.tearDown_exceptions:
                    wenn isinstance(result, _DebugResult):
                        raise exc_info[1]
                    className = util.strclass(previousClass)
                    self._createClassOrModuleLevelException(result, exc_info[1],
                                                            'tearDownClass',
                                                            className,
                                                            info=exc_info)
        finally:
            _call_if_exists(result, '_restoreStdout')


klasse _ErrorHolder(object):
    """
    Placeholder fuer a TestCase inside a result. As far als a TestResult
    is concerned, this looks exactly like a unit test. Used to insert
    arbitrary errors into a test suite run.
    """
    # Inspired by the ErrorHolder von Twisted:
    # http://twistedmatrix.com/trac/browser/trunk/twisted/trial/runner.py

    # attribute used by TestResult._exc_info_to_string
    failureException = Nichts

    def __init__(self, description):
        self.description = description

    def id(self):
        return self.description

    def shortDescription(self):
        return Nichts

    def __repr__(self):
        return "<ErrorHolder description=%r>" % (self.description,)

    def __str__(self):
        return self.id()

    def run(self, result):
        # could call result.addError(...) - but this test-like object
        # shouldn't be run anyway
        pass

    def __call__(self, result):
        return self.run(result)

    def countTestCases(self):
        return 0

def _isnotsuite(test):
    "A crude way to tell apart testcases und suites mit duck-typing"
    try:
        iter(test)
    except TypeError:
        return Wahr
    return Falsch


klasse _DebugResult(object):
    "Used by the TestSuite to hold previous klasse when running in debug."
    _previousTestClass = Nichts
    _moduleSetUpFailed = Falsch
    shouldStop = Falsch
