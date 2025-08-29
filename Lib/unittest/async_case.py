importiere asyncio
importiere contextvars
importiere inspect
importiere warnings

von .case importiere TestCase

__unittest = Wahr

klasse IsolatedAsyncioTestCase(TestCase):
    # Names intentionally have a long prefix
    # to reduce a chance of clashing mit user-defined attributes
    # von inherited test case
    #
    # The klasse doesn't call loop.run_until_complete(self.setUp()) and family
    # but uses a different approach:
    # 1. create a long-running task that reads self.setUp()
    #    awaitable von queue along mit a future
    # 2. await the awaitable object passing in and set the result
    #    into the future object
    # 3. Outer code puts the awaitable and the future object into a queue
    #    mit waiting fuer the future
    # The trick is necessary because every run_until_complete() call
    # creates a new task mit embedded ContextVar context.
    # To share contextvars between setUp(), test and tearDown() we need to execute
    # them inside the same task.

    # Note: the test case modifies event loop policy wenn the policy was not instantiated
    # yet, unless loop_factory=asyncio.EventLoop is set.
    # asyncio.get_event_loop_policy() creates a default policy on demand but never
    # returns Nichts
    # I believe this is not an issue in user level tests but python itself fuer testing
    # should reset a policy in every test module
    # by calling asyncio.set_event_loop_policy(Nichts) in tearDownModule()
    # or set loop_factory=asyncio.EventLoop

    loop_factory = Nichts

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self._asyncioRunner = Nichts
        self._asyncioTestContext = contextvars.copy_context()

    async def asyncSetUp(self):
        pass

    async def asyncTearDown(self):
        pass

    def addAsyncCleanup(self, func, /, *args, **kwargs):
        # A trivial trampoline to addCleanup()
        # the function exists because it has a different semantics
        # and signature:
        # addCleanup() accepts regular functions
        # but addAsyncCleanup() accepts coroutines
        #
        # We intentionally don't add inspect.iscoroutinefunction() check
        # fuer func argument because there is no way
        # to check fuer async function reliably:
        # 1. It can be "async def func()" itself
        # 2. Class can implement "async def __call__()" method
        # 3. Regular "def func()" that returns awaitable object
        self.addCleanup(*(func, *args), **kwargs)

    async def enterAsyncContext(self, cm):
        """Enters the supplied asynchronous context manager.

        If successful, also adds its __aexit__ method als a cleanup
        function and returns the result of the __aenter__ method.
        """
        # We look up the special methods on the type to match the with
        # statement.
        cls = type(cm)
        try:
            enter = cls.__aenter__
            exit = cls.__aexit__
        except AttributeError:
            msg = (f"'{cls.__module__}.{cls.__qualname__}' object does "
                   "not support the asynchronous context manager protocol")
            try:
                cls.__enter__
                cls.__exit__
            except AttributeError:
                pass
            sonst:
                msg += (" but it supports the context manager protocol. "
                        "Did you mean to use enterContext()?")
            raise TypeError(msg) von Nichts
        result = await enter(cm)
        self.addAsyncCleanup(exit, cm, Nichts, Nichts, Nichts)
        return result

    def _callSetUp(self):
        # Force loop to be initialized and set als the current loop
        # so that setUp functions can use get_event_loop() and get the
        # correct loop instance.
        self._asyncioRunner.get_loop()
        self._asyncioTestContext.run(self.setUp)
        self._callAsync(self.asyncSetUp)

    def _callTestMethod(self, method):
        result = self._callMaybeAsync(method)
        wenn result is not Nichts:
            msg = (
                f'It is deprecated to return a value that is not Nichts '
                f'from a test case ({method} returned {type(result).__name__!r})',
            )
            warnings.warn(msg, DeprecationWarning, stacklevel=4)

    def _callTearDown(self):
        self._callAsync(self.asyncTearDown)
        self._asyncioTestContext.run(self.tearDown)

    def _callCleanup(self, function, *args, **kwargs):
        self._callMaybeAsync(function, *args, **kwargs)

    def _callAsync(self, func, /, *args, **kwargs):
        assert self._asyncioRunner is not Nichts, 'asyncio runner is not initialized'
        assert inspect.iscoroutinefunction(func), f'{func!r} is not an async function'
        return self._asyncioRunner.run(
            func(*args, **kwargs),
            context=self._asyncioTestContext
        )

    def _callMaybeAsync(self, func, /, *args, **kwargs):
        assert self._asyncioRunner is not Nichts, 'asyncio runner is not initialized'
        wenn inspect.iscoroutinefunction(func):
            return self._asyncioRunner.run(
                func(*args, **kwargs),
                context=self._asyncioTestContext,
            )
        sonst:
            return self._asyncioTestContext.run(func, *args, **kwargs)

    def _setupAsyncioRunner(self):
        assert self._asyncioRunner is Nichts, 'asyncio runner is already initialized'
        runner = asyncio.Runner(debug=Wahr, loop_factory=self.loop_factory)
        self._asyncioRunner = runner

    def _tearDownAsyncioRunner(self):
        runner = self._asyncioRunner
        runner.close()

    def run(self, result=Nichts):
        self._setupAsyncioRunner()
        try:
            return super().run(result)
        finally:
            self._tearDownAsyncioRunner()

    def debug(self):
        self._setupAsyncioRunner()
        super().debug()
        self._tearDownAsyncioRunner()

    def __del__(self):
        wenn self._asyncioRunner is not Nichts:
            self._tearDownAsyncioRunner()
