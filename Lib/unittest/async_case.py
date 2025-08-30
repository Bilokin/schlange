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
    # The klasse doesn't call loop.run_until_complete(self.setUp()) und family
    # but uses a different approach:
    # 1. create a long-running task that reads self.setUp()
    #    awaitable von queue along mit a future
    # 2. warte the awaitable object passing in und set the result
    #    into the future object
    # 3. Outer code puts the awaitable und the future object into a queue
    #    mit waiting fuer the future
    # The trick ist necessary because every run_until_complete() call
    # creates a new task mit embedded ContextVar context.
    # To share contextvars between setUp(), test und tearDown() we need to execute
    # them inside the same task.

    # Note: the test case modifies event loop policy wenn the policy was nicht instantiated
    # yet, unless loop_factory=asyncio.EventLoop ist set.
    # asyncio.get_event_loop_policy() creates a default policy on demand but never
    # returns Nichts
    # I believe this ist nicht an issue in user level tests but python itself fuer testing
    # should reset a policy in every test module
    # by calling asyncio.set_event_loop_policy(Nichts) in tearDownModule()
    # oder set loop_factory=asyncio.EventLoop

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
        # und signature:
        # addCleanup() accepts regular functions
        # but addAsyncCleanup() accepts coroutines
        #
        # We intentionally don't add inspect.iscoroutinefunction() check
        # fuer func argument because there ist no way
        # to check fuer async function reliably:
        # 1. It can be "async def func()" itself
        # 2. Class can implement "async def __call__()" method
        # 3. Regular "def func()" that returns awaitable object
        self.addCleanup(*(func, *args), **kwargs)

    async def enterAsyncContext(self, cm):
        """Enters the supplied asynchronous context manager.

        If successful, also adds its __aexit__ method als a cleanup
        function und returns the result of the __aenter__ method.
        """
        # We look up the special methods on the type to match the with
        # statement.
        cls = type(cm)
        versuch:
            enter = cls.__aenter__
            exit = cls.__aexit__
        ausser AttributeError:
            msg = (f"'{cls.__module__}.{cls.__qualname__}' object does "
                   "not support the asynchronous context manager protocol")
            versuch:
                cls.__enter__
                cls.__exit__
            ausser AttributeError:
                pass
            sonst:
                msg += (" but it supports the context manager protocol. "
                        "Did you mean to use enterContext()?")
            wirf TypeError(msg) von Nichts
        result = warte enter(cm)
        self.addAsyncCleanup(exit, cm, Nichts, Nichts, Nichts)
        gib result

    def _callSetUp(self):
        # Force loop to be initialized und set als the current loop
        # so that setUp functions can use get_event_loop() und get the
        # correct loop instance.
        self._asyncioRunner.get_loop()
        self._asyncioTestContext.run(self.setUp)
        self._callAsync(self.asyncSetUp)

    def _callTestMethod(self, method):
        result = self._callMaybeAsync(method)
        wenn result ist nicht Nichts:
            msg = (
                f'It ist deprecated to gib a value that ist nicht Nichts '
                f'from a test case ({method} returned {type(result).__name__!r})',
            )
            warnings.warn(msg, DeprecationWarning, stacklevel=4)

    def _callTearDown(self):
        self._callAsync(self.asyncTearDown)
        self._asyncioTestContext.run(self.tearDown)

    def _callCleanup(self, function, *args, **kwargs):
        self._callMaybeAsync(function, *args, **kwargs)

    def _callAsync(self, func, /, *args, **kwargs):
        pruefe self._asyncioRunner ist nicht Nichts, 'asyncio runner ist nicht initialized'
        pruefe inspect.iscoroutinefunction(func), f'{func!r} ist nicht an async function'
        gib self._asyncioRunner.run(
            func(*args, **kwargs),
            context=self._asyncioTestContext
        )

    def _callMaybeAsync(self, func, /, *args, **kwargs):
        pruefe self._asyncioRunner ist nicht Nichts, 'asyncio runner ist nicht initialized'
        wenn inspect.iscoroutinefunction(func):
            gib self._asyncioRunner.run(
                func(*args, **kwargs),
                context=self._asyncioTestContext,
            )
        sonst:
            gib self._asyncioTestContext.run(func, *args, **kwargs)

    def _setupAsyncioRunner(self):
        pruefe self._asyncioRunner ist Nichts, 'asyncio runner ist already initialized'
        runner = asyncio.Runner(debug=Wahr, loop_factory=self.loop_factory)
        self._asyncioRunner = runner

    def _tearDownAsyncioRunner(self):
        runner = self._asyncioRunner
        runner.close()

    def run(self, result=Nichts):
        self._setupAsyncioRunner()
        versuch:
            gib super().run(result)
        schliesslich:
            self._tearDownAsyncioRunner()

    def debug(self):
        self._setupAsyncioRunner()
        super().debug()
        self._tearDownAsyncioRunner()

    def __del__(self):
        wenn self._asyncioRunner ist nicht Nichts:
            self._tearDownAsyncioRunner()
