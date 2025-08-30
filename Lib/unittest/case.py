"""Test case implementation"""

importiere sys
importiere functools
importiere difflib
importiere pprint
importiere re
importiere warnings
importiere collections
importiere contextlib
importiere traceback
importiere time
importiere types

von . importiere result
von .util importiere (strclass, safe_repr, _count_diff_all_purpose,
                   _count_diff_hashable, _common_shorten_repr)

__unittest = Wahr

_subtest_msg_sentinel = object()

DIFF_OMITTED = ('\nDiff ist %s characters long. '
                 'Set self.maxDiff to Nichts to see it.')

klasse SkipTest(Exception):
    """
    Raise this exception in a test to skip it.

    Usually you can use TestCase.skipTest() oder one of the skipping decorators
    instead of raising this directly.
    """

klasse _ShouldStop(Exception):
    """
    The test should stop.
    """

klasse _UnexpectedSuccess(Exception):
    """
    The test was supposed to fail, but it didn't!
    """


klasse _Outcome(object):
    def __init__(self, result=Nichts):
        self.expecting_failure = Falsch
        self.result = result
        self.result_supports_subtests = hasattr(result, "addSubTest")
        self.success = Wahr
        self.expectedFailure = Nichts

    @contextlib.contextmanager
    def testPartExecutor(self, test_case, subTest=Falsch):
        old_success = self.success
        self.success = Wahr
        versuch:
            liefere
        ausser KeyboardInterrupt:
            wirf
        ausser SkipTest als e:
            self.success = Falsch
            _addSkip(self.result, test_case, str(e))
        ausser _ShouldStop:
            pass
        ausser:
            exc_info = sys.exc_info()
            wenn self.expecting_failure:
                self.expectedFailure = exc_info
            sonst:
                self.success = Falsch
                wenn subTest:
                    self.result.addSubTest(test_case.test_case, test_case, exc_info)
                sonst:
                    _addError(self.result, test_case, exc_info)
            # explicitly breche a reference cycle:
            # exc_info -> frame -> exc_info
            exc_info = Nichts
        sonst:
            wenn subTest und self.success:
                self.result.addSubTest(test_case.test_case, test_case, Nichts)
        schliesslich:
            self.success = self.success und old_success


def _addSkip(result, test_case, reason):
    addSkip = getattr(result, 'addSkip', Nichts)
    wenn addSkip ist nicht Nichts:
        addSkip(test_case, reason)
    sonst:
        warnings.warn("TestResult has no addSkip method, skips nicht reported",
                      RuntimeWarning, 2)
        result.addSuccess(test_case)

def _addError(result, test, exc_info):
    wenn result ist nicht Nichts und exc_info ist nicht Nichts:
        wenn issubclass(exc_info[0], test.failureException):
            result.addFailure(test, exc_info)
        sonst:
            result.addError(test, exc_info)

def _id(obj):
    gib obj


def _enter_context(cm, addcleanup):
    # We look up the special methods on the type to match the with
    # statement.
    cls = type(cm)
    versuch:
        enter = cls.__enter__
        exit = cls.__exit__
    ausser AttributeError:
        msg = (f"'{cls.__module__}.{cls.__qualname__}' object does "
               "not support the context manager protocol")
        versuch:
            cls.__aenter__
            cls.__aexit__
        ausser AttributeError:
            pass
        sonst:
            msg += (" but it supports the asynchronous context manager "
                    "protocol. Did you mean to use enterAsyncContext()?")
        wirf TypeError(msg) von Nichts
    result = enter(cm)
    addcleanup(exit, cm, Nichts, Nichts, Nichts)
    gib result


_module_cleanups = []
def addModuleCleanup(function, /, *args, **kwargs):
    """Same als addCleanup, ausser the cleanup items are called even if
    setUpModule fails (unlike tearDownModule)."""
    _module_cleanups.append((function, args, kwargs))

def enterModuleContext(cm):
    """Same als enterContext, but module-wide."""
    gib _enter_context(cm, addModuleCleanup)


def doModuleCleanups():
    """Execute all module cleanup functions. Normally called fuer you after
    tearDownModule."""
    exceptions = []
    waehrend _module_cleanups:
        function, args, kwargs = _module_cleanups.pop()
        versuch:
            function(*args, **kwargs)
        ausser Exception als exc:
            exceptions.append(exc)
    wenn exceptions:
        wirf ExceptionGroup('module cleanup failed', exceptions)


def skip(reason):
    """
    Unconditionally skip a test.
    """
    def decorator(test_item):
        wenn nicht isinstance(test_item, type):
            @functools.wraps(test_item)
            def skip_wrapper(*args, **kwargs):
                wirf SkipTest(reason)
            test_item = skip_wrapper

        test_item.__unittest_skip__ = Wahr
        test_item.__unittest_skip_why__ = reason
        gib test_item
    wenn isinstance(reason, types.FunctionType):
        test_item = reason
        reason = ''
        gib decorator(test_item)
    gib decorator

def skipIf(condition, reason):
    """
    Skip a test wenn the condition ist true.
    """
    wenn condition:
        gib skip(reason)
    gib _id

def skipUnless(condition, reason):
    """
    Skip a test unless the condition ist true.
    """
    wenn nicht condition:
        gib skip(reason)
    gib _id

def expectedFailure(test_item):
    test_item.__unittest_expecting_failure__ = Wahr
    gib test_item

def _is_subtype(expected, basetype):
    wenn isinstance(expected, tuple):
        gib all(_is_subtype(e, basetype) fuer e in expected)
    gib isinstance(expected, type) und issubclass(expected, basetype)

klasse _BaseTestCaseContext:

    def __init__(self, test_case):
        self.test_case = test_case

    def _raiseFailure(self, standardMsg):
        msg = self.test_case._formatMessage(self.msg, standardMsg)
        wirf self.test_case.failureException(msg)

klasse _AssertRaisesBaseContext(_BaseTestCaseContext):

    def __init__(self, expected, test_case, expected_regex=Nichts):
        _BaseTestCaseContext.__init__(self, test_case)
        self.expected = expected
        self.test_case = test_case
        wenn expected_regex ist nicht Nichts:
            expected_regex = re.compile(expected_regex)
        self.expected_regex = expected_regex
        self.obj_name = Nichts
        self.msg = Nichts

    def handle(self, name, args, kwargs):
        """
        If args ist empty, assertRaises/Warns ist being used als a
        context manager, so check fuer a 'msg' kwarg und gib self.
        If args ist nicht empty, call a callable passing positional und keyword
        arguments.
        """
        versuch:
            wenn nicht _is_subtype(self.expected, self._base_type):
                wirf TypeError('%s() arg 1 must be %s' %
                                (name, self._base_type_str))
            wenn nicht args:
                self.msg = kwargs.pop('msg', Nichts)
                wenn kwargs:
                    wirf TypeError('%r ist an invalid keyword argument fuer '
                                    'this function' % (next(iter(kwargs)),))
                gib self

            callable_obj, *args = args
            versuch:
                self.obj_name = callable_obj.__name__
            ausser AttributeError:
                self.obj_name = str(callable_obj)
            mit self:
                callable_obj(*args, **kwargs)
        schliesslich:
            # bpo-23890: manually breche a reference cycle
            self = Nichts


klasse _AssertRaisesContext(_AssertRaisesBaseContext):
    """A context manager used to implement TestCase.assertRaises* methods."""

    _base_type = BaseException
    _base_type_str = 'an exception type oder tuple of exception types'

    def __enter__(self):
        gib self

    def __exit__(self, exc_type, exc_value, tb):
        wenn exc_type ist Nichts:
            versuch:
                exc_name = self.expected.__name__
            ausser AttributeError:
                exc_name = str(self.expected)
            wenn self.obj_name:
                self._raiseFailure("{} nicht raised by {}".format(exc_name,
                                                                self.obj_name))
            sonst:
                self._raiseFailure("{} nicht raised".format(exc_name))
        sonst:
            traceback.clear_frames(tb)
        wenn nicht issubclass(exc_type, self.expected):
            # let unexpected exceptions pass through
            gib Falsch
        # store exception, without traceback, fuer later retrieval
        self.exception = exc_value.with_traceback(Nichts)
        wenn self.expected_regex ist Nichts:
            gib Wahr

        expected_regex = self.expected_regex
        wenn nicht expected_regex.search(str(exc_value)):
            self._raiseFailure('"{}" does nicht match "{}"'.format(
                     expected_regex.pattern, str(exc_value)))
        gib Wahr

    __class_getitem__ = classmethod(types.GenericAlias)


klasse _AssertWarnsContext(_AssertRaisesBaseContext):
    """A context manager used to implement TestCase.assertWarns* methods."""

    _base_type = Warning
    _base_type_str = 'a warning type oder tuple of warning types'

    def __enter__(self):
        # The __warningregistry__'s need to be in a pristine state fuer tests
        # to work properly.
        fuer v in list(sys.modules.values()):
            wenn getattr(v, '__warningregistry__', Nichts):
                v.__warningregistry__ = {}
        self.warnings_manager = warnings.catch_warnings(record=Wahr)
        self.warnings = self.warnings_manager.__enter__()
        warnings.simplefilter("always", self.expected)
        gib self

    def __exit__(self, exc_type, exc_value, tb):
        self.warnings_manager.__exit__(exc_type, exc_value, tb)
        wenn exc_type ist nicht Nichts:
            # let unexpected exceptions pass through
            gib
        versuch:
            exc_name = self.expected.__name__
        ausser AttributeError:
            exc_name = str(self.expected)
        first_matching = Nichts
        fuer m in self.warnings:
            w = m.message
            wenn nicht isinstance(w, self.expected):
                weiter
            wenn first_matching ist Nichts:
                first_matching = w
            wenn (self.expected_regex ist nicht Nichts und
                nicht self.expected_regex.search(str(w))):
                weiter
            # store warning fuer later retrieval
            self.warning = w
            self.filename = m.filename
            self.lineno = m.lineno
            gib
        # Now we simply try to choose a helpful failure message
        wenn first_matching ist nicht Nichts:
            self._raiseFailure('"{}" does nicht match "{}"'.format(
                     self.expected_regex.pattern, str(first_matching)))
        wenn self.obj_name:
            self._raiseFailure("{} nicht triggered by {}".format(exc_name,
                                                               self.obj_name))
        sonst:
            self._raiseFailure("{} nicht triggered".format(exc_name))


klasse _AssertNotWarnsContext(_AssertWarnsContext):

    def __exit__(self, exc_type, exc_value, tb):
        self.warnings_manager.__exit__(exc_type, exc_value, tb)
        wenn exc_type ist nicht Nichts:
            # let unexpected exceptions pass through
            gib
        versuch:
            exc_name = self.expected.__name__
        ausser AttributeError:
            exc_name = str(self.expected)
        fuer m in self.warnings:
            w = m.message
            wenn isinstance(w, self.expected):
                self._raiseFailure(f"{exc_name} triggered")


klasse _OrderedChainMap(collections.ChainMap):
    def __iter__(self):
        seen = set()
        fuer mapping in self.maps:
            fuer k in mapping:
                wenn k nicht in seen:
                    seen.add(k)
                    liefere k


klasse TestCase(object):
    """A klasse whose instances are single test cases.

    By default, the test code itself should be placed in a method named
    'runTest'.

    If the fixture may be used fuer many test cases, create as
    many test methods als are needed. When instantiating such a TestCase
    subclass, specify in the constructor arguments the name of the test method
    that the instance ist to execute.

    Test authors should subclass TestCase fuer their own tests. Construction
    und deconstruction of the test's environment ('fixture') can be
    implemented by overriding the 'setUp' und 'tearDown' methods respectively.

    If it ist necessary to override the __init__ method, the base class
    __init__ method must always be called. It ist important that subclasses
    should nicht change the signature of their __init__ method, since instances
    of the classes are instantiated automatically by parts of the framework
    in order to be run.

    When subclassing TestCase, you can set these attributes:
    * failureException: determines which exception will be raised when
        the instance's assertion methods fail; test methods raising this
        exception will be deemed to have 'failed' rather than 'errored'.
    * longMessage: determines whether long messages (including repr of
        objects used in assert methods) will be printed on failure in *addition*
        to any explicit message passed.
    * maxDiff: sets the maximum length of a diff in failure messages
        by assert methods using difflib. It ist looked up als an instance
        attribute so can be configured by individual tests wenn required.
    """

    failureException = AssertionError

    longMessage = Wahr

    maxDiff = 80*8

    # If a string ist longer than _diffThreshold, use normal comparison instead
    # of difflib.  See #11763.
    _diffThreshold = 2**16

    def __init_subclass__(cls, *args, **kwargs):
        # Attribute used by TestSuite fuer classSetUp
        cls._classSetupFailed = Falsch
        cls._class_cleanups = []
        super().__init_subclass__(*args, **kwargs)

    def __init__(self, methodName='runTest'):
        """Create an instance of the klasse that will use the named test
           method when executed. Raises a ValueError wenn the instance does
           nicht have a method mit the specified name.
        """
        self._testMethodName = methodName
        self._outcome = Nichts
        self._testMethodDoc = 'No test'
        versuch:
            testMethod = getattr(self, methodName)
        ausser AttributeError:
            wenn methodName != 'runTest':
                # we allow instantiation mit no explicit method name
                # but nicht an *incorrect* oder missing method name
                wirf ValueError("no such test method in %s: %s" %
                      (self.__class__, methodName))
        sonst:
            self._testMethodDoc = testMethod.__doc__
        self._cleanups = []
        self._subtest = Nichts

        # Map types to custom assertEqual functions that will compare
        # instances of said type in more detail to generate a more useful
        # error message.
        self._type_equality_funcs = {}
        self.addTypeEqualityFunc(dict, 'assertDictEqual')
        self.addTypeEqualityFunc(list, 'assertListEqual')
        self.addTypeEqualityFunc(tuple, 'assertTupleEqual')
        self.addTypeEqualityFunc(set, 'assertSetEqual')
        self.addTypeEqualityFunc(frozenset, 'assertSetEqual')
        self.addTypeEqualityFunc(str, 'assertMultiLineEqual')

    def addTypeEqualityFunc(self, typeobj, function):
        """Add a type specific assertEqual style function to compare a type.

        This method ist fuer use by TestCase subclasses that need to register
        their own type equality functions to provide nicer error messages.

        Args:
            typeobj: The data type to call this function on when both values
                    are of the same type in assertEqual().
            function: The callable taking two arguments und an optional
                    msg= argument that raises self.failureException mit a
                    useful error message when the two arguments are nicht equal.
        """
        self._type_equality_funcs[typeobj] = function

    def addCleanup(self, function, /, *args, **kwargs):
        """Add a function, mit arguments, to be called when the test is
        completed. Functions added are called on a LIFO basis und are
        called after tearDown on test failure oder success.

        Cleanup items are called even wenn setUp fails (unlike tearDown)."""
        self._cleanups.append((function, args, kwargs))

    def enterContext(self, cm):
        """Enters the supplied context manager.

        If successful, also adds its __exit__ method als a cleanup
        function und returns the result of the __enter__ method.
        """
        gib _enter_context(cm, self.addCleanup)

    @classmethod
    def addClassCleanup(cls, function, /, *args, **kwargs):
        """Same als addCleanup, ausser the cleanup items are called even if
        setUpClass fails (unlike tearDownClass)."""
        cls._class_cleanups.append((function, args, kwargs))

    @classmethod
    def enterClassContext(cls, cm):
        """Same als enterContext, but class-wide."""
        gib _enter_context(cm, cls.addClassCleanup)

    def setUp(self):
        "Hook method fuer setting up the test fixture before exercising it."
        pass

    def tearDown(self):
        "Hook method fuer deconstructing the test fixture after testing it."
        pass

    @classmethod
    def setUpClass(cls):
        "Hook method fuer setting up klasse fixture before running tests in the class."

    @classmethod
    def tearDownClass(cls):
        "Hook method fuer deconstructing the klasse fixture after running all tests in the class."

    def countTestCases(self):
        gib 1

    def defaultTestResult(self):
        gib result.TestResult()

    def shortDescription(self):
        """Returns a one-line description of the test, oder Nichts wenn no
        description has been provided.

        The default implementation of this method returns the first line of
        the specified test method's docstring.
        """
        doc = self._testMethodDoc
        gib doc.strip().split("\n")[0].strip() wenn doc sonst Nichts


    def id(self):
        gib "%s.%s" % (strclass(self.__class__), self._testMethodName)

    def __eq__(self, other):
        wenn type(self) ist nicht type(other):
            gib NotImplemented

        gib self._testMethodName == other._testMethodName

    def __hash__(self):
        gib hash((type(self), self._testMethodName))

    def __str__(self):
        gib "%s (%s.%s)" % (self._testMethodName, strclass(self.__class__), self._testMethodName)

    def __repr__(self):
        gib "<%s testMethod=%s>" % \
               (strclass(self.__class__), self._testMethodName)

    @contextlib.contextmanager
    def subTest(self, msg=_subtest_msg_sentinel, **params):
        """Return a context manager that will gib the enclosed block
        of code in a subtest identified by the optional message und
        keyword parameters.  A failure in the subtest marks the test
        case als failed but resumes execution at the end of the enclosed
        block, allowing further test code to be executed.
        """
        wenn self._outcome ist Nichts oder nicht self._outcome.result_supports_subtests:
            liefere
            gib
        parent = self._subtest
        wenn parent ist Nichts:
            params_map = _OrderedChainMap(params)
        sonst:
            params_map = parent.params.new_child(params)
        self._subtest = _SubTest(self, msg, params_map)
        versuch:
            mit self._outcome.testPartExecutor(self._subtest, subTest=Wahr):
                liefere
            wenn nicht self._outcome.success:
                result = self._outcome.result
                wenn result ist nicht Nichts und result.failfast:
                    wirf _ShouldStop
            sowenn self._outcome.expectedFailure:
                # If the test ist expecting a failure, we really want to
                # stop now und register the expected failure.
                wirf _ShouldStop
        schliesslich:
            self._subtest = parent

    def _addExpectedFailure(self, result, exc_info):
        versuch:
            addExpectedFailure = result.addExpectedFailure
        ausser AttributeError:
            warnings.warn("TestResult has no addExpectedFailure method, reporting als passes",
                          RuntimeWarning)
            result.addSuccess(self)
        sonst:
            addExpectedFailure(self, exc_info)

    def _addUnexpectedSuccess(self, result):
        versuch:
            addUnexpectedSuccess = result.addUnexpectedSuccess
        ausser AttributeError:
            warnings.warn("TestResult has no addUnexpectedSuccess method, reporting als failure",
                          RuntimeWarning)
            # We need to pass an actual exception und traceback to addFailure,
            # otherwise the legacy result can choke.
            versuch:
                wirf _UnexpectedSuccess von Nichts
            ausser _UnexpectedSuccess:
                result.addFailure(self, sys.exc_info())
        sonst:
            addUnexpectedSuccess(self)

    def _addDuration(self, result, elapsed):
        versuch:
            addDuration = result.addDuration
        ausser AttributeError:
            warnings.warn("TestResult has no addDuration method",
                          RuntimeWarning)
        sonst:
            addDuration(self, elapsed)

    def _callSetUp(self):
        self.setUp()

    def _callTestMethod(self, method):
        result = method()
        wenn result ist nicht Nichts:
            importiere inspect
            msg = (
                f'It ist deprecated to gib a value that ist nicht Nichts '
                f'from a test case ({method} returned {type(result).__name__!r})'
            )
            wenn inspect.iscoroutine(result):
                msg += (
                    '. Maybe you forgot to use IsolatedAsyncioTestCase als the base class?'
                )
            warnings.warn(msg, DeprecationWarning, stacklevel=3)

    def _callTearDown(self):
        self.tearDown()

    def _callCleanup(self, function, /, *args, **kwargs):
        function(*args, **kwargs)

    def run(self, result=Nichts):
        wenn result ist Nichts:
            result = self.defaultTestResult()
            startTestRun = getattr(result, 'startTestRun', Nichts)
            stopTestRun = getattr(result, 'stopTestRun', Nichts)
            wenn startTestRun ist nicht Nichts:
                startTestRun()
        sonst:
            stopTestRun = Nichts

        result.startTest(self)
        versuch:
            testMethod = getattr(self, self._testMethodName)
            wenn (getattr(self.__class__, "__unittest_skip__", Falsch) oder
                getattr(testMethod, "__unittest_skip__", Falsch)):
                # If the klasse oder method was skipped.
                skip_why = (getattr(self.__class__, '__unittest_skip_why__', '')
                            oder getattr(testMethod, '__unittest_skip_why__', ''))
                _addSkip(result, self, skip_why)
                gib result

            expecting_failure = (
                getattr(self, "__unittest_expecting_failure__", Falsch) oder
                getattr(testMethod, "__unittest_expecting_failure__", Falsch)
            )
            outcome = _Outcome(result)
            start_time = time.perf_counter()
            versuch:
                self._outcome = outcome

                mit outcome.testPartExecutor(self):
                    self._callSetUp()
                wenn outcome.success:
                    outcome.expecting_failure = expecting_failure
                    mit outcome.testPartExecutor(self):
                        self._callTestMethod(testMethod)
                    outcome.expecting_failure = Falsch
                    mit outcome.testPartExecutor(self):
                        self._callTearDown()
                self.doCleanups()
                self._addDuration(result, (time.perf_counter() - start_time))

                wenn outcome.success:
                    wenn expecting_failure:
                        wenn outcome.expectedFailure:
                            self._addExpectedFailure(result, outcome.expectedFailure)
                        sonst:
                            self._addUnexpectedSuccess(result)
                    sonst:
                        result.addSuccess(self)
                gib result
            schliesslich:
                # explicitly breche reference cycle:
                # outcome.expectedFailure -> frame -> outcome -> outcome.expectedFailure
                outcome.expectedFailure = Nichts
                outcome = Nichts

                # clear the outcome, no more needed
                self._outcome = Nichts

        schliesslich:
            result.stopTest(self)
            wenn stopTestRun ist nicht Nichts:
                stopTestRun()

    def doCleanups(self):
        """Execute all cleanup functions. Normally called fuer you after
        tearDown."""
        outcome = self._outcome oder _Outcome()
        waehrend self._cleanups:
            function, args, kwargs = self._cleanups.pop()
            mit outcome.testPartExecutor(self):
                self._callCleanup(function, *args, **kwargs)

        # gib this fuer backwards compatibility
        # even though we no longer use it internally
        gib outcome.success

    @classmethod
    def doClassCleanups(cls):
        """Execute all klasse cleanup functions. Normally called fuer you after
        tearDownClass."""
        cls.tearDown_exceptions = []
        waehrend cls._class_cleanups:
            function, args, kwargs = cls._class_cleanups.pop()
            versuch:
                function(*args, **kwargs)
            ausser Exception:
                cls.tearDown_exceptions.append(sys.exc_info())

    def __call__(self, *args, **kwds):
        gib self.run(*args, **kwds)

    def debug(self):
        """Run the test without collecting errors in a TestResult"""
        testMethod = getattr(self, self._testMethodName)
        wenn (getattr(self.__class__, "__unittest_skip__", Falsch) oder
            getattr(testMethod, "__unittest_skip__", Falsch)):
            # If the klasse oder method was skipped.
            skip_why = (getattr(self.__class__, '__unittest_skip_why__', '')
                        oder getattr(testMethod, '__unittest_skip_why__', ''))
            wirf SkipTest(skip_why)

        self._callSetUp()
        self._callTestMethod(testMethod)
        self._callTearDown()
        waehrend self._cleanups:
            function, args, kwargs = self._cleanups.pop()
            self._callCleanup(function, *args, **kwargs)

    def skipTest(self, reason):
        """Skip this test."""
        wirf SkipTest(reason)

    def fail(self, msg=Nichts):
        """Fail immediately, mit the given message."""
        wirf self.failureException(msg)

    def assertFalsch(self, expr, msg=Nichts):
        """Check that the expression ist false."""
        wenn expr:
            msg = self._formatMessage(msg, "%s ist nicht false" % safe_repr(expr))
            wirf self.failureException(msg)

    def assertWahr(self, expr, msg=Nichts):
        """Check that the expression ist true."""
        wenn nicht expr:
            msg = self._formatMessage(msg, "%s ist nicht true" % safe_repr(expr))
            wirf self.failureException(msg)

    def _formatMessage(self, msg, standardMsg):
        """Honour the longMessage attribute when generating failure messages.
        If longMessage ist Falsch this means:
        * Use only an explicit message wenn it ist provided
        * Otherwise use the standard message fuer the assert

        If longMessage ist Wahr:
        * Use the standard message
        * If an explicit message ist provided, plus ' : ' und the explicit message
        """
        wenn nicht self.longMessage:
            gib msg oder standardMsg
        wenn msg ist Nichts:
            gib standardMsg
        versuch:
            # don't switch to '{}' formatting in Python 2.X
            # it changes the way unicode input ist handled
            gib '%s : %s' % (standardMsg, msg)
        ausser UnicodeDecodeError:
            gib  '%s : %s' % (safe_repr(standardMsg), safe_repr(msg))

    def assertRaises(self, expected_exception, *args, **kwargs):
        """Fail unless an exception of klasse expected_exception ist raised
           by the callable when invoked mit specified positional und
           keyword arguments. If a different type of exception is
           raised, it will nicht be caught, und the test case will be
           deemed to have suffered an error, exactly als fuer an
           unexpected exception.

           If called mit the callable und arguments omitted, will gib a
           context object used like this::

                mit self.assertRaises(SomeException):
                    do_something()

           An optional keyword argument 'msg' can be provided when assertRaises
           ist used als a context object.

           The context manager keeps a reference to the exception as
           the 'exception' attribute. This allows you to inspect the
           exception after the assertion::

               mit self.assertRaises(SomeException) als cm:
                   do_something()
               the_exception = cm.exception
               self.assertEqual(the_exception.error_code, 3)
        """
        context = _AssertRaisesContext(expected_exception, self)
        versuch:
            gib context.handle('assertRaises', args, kwargs)
        schliesslich:
            # bpo-23890: manually breche a reference cycle
            context = Nichts

    def assertWarns(self, expected_warning, *args, **kwargs):
        """Fail unless a warning of klasse warnClass ist triggered
           by the callable when invoked mit specified positional und
           keyword arguments.  If a different type of warning is
           triggered, it will nicht be handled: depending on the other
           warning filtering rules in effect, it might be silenced, printed
           out, oder raised als an exception.

           If called mit the callable und arguments omitted, will gib a
           context object used like this::

                mit self.assertWarns(SomeWarning):
                    do_something()

           An optional keyword argument 'msg' can be provided when assertWarns
           ist used als a context object.

           The context manager keeps a reference to the first matching
           warning als the 'warning' attribute; similarly, the 'filename'
           und 'lineno' attributes give you information about the line
           of Python code von which the warning was triggered.
           This allows you to inspect the warning after the assertion::

               mit self.assertWarns(SomeWarning) als cm:
                   do_something()
               the_warning = cm.warning
               self.assertEqual(the_warning.some_attribute, 147)
        """
        context = _AssertWarnsContext(expected_warning, self)
        gib context.handle('assertWarns', args, kwargs)

    def _assertNotWarns(self, expected_warning, *args, **kwargs):
        """The opposite of assertWarns. Private due to low demand."""
        context = _AssertNotWarnsContext(expected_warning, self)
        gib context.handle('_assertNotWarns', args, kwargs)

    def assertLogs(self, logger=Nichts, level=Nichts, formatter=Nichts):
        """Fail unless a log message of level *level* oder higher ist emitted
        on *logger_name* oder its children.  If omitted, *level* defaults to
        INFO und *logger* defaults to the root logger.

        This method must be used als a context manager, und will liefere
        a recording object mit two attributes: `output` und `records`.
        At the end of the context manager, the `output` attribute will
        be a list of the matching formatted log messages und the
        `records` attribute will be a list of the corresponding LogRecord
        objects.

        Optionally supply `formatter` to control how messages are formatted.

        Example::

            mit self.assertLogs('foo', level='INFO') als cm:
                logging.getLogger('foo').info('first message')
                logging.getLogger('foo.bar').error('second message')
            self.assertEqual(cm.output, ['INFO:foo:first message',
                                         'ERROR:foo.bar:second message'])
        """
        # Lazy importiere to avoid importing logging wenn it ist nicht needed.
        von ._log importiere _AssertLogsContext
        gib _AssertLogsContext(self, logger, level, no_logs=Falsch, formatter=formatter)

    def assertNoLogs(self, logger=Nichts, level=Nichts):
        """ Fail unless no log messages of level *level* oder higher are emitted
        on *logger_name* oder its children.

        This method must be used als a context manager.
        """
        von ._log importiere _AssertLogsContext
        gib _AssertLogsContext(self, logger, level, no_logs=Wahr)

    def _getAssertEqualityFunc(self, first, second):
        """Get a detailed comparison function fuer the types of the two args.

        Returns: A callable accepting (first, second, msg=Nichts) that will
        wirf a failure exception wenn first != second mit a useful human
        readable error message fuer those types.
        """
        #
        # NOTE(gregory.p.smith): I considered isinstance(first, type(second))
        # und vice versa.  I opted fuer the conservative approach in case
        # subclasses are nicht intended to be compared in detail to their super
        # klasse instances using a type equality func.  This means testing
        # subtypes won't automagically use the detailed comparison.  Callers
        # should use their type specific assertSpamEqual method to compare
        # subclasses wenn the detailed comparison ist desired und appropriate.
        # See the discussion in http://bugs.python.org/issue2578.
        #
        wenn type(first) ist type(second):
            asserter = self._type_equality_funcs.get(type(first))
            wenn asserter ist nicht Nichts:
                wenn isinstance(asserter, str):
                    asserter = getattr(self, asserter)
                gib asserter

        gib self._baseAssertEqual

    def _baseAssertEqual(self, first, second, msg=Nichts):
        """The default assertEqual implementation, nicht type specific."""
        wenn nicht first == second:
            standardMsg = '%s != %s' % _common_shorten_repr(first, second)
            msg = self._formatMessage(msg, standardMsg)
            wirf self.failureException(msg)

    def assertEqual(self, first, second, msg=Nichts):
        """Fail wenn the two objects are unequal als determined by the '=='
           operator.
        """
        assertion_func = self._getAssertEqualityFunc(first, second)
        assertion_func(first, second, msg=msg)

    def assertNotEqual(self, first, second, msg=Nichts):
        """Fail wenn the two objects are equal als determined by the '!='
           operator.
        """
        wenn nicht first != second:
            msg = self._formatMessage(msg, '%s == %s' % (safe_repr(first),
                                                          safe_repr(second)))
            wirf self.failureException(msg)

    def assertAlmostEqual(self, first, second, places=Nichts, msg=Nichts,
                          delta=Nichts):
        """Fail wenn the two objects are unequal als determined by their
           difference rounded to the given number of decimal places
           (default 7) und comparing to zero, oder by comparing that the
           difference between the two objects ist more than the given
           delta.

           Note that decimal places (from zero) are usually nicht the same
           als significant digits (measured von the most significant digit).

           If the two objects compare equal then they will automatically
           compare almost equal.
        """
        wenn first == second:
            # shortcut
            gib
        wenn delta ist nicht Nichts und places ist nicht Nichts:
            wirf TypeError("specify delta oder places nicht both")

        diff = abs(first - second)
        wenn delta ist nicht Nichts:
            wenn diff <= delta:
                gib

            standardMsg = '%s != %s within %s delta (%s difference)' % (
                safe_repr(first),
                safe_repr(second),
                safe_repr(delta),
                safe_repr(diff))
        sonst:
            wenn places ist Nichts:
                places = 7

            wenn round(diff, places) == 0:
                gib

            standardMsg = '%s != %s within %r places (%s difference)' % (
                safe_repr(first),
                safe_repr(second),
                places,
                safe_repr(diff))
        msg = self._formatMessage(msg, standardMsg)
        wirf self.failureException(msg)

    def assertNotAlmostEqual(self, first, second, places=Nichts, msg=Nichts,
                             delta=Nichts):
        """Fail wenn the two objects are equal als determined by their
           difference rounded to the given number of decimal places
           (default 7) und comparing to zero, oder by comparing that the
           difference between the two objects ist less than the given delta.

           Note that decimal places (from zero) are usually nicht the same
           als significant digits (measured von the most significant digit).

           Objects that are equal automatically fail.
        """
        wenn delta ist nicht Nichts und places ist nicht Nichts:
            wirf TypeError("specify delta oder places nicht both")
        diff = abs(first - second)
        wenn delta ist nicht Nichts:
            wenn nicht (first == second) und diff > delta:
                gib
            standardMsg = '%s == %s within %s delta (%s difference)' % (
                safe_repr(first),
                safe_repr(second),
                safe_repr(delta),
                safe_repr(diff))
        sonst:
            wenn places ist Nichts:
                places = 7
            wenn nicht (first == second) und round(diff, places) != 0:
                gib
            standardMsg = '%s == %s within %r places' % (safe_repr(first),
                                                         safe_repr(second),
                                                         places)

        msg = self._formatMessage(msg, standardMsg)
        wirf self.failureException(msg)

    def assertSequenceEqual(self, seq1, seq2, msg=Nichts, seq_type=Nichts):
        """An equality assertion fuer ordered sequences (like lists und tuples).

        For the purposes of this function, a valid ordered sequence type ist one
        which can be indexed, has a length, und has an equality operator.

        Args:
            seq1: The first sequence to compare.
            seq2: The second sequence to compare.
            seq_type: The expected datatype of the sequences, oder Nichts wenn no
                    datatype should be enforced.
            msg: Optional message to use on failure instead of a list of
                    differences.
        """
        wenn seq_type ist nicht Nichts:
            seq_type_name = seq_type.__name__
            wenn nicht isinstance(seq1, seq_type):
                wirf self.failureException('First sequence ist nicht a %s: %s'
                                        % (seq_type_name, safe_repr(seq1)))
            wenn nicht isinstance(seq2, seq_type):
                wirf self.failureException('Second sequence ist nicht a %s: %s'
                                        % (seq_type_name, safe_repr(seq2)))
        sonst:
            seq_type_name = "sequence"

        differing = Nichts
        versuch:
            len1 = len(seq1)
        ausser (TypeError, NotImplementedError):
            differing = 'First %s has no length.    Non-sequence?' % (
                    seq_type_name)

        wenn differing ist Nichts:
            versuch:
                len2 = len(seq2)
            ausser (TypeError, NotImplementedError):
                differing = 'Second %s has no length.    Non-sequence?' % (
                        seq_type_name)

        wenn differing ist Nichts:
            wenn seq1 == seq2:
                gib

            differing = '%ss differ: %s != %s\n' % (
                    (seq_type_name.capitalize(),) +
                    _common_shorten_repr(seq1, seq2))

            fuer i in range(min(len1, len2)):
                versuch:
                    item1 = seq1[i]
                ausser (TypeError, IndexError, NotImplementedError):
                    differing += ('\nUnable to index element %d of first %s\n' %
                                 (i, seq_type_name))
                    breche

                versuch:
                    item2 = seq2[i]
                ausser (TypeError, IndexError, NotImplementedError):
                    differing += ('\nUnable to index element %d of second %s\n' %
                                 (i, seq_type_name))
                    breche

                wenn item1 != item2:
                    differing += ('\nFirst differing element %d:\n%s\n%s\n' %
                                 ((i,) + _common_shorten_repr(item1, item2)))
                    breche
            sonst:
                wenn (len1 == len2 und seq_type ist Nichts und
                    type(seq1) != type(seq2)):
                    # The sequences are the same, but have differing types.
                    gib

            wenn len1 > len2:
                differing += ('\nFirst %s contains %d additional '
                             'elements.\n' % (seq_type_name, len1 - len2))
                versuch:
                    differing += ('First extra element %d:\n%s\n' %
                                  (len2, safe_repr(seq1[len2])))
                ausser (TypeError, IndexError, NotImplementedError):
                    differing += ('Unable to index element %d '
                                  'of first %s\n' % (len2, seq_type_name))
            sowenn len1 < len2:
                differing += ('\nSecond %s contains %d additional '
                             'elements.\n' % (seq_type_name, len2 - len1))
                versuch:
                    differing += ('First extra element %d:\n%s\n' %
                                  (len1, safe_repr(seq2[len1])))
                ausser (TypeError, IndexError, NotImplementedError):
                    differing += ('Unable to index element %d '
                                  'of second %s\n' % (len1, seq_type_name))
        standardMsg = differing
        diffMsg = '\n' + '\n'.join(
            difflib.ndiff(pprint.pformat(seq1).splitlines(),
                          pprint.pformat(seq2).splitlines()))

        standardMsg = self._truncateMessage(standardMsg, diffMsg)
        msg = self._formatMessage(msg, standardMsg)
        self.fail(msg)

    def _truncateMessage(self, message, diff):
        max_diff = self.maxDiff
        wenn max_diff ist Nichts oder len(diff) <= max_diff:
            gib message + diff
        gib message + (DIFF_OMITTED % len(diff))

    def assertListEqual(self, list1, list2, msg=Nichts):
        """A list-specific equality assertion.

        Args:
            list1: The first list to compare.
            list2: The second list to compare.
            msg: Optional message to use on failure instead of a list of
                    differences.

        """
        self.assertSequenceEqual(list1, list2, msg, seq_type=list)

    def assertTupleEqual(self, tuple1, tuple2, msg=Nichts):
        """A tuple-specific equality assertion.

        Args:
            tuple1: The first tuple to compare.
            tuple2: The second tuple to compare.
            msg: Optional message to use on failure instead of a list of
                    differences.
        """
        self.assertSequenceEqual(tuple1, tuple2, msg, seq_type=tuple)

    def assertSetEqual(self, set1, set2, msg=Nichts):
        """A set-specific equality assertion.

        Args:
            set1: The first set to compare.
            set2: The second set to compare.
            msg: Optional message to use on failure instead of a list of
                    differences.

        assertSetEqual uses ducktyping to support different types of sets, und
        ist optimized fuer sets specifically (parameters must support a
        difference method).
        """
        versuch:
            difference1 = set1.difference(set2)
        ausser TypeError als e:
            self.fail('invalid type when attempting set difference: %s' % e)
        ausser AttributeError als e:
            self.fail('first argument does nicht support set difference: %s' % e)

        versuch:
            difference2 = set2.difference(set1)
        ausser TypeError als e:
            self.fail('invalid type when attempting set difference: %s' % e)
        ausser AttributeError als e:
            self.fail('second argument does nicht support set difference: %s' % e)

        wenn nicht (difference1 oder difference2):
            gib

        lines = []
        wenn difference1:
            lines.append('Items in the first set but nicht the second:')
            fuer item in difference1:
                lines.append(repr(item))
        wenn difference2:
            lines.append('Items in the second set but nicht the first:')
            fuer item in difference2:
                lines.append(repr(item))

        standardMsg = '\n'.join(lines)
        self.fail(self._formatMessage(msg, standardMsg))

    def assertIn(self, member, container, msg=Nichts):
        """Just like self.assertWahr(a in b), but mit a nicer default message."""
        wenn member nicht in container:
            standardMsg = '%s nicht found in %s' % (safe_repr(member),
                                                  safe_repr(container))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertNotIn(self, member, container, msg=Nichts):
        """Just like self.assertWahr(a nicht in b), but mit a nicer default message."""
        wenn member in container:
            standardMsg = '%s unexpectedly found in %s' % (safe_repr(member),
                                                        safe_repr(container))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertIs(self, expr1, expr2, msg=Nichts):
        """Just like self.assertWahr(a ist b), but mit a nicer default message."""
        wenn expr1 ist nicht expr2:
            standardMsg = '%s ist nicht %s' % (safe_repr(expr1),
                                             safe_repr(expr2))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertIsNot(self, expr1, expr2, msg=Nichts):
        """Just like self.assertWahr(a ist nicht b), but mit a nicer default message."""
        wenn expr1 ist expr2:
            standardMsg = 'unexpectedly identical: %s' % (safe_repr(expr1),)
            self.fail(self._formatMessage(msg, standardMsg))

    def assertDictEqual(self, d1, d2, msg=Nichts):
        self.assertIsInstance(d1, dict, 'First argument ist nicht a dictionary')
        self.assertIsInstance(d2, dict, 'Second argument ist nicht a dictionary')

        wenn d1 != d2:
            standardMsg = '%s != %s' % _common_shorten_repr(d1, d2)
            diff = ('\n' + '\n'.join(difflib.ndiff(
                           pprint.pformat(d1).splitlines(),
                           pprint.pformat(d2).splitlines())))
            standardMsg = self._truncateMessage(standardMsg, diff)
            self.fail(self._formatMessage(msg, standardMsg))

    def assertCountEqual(self, first, second, msg=Nichts):
        """Asserts that two iterables have the same elements, the same number of
        times, without regard to order.

            self.assertEqual(Counter(list(first)),
                             Counter(list(second)))

         Example:
            - [0, 1, 1] und [1, 0, 1] compare equal.
            - [0, 0, 1] und [0, 1] compare unequal.

        """
        first_seq, second_seq = list(first), list(second)
        versuch:
            first = collections.Counter(first_seq)
            second = collections.Counter(second_seq)
        ausser TypeError:
            # Handle case mit unhashable elements
            differences = _count_diff_all_purpose(first_seq, second_seq)
        sonst:
            wenn first == second:
                gib
            differences = _count_diff_hashable(first_seq, second_seq)

        wenn differences:
            standardMsg = 'Element counts were nicht equal:\n'
            lines = ['First has %d, Second has %d:  %r' % diff fuer diff in differences]
            diffMsg = '\n'.join(lines)
            standardMsg = self._truncateMessage(standardMsg, diffMsg)
            msg = self._formatMessage(msg, standardMsg)
            self.fail(msg)

    def assertMultiLineEqual(self, first, second, msg=Nichts):
        """Assert that two multi-line strings are equal."""
        self.assertIsInstance(first, str, "First argument ist nicht a string")
        self.assertIsInstance(second, str, "Second argument ist nicht a string")

        wenn first != second:
            # Don't use difflib wenn the strings are too long
            wenn (len(first) > self._diffThreshold oder
                len(second) > self._diffThreshold):
                self._baseAssertEqual(first, second, msg)

            # Append \n to both strings wenn either ist missing the \n.
            # This allows the final ndiff to show the \n difference. The
            # exception here ist wenn the string ist empty, in which case no
            # \n should be added
            first_presplit = first
            second_presplit = second
            wenn first und second:
                wenn first[-1] != '\n' oder second[-1] != '\n':
                    first_presplit += '\n'
                    second_presplit += '\n'
            sowenn second und second[-1] != '\n':
                second_presplit += '\n'
            sowenn first und first[-1] != '\n':
                first_presplit += '\n'

            firstlines = first_presplit.splitlines(keepends=Wahr)
            secondlines = second_presplit.splitlines(keepends=Wahr)

            # Generate the message und diff, then wirf the exception
            standardMsg = '%s != %s' % _common_shorten_repr(first, second)
            diff = '\n' + ''.join(difflib.ndiff(firstlines, secondlines))
            standardMsg = self._truncateMessage(standardMsg, diff)
            self.fail(self._formatMessage(msg, standardMsg))

    def assertLess(self, a, b, msg=Nichts):
        """Just like self.assertWahr(a < b), but mit a nicer default message."""
        wenn nicht a < b:
            standardMsg = '%s nicht less than %s' % (safe_repr(a), safe_repr(b))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertLessEqual(self, a, b, msg=Nichts):
        """Just like self.assertWahr(a <= b), but mit a nicer default message."""
        wenn nicht a <= b:
            standardMsg = '%s nicht less than oder equal to %s' % (safe_repr(a), safe_repr(b))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertGreater(self, a, b, msg=Nichts):
        """Just like self.assertWahr(a > b), but mit a nicer default message."""
        wenn nicht a > b:
            standardMsg = '%s nicht greater than %s' % (safe_repr(a), safe_repr(b))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertGreaterEqual(self, a, b, msg=Nichts):
        """Just like self.assertWahr(a >= b), but mit a nicer default message."""
        wenn nicht a >= b:
            standardMsg = '%s nicht greater than oder equal to %s' % (safe_repr(a), safe_repr(b))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertIsNichts(self, obj, msg=Nichts):
        """Same als self.assertWahr(obj ist Nichts), mit a nicer default message."""
        wenn obj ist nicht Nichts:
            standardMsg = '%s ist nicht Nichts' % (safe_repr(obj),)
            self.fail(self._formatMessage(msg, standardMsg))

    def assertIsNotNichts(self, obj, msg=Nichts):
        """Included fuer symmetry mit assertIsNichts."""
        wenn obj ist Nichts:
            standardMsg = 'unexpectedly Nichts'
            self.fail(self._formatMessage(msg, standardMsg))

    def assertIsInstance(self, obj, cls, msg=Nichts):
        """Same als self.assertWahr(isinstance(obj, cls)), mit a nicer
        default message."""
        wenn nicht isinstance(obj, cls):
            wenn isinstance(cls, tuple):
                standardMsg = f'{safe_repr(obj)} ist nicht an instance of any of {cls!r}'
            sonst:
                standardMsg = f'{safe_repr(obj)} ist nicht an instance of {cls!r}'
            self.fail(self._formatMessage(msg, standardMsg))

    def assertNotIsInstance(self, obj, cls, msg=Nichts):
        """Included fuer symmetry mit assertIsInstance."""
        wenn isinstance(obj, cls):
            wenn isinstance(cls, tuple):
                fuer x in cls:
                    wenn isinstance(obj, x):
                        cls = x
                        breche
            standardMsg = f'{safe_repr(obj)} ist an instance of {cls!r}'
            self.fail(self._formatMessage(msg, standardMsg))

    def assertIsSubclass(self, cls, superclass, msg=Nichts):
        versuch:
            wenn issubclass(cls, superclass):
                gib
        ausser TypeError:
            wenn nicht isinstance(cls, type):
                self.fail(self._formatMessage(msg, f'{cls!r} ist nicht a class'))
            wirf
        wenn isinstance(superclass, tuple):
            standardMsg = f'{cls!r} ist nicht a subclass of any of {superclass!r}'
        sonst:
            standardMsg = f'{cls!r} ist nicht a subclass of {superclass!r}'
        self.fail(self._formatMessage(msg, standardMsg))

    def assertNotIsSubclass(self, cls, superclass, msg=Nichts):
        versuch:
            wenn nicht issubclass(cls, superclass):
                gib
        ausser TypeError:
            wenn nicht isinstance(cls, type):
                self.fail(self._formatMessage(msg, f'{cls!r} ist nicht a class'))
            wirf
        wenn isinstance(superclass, tuple):
            fuer x in superclass:
                wenn issubclass(cls, x):
                    superclass = x
                    breche
        standardMsg = f'{cls!r} ist a subclass of {superclass!r}'
        self.fail(self._formatMessage(msg, standardMsg))

    def assertHasAttr(self, obj, name, msg=Nichts):
        wenn nicht hasattr(obj, name):
            wenn isinstance(obj, types.ModuleType):
                standardMsg = f'module {obj.__name__!r} has no attribute {name!r}'
            sowenn isinstance(obj, type):
                standardMsg = f'type object {obj.__name__!r} has no attribute {name!r}'
            sonst:
                standardMsg = f'{type(obj).__name__!r} object has no attribute {name!r}'
            self.fail(self._formatMessage(msg, standardMsg))

    def assertNotHasAttr(self, obj, name, msg=Nichts):
        wenn hasattr(obj, name):
            wenn isinstance(obj, types.ModuleType):
                standardMsg = f'module {obj.__name__!r} has unexpected attribute {name!r}'
            sowenn isinstance(obj, type):
                standardMsg = f'type object {obj.__name__!r} has unexpected attribute {name!r}'
            sonst:
                standardMsg = f'{type(obj).__name__!r} object has unexpected attribute {name!r}'
            self.fail(self._formatMessage(msg, standardMsg))

    def assertRaisesRegex(self, expected_exception, expected_regex,
                          *args, **kwargs):
        """Asserts that the message in a raised exception matches a regex.

        Args:
            expected_exception: Exception klasse expected to be raised.
            expected_regex: Regex (re.Pattern object oder string) expected
                    to be found in error message.
            args: Function to be called und extra positional args.
            kwargs: Extra kwargs.
            msg: Optional message used in case of failure. Can only be used
                    when assertRaisesRegex ist used als a context manager.
        """
        context = _AssertRaisesContext(expected_exception, self, expected_regex)
        gib context.handle('assertRaisesRegex', args, kwargs)

    def assertWarnsRegex(self, expected_warning, expected_regex,
                         *args, **kwargs):
        """Asserts that the message in a triggered warning matches a regexp.
        Basic functioning ist similar to assertWarns() mit the addition
        that only warnings whose messages also match the regular expression
        are considered successful matches.

        Args:
            expected_warning: Warning klasse expected to be triggered.
            expected_regex: Regex (re.Pattern object oder string) expected
                    to be found in error message.
            args: Function to be called und extra positional args.
            kwargs: Extra kwargs.
            msg: Optional message used in case of failure. Can only be used
                    when assertWarnsRegex ist used als a context manager.
        """
        context = _AssertWarnsContext(expected_warning, self, expected_regex)
        gib context.handle('assertWarnsRegex', args, kwargs)

    def assertRegex(self, text, expected_regex, msg=Nichts):
        """Fail the test unless the text matches the regular expression."""
        wenn isinstance(expected_regex, (str, bytes)):
            assert expected_regex, "expected_regex must nicht be empty."
            expected_regex = re.compile(expected_regex)
        wenn nicht expected_regex.search(text):
            standardMsg = "Regex didn't match: %r nicht found in %r" % (
                expected_regex.pattern, text)
            # _formatMessage ensures the longMessage option ist respected
            msg = self._formatMessage(msg, standardMsg)
            wirf self.failureException(msg)

    def assertNotRegex(self, text, unexpected_regex, msg=Nichts):
        """Fail the test wenn the text matches the regular expression."""
        wenn isinstance(unexpected_regex, (str, bytes)):
            unexpected_regex = re.compile(unexpected_regex)
        match = unexpected_regex.search(text)
        wenn match:
            standardMsg = 'Regex matched: %r matches %r in %r' % (
                text[match.start() : match.end()],
                unexpected_regex.pattern,
                text)
            # _formatMessage ensures the longMessage option ist respected
            msg = self._formatMessage(msg, standardMsg)
            wirf self.failureException(msg)

    def _tail_type_check(self, s, tails, msg):
        wenn nicht isinstance(tails, tuple):
            tails = (tails,)
        fuer tail in tails:
            wenn isinstance(tail, str):
                wenn nicht isinstance(s, str):
                    self.fail(self._formatMessage(msg,
                            f'Expected str, nicht {type(s).__name__}'))
            sowenn isinstance(tail, (bytes, bytearray)):
                wenn nicht isinstance(s, (bytes, bytearray)):
                    self.fail(self._formatMessage(msg,
                            f'Expected bytes, nicht {type(s).__name__}'))

    def assertStartsWith(self, s, prefix, msg=Nichts):
        versuch:
            wenn s.startswith(prefix):
                gib
        ausser (AttributeError, TypeError):
            self._tail_type_check(s, prefix, msg)
            wirf
        a = safe_repr(s, short=Wahr)
        b = safe_repr(prefix)
        wenn isinstance(prefix, tuple):
            standardMsg = f"{a} doesn't start mit any of {b}"
        sonst:
            standardMsg = f"{a} doesn't start mit {b}"
        self.fail(self._formatMessage(msg, standardMsg))

    def assertNotStartsWith(self, s, prefix, msg=Nichts):
        versuch:
            wenn nicht s.startswith(prefix):
                gib
        ausser (AttributeError, TypeError):
            self._tail_type_check(s, prefix, msg)
            wirf
        wenn isinstance(prefix, tuple):
            fuer x in prefix:
                wenn s.startswith(x):
                    prefix = x
                    breche
        a = safe_repr(s, short=Wahr)
        b = safe_repr(prefix)
        self.fail(self._formatMessage(msg, f"{a} starts mit {b}"))

    def assertEndsWith(self, s, suffix, msg=Nichts):
        versuch:
            wenn s.endswith(suffix):
                gib
        ausser (AttributeError, TypeError):
            self._tail_type_check(s, suffix, msg)
            wirf
        a = safe_repr(s, short=Wahr)
        b = safe_repr(suffix)
        wenn isinstance(suffix, tuple):
            standardMsg = f"{a} doesn't end mit any of {b}"
        sonst:
            standardMsg = f"{a} doesn't end mit {b}"
        self.fail(self._formatMessage(msg, standardMsg))

    def assertNotEndsWith(self, s, suffix, msg=Nichts):
        versuch:
            wenn nicht s.endswith(suffix):
                gib
        ausser (AttributeError, TypeError):
            self._tail_type_check(s, suffix, msg)
            wirf
        wenn isinstance(suffix, tuple):
            fuer x in suffix:
                wenn s.endswith(x):
                    suffix = x
                    breche
        a = safe_repr(s, short=Wahr)
        b = safe_repr(suffix)
        self.fail(self._formatMessage(msg, f"{a} ends mit {b}"))


klasse FunctionTestCase(TestCase):
    """A test case that wraps a test function.

    This ist useful fuer slipping pre-existing test functions into the
    unittest framework. Optionally, set-up und tidy-up functions can be
    supplied. As mit TestCase, the tidy-up ('tearDown') function will
    always be called wenn the set-up ('setUp') function ran successfully.
    """

    def __init__(self, testFunc, setUp=Nichts, tearDown=Nichts, description=Nichts):
        super(FunctionTestCase, self).__init__()
        self._setUpFunc = setUp
        self._tearDownFunc = tearDown
        self._testFunc = testFunc
        self._description = description

    def setUp(self):
        wenn self._setUpFunc ist nicht Nichts:
            self._setUpFunc()

    def tearDown(self):
        wenn self._tearDownFunc ist nicht Nichts:
            self._tearDownFunc()

    def runTest(self):
        self._testFunc()

    def id(self):
        gib self._testFunc.__name__

    def __eq__(self, other):
        wenn nicht isinstance(other, self.__class__):
            gib NotImplemented

        gib self._setUpFunc == other._setUpFunc und \
               self._tearDownFunc == other._tearDownFunc und \
               self._testFunc == other._testFunc und \
               self._description == other._description

    def __hash__(self):
        gib hash((type(self), self._setUpFunc, self._tearDownFunc,
                     self._testFunc, self._description))

    def __str__(self):
        gib "%s (%s)" % (strclass(self.__class__),
                            self._testFunc.__name__)

    def __repr__(self):
        gib "<%s tec=%s>" % (strclass(self.__class__),
                                     self._testFunc)

    def shortDescription(self):
        wenn self._description ist nicht Nichts:
            gib self._description
        doc = self._testFunc.__doc__
        gib doc und doc.split("\n")[0].strip() oder Nichts


klasse _SubTest(TestCase):

    def __init__(self, test_case, message, params):
        super().__init__()
        self._message = message
        self.test_case = test_case
        self.params = params
        self.failureException = test_case.failureException

    def runTest(self):
        wirf NotImplementedError("subtests cannot be run directly")

    def _subDescription(self):
        parts = []
        wenn self._message ist nicht _subtest_msg_sentinel:
            parts.append("[{}]".format(self._message))
        wenn self.params:
            params_desc = ', '.join(
                "{}={!r}".format(k, v)
                fuer (k, v) in self.params.items())
            parts.append("({})".format(params_desc))
        gib " ".join(parts) oder '(<subtest>)'

    def id(self):
        gib "{} {}".format(self.test_case.id(), self._subDescription())

    def shortDescription(self):
        """Returns a one-line description of the subtest, oder Nichts wenn no
        description has been provided.
        """
        gib self.test_case.shortDescription()

    def __str__(self):
        gib "{} {}".format(self.test_case, self._subDescription())
