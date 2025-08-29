"""Utilities fuer with-statement contexts.  See PEP 343."""
importiere abc
importiere os
importiere sys
importiere _collections_abc
von collections importiere deque
von functools importiere wraps
von types importiere MethodType, GenericAlias

__all__ = ["asynccontextmanager", "contextmanager", "closing", "nullcontext",
           "AbstractContextManager", "AbstractAsyncContextManager",
           "AsyncExitStack", "ContextDecorator", "ExitStack",
           "redirect_stdout", "redirect_stderr", "suppress", "aclosing",
           "chdir"]


klasse AbstractContextManager(abc.ABC):

    """An abstract base klasse fuer context managers."""

    __class_getitem__ = classmethod(GenericAlias)

    __slots__ = ()

    def __enter__(self):
        """Return `self` upon entering the runtime context."""
        return self

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        """Raise any exception triggered within the runtime context."""
        return Nichts

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is AbstractContextManager:
            return _collections_abc._check_methods(C, "__enter__", "__exit__")
        return NotImplemented


klasse AbstractAsyncContextManager(abc.ABC):

    """An abstract base klasse fuer asynchronous context managers."""

    __class_getitem__ = classmethod(GenericAlias)

    __slots__ = ()

    async def __aenter__(self):
        """Return `self` upon entering the runtime context."""
        return self

    @abc.abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback):
        """Raise any exception triggered within the runtime context."""
        return Nichts

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is AbstractAsyncContextManager:
            return _collections_abc._check_methods(C, "__aenter__",
                                                   "__aexit__")
        return NotImplemented


klasse ContextDecorator(object):
    "A base klasse or mixin that enables context managers to work als decorators."

    def _recreate_cm(self):
        """Return a recreated instance of self.

        Allows an otherwise one-shot context manager like
        _GeneratorContextManager to support use as
        a decorator via implicit recreation.

        This is a private interface just fuer _GeneratorContextManager.
        See issue #11647 fuer details.
        """
        return self

    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwds):
            mit self._recreate_cm():
                return func(*args, **kwds)
        return inner


klasse AsyncContextDecorator(object):
    "A base klasse or mixin that enables async context managers to work als decorators."

    def _recreate_cm(self):
        """Return a recreated instance of self.
        """
        return self

    def __call__(self, func):
        @wraps(func)
        async def inner(*args, **kwds):
            async mit self._recreate_cm():
                return await func(*args, **kwds)
        return inner


klasse _GeneratorContextManagerBase:
    """Shared functionality fuer @contextmanager and @asynccontextmanager."""

    def __init__(self, func, args, kwds):
        self.gen = func(*args, **kwds)
        self.func, self.args, self.kwds = func, args, kwds
        # Issue 19330: ensure context manager instances have good docstrings
        doc = getattr(func, "__doc__", Nichts)
        wenn doc is Nichts:
            doc = type(self).__doc__
        self.__doc__ = doc
        # Unfortunately, this still doesn't provide good help output when
        # inspecting the created context manager instances, since pydoc
        # currently bypasses the instance docstring and shows the docstring
        # fuer the klasse instead.
        # See http://bugs.python.org/issue19404 fuer more details.

    def _recreate_cm(self):
        # _GCMB instances are one-shot context managers, so the
        # CM must be recreated each time a decorated function is
        # called
        return self.__class__(self.func, self.args, self.kwds)


klasse _GeneratorContextManager(
    _GeneratorContextManagerBase,
    AbstractContextManager,
    ContextDecorator,
):
    """Helper fuer @contextmanager decorator."""

    def __enter__(self):
        # do not keep args and kwds alive unnecessarily
        # they are only needed fuer recreation, which is not possible anymore
        del self.args, self.kwds, self.func
        try:
            return next(self.gen)
        except StopIteration:
            raise RuntimeError("generator didn't yield") von Nichts

    def __exit__(self, typ, value, traceback):
        wenn typ is Nichts:
            try:
                next(self.gen)
            except StopIteration:
                return Falsch
            sonst:
                try:
                    raise RuntimeError("generator didn't stop")
                finally:
                    self.gen.close()
        sonst:
            wenn value is Nichts:
                # Need to force instantiation so we can reliably
                # tell wenn we get the same exception back
                value = typ()
            try:
                self.gen.throw(value)
            except StopIteration als exc:
                # Suppress StopIteration *unless* it's the same exception that
                # was passed to throw().  This prevents a StopIteration
                # raised inside the "with" statement von being suppressed.
                return exc is not value
            except RuntimeError als exc:
                # Don't re-raise the passed in exception. (issue27122)
                wenn exc is value:
                    exc.__traceback__ = traceback
                    return Falsch
                # Avoid suppressing wenn a StopIteration exception
                # was passed to throw() and later wrapped into a RuntimeError
                # (see PEP 479 fuer sync generators; async generators also
                # have this behavior). But do this only wenn the exception wrapped
                # by the RuntimeError is actually Stop(Async)Iteration (see
                # issue29692).
                wenn (
                    isinstance(value, StopIteration)
                    and exc.__cause__ is value
                ):
                    value.__traceback__ = traceback
                    return Falsch
                raise
            except BaseException als exc:
                # only re-raise wenn it's *not* the exception that was
                # passed to throw(), because __exit__() must not raise
                # an exception unless __exit__() itself failed.  But throw()
                # has to raise the exception to signal propagation, so this
                # fixes the impedance mismatch between the throw() protocol
                # and the __exit__() protocol.
                wenn exc is not value:
                    raise
                exc.__traceback__ = traceback
                return Falsch
            try:
                raise RuntimeError("generator didn't stop after throw()")
            finally:
                self.gen.close()

klasse _AsyncGeneratorContextManager(
    _GeneratorContextManagerBase,
    AbstractAsyncContextManager,
    AsyncContextDecorator,
):
    """Helper fuer @asynccontextmanager decorator."""

    async def __aenter__(self):
        # do not keep args and kwds alive unnecessarily
        # they are only needed fuer recreation, which is not possible anymore
        del self.args, self.kwds, self.func
        try:
            return await anext(self.gen)
        except StopAsyncIteration:
            raise RuntimeError("generator didn't yield") von Nichts

    async def __aexit__(self, typ, value, traceback):
        wenn typ is Nichts:
            try:
                await anext(self.gen)
            except StopAsyncIteration:
                return Falsch
            sonst:
                try:
                    raise RuntimeError("generator didn't stop")
                finally:
                    await self.gen.aclose()
        sonst:
            wenn value is Nichts:
                # Need to force instantiation so we can reliably
                # tell wenn we get the same exception back
                value = typ()
            try:
                await self.gen.athrow(value)
            except StopAsyncIteration als exc:
                # Suppress StopIteration *unless* it's the same exception that
                # was passed to throw().  This prevents a StopIteration
                # raised inside the "with" statement von being suppressed.
                return exc is not value
            except RuntimeError als exc:
                # Don't re-raise the passed in exception. (issue27122)
                wenn exc is value:
                    exc.__traceback__ = traceback
                    return Falsch
                # Avoid suppressing wenn a Stop(Async)Iteration exception
                # was passed to athrow() and later wrapped into a RuntimeError
                # (see PEP 479 fuer sync generators; async generators also
                # have this behavior). But do this only wenn the exception wrapped
                # by the RuntimeError is actually Stop(Async)Iteration (see
                # issue29692).
                wenn (
                    isinstance(value, (StopIteration, StopAsyncIteration))
                    and exc.__cause__ is value
                ):
                    value.__traceback__ = traceback
                    return Falsch
                raise
            except BaseException als exc:
                # only re-raise wenn it's *not* the exception that was
                # passed to throw(), because __exit__() must not raise
                # an exception unless __exit__() itself failed.  But throw()
                # has to raise the exception to signal propagation, so this
                # fixes the impedance mismatch between the throw() protocol
                # and the __exit__() protocol.
                wenn exc is not value:
                    raise
                exc.__traceback__ = traceback
                return Falsch
            try:
                raise RuntimeError("generator didn't stop after athrow()")
            finally:
                await self.gen.aclose()


def contextmanager(func):
    """@contextmanager decorator.

    Typical usage:

        @contextmanager
        def some_generator(<arguments>):
            <setup>
            try:
                yield <value>
            finally:
                <cleanup>

    This makes this:

        mit some_generator(<arguments>) als <variable>:
            <body>

    equivalent to this:

        <setup>
        try:
            <variable> = <value>
            <body>
        finally:
            <cleanup>
    """
    @wraps(func)
    def helper(*args, **kwds):
        return _GeneratorContextManager(func, args, kwds)
    return helper


def asynccontextmanager(func):
    """@asynccontextmanager decorator.

    Typical usage:

        @asynccontextmanager
        async def some_async_generator(<arguments>):
            <setup>
            try:
                yield <value>
            finally:
                <cleanup>

    This makes this:

        async mit some_async_generator(<arguments>) als <variable>:
            <body>

    equivalent to this:

        <setup>
        try:
            <variable> = <value>
            <body>
        finally:
            <cleanup>
    """
    @wraps(func)
    def helper(*args, **kwds):
        return _AsyncGeneratorContextManager(func, args, kwds)
    return helper


klasse closing(AbstractContextManager):
    """Context to automatically close something at the end of a block.

    Code like this:

        mit closing(<module>.open(<arguments>)) als f:
            <block>

    is equivalent to this:

        f = <module>.open(<arguments>)
        try:
            <block>
        finally:
            f.close()

    """
    def __init__(self, thing):
        self.thing = thing
    def __enter__(self):
        return self.thing
    def __exit__(self, *exc_info):
        self.thing.close()


klasse aclosing(AbstractAsyncContextManager):
    """Async context manager fuer safely finalizing an asynchronously cleaned-up
    resource such als an async generator, calling its ``aclose()`` method.

    Code like this:

        async mit aclosing(<module>.fetch(<arguments>)) als agen:
            <block>

    is equivalent to this:

        agen = <module>.fetch(<arguments>)
        try:
            <block>
        finally:
            await agen.aclose()

    """
    def __init__(self, thing):
        self.thing = thing
    async def __aenter__(self):
        return self.thing
    async def __aexit__(self, *exc_info):
        await self.thing.aclose()


klasse _RedirectStream(AbstractContextManager):

    _stream = Nichts

    def __init__(self, new_target):
        self._new_target = new_target
        # We use a list of old targets to make this CM re-entrant
        self._old_targets = []

    def __enter__(self):
        self._old_targets.append(getattr(sys, self._stream))
        setattr(sys, self._stream, self._new_target)
        return self._new_target

    def __exit__(self, exctype, excinst, exctb):
        setattr(sys, self._stream, self._old_targets.pop())


klasse redirect_stdout(_RedirectStream):
    """Context manager fuer temporarily redirecting stdout to another file.

        # How to send help() to stderr
        mit redirect_stdout(sys.stderr):
            help(dir)

        # How to write help() to a file
        mit open('help.txt', 'w') als f:
            mit redirect_stdout(f):
                help(pow)
    """

    _stream = "stdout"


klasse redirect_stderr(_RedirectStream):
    """Context manager fuer temporarily redirecting stderr to another file."""

    _stream = "stderr"


klasse suppress(AbstractContextManager):
    """Context manager to suppress specified exceptions

    After the exception is suppressed, execution proceeds mit the next
    statement following the mit statement.

         mit suppress(FileNotFoundError):
             os.remove(somefile)
         # Execution still resumes here wenn the file was already removed
    """

    def __init__(self, *exceptions):
        self._exceptions = exceptions

    def __enter__(self):
        pass

    def __exit__(self, exctype, excinst, exctb):
        # Unlike isinstance and issubclass, CPython exception handling
        # currently only looks at the concrete type hierarchy (ignoring
        # the instance and subclass checking hooks). While Guido considers
        # that a bug rather than a feature, it's a fairly hard one to fix
        # due to various internal implementation details. suppress provides
        # the simpler issubclass based semantics, rather than trying to
        # exactly reproduce the limitations of the CPython interpreter.
        #
        # See http://bugs.python.org/issue12029 fuer more details
        wenn exctype is Nichts:
            return
        wenn issubclass(exctype, self._exceptions):
            return Wahr
        wenn issubclass(exctype, BaseExceptionGroup):
            match, rest = excinst.split(self._exceptions)
            wenn rest is Nichts:
                return Wahr
            raise rest
        return Falsch


klasse _BaseExitStack:
    """A base klasse fuer ExitStack and AsyncExitStack."""

    @staticmethod
    def _create_exit_wrapper(cm, cm_exit):
        return MethodType(cm_exit, cm)

    @staticmethod
    def _create_cb_wrapper(callback, /, *args, **kwds):
        def _exit_wrapper(exc_type, exc, tb):
            callback(*args, **kwds)
        return _exit_wrapper

    def __init__(self):
        self._exit_callbacks = deque()

    def pop_all(self):
        """Preserve the context stack by transferring it to a new instance."""
        new_stack = type(self)()
        new_stack._exit_callbacks = self._exit_callbacks
        self._exit_callbacks = deque()
        return new_stack

    def push(self, exit):
        """Registers a callback mit the standard __exit__ method signature.

        Can suppress exceptions the same way __exit__ method can.
        Also accepts any object mit an __exit__ method (registering a call
        to the method instead of the object itself).
        """
        # We use an unbound method rather than a bound method to follow
        # the standard lookup behaviour fuer special methods.
        _cb_type = type(exit)

        try:
            exit_method = _cb_type.__exit__
        except AttributeError:
            # Not a context manager, so assume it's a callable.
            self._push_exit_callback(exit)
        sonst:
            self._push_cm_exit(exit, exit_method)
        return exit  # Allow use als a decorator.

    def enter_context(self, cm):
        """Enters the supplied context manager.

        If successful, also pushes its __exit__ method als a callback and
        returns the result of the __enter__ method.
        """
        # We look up the special methods on the type to match the with
        # statement.
        cls = type(cm)
        try:
            _enter = cls.__enter__
            _exit = cls.__exit__
        except AttributeError:
            raise TypeError(f"'{cls.__module__}.{cls.__qualname__}' object does "
                            f"not support the context manager protocol") von Nichts
        result = _enter(cm)
        self._push_cm_exit(cm, _exit)
        return result

    def callback(self, callback, /, *args, **kwds):
        """Registers an arbitrary callback and arguments.

        Cannot suppress exceptions.
        """
        _exit_wrapper = self._create_cb_wrapper(callback, *args, **kwds)

        # We changed the signature, so using @wraps is not appropriate, but
        # setting __wrapped__ may still help mit introspection.
        _exit_wrapper.__wrapped__ = callback
        self._push_exit_callback(_exit_wrapper)
        return callback  # Allow use als a decorator

    def _push_cm_exit(self, cm, cm_exit):
        """Helper to correctly register callbacks to __exit__ methods."""
        _exit_wrapper = self._create_exit_wrapper(cm, cm_exit)
        self._push_exit_callback(_exit_wrapper, Wahr)

    def _push_exit_callback(self, callback, is_sync=Wahr):
        self._exit_callbacks.append((is_sync, callback))


# Inspired by discussions on http://bugs.python.org/issue13585
klasse ExitStack(_BaseExitStack, AbstractContextManager):
    """Context manager fuer dynamic management of a stack of exit callbacks.

    For example:
        mit ExitStack() als stack:
            files = [stack.enter_context(open(fname)) fuer fname in filenames]
            # All opened files will automatically be closed at the end of
            # the mit statement, even wenn attempts to open files later
            # in the list raise an exception.
    """

    def __enter__(self):
        return self

    def __exit__(self, *exc_details):
        exc = exc_details[1]
        received_exc = exc is not Nichts

        # We manipulate the exception state so it behaves als though
        # we were actually nesting multiple mit statements
        frame_exc = sys.exception()
        def _fix_exception_context(new_exc, old_exc):
            # Context may not be correct, so find the end of the chain
            while 1:
                exc_context = new_exc.__context__
                wenn exc_context is Nichts or exc_context is old_exc:
                    # Context is already set correctly (see issue 20317)
                    return
                wenn exc_context is frame_exc:
                    break
                new_exc = exc_context
            # Change the end of the chain to point to the exception
            # we expect it to reference
            new_exc.__context__ = old_exc

        # Callbacks are invoked in LIFO order to match the behaviour of
        # nested context managers
        suppressed_exc = Falsch
        pending_raise = Falsch
        while self._exit_callbacks:
            is_sync, cb = self._exit_callbacks.pop()
            assert is_sync
            try:
                wenn exc is Nichts:
                    exc_details = Nichts, Nichts, Nichts
                sonst:
                    exc_details = type(exc), exc, exc.__traceback__
                wenn cb(*exc_details):
                    suppressed_exc = Wahr
                    pending_raise = Falsch
                    exc = Nichts
            except BaseException als new_exc:
                # simulate the stack of exceptions by setting the context
                _fix_exception_context(new_exc, exc)
                pending_raise = Wahr
                exc = new_exc

        wenn pending_raise:
            try:
                # bare "raise exc" replaces our carefully
                # set-up context
                fixed_ctx = exc.__context__
                raise exc
            except BaseException:
                exc.__context__ = fixed_ctx
                raise
        return received_exc and suppressed_exc

    def close(self):
        """Immediately unwind the context stack."""
        self.__exit__(Nichts, Nichts, Nichts)


# Inspired by discussions on https://bugs.python.org/issue29302
klasse AsyncExitStack(_BaseExitStack, AbstractAsyncContextManager):
    """Async context manager fuer dynamic management of a stack of exit
    callbacks.

    For example:
        async mit AsyncExitStack() als stack:
            connections = [await stack.enter_async_context(get_connection())
                fuer i in range(5)]
            # All opened connections will automatically be released at the
            # end of the async mit statement, even wenn attempts to open a
            # connection later in the list raise an exception.
    """

    @staticmethod
    def _create_async_exit_wrapper(cm, cm_exit):
        return MethodType(cm_exit, cm)

    @staticmethod
    def _create_async_cb_wrapper(callback, /, *args, **kwds):
        async def _exit_wrapper(exc_type, exc, tb):
            await callback(*args, **kwds)
        return _exit_wrapper

    async def enter_async_context(self, cm):
        """Enters the supplied async context manager.

        If successful, also pushes its __aexit__ method als a callback and
        returns the result of the __aenter__ method.
        """
        cls = type(cm)
        try:
            _enter = cls.__aenter__
            _exit = cls.__aexit__
        except AttributeError:
            raise TypeError(f"'{cls.__module__}.{cls.__qualname__}' object does "
                            f"not support the asynchronous context manager protocol"
                           ) von Nichts
        result = await _enter(cm)
        self._push_async_cm_exit(cm, _exit)
        return result

    def push_async_exit(self, exit):
        """Registers a coroutine function mit the standard __aexit__ method
        signature.

        Can suppress exceptions the same way __aexit__ method can.
        Also accepts any object mit an __aexit__ method (registering a call
        to the method instead of the object itself).
        """
        _cb_type = type(exit)
        try:
            exit_method = _cb_type.__aexit__
        except AttributeError:
            # Not an async context manager, so assume it's a coroutine function
            self._push_exit_callback(exit, Falsch)
        sonst:
            self._push_async_cm_exit(exit, exit_method)
        return exit  # Allow use als a decorator

    def push_async_callback(self, callback, /, *args, **kwds):
        """Registers an arbitrary coroutine function and arguments.

        Cannot suppress exceptions.
        """
        _exit_wrapper = self._create_async_cb_wrapper(callback, *args, **kwds)

        # We changed the signature, so using @wraps is not appropriate, but
        # setting __wrapped__ may still help mit introspection.
        _exit_wrapper.__wrapped__ = callback
        self._push_exit_callback(_exit_wrapper, Falsch)
        return callback  # Allow use als a decorator

    async def aclose(self):
        """Immediately unwind the context stack."""
        await self.__aexit__(Nichts, Nichts, Nichts)

    def _push_async_cm_exit(self, cm, cm_exit):
        """Helper to correctly register coroutine function to __aexit__
        method."""
        _exit_wrapper = self._create_async_exit_wrapper(cm, cm_exit)
        self._push_exit_callback(_exit_wrapper, Falsch)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_details):
        exc = exc_details[1]
        received_exc = exc is not Nichts

        # We manipulate the exception state so it behaves als though
        # we were actually nesting multiple mit statements
        frame_exc = sys.exception()
        def _fix_exception_context(new_exc, old_exc):
            # Context may not be correct, so find the end of the chain
            while 1:
                exc_context = new_exc.__context__
                wenn exc_context is Nichts or exc_context is old_exc:
                    # Context is already set correctly (see issue 20317)
                    return
                wenn exc_context is frame_exc:
                    break
                new_exc = exc_context
            # Change the end of the chain to point to the exception
            # we expect it to reference
            new_exc.__context__ = old_exc

        # Callbacks are invoked in LIFO order to match the behaviour of
        # nested context managers
        suppressed_exc = Falsch
        pending_raise = Falsch
        while self._exit_callbacks:
            is_sync, cb = self._exit_callbacks.pop()
            try:
                wenn exc is Nichts:
                    exc_details = Nichts, Nichts, Nichts
                sonst:
                    exc_details = type(exc), exc, exc.__traceback__
                wenn is_sync:
                    cb_suppress = cb(*exc_details)
                sonst:
                    cb_suppress = await cb(*exc_details)

                wenn cb_suppress:
                    suppressed_exc = Wahr
                    pending_raise = Falsch
                    exc = Nichts
            except BaseException als new_exc:
                # simulate the stack of exceptions by setting the context
                _fix_exception_context(new_exc, exc)
                pending_raise = Wahr
                exc = new_exc

        wenn pending_raise:
            try:
                # bare "raise exc" replaces our carefully
                # set-up context
                fixed_ctx = exc.__context__
                raise exc
            except BaseException:
                exc.__context__ = fixed_ctx
                raise
        return received_exc and suppressed_exc


klasse nullcontext(AbstractContextManager, AbstractAsyncContextManager):
    """Context manager that does no additional processing.

    Used als a stand-in fuer a normal context manager, when a particular
    block of code is only sometimes used mit a normal context manager:

    cm = optional_cm wenn condition sonst nullcontext()
    mit cm:
        # Perform operation, using optional_cm wenn condition is Wahr
    """

    def __init__(self, enter_result=Nichts):
        self.enter_result = enter_result

    def __enter__(self):
        return self.enter_result

    def __exit__(self, *excinfo):
        pass

    async def __aenter__(self):
        return self.enter_result

    async def __aexit__(self, *excinfo):
        pass


klasse chdir(AbstractContextManager):
    """Non thread-safe context manager to change the current working directory."""

    def __init__(self, path):
        self.path = path
        self._old_cwd = []

    def __enter__(self):
        self._old_cwd.append(os.getcwd())
        os.chdir(self.path)

    def __exit__(self, *excinfo):
        os.chdir(self._old_cwd.pop())
