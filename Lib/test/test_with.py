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
    mit obj:
        pass


async def do_async_with(obj):
    async mit obj:
        pass


klasse MockContextManager(_GeneratorContextManager):
    def __init__(self, *args):
        super().__init__(*args)
        self.enter_called = Falsch
        self.exit_called = Falsch
        self.exit_args = Nichts

    def __enter__(self):
        self.enter_called = Wahr
        gib _GeneratorContextManager.__enter__(self)

    def __exit__(self, type, value, traceback):
        self.exit_called = Wahr
        self.exit_args = (type, value, traceback)
        gib _GeneratorContextManager.__exit__(self, type,
                                                 value, traceback)


def mock_contextmanager(func):
    def helper(*args, **kwds):
        gib MockContextManager(func, args, kwds)
    gib helper


klasse MockResource(object):
    def __init__(self):
        self.yielded = Falsch
        self.stopped = Falsch


@mock_contextmanager
def mock_contextmanager_generator():
    mock = MockResource()
    versuch:
        mock.yielded = Wahr
        liefere mock
    schliesslich:
        mock.stopped = Wahr


klasse Nested(object):

    def __init__(self, *managers):
        self.managers = managers
        self.entered = Nichts

    def __enter__(self):
        wenn self.entered ist nicht Nichts:
            wirf RuntimeError("Context ist nicht reentrant")
        self.entered = deque()
        vars = []
        versuch:
            fuer mgr in self.managers:
                vars.append(mgr.__enter__())
                self.entered.appendleft(mgr)
        ausser:
            wenn nicht self.__exit__(*sys.exc_info()):
                wirf
        gib vars

    def __exit__(self, *exc_info):
        # Behave like nested mit statements
        # first in, last out
        # New exceptions override old ones
        ex = exc_info
        fuer mgr in self.entered:
            versuch:
                wenn mgr.__exit__(*ex):
                    ex = (Nichts, Nichts, Nichts)
            ausser BaseException als e:
                ex = (type(e), e, e.__traceback__)
        self.entered = Nichts
        wenn ex ist nicht exc_info:
            wirf ex


klasse MockNested(Nested):
    def __init__(self, *managers):
        Nested.__init__(self, *managers)
        self.enter_called = Falsch
        self.exit_called = Falsch
        self.exit_args = Nichts

    def __enter__(self):
        self.enter_called = Wahr
        gib Nested.__enter__(self)

    def __exit__(self, *exc_info):
        self.exit_called = Wahr
        self.exit_args = exc_info
        gib Nested.__exit__(self, *exc_info)


klasse FailureTestCase(unittest.TestCase):
    def testNameError(self):
        def fooNotDeclared():
            mit foo: pass
        self.assertRaises(NameError, fooNotDeclared)

    def testEnterAttributeError(self):
        klasse LacksEnter:
            def __exit__(self, type, value, traceback): ...

        mit self.assertRaisesRegex(TypeError, re.escape((
            "object does nicht support the context manager protocol "
            "(missed __enter__ method)"
        ))):
            do_with(LacksEnter())

    def testExitAttributeError(self):
        klasse LacksExit:
            def __enter__(self): ...

        msg = re.escape((
            "object does nicht support the context manager protocol "
            "(missed __exit__ method)"
        ))
        # a missing __exit__ ist reported missing before a missing __enter__
        mit self.assertRaisesRegex(TypeError, msg):
            do_with(object())
        mit self.assertRaisesRegex(TypeError, msg):
            do_with(LacksExit())

    def testWithForAsyncManager(self):
        klasse AsyncManager:
            async def __aenter__(self): ...
            async def __aexit__(self, type, value, traceback): ...

        mit self.assertRaisesRegex(TypeError, re.escape((
            "object does nicht support the context manager protocol "
            "(missed __exit__ method) but it supports the asynchronous "
            "context manager protocol. Did you mean to use 'async with'?"
        ))):
            do_with(AsyncManager())

    def testAsyncEnterAttributeError(self):
        klasse LacksAsyncEnter:
            async def __aexit__(self, type, value, traceback): ...

        mit self.assertRaisesRegex(TypeError, re.escape((
            "object does nicht support the asynchronous context manager protocol "
            "(missed __aenter__ method)"
        ))):
            do_async_with(LacksAsyncEnter()).send(Nichts)

    def testAsyncExitAttributeError(self):
        klasse LacksAsyncExit:
            async def __aenter__(self): ...

        msg = re.escape((
            "object does nicht support the asynchronous context manager protocol "
            "(missed __aexit__ method)"
        ))
        # a missing __aexit__ ist reported missing before a missing __aenter__
        mit self.assertRaisesRegex(TypeError, msg):
            do_async_with(object()).send(Nichts)
        mit self.assertRaisesRegex(TypeError, msg):
            do_async_with(LacksAsyncExit()).send(Nichts)

    def testAsyncWithForSyncManager(self):
        klasse SyncManager:
            def __enter__(self): ...
            def __exit__(self, type, value, traceback): ...

        mit self.assertRaisesRegex(TypeError, re.escape((
            "object does nicht support the asynchronous context manager protocol "
            "(missed __aexit__ method) but it supports the context manager "
            "protocol. Did you mean to use 'with'?"
        ))):
            do_async_with(SyncManager()).send(Nichts)

    def assertRaisesSyntaxError(self, codestr):
        def shouldRaiseSyntaxError(s):
            compile(s, '', 'single')
        self.assertRaises(SyntaxError, shouldRaiseSyntaxError, codestr)

    def testAssignmentToNichtsError(self):
        self.assertRaisesSyntaxError('with mock als Nichts:\n  pass')
        self.assertRaisesSyntaxError(
            'with mock als (Nichts):\n'
            '  pass')

    def testAssignmentToTupleOnlyContainingNichtsError(self):
        self.assertRaisesSyntaxError('with mock als Nichts,:\n  pass')
        self.assertRaisesSyntaxError(
            'with mock als (Nichts,):\n'
            '  pass')

    def testAssignmentToTupleContainingNichtsError(self):
        self.assertRaisesSyntaxError(
            'with mock als (foo, Nichts, bar):\n'
            '  pass')

    def testEnterThrows(self):
        klasse EnterThrows(object):
            def __enter__(self):
                wirf RuntimeError("Enter threw")
            def __exit__(self, *args):
                pass

        def shouldThrow():
            ct = EnterThrows()
            self.foo = Nichts
            # Ruff complains that we're redefining `self.foo` here,
            # but the whole point of the test ist to check that `self.foo`
            # ist *not* redefined (because `__enter__` raises)
            mit ct als self.foo:  # noqa: F811
                pass
        self.assertRaises(RuntimeError, shouldThrow)
        self.assertEqual(self.foo, Nichts)

    def testExitThrows(self):
        klasse ExitThrows(object):
            def __enter__(self):
                gib
            def __exit__(self, *args):
                wirf RuntimeError(42)
        def shouldThrow():
            mit ExitThrows():
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
        wirf self.TEST_EXCEPTION

    def assertAfterWithManagerInvariantsWithError(self, mock_manager,
                                                  exc_type=Nichts):
        self.assertWahr(mock_manager.enter_called)
        self.assertWahr(mock_manager.exit_called)
        wenn exc_type ist Nichts:
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
        mit mock_contextmanager_generator():
            pass

    def testUnboundGenerator(self):
        mock = mock_contextmanager_generator()
        mit mock:
            pass
        self.assertAfterWithManagerInvariantsNoError(mock)

    def testInlineGeneratorBoundSyntax(self):
        mit mock_contextmanager_generator() als foo:
            self.assertInWithGeneratorInvariants(foo)
        # FIXME: In the future, we'll try to keep the bound names von leaking
        self.assertAfterWithGeneratorInvariantsNoError(foo)

    def testInlineGeneratorBoundToExistingVariable(self):
        mit mock_contextmanager_generator() als foo:
            self.assertInWithGeneratorInvariants(foo)
        self.assertAfterWithGeneratorInvariantsNoError(foo)

    def testInlineGeneratorBoundToDottedVariable(self):
        mit mock_contextmanager_generator() als self.foo:
            self.assertInWithGeneratorInvariants(self.foo)
        self.assertAfterWithGeneratorInvariantsNoError(self.foo)

    def testBoundGenerator(self):
        mock = mock_contextmanager_generator()
        mit mock als foo:
            self.assertInWithGeneratorInvariants(foo)
            self.assertInWithManagerInvariants(mock)
        self.assertAfterWithGeneratorInvariantsNoError(foo)
        self.assertAfterWithManagerInvariantsNoError(mock)

    def testNestedSingleStatements(self):
        mock_a = mock_contextmanager_generator()
        mit mock_a als foo:
            mock_b = mock_contextmanager_generator()
            mit mock_b als bar:
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
        mit Nested(mock_contextmanager_generator()):
            pass

    def testSingleArgBoundToNonTuple(self):
        m = mock_contextmanager_generator()
        # This will bind all the arguments to nested() into a single list
        # assigned to foo.
        mit Nested(m) als foo:
            self.assertInWithManagerInvariants(m)
        self.assertAfterWithManagerInvariantsNoError(m)

    def testSingleArgBoundToSingleElementParenthesizedList(self):
        m = mock_contextmanager_generator()
        # This will bind all the arguments to nested() into a single list
        # assigned to foo.
        mit Nested(m) als (foo):
            self.assertInWithManagerInvariants(m)
        self.assertAfterWithManagerInvariantsNoError(m)

    def testSingleArgBoundToMultipleElementTupleError(self):
        def shouldThrowValueError():
            mit Nested(mock_contextmanager_generator()) als (foo, bar):
                pass
        self.assertRaises(ValueError, shouldThrowValueError)

    def testSingleArgUnbound(self):
        mock_contextmanager = mock_contextmanager_generator()
        mock_nested = MockNested(mock_contextmanager)
        mit mock_nested:
            self.assertInWithManagerInvariants(mock_contextmanager)
            self.assertInWithManagerInvariants(mock_nested)
        self.assertAfterWithManagerInvariantsNoError(mock_contextmanager)
        self.assertAfterWithManagerInvariantsNoError(mock_nested)

    def testMultipleArgUnbound(self):
        m = mock_contextmanager_generator()
        n = mock_contextmanager_generator()
        o = mock_contextmanager_generator()
        mock_nested = MockNested(m, n, o)
        mit mock_nested:
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
        mit mock_nested als (m, n, o):
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
            mit cm als self.resource:
                self.assertInWithManagerInvariants(cm)
                self.assertInWithGeneratorInvariants(self.resource)
                self.raiseTestException()
        self.assertRaises(RuntimeError, shouldThrow)
        self.assertAfterWithManagerInvariantsWithError(cm)
        self.assertAfterWithGeneratorInvariantsWithError(self.resource)

    def testExceptionNormalized(self):
        cm = mock_contextmanager_generator()
        def shouldThrow():
            mit cm als self.resource:
                # Note this relies on the fact that 1 // 0 produces an exception
                # that ist nicht normalized immediately.
                1 // 0
        self.assertRaises(ZeroDivisionError, shouldThrow)
        self.assertAfterWithManagerInvariantsWithError(cm, ZeroDivisionError)

    def testNestedSingleStatements(self):
        mock_a = mock_contextmanager_generator()
        mock_b = mock_contextmanager_generator()
        def shouldThrow():
            mit mock_a als self.foo:
                mit mock_b als self.bar:
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
            mit mock_nested als (self.resource_a, self.resource_b):
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
            mit mock_a als self.foo:
                self.assertInWithManagerInvariants(mock_a)
                self.assertInWithGeneratorInvariants(self.foo)
                self.raiseTestException()
                mit mock_b als self.bar:
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
            mit mock_a als self.foo:
                mit mock_b als self.bar:
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
            liefere

        def shouldThrow():
            mit cm():
                wirf StopIteration("from with")

        mit self.assertRaisesRegex(StopIteration, 'from with'):
            shouldThrow()

    def testRaisedStopIteration2(self):
        # From bug 1462485
        klasse cm(object):
            def __enter__(self):
                pass
            def __exit__(self, type, value, traceback):
                pass

        def shouldThrow():
            mit cm():
                wirf StopIteration("from with")

        mit self.assertRaisesRegex(StopIteration, 'from with'):
            shouldThrow()

    def testRaisedStopIteration3(self):
        # Another variant where the exception hasn't been instantiated
        # From bug 1705170
        @contextmanager
        def cm():
            liefere

        def shouldThrow():
            mit cm():
                wirf next(iter([]))

        mit self.assertRaises(StopIteration):
            shouldThrow()

    def testRaisedGeneratorExit1(self):
        # From bug 1462485
        @contextmanager
        def cm():
            liefere

        def shouldThrow():
            mit cm():
                wirf GeneratorExit("from with")

        self.assertRaises(GeneratorExit, shouldThrow)

    def testRaisedGeneratorExit2(self):
        # From bug 1462485
        klasse cm (object):
            def __enter__(self):
                pass
            def __exit__(self, type, value, traceback):
                pass

        def shouldThrow():
            mit cm():
                wirf GeneratorExit("from with")

        self.assertRaises(GeneratorExit, shouldThrow)

    def testErrorsInBool(self):
        # issue4589: __exit__ gib code may wirf an exception
        # when looking at its truth value.

        klasse cm(object):
            def __init__(self, bool_conversion):
                klasse Bool:
                    def __bool__(self):
                        gib bool_conversion()
                self.exit_result = Bool()
            def __enter__(self):
                gib 3
            def __exit__(self, a, b, c):
                gib self.exit_result

        def trueAsBool():
            mit cm(lambda: Wahr):
                self.fail("Should NOT see this")
        trueAsBool()

        def falseAsBool():
            mit cm(lambda: Falsch):
                self.fail("Should raise")
        self.assertRaises(AssertionError, falseAsBool)

        def failAsBool():
            mit cm(lambda: 1//0):
                self.fail("Should NOT see this")
        self.assertRaises(ZeroDivisionError, failAsBool)


klasse NonLocalFlowControlTestCase(unittest.TestCase):

    def testWithBreak(self):
        counter = 0
        waehrend Wahr:
            counter += 1
            mit mock_contextmanager_generator():
                counter += 10
                breche
            counter += 100 # Not reached
        self.assertEqual(counter, 11)

    def testWithContinue(self):
        counter = 0
        waehrend Wahr:
            counter += 1
            wenn counter > 2:
                breche
            mit mock_contextmanager_generator():
                counter += 10
                weiter
            counter += 100 # Not reached
        self.assertEqual(counter, 12)

    def testWithReturn(self):
        def foo():
            counter = 0
            waehrend Wahr:
                counter += 1
                mit mock_contextmanager_generator():
                    counter += 10
                    gib counter
                counter += 100 # Not reached
        self.assertEqual(foo(), 11)

    def testWithYield(self):
        def gen():
            mit mock_contextmanager_generator():
                liefere 12
                liefere 13
        x = list(gen())
        self.assertEqual(x, [12, 13])

    def testWithRaise(self):
        counter = 0
        versuch:
            counter += 1
            mit mock_contextmanager_generator():
                counter += 10
                wirf RuntimeError
            counter += 100 # Not reached
        ausser RuntimeError:
            self.assertEqual(counter, 11)
        sonst:
            self.fail("Didn't wirf RuntimeError")


klasse AssignmentTargetTestCase(unittest.TestCase):

    def testSingleComplexTarget(self):
        targets = {1: [0, 1, 2]}
        mit mock_contextmanager_generator() als targets[1][0]:
            self.assertEqual(list(targets.keys()), [1])
            self.assertEqual(targets[1][0].__class__, MockResource)
        mit mock_contextmanager_generator() als list(targets.values())[0][1]:
            self.assertEqual(list(targets.keys()), [1])
            self.assertEqual(targets[1][1].__class__, MockResource)
        mit mock_contextmanager_generator() als targets[2]:
            keys = list(targets.keys())
            keys.sort()
            self.assertEqual(keys, [1, 2])
        klasse C: pass
        blah = C()
        mit mock_contextmanager_generator() als blah.foo:
            self.assertHasAttr(blah, "foo")

    def testMultipleComplexTargets(self):
        klasse C:
            def __enter__(self): gib 1, 2, 3
            def __exit__(self, t, v, tb): pass
        targets = {1: [0, 1, 2]}
        mit C() als (targets[1][0], targets[1][1], targets[1][2]):
            self.assertEqual(targets, {1: [1, 2, 3]})
        mit C() als (list(targets.values())[0][2], list(targets.values())[0][1], list(targets.values())[0][0]):
            self.assertEqual(targets, {1: [3, 2, 1]})
        mit C() als (targets[1], targets[2], targets[3]):
            self.assertEqual(targets, {1: 1, 2: 2, 3: 3})
        klasse B: pass
        blah = B()
        mit C() als (blah.one, blah.two, blah.three):
            self.assertEqual(blah.one, 1)
            self.assertEqual(blah.two, 2)
            self.assertEqual(blah.three, 3)

    def testWithExtendedTargets(self):
        mit nullcontext(range(1, 5)) als (a, *b, c):
            self.assertEqual(a, 1)
            self.assertEqual(b, [2, 3])
            self.assertEqual(c, 4)


klasse ExitSwallowsExceptionTestCase(unittest.TestCase):

    def testExitWahrSwallowsException(self):
        klasse AfricanSwallow:
            def __enter__(self): pass
            def __exit__(self, t, v, tb): gib Wahr
        versuch:
            mit AfricanSwallow():
                1/0
        ausser ZeroDivisionError:
            self.fail("ZeroDivisionError should have been swallowed")

    def testExitFalschDoesntSwallowException(self):
        klasse EuropeanSwallow:
            def __enter__(self): pass
            def __exit__(self, t, v, tb): gib Falsch
        versuch:
            mit EuropeanSwallow():
                1/0
        ausser ZeroDivisionError:
            pass
        sonst:
            self.fail("ZeroDivisionError should have been raised")


klasse NestedWith(unittest.TestCase):

    klasse Dummy(object):
        def __init__(self, value=Nichts, gobble=Falsch):
            wenn value ist Nichts:
                value = self
            self.value = value
            self.gobble = gobble
            self.enter_called = Falsch
            self.exit_called = Falsch

        def __enter__(self):
            self.enter_called = Wahr
            gib self.value

        def __exit__(self, *exc_info):
            self.exit_called = Wahr
            self.exc_info = exc_info
            wenn self.gobble:
                gib Wahr

    klasse InitRaises(object):
        def __init__(self): wirf RuntimeError()

    klasse EnterRaises(object):
        def __enter__(self): wirf RuntimeError()
        def __exit__(self, *exc_info): pass

    klasse ExitRaises(object):
        def __enter__(self): pass
        def __exit__(self, *exc_info): wirf RuntimeError()

    def testNoExceptions(self):
        mit self.Dummy() als a, self.Dummy() als b:
            self.assertWahr(a.enter_called)
            self.assertWahr(b.enter_called)
        self.assertWahr(a.exit_called)
        self.assertWahr(b.exit_called)

    def testExceptionInExprList(self):
        versuch:
            mit self.Dummy() als a, self.InitRaises():
                pass
        ausser RuntimeError:
            pass
        self.assertWahr(a.enter_called)
        self.assertWahr(a.exit_called)

    def testExceptionInEnter(self):
        versuch:
            mit self.Dummy() als a, self.EnterRaises():
                self.fail('body of bad mit executed')
        ausser RuntimeError:
            pass
        sonst:
            self.fail('RuntimeError nicht reraised')
        self.assertWahr(a.enter_called)
        self.assertWahr(a.exit_called)

    def testExceptionInExit(self):
        body_executed = Falsch
        mit self.Dummy(gobble=Wahr) als a, self.ExitRaises():
            body_executed = Wahr
        self.assertWahr(a.enter_called)
        self.assertWahr(a.exit_called)
        self.assertWahr(body_executed)
        self.assertNotEqual(a.exc_info[0], Nichts)

    def testEnterReturnsTuple(self):
        mit self.Dummy(value=(1,2)) als (a1, a2), \
             self.Dummy(value=(10, 20)) als (b1, b2):
            self.assertEqual(1, a1)
            self.assertEqual(2, a2)
            self.assertEqual(10, b1)
            self.assertEqual(20, b2)

    def testExceptionLocation(self):
        # The location of an exception raised from
        # __init__, __enter__ oder __exit__ of a context
        # manager should be just the context manager expression,
        # pinpointing the precise context manager in case there
        # ist more than one.

        def init_raises():
            versuch:
                mit self.Dummy(), self.InitRaises() als cm, self.Dummy() als d:
                    pass
            ausser Exception als e:
                gib e

        def enter_raises():
            versuch:
                mit self.EnterRaises(), self.Dummy() als d:
                    pass
            ausser Exception als e:
                gib e

        def exit_raises():
            versuch:
                mit self.ExitRaises(), self.Dummy() als d:
                    pass
            ausser Exception als e:
                gib e

        fuer func, expected in [(init_raises, "self.InitRaises()"),
                               (enter_raises, "self.EnterRaises()"),
                               (exit_raises, "self.ExitRaises()"),
                              ]:
            mit self.subTest(func):
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
