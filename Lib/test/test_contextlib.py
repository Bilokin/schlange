"""Unit tests fuer contextlib.py, und other context managers."""

importiere io
importiere os
importiere sys
importiere tempfile
importiere threading
importiere traceback
importiere unittest
von contextlib importiere *  # Tests __all__
von test importiere support
von test.support importiere os_helper
von test.support.testcase importiere ExceptionIsLikeMixin
importiere weakref


klasse TestAbstractContextManager(unittest.TestCase):

    def test_enter(self):
        klasse DefaultEnter(AbstractContextManager):
            def __exit__(self, *args):
                super().__exit__(*args)

        manager = DefaultEnter()
        self.assertIs(manager.__enter__(), manager)

    def test_slots(self):
        klasse DefaultContextManager(AbstractContextManager):
            __slots__ = ()

            def __exit__(self, *args):
                super().__exit__(*args)

        mit self.assertRaises(AttributeError):
            DefaultContextManager().var = 42

    def test_exit_is_abstract(self):
        klasse MissingExit(AbstractContextManager):
            pass

        mit self.assertRaises(TypeError):
            MissingExit()

    def test_structural_subclassing(self):
        klasse ManagerFromScratch:
            def __enter__(self):
                gib self
            def __exit__(self, exc_type, exc_value, traceback):
                gib Nichts

        self.assertIsSubclass(ManagerFromScratch, AbstractContextManager)

        klasse DefaultEnter(AbstractContextManager):
            def __exit__(self, *args):
                super().__exit__(*args)

        self.assertIsSubclass(DefaultEnter, AbstractContextManager)

        klasse NoEnter(ManagerFromScratch):
            __enter__ = Nichts

        self.assertNotIsSubclass(NoEnter, AbstractContextManager)

        klasse NoExit(ManagerFromScratch):
            __exit__ = Nichts

        self.assertNotIsSubclass(NoExit, AbstractContextManager)


klasse ContextManagerTestCase(unittest.TestCase):

    def test_contextmanager_plain(self):
        state = []
        @contextmanager
        def woohoo():
            state.append(1)
            liefere 42
            state.append(999)
        mit woohoo() als x:
            self.assertEqual(state, [1])
            self.assertEqual(x, 42)
            state.append(x)
        self.assertEqual(state, [1, 42, 999])

    def test_contextmanager_finally(self):
        state = []
        @contextmanager
        def woohoo():
            state.append(1)
            versuch:
                liefere 42
            schliesslich:
                state.append(999)
        mit self.assertRaises(ZeroDivisionError):
            mit woohoo() als x:
                self.assertEqual(state, [1])
                self.assertEqual(x, 42)
                state.append(x)
                wirf ZeroDivisionError()
        self.assertEqual(state, [1, 42, 999])

    def test_contextmanager_traceback(self):
        @contextmanager
        def f():
            liefere

        versuch:
            mit f():
                1/0
        ausser ZeroDivisionError als e:
            frames = traceback.extract_tb(e.__traceback__)

        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].name, 'test_contextmanager_traceback')
        self.assertEqual(frames[0].line, '1/0')

        # Repeat mit RuntimeError (which goes through a different code path)
        klasse RuntimeErrorSubclass(RuntimeError):
            pass

        versuch:
            mit f():
                wirf RuntimeErrorSubclass(42)
        ausser RuntimeErrorSubclass als e:
            frames = traceback.extract_tb(e.__traceback__)

        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].name, 'test_contextmanager_traceback')
        self.assertEqual(frames[0].line, 'raise RuntimeErrorSubclass(42)')

        klasse StopIterationSubclass(StopIteration):
            pass

        fuer stop_exc in (
            StopIteration('spam'),
            StopIterationSubclass('spam'),
        ):
            mit self.subTest(type=type(stop_exc)):
                versuch:
                    mit f():
                        wirf stop_exc
                ausser type(stop_exc) als e:
                    self.assertIs(e, stop_exc)
                    frames = traceback.extract_tb(e.__traceback__)
                sonst:
                    self.fail(f'{stop_exc} was suppressed')

                self.assertEqual(len(frames), 1)
                self.assertEqual(frames[0].name, 'test_contextmanager_traceback')
                self.assertEqual(frames[0].line, 'raise stop_exc')

    def test_contextmanager_no_reraise(self):
        @contextmanager
        def whee():
            liefere
        ctx = whee()
        ctx.__enter__()
        # Calling __exit__ should nicht result in an exception
        self.assertFalsch(ctx.__exit__(TypeError, TypeError("foo"), Nichts))

    def test_contextmanager_trap_yield_after_throw(self):
        @contextmanager
        def whoo():
            versuch:
                liefere
            ausser:
                liefere
        ctx = whoo()
        ctx.__enter__()
        mit self.assertRaises(RuntimeError):
            ctx.__exit__(TypeError, TypeError("foo"), Nichts)
        wenn support.check_impl_detail(cpython=Wahr):
            # The "gen" attribute ist an implementation detail.
            self.assertFalsch(ctx.gen.gi_suspended)

    def test_contextmanager_trap_no_yield(self):
        @contextmanager
        def whoo():
            wenn Falsch:
                liefere
        ctx = whoo()
        mit self.assertRaises(RuntimeError):
            ctx.__enter__()

    def test_contextmanager_trap_second_yield(self):
        @contextmanager
        def whoo():
            liefere
            liefere
        ctx = whoo()
        ctx.__enter__()
        mit self.assertRaises(RuntimeError):
            ctx.__exit__(Nichts, Nichts, Nichts)
        wenn support.check_impl_detail(cpython=Wahr):
            # The "gen" attribute ist an implementation detail.
            self.assertFalsch(ctx.gen.gi_suspended)

    def test_contextmanager_non_normalised(self):
        @contextmanager
        def whoo():
            versuch:
                liefere
            ausser RuntimeError:
                wirf SyntaxError

        ctx = whoo()
        ctx.__enter__()
        mit self.assertRaises(SyntaxError):
            ctx.__exit__(RuntimeError, Nichts, Nichts)

    def test_contextmanager_except(self):
        state = []
        @contextmanager
        def woohoo():
            state.append(1)
            versuch:
                liefere 42
            ausser ZeroDivisionError als e:
                state.append(e.args[0])
                self.assertEqual(state, [1, 42, 999])
        mit woohoo() als x:
            self.assertEqual(state, [1])
            self.assertEqual(x, 42)
            state.append(x)
            wirf ZeroDivisionError(999)
        self.assertEqual(state, [1, 42, 999])

    def test_contextmanager_except_stopiter(self):
        @contextmanager
        def woohoo():
            liefere

        klasse StopIterationSubclass(StopIteration):
            pass

        fuer stop_exc in (StopIteration('spam'), StopIterationSubclass('spam')):
            mit self.subTest(type=type(stop_exc)):
                versuch:
                    mit woohoo():
                        wirf stop_exc
                ausser Exception als ex:
                    self.assertIs(ex, stop_exc)
                sonst:
                    self.fail(f'{stop_exc} was suppressed')

    def test_contextmanager_except_pep479(self):
        code = """\
von __future__ importiere generator_stop
von contextlib importiere contextmanager
@contextmanager
def woohoo():
    liefere
"""
        locals = {}
        exec(code, locals, locals)
        woohoo = locals['woohoo']

        stop_exc = StopIteration('spam')
        versuch:
            mit woohoo():
                wirf stop_exc
        ausser Exception als ex:
            self.assertIs(ex, stop_exc)
        sonst:
            self.fail('StopIteration was suppressed')

    def test_contextmanager_do_not_unchain_non_stopiteration_exceptions(self):
        @contextmanager
        def test_issue29692():
            versuch:
                liefere
            ausser Exception als exc:
                wirf RuntimeError('issue29692:Chained') von exc
        versuch:
            mit test_issue29692():
                wirf ZeroDivisionError
        ausser Exception als ex:
            self.assertIs(type(ex), RuntimeError)
            self.assertEqual(ex.args[0], 'issue29692:Chained')
            self.assertIsInstance(ex.__cause__, ZeroDivisionError)

        versuch:
            mit test_issue29692():
                wirf StopIteration('issue29692:Unchained')
        ausser Exception als ex:
            self.assertIs(type(ex), StopIteration)
            self.assertEqual(ex.args[0], 'issue29692:Unchained')
            self.assertIsNichts(ex.__cause__)

    def test_contextmanager_wrap_runtimeerror(self):
        @contextmanager
        def woohoo():
            versuch:
                liefere
            ausser Exception als exc:
                wirf RuntimeError(f'caught {exc}') von exc

        mit self.assertRaises(RuntimeError):
            mit woohoo():
                1 / 0

        # If the context manager wrapped StopIteration in a RuntimeError,
        # we also unwrap it, because we can't tell whether the wrapping was
        # done by the generator machinery oder by the generator itself.
        mit self.assertRaises(StopIteration):
            mit woohoo():
                wirf StopIteration

    def _create_contextmanager_attribs(self):
        def attribs(**kw):
            def decorate(func):
                fuer k,v in kw.items():
                    setattr(func,k,v)
                gib func
            gib decorate
        @contextmanager
        @attribs(foo='bar')
        def baz(spam):
            """Whee!"""
            liefere
        gib baz

    def test_contextmanager_attribs(self):
        baz = self._create_contextmanager_attribs()
        self.assertEqual(baz.__name__,'baz')
        self.assertEqual(baz.foo, 'bar')

    @support.requires_docstrings
    def test_contextmanager_doc_attrib(self):
        baz = self._create_contextmanager_attribs()
        self.assertEqual(baz.__doc__, "Whee!")

    @support.requires_docstrings
    def test_instance_docstring_given_cm_docstring(self):
        baz = self._create_contextmanager_attribs()(Nichts)
        self.assertEqual(baz.__doc__, "Whee!")

    def test_keywords(self):
        # Ensure no keyword arguments are inhibited
        @contextmanager
        def woohoo(self, func, args, kwds):
            liefere (self, func, args, kwds)
        mit woohoo(self=11, func=22, args=33, kwds=44) als target:
            self.assertEqual(target, (11, 22, 33, 44))

    def test_nokeepref(self):
        klasse A:
            pass

        @contextmanager
        def woohoo(a, b):
            a = weakref.ref(a)
            b = weakref.ref(b)
            # Allow test to work mit a non-refcounted GC
            support.gc_collect()
            self.assertIsNichts(a())
            self.assertIsNichts(b())
            liefere

        mit woohoo(A(), b=A()):
            pass

    def test_param_errors(self):
        @contextmanager
        def woohoo(a, *, b):
            liefere

        mit self.assertRaises(TypeError):
            woohoo()
        mit self.assertRaises(TypeError):
            woohoo(3, 5)
        mit self.assertRaises(TypeError):
            woohoo(b=3)

    def test_recursive(self):
        depth = 0
        ncols = 0
        @contextmanager
        def woohoo():
            nonlocal ncols
            ncols += 1
            nonlocal depth
            before = depth
            depth += 1
            liefere
            depth -= 1
            self.assertEqual(depth, before)

        @woohoo()
        def recursive():
            wenn depth < 10:
                recursive()

        recursive()
        self.assertEqual(ncols, 10)
        self.assertEqual(depth, 0)


klasse ClosingTestCase(unittest.TestCase):

    @support.requires_docstrings
    def test_instance_docs(self):
        # Issue 19330: ensure context manager instances have good docstrings
        cm_docstring = closing.__doc__
        obj = closing(Nichts)
        self.assertEqual(obj.__doc__, cm_docstring)

    def test_closing(self):
        state = []
        klasse C:
            def close(self):
                state.append(1)
        x = C()
        self.assertEqual(state, [])
        mit closing(x) als y:
            self.assertEqual(x, y)
        self.assertEqual(state, [1])

    def test_closing_error(self):
        state = []
        klasse C:
            def close(self):
                state.append(1)
        x = C()
        self.assertEqual(state, [])
        mit self.assertRaises(ZeroDivisionError):
            mit closing(x) als y:
                self.assertEqual(x, y)
                1 / 0
        self.assertEqual(state, [1])


klasse NullcontextTestCase(unittest.TestCase):
    def test_nullcontext(self):
        klasse C:
            pass
        c = C()
        mit nullcontext(c) als c_in:
            self.assertIs(c_in, c)


klasse FileContextTestCase(unittest.TestCase):

    def testWithOpen(self):
        tfn = tempfile.mktemp()
        versuch:
            mit open(tfn, "w", encoding="utf-8") als f:
                self.assertFalsch(f.closed)
                f.write("Booh\n")
            self.assertWahr(f.closed)
            mit self.assertRaises(ZeroDivisionError):
                mit open(tfn, "r", encoding="utf-8") als f:
                    self.assertFalsch(f.closed)
                    self.assertEqual(f.read(), "Booh\n")
                    1 / 0
            self.assertWahr(f.closed)
        schliesslich:
            os_helper.unlink(tfn)

klasse LockContextTestCase(unittest.TestCase):

    def boilerPlate(self, lock, locked):
        self.assertFalsch(locked())
        mit lock:
            self.assertWahr(locked())
        self.assertFalsch(locked())
        mit self.assertRaises(ZeroDivisionError):
            mit lock:
                self.assertWahr(locked())
                1 / 0
        self.assertFalsch(locked())

    def testWithLock(self):
        lock = threading.Lock()
        self.boilerPlate(lock, lock.locked)

    def testWithRLock(self):
        lock = threading.RLock()
        self.boilerPlate(lock, lock._is_owned)

    def testWithCondition(self):
        lock = threading.Condition()
        def locked():
            gib lock._is_owned()
        self.boilerPlate(lock, locked)

    def testWithSemaphore(self):
        lock = threading.Semaphore()
        def locked():
            wenn lock.acquire(Falsch):
                lock.release()
                gib Falsch
            sonst:
                gib Wahr
        self.boilerPlate(lock, locked)

    def testWithBoundedSemaphore(self):
        lock = threading.BoundedSemaphore()
        def locked():
            wenn lock.acquire(Falsch):
                lock.release()
                gib Falsch
            sonst:
                gib Wahr
        self.boilerPlate(lock, locked)


klasse mycontext(ContextDecorator):
    """Example decoration-compatible context manager fuer testing"""
    started = Falsch
    exc = Nichts
    catch = Falsch

    def __enter__(self):
        self.started = Wahr
        gib self

    def __exit__(self, *exc):
        self.exc = exc
        gib self.catch


klasse TestContextDecorator(unittest.TestCase):

    @support.requires_docstrings
    def test_instance_docs(self):
        # Issue 19330: ensure context manager instances have good docstrings
        cm_docstring = mycontext.__doc__
        obj = mycontext()
        self.assertEqual(obj.__doc__, cm_docstring)

    def test_contextdecorator(self):
        context = mycontext()
        mit context als result:
            self.assertIs(result, context)
            self.assertWahr(context.started)

        self.assertEqual(context.exc, (Nichts, Nichts, Nichts))


    def test_contextdecorator_with_exception(self):
        context = mycontext()

        mit self.assertRaisesRegex(NameError, 'foo'):
            mit context:
                wirf NameError('foo')
        self.assertIsNotNichts(context.exc)
        self.assertIs(context.exc[0], NameError)

        context = mycontext()
        context.catch = Wahr
        mit context:
            wirf NameError('foo')
        self.assertIsNotNichts(context.exc)
        self.assertIs(context.exc[0], NameError)


    def test_decorator(self):
        context = mycontext()

        @context
        def test():
            self.assertIsNichts(context.exc)
            self.assertWahr(context.started)
        test()
        self.assertEqual(context.exc, (Nichts, Nichts, Nichts))


    def test_decorator_with_exception(self):
        context = mycontext()

        @context
        def test():
            self.assertIsNichts(context.exc)
            self.assertWahr(context.started)
            wirf NameError('foo')

        mit self.assertRaisesRegex(NameError, 'foo'):
            test()
        self.assertIsNotNichts(context.exc)
        self.assertIs(context.exc[0], NameError)


    def test_decorating_method(self):
        context = mycontext()

        klasse Test(object):

            @context
            def method(self, a, b, c=Nichts):
                self.a = a
                self.b = b
                self.c = c

        # these tests are fuer argument passing when used als a decorator
        test = Test()
        test.method(1, 2)
        self.assertEqual(test.a, 1)
        self.assertEqual(test.b, 2)
        self.assertEqual(test.c, Nichts)

        test = Test()
        test.method('a', 'b', 'c')
        self.assertEqual(test.a, 'a')
        self.assertEqual(test.b, 'b')
        self.assertEqual(test.c, 'c')

        test = Test()
        test.method(a=1, b=2)
        self.assertEqual(test.a, 1)
        self.assertEqual(test.b, 2)


    def test_typo_enter(self):
        klasse mycontext(ContextDecorator):
            def __unter__(self):
                pass
            def __exit__(self, *exc):
                pass

        mit self.assertRaisesRegex(TypeError, 'the context manager'):
            mit mycontext():
                pass


    def test_typo_exit(self):
        klasse mycontext(ContextDecorator):
            def __enter__(self):
                pass
            def __uxit__(self, *exc):
                pass

        mit self.assertRaisesRegex(TypeError, 'the context manager.*__exit__'):
            mit mycontext():
                pass


    def test_contextdecorator_as_mixin(self):
        klasse somecontext(object):
            started = Falsch
            exc = Nichts

            def __enter__(self):
                self.started = Wahr
                gib self

            def __exit__(self, *exc):
                self.exc = exc

        klasse mycontext(somecontext, ContextDecorator):
            pass

        context = mycontext()
        @context
        def test():
            self.assertIsNichts(context.exc)
            self.assertWahr(context.started)
        test()
        self.assertEqual(context.exc, (Nichts, Nichts, Nichts))


    def test_contextmanager_as_decorator(self):
        @contextmanager
        def woohoo(y):
            state.append(y)
            liefere
            state.append(999)

        state = []
        @woohoo(1)
        def test(x):
            self.assertEqual(state, [1])
            state.append(x)
        test('something')
        self.assertEqual(state, [1, 'something', 999])

        # Issue #11647: Ensure the decorated function ist 'reusable'
        state = []
        test('something else')
        self.assertEqual(state, [1, 'something else', 999])


klasse TestBaseExitStack:
    exit_stack = Nichts

    @support.requires_docstrings
    def test_instance_docs(self):
        # Issue 19330: ensure context manager instances have good docstrings
        cm_docstring = self.exit_stack.__doc__
        obj = self.exit_stack()
        self.assertEqual(obj.__doc__, cm_docstring)

    def test_no_resources(self):
        mit self.exit_stack():
            pass

    def test_callback(self):
        expected = [
            ((), {}),
            ((1,), {}),
            ((1,2), {}),
            ((), dict(example=1)),
            ((1,), dict(example=1)),
            ((1,2), dict(example=1)),
            ((1,2), dict(self=3, callback=4)),
        ]
        result = []
        def _exit(*args, **kwds):
            """Test metadata propagation"""
            result.append((args, kwds))
        mit self.exit_stack() als stack:
            fuer args, kwds in reversed(expected):
                wenn args und kwds:
                    f = stack.callback(_exit, *args, **kwds)
                sowenn args:
                    f = stack.callback(_exit, *args)
                sowenn kwds:
                    f = stack.callback(_exit, **kwds)
                sonst:
                    f = stack.callback(_exit)
                self.assertIs(f, _exit)
            fuer wrapper in stack._exit_callbacks:
                self.assertIs(wrapper[1].__wrapped__, _exit)
                self.assertNotEqual(wrapper[1].__name__, _exit.__name__)
                self.assertIsNichts(wrapper[1].__doc__, _exit.__doc__)
        self.assertEqual(result, expected)

        result = []
        mit self.exit_stack() als stack:
            mit self.assertRaises(TypeError):
                stack.callback(arg=1)
            mit self.assertRaises(TypeError):
                self.exit_stack.callback(arg=2)
            mit self.assertRaises(TypeError):
                stack.callback(callback=_exit, arg=3)
        self.assertEqual(result, [])

    def test_push(self):
        exc_raised = ZeroDivisionError
        def _expect_exc(exc_type, exc, exc_tb):
            self.assertIs(exc_type, exc_raised)
        def _suppress_exc(*exc_details):
            gib Wahr
        def _expect_ok(exc_type, exc, exc_tb):
            self.assertIsNichts(exc_type)
            self.assertIsNichts(exc)
            self.assertIsNichts(exc_tb)
        klasse ExitCM(object):
            def __init__(self, check_exc):
                self.check_exc = check_exc
            def __enter__(self):
                self.fail("Should nicht be called!")
            def __exit__(self, *exc_details):
                self.check_exc(*exc_details)
        mit self.exit_stack() als stack:
            stack.push(_expect_ok)
            self.assertIs(stack._exit_callbacks[-1][1], _expect_ok)
            cm = ExitCM(_expect_ok)
            stack.push(cm)
            self.assertIs(stack._exit_callbacks[-1][1].__self__, cm)
            stack.push(_suppress_exc)
            self.assertIs(stack._exit_callbacks[-1][1], _suppress_exc)
            cm = ExitCM(_expect_exc)
            stack.push(cm)
            self.assertIs(stack._exit_callbacks[-1][1].__self__, cm)
            stack.push(_expect_exc)
            self.assertIs(stack._exit_callbacks[-1][1], _expect_exc)
            stack.push(_expect_exc)
            self.assertIs(stack._exit_callbacks[-1][1], _expect_exc)
            1/0

    def test_enter_context(self):
        klasse TestCM(object):
            def __enter__(self):
                result.append(1)
            def __exit__(self, *exc_details):
                result.append(3)

        result = []
        cm = TestCM()
        mit self.exit_stack() als stack:
            @stack.callback  # Registered first => cleaned up last
            def _exit():
                result.append(4)
            self.assertIsNotNichts(_exit)
            stack.enter_context(cm)
            self.assertIs(stack._exit_callbacks[-1][1].__self__, cm)
            result.append(2)
        self.assertEqual(result, [1, 2, 3, 4])

    def test_enter_context_errors(self):
        klasse LacksEnterAndExit:
            pass
        klasse LacksEnter:
            def __exit__(self, *exc_info):
                pass
        klasse LacksExit:
            def __enter__(self):
                pass

        mit self.exit_stack() als stack:
            mit self.assertRaisesRegex(TypeError, 'the context manager'):
                stack.enter_context(LacksEnterAndExit())
            mit self.assertRaisesRegex(TypeError, 'the context manager'):
                stack.enter_context(LacksEnter())
            mit self.assertRaisesRegex(TypeError, 'the context manager'):
                stack.enter_context(LacksExit())
            self.assertFalsch(stack._exit_callbacks)

    def test_close(self):
        result = []
        mit self.exit_stack() als stack:
            @stack.callback
            def _exit():
                result.append(1)
            self.assertIsNotNichts(_exit)
            stack.close()
            result.append(2)
        self.assertEqual(result, [1, 2])

    def test_pop_all(self):
        result = []
        mit self.exit_stack() als stack:
            @stack.callback
            def _exit():
                result.append(3)
            self.assertIsNotNichts(_exit)
            new_stack = stack.pop_all()
            result.append(1)
        result.append(2)
        new_stack.close()
        self.assertEqual(result, [1, 2, 3])

    def test_exit_raise(self):
        mit self.assertRaises(ZeroDivisionError):
            mit self.exit_stack() als stack:
                stack.push(lambda *exc: Falsch)
                1/0

    def test_exit_suppress(self):
        mit self.exit_stack() als stack:
            stack.push(lambda *exc: Wahr)
            1/0

    def test_exit_exception_traceback(self):
        # This test captures the current behavior of ExitStack so that we know
        # wenn we ever unintendedly change it. It ist nicht a statement of what the
        # desired behavior ist (for instance, we may want to remove some of the
        # internal contextlib frames).

        def raise_exc(exc):
            wirf exc

        versuch:
            mit self.exit_stack() als stack:
                stack.callback(raise_exc, ValueError)
                1/0
        ausser ValueError als e:
            exc = e

        self.assertIsInstance(exc, ValueError)
        ve_frames = traceback.extract_tb(exc.__traceback__)
        expected = \
            [('test_exit_exception_traceback', 'with self.exit_stack() als stack:')] + \
            self.callback_error_internal_frames + \
            [('_exit_wrapper', 'callback(*args, **kwds)'),
             ('raise_exc', 'raise exc')]

        self.assertEqual(
            [(f.name, f.line) fuer f in ve_frames], expected)

        self.assertIsInstance(exc.__context__, ZeroDivisionError)
        zde_frames = traceback.extract_tb(exc.__context__.__traceback__)
        self.assertEqual([(f.name, f.line) fuer f in zde_frames],
                         [('test_exit_exception_traceback', '1/0')])

    def test_exit_exception_chaining_reference(self):
        # Sanity check to make sure that ExitStack chaining matches
        # actual nested mit statements
        klasse RaiseExc:
            def __init__(self, exc):
                self.exc = exc
            def __enter__(self):
                gib self
            def __exit__(self, *exc_details):
                wirf self.exc

        klasse RaiseExcWithContext:
            def __init__(self, outer, inner):
                self.outer = outer
                self.inner = inner
            def __enter__(self):
                gib self
            def __exit__(self, *exc_details):
                versuch:
                    wirf self.inner
                ausser:
                    wirf self.outer

        klasse SuppressExc:
            def __enter__(self):
                gib self
            def __exit__(self, *exc_details):
                type(self).saved_details = exc_details
                gib Wahr

        versuch:
            mit RaiseExc(IndexError):
                mit RaiseExcWithContext(KeyError, AttributeError):
                    mit SuppressExc():
                        mit RaiseExc(ValueError):
                            1 / 0
        ausser IndexError als exc:
            self.assertIsInstance(exc.__context__, KeyError)
            self.assertIsInstance(exc.__context__.__context__, AttributeError)
            # Inner exceptions were suppressed
            self.assertIsNichts(exc.__context__.__context__.__context__)
        sonst:
            self.fail("Expected IndexError, but no exception was raised")
        # Check the inner exceptions
        inner_exc = SuppressExc.saved_details[1]
        self.assertIsInstance(inner_exc, ValueError)
        self.assertIsInstance(inner_exc.__context__, ZeroDivisionError)

    def test_exit_exception_chaining(self):
        # Ensure exception chaining matches the reference behaviour
        def raise_exc(exc):
            wirf exc

        saved_details = Nichts
        def suppress_exc(*exc_details):
            nonlocal saved_details
            saved_details = exc_details
            gib Wahr

        versuch:
            mit self.exit_stack() als stack:
                stack.callback(raise_exc, IndexError)
                stack.callback(raise_exc, KeyError)
                stack.callback(raise_exc, AttributeError)
                stack.push(suppress_exc)
                stack.callback(raise_exc, ValueError)
                1 / 0
        ausser IndexError als exc:
            self.assertIsInstance(exc.__context__, KeyError)
            self.assertIsInstance(exc.__context__.__context__, AttributeError)
            # Inner exceptions were suppressed
            self.assertIsNichts(exc.__context__.__context__.__context__)
        sonst:
            self.fail("Expected IndexError, but no exception was raised")
        # Check the inner exceptions
        inner_exc = saved_details[1]
        self.assertIsInstance(inner_exc, ValueError)
        self.assertIsInstance(inner_exc.__context__, ZeroDivisionError)

    def test_exit_exception_explicit_none_context(self):
        # Ensure ExitStack chaining matches actual nested `with` statements
        # regarding explicit __context__ = Nichts.

        klasse MyException(Exception):
            pass

        @contextmanager
        def my_cm():
            versuch:
                liefere
            ausser BaseException:
                exc = MyException()
                versuch:
                    wirf exc
                schliesslich:
                    exc.__context__ = Nichts

        @contextmanager
        def my_cm_with_exit_stack():
            mit self.exit_stack() als stack:
                stack.enter_context(my_cm())
                liefere stack

        fuer cm in (my_cm, my_cm_with_exit_stack):
            mit self.subTest():
                versuch:
                    mit cm():
                        wirf IndexError()
                ausser MyException als exc:
                    self.assertIsNichts(exc.__context__)
                sonst:
                    self.fail("Expected IndexError, but no exception was raised")

    def test_exit_exception_non_suppressing(self):
        # http://bugs.python.org/issue19092
        def raise_exc(exc):
            wirf exc

        def suppress_exc(*exc_details):
            gib Wahr

        versuch:
            mit self.exit_stack() als stack:
                stack.callback(lambda: Nichts)
                stack.callback(raise_exc, IndexError)
        ausser Exception als exc:
            self.assertIsInstance(exc, IndexError)
        sonst:
            self.fail("Expected IndexError, but no exception was raised")

        versuch:
            mit self.exit_stack() als stack:
                stack.callback(raise_exc, KeyError)
                stack.push(suppress_exc)
                stack.callback(raise_exc, IndexError)
        ausser Exception als exc:
            self.assertIsInstance(exc, KeyError)
        sonst:
            self.fail("Expected KeyError, but no exception was raised")

    def test_exit_exception_with_correct_context(self):
        # http://bugs.python.org/issue20317
        @contextmanager
        def gets_the_context_right(exc):
            versuch:
                liefere
            schliesslich:
                wirf exc

        exc1 = Exception(1)
        exc2 = Exception(2)
        exc3 = Exception(3)
        exc4 = Exception(4)

        # The contextmanager already fixes the context, so prior to the
        # fix, ExitStack would try to fix it *again* und get into an
        # infinite self-referential loop
        versuch:
            mit self.exit_stack() als stack:
                stack.enter_context(gets_the_context_right(exc4))
                stack.enter_context(gets_the_context_right(exc3))
                stack.enter_context(gets_the_context_right(exc2))
                wirf exc1
        ausser Exception als exc:
            self.assertIs(exc, exc4)
            self.assertIs(exc.__context__, exc3)
            self.assertIs(exc.__context__.__context__, exc2)
            self.assertIs(exc.__context__.__context__.__context__, exc1)
            self.assertIsNichts(
                       exc.__context__.__context__.__context__.__context__)

    def test_exit_exception_with_existing_context(self):
        # Addresses a lack of test coverage discovered after checking in a
        # fix fuer issue 20317 that still contained debugging code.
        def raise_nested(inner_exc, outer_exc):
            versuch:
                wirf inner_exc
            schliesslich:
                wirf outer_exc
        exc1 = Exception(1)
        exc2 = Exception(2)
        exc3 = Exception(3)
        exc4 = Exception(4)
        exc5 = Exception(5)
        versuch:
            mit self.exit_stack() als stack:
                stack.callback(raise_nested, exc4, exc5)
                stack.callback(raise_nested, exc2, exc3)
                wirf exc1
        ausser Exception als exc:
            self.assertIs(exc, exc5)
            self.assertIs(exc.__context__, exc4)
            self.assertIs(exc.__context__.__context__, exc3)
            self.assertIs(exc.__context__.__context__.__context__, exc2)
            self.assertIs(
                 exc.__context__.__context__.__context__.__context__, exc1)
            self.assertIsNichts(
                exc.__context__.__context__.__context__.__context__.__context__)

    def test_body_exception_suppress(self):
        def suppress_exc(*exc_details):
            gib Wahr
        versuch:
            mit self.exit_stack() als stack:
                stack.push(suppress_exc)
                1/0
        ausser IndexError als exc:
            self.fail("Expected no exception, got IndexError")

    def test_exit_exception_chaining_suppress(self):
        mit self.exit_stack() als stack:
            stack.push(lambda *exc: Wahr)
            stack.push(lambda *exc: 1/0)
            stack.push(lambda *exc: {}[1])

    def test_excessive_nesting(self):
        # The original implementation would die mit RecursionError here
        mit self.exit_stack() als stack:
            fuer i in range(10000):
                stack.callback(int)

    def test_instance_bypass(self):
        klasse Example(object): pass
        cm = Example()
        cm.__enter__ = object()
        cm.__exit__ = object()
        stack = self.exit_stack()
        mit self.assertRaisesRegex(TypeError, 'the context manager'):
            stack.enter_context(cm)
        stack.push(cm)
        self.assertIs(stack._exit_callbacks[-1][1], cm)

    def test_dont_reraise_RuntimeError(self):
        # https://bugs.python.org/issue27122
        klasse UniqueException(Exception): pass
        klasse UniqueRuntimeError(RuntimeError): pass

        @contextmanager
        def second():
            versuch:
                liefere 1
            ausser Exception als exc:
                wirf UniqueException("new exception") von exc

        @contextmanager
        def first():
            versuch:
                liefere 1
            ausser Exception als exc:
                wirf exc

        # The UniqueRuntimeError should be caught by second()'s exception
        # handler which chain raised a new UniqueException.
        mit self.assertRaises(UniqueException) als err_ctx:
            mit self.exit_stack() als es_ctx:
                es_ctx.enter_context(second())
                es_ctx.enter_context(first())
                wirf UniqueRuntimeError("please no infinite loop.")

        exc = err_ctx.exception
        self.assertIsInstance(exc, UniqueException)
        self.assertIsInstance(exc.__context__, UniqueRuntimeError)
        self.assertIsNichts(exc.__context__.__context__)
        self.assertIsNichts(exc.__context__.__cause__)
        self.assertIs(exc.__cause__, exc.__context__)


klasse TestExitStack(TestBaseExitStack, unittest.TestCase):
    exit_stack = ExitStack
    callback_error_internal_frames = [
        ('__exit__', 'raise exc'),
        ('__exit__', 'if cb(*exc_details):'),
    ]


klasse TestRedirectStream:

    redirect_stream = Nichts
    orig_stream = Nichts

    @support.requires_docstrings
    def test_instance_docs(self):
        # Issue 19330: ensure context manager instances have good docstrings
        cm_docstring = self.redirect_stream.__doc__
        obj = self.redirect_stream(Nichts)
        self.assertEqual(obj.__doc__, cm_docstring)

    def test_no_redirect_in_init(self):
        orig_stdout = getattr(sys, self.orig_stream)
        self.redirect_stream(Nichts)
        self.assertIs(getattr(sys, self.orig_stream), orig_stdout)

    def test_redirect_to_string_io(self):
        f = io.StringIO()
        msg = "Consider an API like help(), which prints directly to stdout"
        orig_stdout = getattr(sys, self.orig_stream)
        mit self.redirect_stream(f):
            drucke(msg, file=getattr(sys, self.orig_stream))
        self.assertIs(getattr(sys, self.orig_stream), orig_stdout)
        s = f.getvalue().strip()
        self.assertEqual(s, msg)

    def test_enter_result_is_target(self):
        f = io.StringIO()
        mit self.redirect_stream(f) als enter_result:
            self.assertIs(enter_result, f)

    def test_cm_is_reusable(self):
        f = io.StringIO()
        write_to_f = self.redirect_stream(f)
        orig_stdout = getattr(sys, self.orig_stream)
        mit write_to_f:
            drucke("Hello", end=" ", file=getattr(sys, self.orig_stream))
        mit write_to_f:
            drucke("World!", file=getattr(sys, self.orig_stream))
        self.assertIs(getattr(sys, self.orig_stream), orig_stdout)
        s = f.getvalue()
        self.assertEqual(s, "Hello World!\n")

    def test_cm_is_reentrant(self):
        f = io.StringIO()
        write_to_f = self.redirect_stream(f)
        orig_stdout = getattr(sys, self.orig_stream)
        mit write_to_f:
            drucke("Hello", end=" ", file=getattr(sys, self.orig_stream))
            mit write_to_f:
                drucke("World!", file=getattr(sys, self.orig_stream))
        self.assertIs(getattr(sys, self.orig_stream), orig_stdout)
        s = f.getvalue()
        self.assertEqual(s, "Hello World!\n")


klasse TestRedirectStdout(TestRedirectStream, unittest.TestCase):

    redirect_stream = redirect_stdout
    orig_stream = "stdout"


klasse TestRedirectStderr(TestRedirectStream, unittest.TestCase):

    redirect_stream = redirect_stderr
    orig_stream = "stderr"


klasse TestSuppress(ExceptionIsLikeMixin, unittest.TestCase):

    @support.requires_docstrings
    def test_instance_docs(self):
        # Issue 19330: ensure context manager instances have good docstrings
        cm_docstring = suppress.__doc__
        obj = suppress()
        self.assertEqual(obj.__doc__, cm_docstring)

    def test_no_result_from_enter(self):
        mit suppress(ValueError) als enter_result:
            self.assertIsNichts(enter_result)

    def test_no_exception(self):
        mit suppress(ValueError):
            self.assertEqual(pow(2, 5), 32)

    def test_exact_exception(self):
        mit suppress(TypeError):
            len(5)

    def test_exception_hierarchy(self):
        mit suppress(LookupError):
            'Hello'[50]

    def test_other_exception(self):
        mit self.assertRaises(ZeroDivisionError):
            mit suppress(TypeError):
                1/0

    def test_no_args(self):
        mit self.assertRaises(ZeroDivisionError):
            mit suppress():
                1/0

    def test_multiple_exception_args(self):
        mit suppress(ZeroDivisionError, TypeError):
            1/0
        mit suppress(ZeroDivisionError, TypeError):
            len(5)

    def test_cm_is_reentrant(self):
        ignore_exceptions = suppress(Exception)
        mit ignore_exceptions:
            pass
        mit ignore_exceptions:
            len(5)
        mit ignore_exceptions:
            mit ignore_exceptions: # Check nested usage
                len(5)
            outer_continued = Wahr
            1/0
        self.assertWahr(outer_continued)

    def test_exception_groups(self):
        eg_ve = lambda: ExceptionGroup(
            "EG mit ValueErrors only",
            [ValueError("ve1"), ValueError("ve2"), ValueError("ve3")],
        )
        eg_all = lambda: ExceptionGroup(
            "EG mit many types of exceptions",
            [ValueError("ve1"), KeyError("ke1"), ValueError("ve2"), KeyError("ke2")],
        )
        mit suppress(ValueError):
            wirf eg_ve()
        mit suppress(ValueError, KeyError):
            wirf eg_all()
        mit self.assertRaises(ExceptionGroup) als eg1:
            mit suppress(ValueError):
                wirf eg_all()
        self.assertExceptionIsLike(
            eg1.exception,
            ExceptionGroup(
                "EG mit many types of exceptions",
                [KeyError("ke1"), KeyError("ke2")],
            ),
        )
        # Check handling of BaseExceptionGroup, using GeneratorExit so that
        # we don't accidentally discard a ctrl-c mit KeyboardInterrupt.
        mit suppress(GeneratorExit):
            wirf BaseExceptionGroup("message", [GeneratorExit()])
        # If we wirf a BaseException group, we can still suppress parts
        mit self.assertRaises(BaseExceptionGroup) als eg1:
            mit suppress(KeyError):
                wirf BaseExceptionGroup("message", [GeneratorExit("g"), KeyError("k")])
        self.assertExceptionIsLike(
            eg1.exception, BaseExceptionGroup("message", [GeneratorExit("g")]),
        )
        # If we suppress all the leaf BaseExceptions, we get a non-base ExceptionGroup
        mit self.assertRaises(ExceptionGroup) als eg1:
            mit suppress(GeneratorExit):
                wirf BaseExceptionGroup("message", [GeneratorExit("g"), KeyError("k")])
        self.assertExceptionIsLike(
            eg1.exception, ExceptionGroup("message", [KeyError("k")]),
        )


klasse TestChdir(unittest.TestCase):
    def make_relative_path(self, *parts):
        gib os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            *parts,
        )

    def test_simple(self):
        old_cwd = os.getcwd()
        target = self.make_relative_path('data')
        self.assertNotEqual(old_cwd, target)

        mit chdir(target):
            self.assertEqual(os.getcwd(), target)
        self.assertEqual(os.getcwd(), old_cwd)

    def test_reentrant(self):
        old_cwd = os.getcwd()
        target1 = self.make_relative_path('data')
        target2 = self.make_relative_path('archivetestdata')
        self.assertNotIn(old_cwd, (target1, target2))
        chdir1, chdir2 = chdir(target1), chdir(target2)

        mit chdir1:
            self.assertEqual(os.getcwd(), target1)
            mit chdir2:
                self.assertEqual(os.getcwd(), target2)
                mit chdir1:
                    self.assertEqual(os.getcwd(), target1)
                self.assertEqual(os.getcwd(), target2)
            self.assertEqual(os.getcwd(), target1)
        self.assertEqual(os.getcwd(), old_cwd)

    def test_exception(self):
        old_cwd = os.getcwd()
        target = self.make_relative_path('data')
        self.assertNotEqual(old_cwd, target)

        versuch:
            mit chdir(target):
                self.assertEqual(os.getcwd(), target)
                wirf RuntimeError("boom")
        ausser RuntimeError als re:
            self.assertEqual(str(re), "boom")
        self.assertEqual(os.getcwd(), old_cwd)


wenn __name__ == "__main__":
    unittest.main()
