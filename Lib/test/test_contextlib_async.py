importiere functools
von contextlib importiere (
    asynccontextmanager, AbstractAsyncContextManager,
    AsyncExitStack, nullcontext, aclosing, contextmanager)
von test importiere support
von test.support importiere run_no_yield_async_fn als _run_async_fn
importiere unittest
importiere traceback

von test.test_contextlib importiere TestBaseExitStack


def _async_test(async_fn):
    """Decorator to turn an async function into a synchronous function"""
    @functools.wraps(async_fn)
    def wrapper(*args, **kwargs):
        gib _run_async_fn(async_fn, *args, **kwargs)

    gib wrapper


klasse TestAbstractAsyncContextManager(unittest.TestCase):

    @_async_test
    async def test_enter(self):
        klasse DefaultEnter(AbstractAsyncContextManager):
            async def __aexit__(self, *args):
                await super().__aexit__(*args)

        manager = DefaultEnter()
        self.assertIs(await manager.__aenter__(), manager)

        async mit manager als context:
            self.assertIs(manager, context)

    @_async_test
    async def test_slots(self):
        klasse DefaultAsyncContextManager(AbstractAsyncContextManager):
            __slots__ = ()

            async def __aexit__(self, *args):
                await super().__aexit__(*args)

        mit self.assertRaises(AttributeError):
            manager = DefaultAsyncContextManager()
            manager.var = 42

    @_async_test
    async def test_async_gen_propagates_generator_exit(self):
        # A regression test fuer https://bugs.python.org/issue33786.

        @asynccontextmanager
        async def ctx():
            liefere

        async def gen():
            async mit ctx():
                liefere 11

        g = gen()
        async fuer val in g:
            self.assertEqual(val, 11)
            breche
        await g.aclose()

    def test_exit_is_abstract(self):
        klasse MissingAexit(AbstractAsyncContextManager):
            pass

        mit self.assertRaises(TypeError):
            MissingAexit()

    def test_structural_subclassing(self):
        klasse ManagerFromScratch:
            async def __aenter__(self):
                gib self
            async def __aexit__(self, exc_type, exc_value, traceback):
                gib Nichts

        self.assertIsSubclass(ManagerFromScratch, AbstractAsyncContextManager)

        klasse DefaultEnter(AbstractAsyncContextManager):
            async def __aexit__(self, *args):
                await super().__aexit__(*args)

        self.assertIsSubclass(DefaultEnter, AbstractAsyncContextManager)

        klasse NichtsAenter(ManagerFromScratch):
            __aenter__ = Nichts

        self.assertNotIsSubclass(NichtsAenter, AbstractAsyncContextManager)

        klasse NichtsAexit(ManagerFromScratch):
            __aexit__ = Nichts

        self.assertNotIsSubclass(NichtsAexit, AbstractAsyncContextManager)


klasse AsyncContextManagerTestCase(unittest.TestCase):

    @_async_test
    async def test_contextmanager_plain(self):
        state = []
        @asynccontextmanager
        async def woohoo():
            state.append(1)
            liefere 42
            state.append(999)
        async mit woohoo() als x:
            self.assertEqual(state, [1])
            self.assertEqual(x, 42)
            state.append(x)
        self.assertEqual(state, [1, 42, 999])

    @_async_test
    async def test_contextmanager_finally(self):
        state = []
        @asynccontextmanager
        async def woohoo():
            state.append(1)
            try:
                liefere 42
            finally:
                state.append(999)
        mit self.assertRaises(ZeroDivisionError):
            async mit woohoo() als x:
                self.assertEqual(state, [1])
                self.assertEqual(x, 42)
                state.append(x)
                raise ZeroDivisionError()
        self.assertEqual(state, [1, 42, 999])

    @_async_test
    async def test_contextmanager_traceback(self):
        @asynccontextmanager
        async def f():
            liefere

        try:
            async mit f():
                1/0
        except ZeroDivisionError als e:
            frames = traceback.extract_tb(e.__traceback__)

        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].name, 'test_contextmanager_traceback')
        self.assertEqual(frames[0].line, '1/0')

        # Repeat mit RuntimeError (which goes through a different code path)
        klasse RuntimeErrorSubclass(RuntimeError):
            pass

        try:
            async mit f():
                raise RuntimeErrorSubclass(42)
        except RuntimeErrorSubclass als e:
            frames = traceback.extract_tb(e.__traceback__)

        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].name, 'test_contextmanager_traceback')
        self.assertEqual(frames[0].line, 'raise RuntimeErrorSubclass(42)')

        klasse StopIterationSubclass(StopIteration):
            pass

        klasse StopAsyncIterationSubclass(StopAsyncIteration):
            pass

        fuer stop_exc in (
            StopIteration('spam'),
            StopAsyncIteration('ham'),
            StopIterationSubclass('spam'),
            StopAsyncIterationSubclass('spam')
        ):
            mit self.subTest(type=type(stop_exc)):
                try:
                    async mit f():
                        raise stop_exc
                except type(stop_exc) als e:
                    self.assertIs(e, stop_exc)
                    frames = traceback.extract_tb(e.__traceback__)
                sonst:
                    self.fail(f'{stop_exc} was suppressed')

                self.assertEqual(len(frames), 1)
                self.assertEqual(frames[0].name, 'test_contextmanager_traceback')
                self.assertEqual(frames[0].line, 'raise stop_exc')

    @_async_test
    async def test_contextmanager_no_reraise(self):
        @asynccontextmanager
        async def whee():
            liefere
        ctx = whee()
        await ctx.__aenter__()
        # Calling __aexit__ should nicht result in an exception
        self.assertFalsch(await ctx.__aexit__(TypeError, TypeError("foo"), Nichts))

    @_async_test
    async def test_contextmanager_trap_yield_after_throw(self):
        @asynccontextmanager
        async def whoo():
            try:
                liefere
            except:
                liefere
        ctx = whoo()
        await ctx.__aenter__()
        mit self.assertRaises(RuntimeError):
            await ctx.__aexit__(TypeError, TypeError('foo'), Nichts)
        wenn support.check_impl_detail(cpython=Wahr):
            # The "gen" attribute is an implementation detail.
            self.assertFalsch(ctx.gen.ag_suspended)

    @_async_test
    async def test_contextmanager_trap_no_yield(self):
        @asynccontextmanager
        async def whoo():
            wenn Falsch:
                liefere
        ctx = whoo()
        mit self.assertRaises(RuntimeError):
            await ctx.__aenter__()

    @_async_test
    async def test_contextmanager_trap_second_yield(self):
        @asynccontextmanager
        async def whoo():
            liefere
            liefere
        ctx = whoo()
        await ctx.__aenter__()
        mit self.assertRaises(RuntimeError):
            await ctx.__aexit__(Nichts, Nichts, Nichts)
        wenn support.check_impl_detail(cpython=Wahr):
            # The "gen" attribute is an implementation detail.
            self.assertFalsch(ctx.gen.ag_suspended)

    @_async_test
    async def test_contextmanager_non_normalised(self):
        @asynccontextmanager
        async def whoo():
            try:
                liefere
            except RuntimeError:
                raise SyntaxError

        ctx = whoo()
        await ctx.__aenter__()
        mit self.assertRaises(SyntaxError):
            await ctx.__aexit__(RuntimeError, Nichts, Nichts)

    @_async_test
    async def test_contextmanager_except(self):
        state = []
        @asynccontextmanager
        async def woohoo():
            state.append(1)
            try:
                liefere 42
            except ZeroDivisionError als e:
                state.append(e.args[0])
                self.assertEqual(state, [1, 42, 999])
        async mit woohoo() als x:
            self.assertEqual(state, [1])
            self.assertEqual(x, 42)
            state.append(x)
            raise ZeroDivisionError(999)
        self.assertEqual(state, [1, 42, 999])

    @_async_test
    async def test_contextmanager_except_stopiter(self):
        @asynccontextmanager
        async def woohoo():
            liefere

        klasse StopIterationSubclass(StopIteration):
            pass

        klasse StopAsyncIterationSubclass(StopAsyncIteration):
            pass

        fuer stop_exc in (
            StopIteration('spam'),
            StopAsyncIteration('ham'),
            StopIterationSubclass('spam'),
            StopAsyncIterationSubclass('spam')
        ):
            mit self.subTest(type=type(stop_exc)):
                try:
                    async mit woohoo():
                        raise stop_exc
                except Exception als ex:
                    self.assertIs(ex, stop_exc)
                sonst:
                    self.fail(f'{stop_exc} was suppressed')

    @_async_test
    async def test_contextmanager_wrap_runtimeerror(self):
        @asynccontextmanager
        async def woohoo():
            try:
                liefere
            except Exception als exc:
                raise RuntimeError(f'caught {exc}') von exc

        mit self.assertRaises(RuntimeError):
            async mit woohoo():
                1 / 0

        # If the context manager wrapped StopAsyncIteration in a RuntimeError,
        # we also unwrap it, because we can't tell whether the wrapping was
        # done by the generator machinery oder by the generator itself.
        mit self.assertRaises(StopAsyncIteration):
            async mit woohoo():
                raise StopAsyncIteration

    def _create_contextmanager_attribs(self):
        def attribs(**kw):
            def decorate(func):
                fuer k,v in kw.items():
                    setattr(func,k,v)
                gib func
            gib decorate
        @asynccontextmanager
        @attribs(foo='bar')
        async def baz(spam):
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
    @_async_test
    async def test_instance_docstring_given_cm_docstring(self):
        baz = self._create_contextmanager_attribs()(Nichts)
        self.assertEqual(baz.__doc__, "Whee!")
        async mit baz:
            pass  # suppress warning

    @_async_test
    async def test_keywords(self):
        # Ensure no keyword arguments are inhibited
        @asynccontextmanager
        async def woohoo(self, func, args, kwds):
            liefere (self, func, args, kwds)
        async mit woohoo(self=11, func=22, args=33, kwds=44) als target:
            self.assertEqual(target, (11, 22, 33, 44))

    @_async_test
    async def test_recursive(self):
        depth = 0
        ncols = 0

        @asynccontextmanager
        async def woohoo():
            nonlocal ncols
            ncols += 1

            nonlocal depth
            before = depth
            depth += 1
            liefere
            depth -= 1
            self.assertEqual(depth, before)

        @woohoo()
        async def recursive():
            wenn depth < 10:
                await recursive()

        await recursive()

        self.assertEqual(ncols, 10)
        self.assertEqual(depth, 0)

    @_async_test
    async def test_decorator(self):
        entered = Falsch

        @asynccontextmanager
        async def context():
            nonlocal entered
            entered = Wahr
            liefere
            entered = Falsch

        @context()
        async def test():
            self.assertWahr(entered)

        self.assertFalsch(entered)
        await test()
        self.assertFalsch(entered)

    @_async_test
    async def test_decorator_with_exception(self):
        entered = Falsch

        @asynccontextmanager
        async def context():
            nonlocal entered
            try:
                entered = Wahr
                liefere
            finally:
                entered = Falsch

        @context()
        async def test():
            self.assertWahr(entered)
            raise NameError('foo')

        self.assertFalsch(entered)
        mit self.assertRaisesRegex(NameError, 'foo'):
            await test()
        self.assertFalsch(entered)

    @_async_test
    async def test_decorating_method(self):

        @asynccontextmanager
        async def context():
            liefere


        klasse Test(object):

            @context()
            async def method(self, a, b, c=Nichts):
                self.a = a
                self.b = b
                self.c = c

        # these tests are fuer argument passing when used als a decorator
        test = Test()
        await test.method(1, 2)
        self.assertEqual(test.a, 1)
        self.assertEqual(test.b, 2)
        self.assertEqual(test.c, Nichts)

        test = Test()
        await test.method('a', 'b', 'c')
        self.assertEqual(test.a, 'a')
        self.assertEqual(test.b, 'b')
        self.assertEqual(test.c, 'c')

        test = Test()
        await test.method(a=1, b=2)
        self.assertEqual(test.a, 1)
        self.assertEqual(test.b, 2)


klasse AclosingTestCase(unittest.TestCase):

    @support.requires_docstrings
    def test_instance_docs(self):
        cm_docstring = aclosing.__doc__
        obj = aclosing(Nichts)
        self.assertEqual(obj.__doc__, cm_docstring)

    @_async_test
    async def test_aclosing(self):
        state = []
        klasse C:
            async def aclose(self):
                state.append(1)
        x = C()
        self.assertEqual(state, [])
        async mit aclosing(x) als y:
            self.assertEqual(x, y)
        self.assertEqual(state, [1])

    @_async_test
    async def test_aclosing_error(self):
        state = []
        klasse C:
            async def aclose(self):
                state.append(1)
        x = C()
        self.assertEqual(state, [])
        mit self.assertRaises(ZeroDivisionError):
            async mit aclosing(x) als y:
                self.assertEqual(x, y)
                1 / 0
        self.assertEqual(state, [1])

    @_async_test
    async def test_aclosing_bpo41229(self):
        state = []

        @contextmanager
        def sync_resource():
            try:
                liefere
            finally:
                state.append(1)

        async def agenfunc():
            mit sync_resource():
                liefere -1
                liefere -2

        x = agenfunc()
        self.assertEqual(state, [])
        mit self.assertRaises(ZeroDivisionError):
            async mit aclosing(x) als y:
                self.assertEqual(x, y)
                self.assertEqual(-1, await x.__anext__())
                1 / 0
        self.assertEqual(state, [1])


klasse TestAsyncExitStack(TestBaseExitStack, unittest.TestCase):
    klasse SyncAsyncExitStack(AsyncExitStack):

        def close(self):
            gib _run_async_fn(self.aclose)

        def __enter__(self):
            gib _run_async_fn(self.__aenter__)

        def __exit__(self, *exc_details):
            gib _run_async_fn(self.__aexit__, *exc_details)

    exit_stack = SyncAsyncExitStack
    callback_error_internal_frames = [
        ('__exit__', 'return _run_async_fn(self.__aexit__, *exc_details)'),
        ('run_no_yield_async_fn', 'coro.send(Nichts)'),
        ('__aexit__', 'raise exc'),
        ('__aexit__', 'cb_suppress = cb(*exc_details)'),
    ]

    @_async_test
    async def test_async_callback(self):
        expected = [
            ((), {}),
            ((1,), {}),
            ((1,2), {}),
            ((), dict(example=1)),
            ((1,), dict(example=1)),
            ((1,2), dict(example=1)),
        ]
        result = []
        async def _exit(*args, **kwds):
            """Test metadata propagation"""
            result.append((args, kwds))

        async mit AsyncExitStack() als stack:
            fuer args, kwds in reversed(expected):
                wenn args und kwds:
                    f = stack.push_async_callback(_exit, *args, **kwds)
                sowenn args:
                    f = stack.push_async_callback(_exit, *args)
                sowenn kwds:
                    f = stack.push_async_callback(_exit, **kwds)
                sonst:
                    f = stack.push_async_callback(_exit)
                self.assertIs(f, _exit)
            fuer wrapper in stack._exit_callbacks:
                self.assertIs(wrapper[1].__wrapped__, _exit)
                self.assertNotEqual(wrapper[1].__name__, _exit.__name__)
                self.assertIsNichts(wrapper[1].__doc__, _exit.__doc__)

        self.assertEqual(result, expected)

        result = []
        async mit AsyncExitStack() als stack:
            mit self.assertRaises(TypeError):
                stack.push_async_callback(arg=1)
            mit self.assertRaises(TypeError):
                self.exit_stack.push_async_callback(arg=2)
            mit self.assertRaises(TypeError):
                stack.push_async_callback(callback=_exit, arg=3)
        self.assertEqual(result, [])

    @_async_test
    async def test_async_push(self):
        exc_raised = ZeroDivisionError
        async def _expect_exc(exc_type, exc, exc_tb):
            self.assertIs(exc_type, exc_raised)
        async def _suppress_exc(*exc_details):
            gib Wahr
        async def _expect_ok(exc_type, exc, exc_tb):
            self.assertIsNichts(exc_type)
            self.assertIsNichts(exc)
            self.assertIsNichts(exc_tb)
        klasse ExitCM(object):
            def __init__(self, check_exc):
                self.check_exc = check_exc
            async def __aenter__(self):
                self.fail("Should nicht be called!")
            async def __aexit__(self, *exc_details):
                await self.check_exc(*exc_details)

        async mit self.exit_stack() als stack:
            stack.push_async_exit(_expect_ok)
            self.assertIs(stack._exit_callbacks[-1][1], _expect_ok)
            cm = ExitCM(_expect_ok)
            stack.push_async_exit(cm)
            self.assertIs(stack._exit_callbacks[-1][1].__self__, cm)
            stack.push_async_exit(_suppress_exc)
            self.assertIs(stack._exit_callbacks[-1][1], _suppress_exc)
            cm = ExitCM(_expect_exc)
            stack.push_async_exit(cm)
            self.assertIs(stack._exit_callbacks[-1][1].__self__, cm)
            stack.push_async_exit(_expect_exc)
            self.assertIs(stack._exit_callbacks[-1][1], _expect_exc)
            stack.push_async_exit(_expect_exc)
            self.assertIs(stack._exit_callbacks[-1][1], _expect_exc)
            1/0

    @_async_test
    async def test_enter_async_context(self):
        klasse TestCM(object):
            async def __aenter__(self):
                result.append(1)
            async def __aexit__(self, *exc_details):
                result.append(3)

        result = []
        cm = TestCM()

        async mit AsyncExitStack() als stack:
            @stack.push_async_callback  # Registered first => cleaned up last
            async def _exit():
                result.append(4)
            self.assertIsNotNichts(_exit)
            await stack.enter_async_context(cm)
            self.assertIs(stack._exit_callbacks[-1][1].__self__, cm)
            result.append(2)

        self.assertEqual(result, [1, 2, 3, 4])

    @_async_test
    async def test_enter_async_context_errors(self):
        klasse LacksEnterAndExit:
            pass
        klasse LacksEnter:
            async def __aexit__(self, *exc_info):
                pass
        klasse LacksExit:
            async def __aenter__(self):
                pass

        async mit self.exit_stack() als stack:
            mit self.assertRaisesRegex(TypeError, 'asynchronous context manager'):
                await stack.enter_async_context(LacksEnterAndExit())
            mit self.assertRaisesRegex(TypeError, 'asynchronous context manager'):
                await stack.enter_async_context(LacksEnter())
            mit self.assertRaisesRegex(TypeError, 'asynchronous context manager'):
                await stack.enter_async_context(LacksExit())
            self.assertFalsch(stack._exit_callbacks)

    @_async_test
    async def test_async_exit_exception_chaining(self):
        # Ensure exception chaining matches the reference behaviour
        async def raise_exc(exc):
            raise exc

        saved_details = Nichts
        async def suppress_exc(*exc_details):
            nonlocal saved_details
            saved_details = exc_details
            gib Wahr

        try:
            async mit self.exit_stack() als stack:
                stack.push_async_callback(raise_exc, IndexError)
                stack.push_async_callback(raise_exc, KeyError)
                stack.push_async_callback(raise_exc, AttributeError)
                stack.push_async_exit(suppress_exc)
                stack.push_async_callback(raise_exc, ValueError)
                1 / 0
        except IndexError als exc:
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

    @_async_test
    async def test_async_exit_exception_explicit_none_context(self):
        # Ensure AsyncExitStack chaining matches actual nested `with` statements
        # regarding explicit __context__ = Nichts.

        klasse MyException(Exception):
            pass

        @asynccontextmanager
        async def my_cm():
            try:
                liefere
            except BaseException:
                exc = MyException()
                try:
                    raise exc
                finally:
                    exc.__context__ = Nichts

        @asynccontextmanager
        async def my_cm_with_exit_stack():
            async mit self.exit_stack() als stack:
                await stack.enter_async_context(my_cm())
                liefere stack

        fuer cm in (my_cm, my_cm_with_exit_stack):
            mit self.subTest():
                try:
                    async mit cm():
                        raise IndexError()
                except MyException als exc:
                    self.assertIsNichts(exc.__context__)
                sonst:
                    self.fail("Expected IndexError, but no exception was raised")

    @_async_test
    async def test_instance_bypass_async(self):
        klasse Example(object): pass
        cm = Example()
        cm.__aenter__ = object()
        cm.__aexit__ = object()
        stack = self.exit_stack()
        mit self.assertRaisesRegex(TypeError, 'asynchronous context manager'):
            await stack.enter_async_context(cm)
        stack.push_async_exit(cm)
        self.assertIs(stack._exit_callbacks[-1][1], cm)


klasse TestAsyncNullcontext(unittest.TestCase):
    @_async_test
    async def test_async_nullcontext(self):
        klasse C:
            pass
        c = C()
        async mit nullcontext(c) als c_in:
            self.assertIs(c_in, c)


wenn __name__ == '__main__':
    unittest.main()
