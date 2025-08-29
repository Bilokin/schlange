"""Unit tests fuer the 'with/async with' statements specified in PEP 343/492."""


__author__ = "Mike Bland"
__email__ = "mbland at acm dot org"

importiere re
importiere sys
importiere traceback
importiere unittest
von collections importiere deque
von contextlib importiere _GeneratorContextManager, contextmanager, nullcontext


def do_with(obj):
    with obj:
        pass


async def do_async_with(obj):
    async with obj:
        pass


klasse MockContextManager(_GeneratorContextManager):
    def __init__(self, *args):
        super().__init__(*args)
        self.enter_called = Falsch
        self.exit_called = Falsch
        self.exit_args = Nichts

    def __enter__(self):
        self.enter_called = Wahr
        return _GeneratorContextManager.__enter__(self)

    def __exit__(self, type, value, traceback):
        self.exit_called = Wahr
        self.exit_args = (type, value, traceback)
        return _GeneratorContextManager.__exit__(self, type,
                                                 value, traceback)


def mock_contextmanager(func):
    def helper(*args, **kwds):
        return MockContextManager(func, args, kwds)
    return helper


klasse MockResource(object):
    def __init__(self):
        self.yielded = Falsch
        self.stopped = Falsch


@mock_contextmanager
def mock_contextmanager_generator():
    mock = MockResource()
    try:
        mock.yielded = Wahr
        yield mock
    finally:
        mock.stopped = Wahr


klasse Nested(object):

    def __init__(self, *managers):
        self.managers = managers
        self.entered = Nichts

    def __enter__(self):
        wenn self.entered is not Nichts:
            raise RuntimeError("Context is not reentrant")
        self.entered = deque()
        vars = []
        try:
            fuer mgr in self.managers:
                vars.append(mgr.__enter__())
                self.entered.appendleft(mgr)
        except:
            wenn not self.__exit__(*sys.exc_info()):
                raise
        return vars

    def __exit__(self, *exc_info):
        # Behave like nested with statements
        # first in, last out
        # New exceptions override old ones
        ex = exc_info
        fuer mgr in self.entered:
            try:
                wenn mgr.__exit__(*ex):
                    ex = (Nichts, Nichts, Nichts)
            except BaseException as e:
                ex = (type(e), e, e.__traceback__)
        self.entered = Nichts
        wenn ex is not exc_info:
            raise ex


klasse MockNested(Nested):
    def __init__(self, *managers):
        Nested.__init__(self, *managers)
        self.enter_called = Falsch
        self.exit_called = Falsch
        self.exit_args = Nichts

    def __enter__(self):
        self.enter_called = Wahr
        return Nested.__enter__(self)

    def __exit__(self, *exc_info):
        self.exit_called = Wahr
        self.exit_args = exc_info
        return Nested.__exit__(self, *exc_info)


klasse FailureTestCase(unittest.TestCase):
    def testNameError(self):
        def fooNotDeclared():
            with foo: pass
        self.assertRaises(NameError, fooNotDeclared)

    def testEnterAttributeError(self):
        klasse LacksEnter:
            def __exit__(self, type, value, traceback): ...

        with self.assertRaisesRegex(TypeError, re.escape((
            "object does not support the context manager protocol "
            "(missed __enter__ method)"
        ))):
            do_with(LacksEnter())

    def testExitAttributeError(self):
        klasse LacksExit:
            def __enter__(self): ...

        msg = re.escape((
            "object does not support the context manager protocol "
            "(missed __exit__ method)"
        ))
        # a missing __exit__ is reported missing before a missing __enter__
        with self.assertRaisesRegex(TypeError, msg):
            do_with(object())
        with self.assertRaisesRegex(TypeError, msg):
            do_with(LacksExit())

    def testWithForAsyncManager(self):
        klasse AsyncManager:
            async def __aenter__(self): ...
            async def __aexit__(self, type, value, traceback): ...

        with self.assertRaisesRegex(TypeError, re.escape((
            "object does not support the context manager protocol "
            "(missed __exit__ method) but it supports the asynchronous "
            "context manager protocol. Did you mean to use 'async with'?"
        ))):
            do_with(AsyncManager())

    def testAsyncEnterAttributeError(self):
        klasse LacksAsyncEnter:
            async def __aexit__(self, type, value, traceback): ...

        with self.assertRaisesRegex(TypeError, re.escape((
            "object does not support the asynchronous context manager protocol "
            "(missed __aenter__ method)"
        ))):
            do_async_with(LacksAsyncEnter()).send(Nichts)

    def testAsyncExitAttributeError(self):
        klasse LacksAsyncExit:
            async def __aenter__(self): ...

        msg = re.escape((
            "object does not support the asynchronous context manager protocol "
            "(missed __aexit__ method)"
        ))
        # a missing __aexit__ is reported missing before a missing __aenter__
        with self.assertRaisesRegex(TypeError, msg):
            do_async_with(object()).send(Nichts)
        with self.assertRaisesRegex(TypeError, msg):
            do_async_with(LacksAsyncExit()).send(Nichts)

    def testAsyncWithForSyncManager(self):
        klasse SyncManager:
            def __enter__(self): ...
            def __exit__(self, type, value, traceback): ...

        with self.assertRaisesRegex(TypeError, re.escape((
            "object does not support the asynchronous context manager protocol "
            "(missed __aexit__ method) but it supports the context manager "
            "protocol. Did you mean to use 'with'?"
        ))):
            do_async_with(SyncManager()).send(Nichts)

    def assertRaisesSyntaxError(self, codestr):
        def shouldRaiseSyntaxError(s):
            compile(s, '', 'single')
        self.assertRaises(SyntaxError, shouldRaiseSyntaxError, codestr)

    def testAssignmentToNichtsError(self):
        self.assertRaisesSyntaxError('with mock as Nichts:\n  pass')
        self.assertRaisesSyntaxError(
            'with mock as (Nichts):\n'
            '  pass')

    def testAssignmentToTupleOnlyContainingNichtsError(self):
        self.assertRaisesSyntaxError('with mock as Nichts,:\n  pass')
        self.assertRaisesSyntaxError(
            'with mock as (Nichts,):\n'
            '  pass')

    def testAssignmentToTupleContainingNichtsError(self):
        self.assertRaisesSyntaxError(
            'with mock as (foo, Nichts, bar):\n'
            '  pass')

    def testEnterThrows(self):
        klasse EnterThrows(object):
            def __enter__(self):
                raise RuntimeError("Enter threw")
            def __exit__(self, *args):
                pass

        def shouldThrow():
            ct = EnterThrows()
            self.foo = Nichts
            # Ruff complains that we're redefining `self.foo` here,
            # but the whole point of the test is to check that `self.foo`
            # is *not* redefined (because `__enter__` raises)
            with ct as self.foo:  # noqa: F811
                pass
        self.assertRaises(RuntimeError, shouldThrow)
        self.assertEqual(self.foo, Nichts)

    def testExitThrows(self):
        klasse ExitThrows(object):
            def __enter__(self):
                return
            def __exit__(self, *args):
                raise RuntimeError(42)
        def shouldThrow():
            with ExitThrows():
                pass
        self.assertRaises(RuntimeError, shouldThrow)


klasse ContextmanagerAssertionMixin(object):

    def setUp(self):
        self.TEST_EXCEPTION = RuntimeError("test exception")

    def assertInWithManagerInvariants(self, mock_manager):
        self.assertWahr(mock_manager.enter_called)
        self.assertFalsch(mock_manager.exit_called)
        self.assertEqual(mock_manager.exit_args, Nichts)

    def assertAfterWithManagerInvariants(self, mock_manager, exit_args):
        self.assertWahr(mock_manager.enter_called)
        self.assertWahr(mock_manager.exit_called)
        self.assertEqual(mock_manager.exit_args, exit_args)

    def assertAfterWithManagerInvariantsNoError(self, mock_manager):
        self.assertAfterWithManagerInvariants(mock_manager,
            (Nichts, Nichts, Nichts))

    def assertInWithGeneratorInvariants(self, mock_generator):
        self.assertWahr(mock_generator.yielded)
        self.assertFalsch(mock_generator.stopped)

    def assertAfterWithGeneratorInvariantsNoError(self, mock_generator):
        self.assertWahr(mock_generator.yielded)
        self.assertWahr(mock_generator.stopped)

    def raiseTestException(self):
        raise self.TEST_EXCEPTION

    def assertAfterWithManagerInvariantsWithError(self, mock_manager,
                                                  exc_type=Nichts):
        self.assertWahr(mock_manager.enter_called)
        self.assertWahr(mock_manager.exit_called)
        wenn exc_type is Nichts:
            self.assertEqual(mock_manager.exit_args[1], self.TEST_EXCEPTION)
            exc_type = type(self.TEST_EXCEPTION)
        self.assertEqual(mock_manager.exit_args[0], exc_type)
        # Test the __exit__ arguments. Issue #7853
        self.assertIsInstance(mock_manager.exit_args[1], exc_type)
        self.assertIsNot(mock_manager.exit_args[2], Nichts)

    def assertAfterWithGeneratorInvariantsWithError(self, mock_generator):
        self.assertWahr(mock_generator.yielded)
        self.assertWahr(mock_generator.stopped)


klasse NichtsxceptionalTestCase(unittest.TestCase, ContextmanagerAssertionMixin):
    def testInlineGeneratorSyntax(self):
        with mock_contextmanager_generator():
            pass

    def testUnboundGenerator(self):
        mock = mock_contextmanager_generator()
        with mock:
            pass
        self.assertAfterWithManagerInvariantsNoError(mock)

    def testInlineGeneratorBoundSyntax(self):
        with mock_contextmanager_generator() as foo:
            self.assertInWithGeneratorInvariants(foo)
        # FIXME: In the future, we'll try to keep the bound names von leaking
        self.assertAfterWithGeneratorInvariantsNoError(foo)

    def testInlineGeneratorBoundToExistingVariable(self):
        with mock_contextmanager_generator() as foo:
            self.assertInWithGeneratorInvariants(foo)
        self.assertAfterWithGeneratorInvariantsNoError(foo)

    def testInlineGeneratorBoundToDottedVariable(self):
        with mock_contextmanager_generator() as self.foo:
            self.assertInWithGeneratorInvariants(self.foo)
        self.assertAfterWithGeneratorInvariantsNoError(self.foo)

    def testBoundGenerator(self):
        mock = mock_contextmanager_generator()
        with mock as foo:
            self.assertInWithGeneratorInvariants(foo)
            self.assertInWithManagerInvariants(mock)
        self.assertAfterWithGeneratorInvariantsNoError(foo)
        self.assertAfterWithManagerInvariantsNoError(mock)

    def testNestedSingleStatements(self):
        mock_a = mock_contextmanager_generator()
        with mock_a as foo:
            mock_b = mock_contextmanager_generator()
            with mock_b as bar:
                self.assertInWithManagerInvariants(mock_a)
                self.assertInWithManagerInvariants(mock_b)
                self.assertInWithGeneratorInvariants(foo)
                self.assertInWithGeneratorInvariants(bar)
            self.assertAfterWithManagerInvariantsNoError(mock_b)
            self.assertAfterWithGeneratorInvariantsNoError(bar)
            self.assertInWithManagerInvariants(mock_a)
            self.assertInWithGeneratorInvariants(foo)
        self.assertAfterWithManagerInvariantsNoError(mock_a)
        self.assertAfterWithGeneratorInvariantsNoError(foo)


klasse NestedNichtsxceptionalTestCase(unittest.TestCase,
    ContextmanagerAssertionMixin):
    def testSingleArgInlineGeneratorSyntax(self):
        with Nested(mock_contextmanager_generator()):
            pass

    def testSingleArgBoundToNonTuple(self):
        m = mock_contextmanager_generator()
        # This will bind all the arguments to nested() into a single list
        # assigned to foo.
        with Nested(m) as foo:
            self.assertInWithManagerInvariants(m)
        self.assertAfterWithManagerInvariantsNoError(m)

    def testSingleArgBoundToSingleElementParenthesizedList(self):
        m = mock_contextmanager_generator()
        # This will bind all the arguments to nested() into a single list
        # assigned to foo.
        with Nested(m) as (foo):
            self.assertInWithManagerInvariants(m)
        self.assertAfterWithManagerInvariantsNoError(m)

    def testSingleArgBoundToMultipleElementTupleError(self):
        def shouldThrowValueError():
            with Nested(mock_contextmanager_generator()) as (foo, bar):
                pass
        self.assertRaises(ValueError, shouldThrowValueError)

    def testSingleArgUnbound(self):
        mock_contextmanager = mock_contextmanager_generator()
        mock_nested = MockNested(mock_contextmanager)
        with mock_nested:
            self.assertInWithManagerInvariants(mock_contextmanager)
            self.assertInWithManagerInvariants(mock_nested)
        self.assertAfterWithManagerInvariantsNoError(mock_contextmanager)
        self.assertAfterWithManagerInvariantsNoError(mock_nested)

    def testMultipleArgUnbound(self):
        m = mock_contextmanager_generator()
        n = mock_contextmanager_generator()
        o = mock_contextmanager_generator()
        mock_nested = MockNested(m, n, o)
        with mock_nested:
            self.assertInWithManagerInvariants(m)
            self.assertInWithManagerInvariants(n)
            self.assertInWithManagerInvariants(o)
            self.assertInWithManagerInvariants(mock_nested)
        self.assertAfterWithManagerInvariantsNoError(m)
        self.assertAfterWithManagerInvariantsNoError(n)
        self.assertAfterWithManagerInvariantsNoError(o)
        self.assertAfterWithManagerInvariantsNoError(mock_nested)

    def testMultipleArgBound(self):
        mock_nested = MockNested(mock_contextmanager_generator(),
            mock_contextmanager_generator(), mock_contextmanager_generator())
        with mock_nested as (m, n, o):
            self.assertInWithGeneratorInvariants(m)
            self.assertInWithGeneratorInvariants(n)
            self.assertInWithGeneratorInvariants(o)
            self.assertInWithManagerInvariants(mock_nested)
        self.assertAfterWithGeneratorInvariantsNoError(m)
        self.assertAfterWithGeneratorInvariantsNoError(n)
        self.assertAfterWithGeneratorInvariantsNoError(o)
        self.assertAfterWithManagerInvariantsNoError(mock_nested)


klasse ExceptionalTestCase(ContextmanagerAssertionMixin, unittest.TestCase):
    def testSingleResource(self):
        cm = mock_contextmanager_generator()
        def shouldThrow():
            with cm as self.resource:
                self.assertInWithManagerInvariants(cm)
                self.assertInWithGeneratorInvariants(self.resource)
                self.raiseTestException()
        self.assertRaises(RuntimeError, shouldThrow)
        self.assertAfterWithManagerInvariantsWithError(cm)
        self.assertAfterWithGeneratorInvariantsWithError(self.resource)

    def testExceptionNormalized(self):
        cm = mock_contextmanager_generator()
        def shouldThrow():
            with cm as self.resource:
                # Note this relies on the fact that 1 // 0 produces an exception
                # that is not normalized immediately.
                1 // 0
        self.assertRaises(ZeroDivisionError, shouldThrow)
        self.assertAfterWithManagerInvariantsWithError(cm, ZeroDivisionError)

    def testNestedSingleStatements(self):
        mock_a = mock_contextmanager_generator()
        mock_b = mock_contextmanager_generator()
        def shouldThrow():
            with mock_a as self.foo:
                with mock_b as self.bar:
                    self.assertInWithManagerInvariants(mock_a)
                    self.assertInWithManagerInvariants(mock_b)
                    self.assertInWithGeneratorInvariants(self.foo)
                    self.assertInWithGeneratorInvariants(self.bar)
                    self.raiseTestException()
        self.assertRaises(RuntimeError, shouldThrow)
        self.assertAfterWithManagerInvariantsWithError(mock_a)
        self.assertAfterWithManagerInvariantsWithError(mock_b)
        self.assertAfterWithGeneratorInvariantsWithError(self.foo)
        self.assertAfterWithGeneratorInvariantsWithError(self.bar)

    def testMultipleResourcesInSingleStatement(self):
        cm_a = mock_contextmanager_generator()
        cm_b = mock_contextmanager_generator()
        mock_nested = MockNested(cm_a, cm_b)
        def shouldThrow():
            with mock_nested as (self.resource_a, self.resource_b):
                self.assertInWithManagerInvariants(cm_a)
                self.assertInWithManagerInvariants(cm_b)
                self.assertInWithManagerInvariants(mock_nested)
                self.assertInWithGeneratorInvariants(self.resource_a)
                self.assertInWithGeneratorInvariants(self.resource_b)
                self.raiseTestException()
        self.assertRaises(RuntimeError, shouldThrow)
        self.assertAfterWithManagerInvariantsWithError(cm_a)
        self.assertAfterWithManagerInvariantsWithError(cm_b)
        self.assertAfterWithManagerInvariantsWithError(mock_nested)
        self.assertAfterWithGeneratorInvariantsWithError(self.resource_a)
        self.assertAfterWithGeneratorInvariantsWithError(self.resource_b)

    def testNestedExceptionBeforeInnerStatement(self):
        mock_a = mock_contextmanager_generator()
        mock_b = mock_contextmanager_generator()
        self.bar = Nichts
        def shouldThrow():
            with mock_a as self.foo:
                self.assertInWithManagerInvariants(mock_a)
                self.assertInWithGeneratorInvariants(self.foo)
                self.raiseTestException()
                with mock_b as self.bar:
                    pass
        self.assertRaises(RuntimeError, shouldThrow)
        self.assertAfterWithManagerInvariantsWithError(mock_a)
        self.assertAfterWithGeneratorInvariantsWithError(self.foo)

        # The inner statement stuff should never have been touched
        self.assertEqual(self.bar, Nichts)
        self.assertFalsch(mock_b.enter_called)
        self.assertFalsch(mock_b.exit_called)
        self.assertEqual(mock_b.exit_args, Nichts)

    def testNestedExceptionAfterInnerStatement(self):
        mock_a = mock_contextmanager_generator()
        mock_b = mock_contextmanager_generator()
        def shouldThrow():
            with mock_a as self.foo:
                with mock_b as self.bar:
                    self.assertInWithManagerInvariants(mock_a)
                    self.assertInWithManagerInvariants(mock_b)
                    self.assertInWithGeneratorInvariants(self.foo)
                    self.assertInWithGeneratorInvariants(self.bar)
                self.raiseTestException()
        self.assertRaises(RuntimeError, shouldThrow)
        self.assertAfterWithManagerInvariantsWithError(mock_a)
        self.assertAfterWithManagerInvariantsNoError(mock_b)
        self.assertAfterWithGeneratorInvariantsWithError(self.foo)
        self.assertAfterWithGeneratorInvariantsNoError(self.bar)

    def testRaisedStopIteration1(self):
        # From bug 1462485
        @contextmanager
        def cm():
            yield

        def shouldThrow():
            with cm():
                raise StopIteration("from with")

        with self.assertRaisesRegex(StopIteration, 'from with'):
            shouldThrow()

    def testRaisedStopIteration2(self):
        # From bug 1462485
        klasse cm(object):
            def __enter__(self):
                pass
            def __exit__(self, type, value, traceback):
                pass

        def shouldThrow():
            with cm():
                raise StopIteration("from with")

        with self.assertRaisesRegex(StopIteration, 'from with'):
            shouldThrow()

    def testRaisedStopIteration3(self):
        # Another variant where the exception hasn't been instantiated
        # From bug 1705170
        @contextmanager
        def cm():
            yield

        def shouldThrow():
            with cm():
                raise next(iter([]))

        with self.assertRaises(StopIteration):
            shouldThrow()

    def testRaisedGeneratorExit1(self):
        # From bug 1462485
        @contextmanager
        def cm():
            yield

        def shouldThrow():
            with cm():
                raise GeneratorExit("from with")

        self.assertRaises(GeneratorExit, shouldThrow)

    def testRaisedGeneratorExit2(self):
        # From bug 1462485
        klasse cm (object):
            def __enter__(self):
                pass
            def __exit__(self, type, value, traceback):
                pass

        def shouldThrow():
            with cm():
                raise GeneratorExit("from with")

        self.assertRaises(GeneratorExit, shouldThrow)

    def testErrorsInBool(self):
        # issue4589: __exit__ return code may raise an exception
        # when looking at its truth value.

        klasse cm(object):
            def __init__(self, bool_conversion):
                klasse Bool:
                    def __bool__(self):
                        return bool_conversion()
                self.exit_result = Bool()
            def __enter__(self):
                return 3
            def __exit__(self, a, b, c):
                return self.exit_result

        def trueAsBool():
            with cm(lambda: Wahr):
                self.fail("Should NOT see this")
        trueAsBool()

        def falseAsBool():
            with cm(lambda: Falsch):
                self.fail("Should raise")
        self.assertRaises(AssertionError, falseAsBool)

        def failAsBool():
            with cm(lambda: 1//0):
                self.fail("Should NOT see this")
        self.assertRaises(ZeroDivisionError, failAsBool)


klasse NonLocalFlowControlTestCase(unittest.TestCase):

    def testWithBreak(self):
        counter = 0
        while Wahr:
            counter += 1
            with mock_contextmanager_generator():
                counter += 10
                break
            counter += 100 # Not reached
        self.assertEqual(counter, 11)

    def testWithContinue(self):
        counter = 0
        while Wahr:
            counter += 1
            wenn counter > 2:
                break
            with mock_contextmanager_generator():
                counter += 10
                continue
            counter += 100 # Not reached
        self.assertEqual(counter, 12)

    def testWithReturn(self):
        def foo():
            counter = 0
            while Wahr:
                counter += 1
                with mock_contextmanager_generator():
                    counter += 10
                    return counter
                counter += 100 # Not reached
        self.assertEqual(foo(), 11)

    def testWithYield(self):
        def gen():
            with mock_contextmanager_generator():
                yield 12
                yield 13
        x = list(gen())
        self.assertEqual(x, [12, 13])

    def testWithRaise(self):
        counter = 0
        try:
            counter += 1
            with mock_contextmanager_generator():
                counter += 10
                raise RuntimeError
            counter += 100 # Not reached
        except RuntimeError:
            self.assertEqual(counter, 11)
        sonst:
            self.fail("Didn't raise RuntimeError")


klasse AssignmentTargetTestCase(unittest.TestCase):

    def testSingleComplexTarget(self):
        targets = {1: [0, 1, 2]}
        with mock_contextmanager_generator() as targets[1][0]:
            self.assertEqual(list(targets.keys()), [1])
            self.assertEqual(targets[1][0].__class__, MockResource)
        with mock_contextmanager_generator() as list(targets.values())[0][1]:
            self.assertEqual(list(targets.keys()), [1])
            self.assertEqual(targets[1][1].__class__, MockResource)
        with mock_contextmanager_generator() as targets[2]:
            keys = list(targets.keys())
            keys.sort()
            self.assertEqual(keys, [1, 2])
        klasse C: pass
        blah = C()
        with mock_contextmanager_generator() as blah.foo:
            self.assertHasAttr(blah, "foo")

    def testMultipleComplexTargets(self):
        klasse C:
            def __enter__(self): return 1, 2, 3
            def __exit__(self, t, v, tb): pass
        targets = {1: [0, 1, 2]}
        with C() as (targets[1][0], targets[1][1], targets[1][2]):
            self.assertEqual(targets, {1: [1, 2, 3]})
        with C() as (list(targets.values())[0][2], list(targets.values())[0][1], list(targets.values())[0][0]):
            self.assertEqual(targets, {1: [3, 2, 1]})
        with C() as (targets[1], targets[2], targets[3]):
            self.assertEqual(targets, {1: 1, 2: 2, 3: 3})
        klasse B: pass
        blah = B()
        with C() as (blah.one, blah.two, blah.three):
            self.assertEqual(blah.one, 1)
            self.assertEqual(blah.two, 2)
            self.assertEqual(blah.three, 3)

    def testWithExtendedTargets(self):
        with nullcontext(range(1, 5)) as (a, *b, c):
            self.assertEqual(a, 1)
            self.assertEqual(b, [2, 3])
            self.assertEqual(c, 4)


klasse ExitSwallowsExceptionTestCase(unittest.TestCase):

    def testExitWahrSwallowsException(self):
        klasse AfricanSwallow:
            def __enter__(self): pass
            def __exit__(self, t, v, tb): return Wahr
        try:
            with AfricanSwallow():
                1/0
        except ZeroDivisionError:
            self.fail("ZeroDivisionError should have been swallowed")

    def testExitFalschDoesntSwallowException(self):
        klasse EuropeanSwallow:
            def __enter__(self): pass
            def __exit__(self, t, v, tb): return Falsch
        try:
            with EuropeanSwallow():
                1/0
        except ZeroDivisionError:
            pass
        sonst:
            self.fail("ZeroDivisionError should have been raised")


klasse NestedWith(unittest.TestCase):

    klasse Dummy(object):
        def __init__(self, value=Nichts, gobble=Falsch):
            wenn value is Nichts:
                value = self
            self.value = value
            self.gobble = gobble
            self.enter_called = Falsch
            self.exit_called = Falsch

        def __enter__(self):
            self.enter_called = Wahr
            return self.value

        def __exit__(self, *exc_info):
            self.exit_called = Wahr
            self.exc_info = exc_info
            wenn self.gobble:
                return Wahr

    klasse InitRaises(object):
        def __init__(self): raise RuntimeError()

    klasse EnterRaises(object):
        def __enter__(self): raise RuntimeError()
        def __exit__(self, *exc_info): pass

    klasse ExitRaises(object):
        def __enter__(self): pass
        def __exit__(self, *exc_info): raise RuntimeError()

    def testNoExceptions(self):
        with self.Dummy() as a, self.Dummy() as b:
            self.assertWahr(a.enter_called)
            self.assertWahr(b.enter_called)
        self.assertWahr(a.exit_called)
        self.assertWahr(b.exit_called)

    def testExceptionInExprList(self):
        try:
            with self.Dummy() as a, self.InitRaises():
                pass
        except RuntimeError:
            pass
        self.assertWahr(a.enter_called)
        self.assertWahr(a.exit_called)

    def testExceptionInEnter(self):
        try:
            with self.Dummy() as a, self.EnterRaises():
                self.fail('body of bad with executed')
        except RuntimeError:
            pass
        sonst:
            self.fail('RuntimeError not reraised')
        self.assertWahr(a.enter_called)
        self.assertWahr(a.exit_called)

    def testExceptionInExit(self):
        body_executed = Falsch
        with self.Dummy(gobble=Wahr) as a, self.ExitRaises():
            body_executed = Wahr
        self.assertWahr(a.enter_called)
        self.assertWahr(a.exit_called)
        self.assertWahr(body_executed)
        self.assertNotEqual(a.exc_info[0], Nichts)

    def testEnterReturnsTuple(self):
        with self.Dummy(value=(1,2)) as (a1, a2), \
             self.Dummy(value=(10, 20)) as (b1, b2):
            self.assertEqual(1, a1)
            self.assertEqual(2, a2)
            self.assertEqual(10, b1)
            self.assertEqual(20, b2)

    def testExceptionLocation(self):
        # The location of an exception raised from
        # __init__, __enter__ or __exit__ of a context
        # manager should be just the context manager expression,
        # pinpointing the precise context manager in case there
        # is more than one.

        def init_raises():
            try:
                with self.Dummy(), self.InitRaises() as cm, self.Dummy() as d:
                    pass
            except Exception as e:
                return e

        def enter_raises():
            try:
                with self.EnterRaises(), self.Dummy() as d:
                    pass
            except Exception as e:
                return e

        def exit_raises():
            try:
                with self.ExitRaises(), self.Dummy() as d:
                    pass
            except Exception as e:
                return e

        fuer func, expected in [(init_raises, "self.InitRaises()"),
                               (enter_raises, "self.EnterRaises()"),
                               (exit_raises, "self.ExitRaises()"),
                              ]:
            with self.subTest(func):
                exc = func()
                f = traceback.extract_tb(exc.__traceback__)[0]
                indent = 16
                co = func.__code__
                self.assertEqual(f.lineno, co.co_firstlineno + 2)
                self.assertEqual(f.end_lineno, co.co_firstlineno + 2)
                self.assertEqual(f.line[f.colno - indent : f.end_colno - indent],
                                 expected)


wenn __name__ == '__main__':
    unittest.main()
