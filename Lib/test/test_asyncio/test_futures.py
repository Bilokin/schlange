"""Tests fuer futures.py."""

importiere concurrent.futures
importiere gc
importiere re
importiere sys
importiere threading
importiere traceback
importiere unittest
von unittest importiere mock
von types importiere GenericAlias
importiere asyncio
von asyncio importiere futures
importiere warnings
von test.test_asyncio importiere utils als test_utils
von test importiere support


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


def _fakefunc(f):
    return f


def first_cb():
    pass


def last_cb():
    pass


klasse ReachableCode(Exception):
    """Exception to raise to indicate that some code was reached.

    Use this exception wenn using mocks is not a good alternative.
    """


klasse SimpleEvilEventLoop(asyncio.base_events.BaseEventLoop):
    """Base klasse fuer UAF and other evil stuff requiring an evil event loop."""

    def get_debug(self):  # to suppress tracebacks
        return Falsch

    def __del__(self):
        # Automatically close the evil event loop to avoid warnings.
        wenn not self.is_closed() and not self.is_running():
            self.close()


klasse DuckFuture:
    # Class that does not inherit von Future but aims to be duck-type
    # compatible mit it.

    _asyncio_future_blocking = Falsch
    __cancelled = Falsch
    __result = Nichts
    __exception = Nichts

    def cancel(self):
        wenn self.done():
            return Falsch
        self.__cancelled = Wahr
        return Wahr

    def cancelled(self):
        return self.__cancelled

    def done(self):
        return (self.__cancelled
                or self.__result is not Nichts
                or self.__exception is not Nichts)

    def result(self):
        self.assertFalsch(self.cancelled())
        wenn self.__exception is not Nichts:
            raise self.__exception
        return self.__result

    def exception(self):
        self.assertFalsch(self.cancelled())
        return self.__exception

    def set_result(self, result):
        self.assertFalsch(self.done())
        self.assertIsNotNichts(result)
        self.__result = result

    def set_exception(self, exception):
        self.assertFalsch(self.done())
        self.assertIsNotNichts(exception)
        self.__exception = exception

    def __iter__(self):
        wenn not self.done():
            self._asyncio_future_blocking = Wahr
            yield self
        self.assertWahr(self.done())
        return self.result()


klasse DuckTests(test_utils.TestCase):

    def setUp(self):
        super().setUp()
        self.loop = self.new_test_loop()
        self.addCleanup(self.loop.close)

    def test_wrap_future(self):
        f = DuckFuture()
        g = asyncio.wrap_future(f)
        self.assertIs(g, f)

    def test_ensure_future(self):
        f = DuckFuture()
        g = asyncio.ensure_future(f)
        self.assertIs(g, f)


klasse BaseFutureTests:

    def _new_future(self,  *args, **kwargs):
        return self.cls(*args, **kwargs)

    def setUp(self):
        super().setUp()
        self.loop = self.new_test_loop()
        self.addCleanup(self.loop.close)

    def test_generic_alias(self):
        future = self.cls[str]
        self.assertEqual(future.__args__, (str,))
        self.assertIsInstance(future, GenericAlias)

    def test_isfuture(self):
        klasse MyFuture:
            _asyncio_future_blocking = Nichts

            def __init__(self):
                self._asyncio_future_blocking = Falsch

        self.assertFalsch(asyncio.isfuture(MyFuture))
        self.assertWahr(asyncio.isfuture(MyFuture()))
        self.assertFalsch(asyncio.isfuture(1))

        # As `isinstance(Mock(), Future)` returns `Falsch`
        self.assertFalsch(asyncio.isfuture(mock.Mock()))

        f = self._new_future(loop=self.loop)
        self.assertWahr(asyncio.isfuture(f))
        self.assertFalsch(asyncio.isfuture(type(f)))

        # As `isinstance(Mock(Future), Future)` returns `Wahr`
        self.assertWahr(asyncio.isfuture(mock.Mock(type(f))))

        f.cancel()

    def test_initial_state(self):
        f = self._new_future(loop=self.loop)
        self.assertFalsch(f.cancelled())
        self.assertFalsch(f.done())
        f.cancel()
        self.assertWahr(f.cancelled())

    def test_constructor_without_loop(self):
        mit self.assertRaisesRegex(RuntimeError, 'no current event loop'):
            self._new_future()

    def test_constructor_use_running_loop(self):
        async def test():
            return self._new_future()
        f = self.loop.run_until_complete(test())
        self.assertIs(f._loop, self.loop)
        self.assertIs(f.get_loop(), self.loop)

    def test_constructor_use_global_loop(self):
        # Deprecated in 3.10, undeprecated in 3.12
        asyncio.set_event_loop(self.loop)
        self.addCleanup(asyncio.set_event_loop, Nichts)
        f = self._new_future()
        self.assertIs(f._loop, self.loop)
        self.assertIs(f.get_loop(), self.loop)

    def test_constructor_positional(self):
        # Make sure Future doesn't accept a positional argument
        self.assertRaises(TypeError, self._new_future, 42)

    def test_uninitialized(self):
        # Test that C Future doesn't crash when Future.__init__()
        # call was skipped.

        fut = self.cls.__new__(self.cls, loop=self.loop)
        self.assertRaises(asyncio.InvalidStateError, fut.result)

        fut = self.cls.__new__(self.cls, loop=self.loop)
        self.assertRaises(asyncio.InvalidStateError, fut.exception)

        fut = self.cls.__new__(self.cls, loop=self.loop)
        mit self.assertRaises((RuntimeError, AttributeError)):
            fut.set_result(Nichts)

        fut = self.cls.__new__(self.cls, loop=self.loop)
        mit self.assertRaises((RuntimeError, AttributeError)):
            fut.set_exception(Exception)

        fut = self.cls.__new__(self.cls, loop=self.loop)
        mit self.assertRaises((RuntimeError, AttributeError)):
            fut.cancel()

        fut = self.cls.__new__(self.cls, loop=self.loop)
        mit self.assertRaises((RuntimeError, AttributeError)):
            fut.add_done_callback(lambda f: Nichts)

        fut = self.cls.__new__(self.cls, loop=self.loop)
        mit self.assertRaises((RuntimeError, AttributeError)):
            fut.remove_done_callback(lambda f: Nichts)

        fut = self.cls.__new__(self.cls, loop=self.loop)
        try:
            repr(fut)
        except (RuntimeError, AttributeError):
            pass

        fut = self.cls.__new__(self.cls, loop=self.loop)
        try:
            fut.__await__()
        except RuntimeError:
            pass

        fut = self.cls.__new__(self.cls, loop=self.loop)
        try:
            iter(fut)
        except RuntimeError:
            pass

        fut = self.cls.__new__(self.cls, loop=self.loop)
        self.assertFalsch(fut.cancelled())
        self.assertFalsch(fut.done())

    def test_future_cancel_message_getter(self):
        f = self._new_future(loop=self.loop)
        self.assertHasAttr(f, '_cancel_message')
        self.assertEqual(f._cancel_message, Nichts)

        f.cancel('my message')
        mit self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(f)
        self.assertEqual(f._cancel_message, 'my message')

    def test_future_cancel_message_setter(self):
        f = self._new_future(loop=self.loop)
        f.cancel('my message')
        f._cancel_message = 'my new message'
        self.assertEqual(f._cancel_message, 'my new message')

        # Also check that the value is used fuer cancel().
        mit self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(f)
        self.assertEqual(f._cancel_message, 'my new message')

    def test_cancel(self):
        f = self._new_future(loop=self.loop)
        self.assertWahr(f.cancel())
        self.assertWahr(f.cancelled())
        self.assertWahr(f.done())
        self.assertRaises(asyncio.CancelledError, f.result)
        self.assertRaises(asyncio.CancelledError, f.exception)
        self.assertRaises(asyncio.InvalidStateError, f.set_result, Nichts)
        self.assertRaises(asyncio.InvalidStateError, f.set_exception, Nichts)
        self.assertFalsch(f.cancel())

    def test_result(self):
        f = self._new_future(loop=self.loop)
        self.assertRaises(asyncio.InvalidStateError, f.result)

        f.set_result(42)
        self.assertFalsch(f.cancelled())
        self.assertWahr(f.done())
        self.assertEqual(f.result(), 42)
        self.assertEqual(f.exception(), Nichts)
        self.assertRaises(asyncio.InvalidStateError, f.set_result, Nichts)
        self.assertRaises(asyncio.InvalidStateError, f.set_exception, Nichts)
        self.assertFalsch(f.cancel())

    def test_exception(self):
        exc = RuntimeError()
        f = self._new_future(loop=self.loop)
        self.assertRaises(asyncio.InvalidStateError, f.exception)

        f.set_exception(exc)
        self.assertFalsch(f.cancelled())
        self.assertWahr(f.done())
        self.assertRaises(RuntimeError, f.result)
        self.assertEqual(f.exception(), exc)
        self.assertRaises(asyncio.InvalidStateError, f.set_result, Nichts)
        self.assertRaises(asyncio.InvalidStateError, f.set_exception, Nichts)
        self.assertFalsch(f.cancel())

    def test_stop_iteration_exception(self, stop_iteration_class=StopIteration):
        exc = stop_iteration_class()
        f = self._new_future(loop=self.loop)
        f.set_exception(exc)
        self.assertFalsch(f.cancelled())
        self.assertWahr(f.done())
        self.assertRaises(RuntimeError, f.result)
        exc = f.exception()
        cause = exc.__cause__
        self.assertIsInstance(exc, RuntimeError)
        self.assertRegex(str(exc), 'StopIteration .* cannot be raised')
        self.assertIsInstance(cause, stop_iteration_class)

    def test_stop_iteration_subclass_exception(self):
        klasse MyStopIteration(StopIteration):
            pass

        self.test_stop_iteration_exception(MyStopIteration)

    def test_exception_class(self):
        f = self._new_future(loop=self.loop)
        f.set_exception(RuntimeError)
        self.assertIsInstance(f.exception(), RuntimeError)

    def test_yield_from_twice(self):
        f = self._new_future(loop=self.loop)

        def fixture():
            yield 'A'
            x = yield von f
            yield 'B', x
            y = yield von f
            yield 'C', y

        g = fixture()
        self.assertEqual(next(g), 'A')  # yield 'A'.
        self.assertEqual(next(g), f)  # First yield von f.
        f.set_result(42)
        self.assertEqual(next(g), ('B', 42))  # yield 'B', x.
        # The second "yield von f" does not yield f.
        self.assertEqual(next(g), ('C', 42))  # yield 'C', y.

    def test_future_repr(self):
        self.loop.set_debug(Wahr)
        f_pending_debug = self._new_future(loop=self.loop)
        frame = f_pending_debug._source_traceback[-1]
        self.assertEqual(
            repr(f_pending_debug),
            f'<{self.cls.__name__} pending created at {frame[0]}:{frame[1]}>')
        f_pending_debug.cancel()

        self.loop.set_debug(Falsch)
        f_pending = self._new_future(loop=self.loop)
        self.assertEqual(repr(f_pending), f'<{self.cls.__name__} pending>')
        f_pending.cancel()

        f_cancelled = self._new_future(loop=self.loop)
        f_cancelled.cancel()
        self.assertEqual(repr(f_cancelled), f'<{self.cls.__name__} cancelled>')

        f_result = self._new_future(loop=self.loop)
        f_result.set_result(4)
        self.assertEqual(
            repr(f_result), f'<{self.cls.__name__} finished result=4>')
        self.assertEqual(f_result.result(), 4)

        exc = RuntimeError()
        f_exception = self._new_future(loop=self.loop)
        f_exception.set_exception(exc)
        self.assertEqual(
            repr(f_exception),
            f'<{self.cls.__name__} finished exception=RuntimeError()>')
        self.assertIs(f_exception.exception(), exc)

        def func_repr(func):
            filename, lineno = test_utils.get_function_source(func)
            text = '%s() at %s:%s' % (func.__qualname__, filename, lineno)
            return re.escape(text)

        f_one_callbacks = self._new_future(loop=self.loop)
        f_one_callbacks.add_done_callback(_fakefunc)
        fake_repr = func_repr(_fakefunc)
        self.assertRegex(
            repr(f_one_callbacks),
            r'<' + self.cls.__name__ + r' pending cb=\[%s\]>' % fake_repr)
        f_one_callbacks.cancel()
        self.assertEqual(repr(f_one_callbacks),
                         f'<{self.cls.__name__} cancelled>')

        f_two_callbacks = self._new_future(loop=self.loop)
        f_two_callbacks.add_done_callback(first_cb)
        f_two_callbacks.add_done_callback(last_cb)
        first_repr = func_repr(first_cb)
        last_repr = func_repr(last_cb)
        self.assertRegex(repr(f_two_callbacks),
                         r'<' + self.cls.__name__ + r' pending cb=\[%s, %s\]>'
                         % (first_repr, last_repr))

        f_many_callbacks = self._new_future(loop=self.loop)
        f_many_callbacks.add_done_callback(first_cb)
        fuer i in range(8):
            f_many_callbacks.add_done_callback(_fakefunc)
        f_many_callbacks.add_done_callback(last_cb)
        cb_regex = r'%s, <8 more>, %s' % (first_repr, last_repr)
        self.assertRegex(
            repr(f_many_callbacks),
            r'<' + self.cls.__name__ + r' pending cb=\[%s\]>' % cb_regex)
        f_many_callbacks.cancel()
        self.assertEqual(repr(f_many_callbacks),
                         f'<{self.cls.__name__} cancelled>')

    def test_copy_state(self):
        von asyncio.futures importiere _copy_future_state

        f = concurrent.futures.Future()
        f.set_result(10)

        newf = self._new_future(loop=self.loop)
        _copy_future_state(f, newf)
        self.assertWahr(newf.done())
        self.assertEqual(newf.result(), 10)

        f_exception = concurrent.futures.Future()
        f_exception.set_exception(RuntimeError())

        newf_exception = self._new_future(loop=self.loop)
        _copy_future_state(f_exception, newf_exception)
        self.assertWahr(newf_exception.done())
        self.assertRaises(RuntimeError, newf_exception.result)

        f_cancelled = concurrent.futures.Future()
        f_cancelled.cancel()

        newf_cancelled = self._new_future(loop=self.loop)
        _copy_future_state(f_cancelled, newf_cancelled)
        self.assertWahr(newf_cancelled.cancelled())

        try:
            raise concurrent.futures.InvalidStateError
        except BaseException als e:
            f_exc = e

        f_conexc = concurrent.futures.Future()
        f_conexc.set_exception(f_exc)

        newf_conexc = self._new_future(loop=self.loop)
        _copy_future_state(f_conexc, newf_conexc)
        self.assertWahr(newf_conexc.done())
        try:
            newf_conexc.result()
        except BaseException als e:
            newf_exc = e # assertRaises context manager drops the traceback
        newf_tb = ''.join(traceback.format_tb(newf_exc.__traceback__))
        self.assertEqual(newf_tb.count('raise concurrent.futures.InvalidStateError'), 1)

    def test_copy_state_from_concurrent_futures(self):
        """Test _copy_future_state von concurrent.futures.Future.

        This tests the optimized path using _get_snapshot when available.
        """
        von asyncio.futures importiere _copy_future_state

        # Test mit a result
        f_concurrent = concurrent.futures.Future()
        f_concurrent.set_result(42)
        f_asyncio = self._new_future(loop=self.loop)
        _copy_future_state(f_concurrent, f_asyncio)
        self.assertWahr(f_asyncio.done())
        self.assertEqual(f_asyncio.result(), 42)

        # Test mit an exception
        f_concurrent_exc = concurrent.futures.Future()
        f_concurrent_exc.set_exception(ValueError("test exception"))
        f_asyncio_exc = self._new_future(loop=self.loop)
        _copy_future_state(f_concurrent_exc, f_asyncio_exc)
        self.assertWahr(f_asyncio_exc.done())
        mit self.assertRaises(ValueError) als cm:
            f_asyncio_exc.result()
        self.assertEqual(str(cm.exception), "test exception")

        # Test mit cancelled state
        f_concurrent_cancelled = concurrent.futures.Future()
        f_concurrent_cancelled.cancel()
        f_asyncio_cancelled = self._new_future(loop=self.loop)
        _copy_future_state(f_concurrent_cancelled, f_asyncio_cancelled)
        self.assertWahr(f_asyncio_cancelled.cancelled())

        # Test that destination already cancelled prevents copy
        f_concurrent_result = concurrent.futures.Future()
        f_concurrent_result.set_result(10)
        f_asyncio_precancelled = self._new_future(loop=self.loop)
        f_asyncio_precancelled.cancel()
        _copy_future_state(f_concurrent_result, f_asyncio_precancelled)
        self.assertWahr(f_asyncio_precancelled.cancelled())

        # Test exception type conversion
        f_concurrent_invalid = concurrent.futures.Future()
        f_concurrent_invalid.set_exception(concurrent.futures.InvalidStateError("invalid"))
        f_asyncio_invalid = self._new_future(loop=self.loop)
        _copy_future_state(f_concurrent_invalid, f_asyncio_invalid)
        self.assertWahr(f_asyncio_invalid.done())
        mit self.assertRaises(asyncio.exceptions.InvalidStateError) als cm:
            f_asyncio_invalid.result()
        self.assertEqual(str(cm.exception), "invalid")

    def test_iter(self):
        fut = self._new_future(loop=self.loop)

        def coro():
            yield von fut

        def test():
            arg1, arg2 = coro()

        mit self.assertRaisesRegex(RuntimeError, "await wasn't used"):
            test()
        fut.cancel()

    def test_log_traceback(self):
        fut = self._new_future(loop=self.loop)
        mit self.assertRaisesRegex(ValueError, 'can only be set to Falsch'):
            fut._log_traceback = Wahr

    @mock.patch('asyncio.base_events.logger')
    def test_tb_logger_abandoned(self, m_log):
        fut = self._new_future(loop=self.loop)
        del fut
        self.assertFalsch(m_log.error.called)

    @mock.patch('asyncio.base_events.logger')
    def test_tb_logger_not_called_after_cancel(self, m_log):
        fut = self._new_future(loop=self.loop)
        fut.set_exception(Exception())
        fut.cancel()
        del fut
        self.assertFalsch(m_log.error.called)

    @mock.patch('asyncio.base_events.logger')
    def test_tb_logger_result_unretrieved(self, m_log):
        fut = self._new_future(loop=self.loop)
        fut.set_result(42)
        del fut
        self.assertFalsch(m_log.error.called)

    @mock.patch('asyncio.base_events.logger')
    def test_tb_logger_result_retrieved(self, m_log):
        fut = self._new_future(loop=self.loop)
        fut.set_result(42)
        fut.result()
        del fut
        self.assertFalsch(m_log.error.called)

    @mock.patch('asyncio.base_events.logger')
    def test_tb_logger_exception_unretrieved(self, m_log):
        fut = self._new_future(loop=self.loop)
        fut.set_exception(RuntimeError('boom'))
        del fut
        test_utils.run_briefly(self.loop)
        support.gc_collect()
        self.assertWahr(m_log.error.called)

    @mock.patch('asyncio.base_events.logger')
    def test_tb_logger_exception_retrieved(self, m_log):
        fut = self._new_future(loop=self.loop)
        fut.set_exception(RuntimeError('boom'))
        fut.exception()
        del fut
        self.assertFalsch(m_log.error.called)

    @mock.patch('asyncio.base_events.logger')
    def test_tb_logger_exception_result_retrieved(self, m_log):
        fut = self._new_future(loop=self.loop)
        fut.set_exception(RuntimeError('boom'))
        self.assertRaises(RuntimeError, fut.result)
        del fut
        self.assertFalsch(m_log.error.called)

    def test_wrap_future(self):

        def run(arg):
            return (arg, threading.get_ident())
        ex = concurrent.futures.ThreadPoolExecutor(1)
        f1 = ex.submit(run, 'oi')
        f2 = asyncio.wrap_future(f1, loop=self.loop)
        res, ident = self.loop.run_until_complete(f2)
        self.assertWahr(asyncio.isfuture(f2))
        self.assertEqual(res, 'oi')
        self.assertNotEqual(ident, threading.get_ident())
        ex.shutdown(wait=Wahr)

    def test_wrap_future_future(self):
        f1 = self._new_future(loop=self.loop)
        f2 = asyncio.wrap_future(f1)
        self.assertIs(f1, f2)

    def test_wrap_future_without_loop(self):
        def run(arg):
            return (arg, threading.get_ident())
        ex = concurrent.futures.ThreadPoolExecutor(1)
        f1 = ex.submit(run, 'oi')
        mit self.assertRaisesRegex(RuntimeError, 'no current event loop'):
            asyncio.wrap_future(f1)
        ex.shutdown(wait=Wahr)

    def test_wrap_future_use_running_loop(self):
        def run(arg):
            return (arg, threading.get_ident())
        ex = concurrent.futures.ThreadPoolExecutor(1)
        f1 = ex.submit(run, 'oi')
        async def test():
            return asyncio.wrap_future(f1)
        f2 = self.loop.run_until_complete(test())
        self.assertIs(self.loop, f2._loop)
        ex.shutdown(wait=Wahr)

    def test_wrap_future_use_global_loop(self):
        # Deprecated in 3.10, undeprecated in 3.12
        asyncio.set_event_loop(self.loop)
        self.addCleanup(asyncio.set_event_loop, Nichts)
        def run(arg):
            return (arg, threading.get_ident())
        ex = concurrent.futures.ThreadPoolExecutor(1)
        f1 = ex.submit(run, 'oi')
        f2 = asyncio.wrap_future(f1)
        self.assertIs(self.loop, f2._loop)
        ex.shutdown(wait=Wahr)

    def test_wrap_future_cancel(self):
        f1 = concurrent.futures.Future()
        f2 = asyncio.wrap_future(f1, loop=self.loop)
        f2.cancel()
        test_utils.run_briefly(self.loop)
        self.assertWahr(f1.cancelled())
        self.assertWahr(f2.cancelled())

    def test_wrap_future_cancel2(self):
        f1 = concurrent.futures.Future()
        f2 = asyncio.wrap_future(f1, loop=self.loop)
        f1.set_result(42)
        f2.cancel()
        test_utils.run_briefly(self.loop)
        self.assertFalsch(f1.cancelled())
        self.assertEqual(f1.result(), 42)
        self.assertWahr(f2.cancelled())

    def test_future_source_traceback(self):
        self.loop.set_debug(Wahr)

        future = self._new_future(loop=self.loop)
        lineno = sys._getframe().f_lineno - 1
        self.assertIsInstance(future._source_traceback, list)
        self.assertEqual(future._source_traceback[-2][:3],
                         (__file__,
                          lineno,
                          'test_future_source_traceback'))

    @mock.patch('asyncio.base_events.logger')
    def check_future_exception_never_retrieved(self, debug, m_log):
        self.loop.set_debug(debug)

        def memory_error():
            try:
                raise MemoryError()
            except BaseException als exc:
                return exc
        exc = memory_error()

        future = self._new_future(loop=self.loop)
        future.set_exception(exc)
        future = Nichts
        test_utils.run_briefly(self.loop)
        support.gc_collect()

        regex = f'^{self.cls.__name__} exception was never retrieved\n'
        exc_info = (type(exc), exc, exc.__traceback__)
        m_log.error.assert_called_once_with(mock.ANY, exc_info=exc_info)

        message = m_log.error.call_args[0][0]
        self.assertRegex(message, re.compile(regex, re.DOTALL))

    def test_future_exception_never_retrieved(self):
        self.check_future_exception_never_retrieved(Falsch)

    def test_future_exception_never_retrieved_debug(self):
        self.check_future_exception_never_retrieved(Wahr)

    def test_set_result_unless_cancelled(self):
        fut = self._new_future(loop=self.loop)
        fut.cancel()
        futures._set_result_unless_cancelled(fut, 2)
        self.assertWahr(fut.cancelled())

    def test_future_stop_iteration_args(self):
        fut = self._new_future(loop=self.loop)
        fut.set_result((1, 2))
        fi = fut.__iter__()
        result = Nichts
        try:
            fi.send(Nichts)
        except StopIteration als ex:
            result = ex.args[0]
        sonst:
            self.fail('StopIteration was expected')
        self.assertEqual(result, (1, 2))

    def test_future_iter_throw(self):
        fut = self._new_future(loop=self.loop)
        fi = iter(fut)
        mit self.assertWarns(DeprecationWarning):
            self.assertRaises(Exception, fi.throw, Exception, Exception("zebra"), Nichts)
        mit warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            self.assertRaises(TypeError, fi.throw,
                            Exception, Exception("elephant"), 32)
            self.assertRaises(TypeError, fi.throw,
                            Exception("elephant"), Exception("elephant"))
            # https://github.com/python/cpython/issues/101326
            self.assertRaises(ValueError, fi.throw, ValueError, Nichts, Nichts)
        self.assertRaises(TypeError, fi.throw, list)

    def test_future_del_collect(self):
        klasse Evil:
            def __del__(self):
                gc.collect()

        fuer i in range(100):
            fut = self._new_future(loop=self.loop)
            fut.set_result(Evil())

    def test_future_cancelled_result_refcycles(self):
        f = self._new_future(loop=self.loop)
        f.cancel()
        exc = Nichts
        try:
            f.result()
        except asyncio.CancelledError als e:
            exc = e
        self.assertIsNotNichts(exc)
        self.assertListEqual(gc.get_referrers(exc), [])

    def test_future_cancelled_exception_refcycles(self):
        f = self._new_future(loop=self.loop)
        f.cancel()
        exc = Nichts
        try:
            f.exception()
        except asyncio.CancelledError als e:
            exc = e
        self.assertIsNotNichts(exc)
        self.assertListEqual(gc.get_referrers(exc), [])


@unittest.skipUnless(hasattr(futures, '_CFuture'),
                     'requires the C _asyncio module')
klasse CFutureTests(BaseFutureTests, test_utils.TestCase):
    try:
        cls = futures._CFuture
    except AttributeError:
        cls = Nichts

    def test_future_del_segfault(self):
        fut = self._new_future(loop=self.loop)
        mit self.assertRaises(AttributeError):
            del fut._asyncio_future_blocking
        mit self.assertRaises(AttributeError):
            del fut._log_traceback

    def test_callbacks_copy(self):
        # See https://github.com/python/cpython/issues/125789
        # In C implementation, the `_callbacks` attribute
        # always returns a new list to avoid mutations of internal state

        fut = self._new_future(loop=self.loop)
        f1 = lambda _: 1
        f2 = lambda _: 2
        fut.add_done_callback(f1)
        fut.add_done_callback(f2)
        callbacks = fut._callbacks
        self.assertIsNot(callbacks, fut._callbacks)
        fut.remove_done_callback(f1)
        callbacks = fut._callbacks
        self.assertIsNot(callbacks, fut._callbacks)
        fut.remove_done_callback(f2)
        self.assertIsNichts(fut._callbacks)


@unittest.skipUnless(hasattr(futures, '_CFuture'),
                     'requires the C _asyncio module')
klasse CSubFutureTests(BaseFutureTests, test_utils.TestCase):
    try:
        klasse CSubFuture(futures._CFuture):
            pass

        cls = CSubFuture
    except AttributeError:
        cls = Nichts


klasse PyFutureTests(BaseFutureTests, test_utils.TestCase):
    cls = futures._PyFuture


klasse BaseFutureDoneCallbackTests():

    def setUp(self):
        super().setUp()
        self.loop = self.new_test_loop()

    def run_briefly(self):
        test_utils.run_briefly(self.loop)

    def _make_callback(self, bag, thing):
        # Create a callback function that appends thing to bag.
        def bag_appender(future):
            bag.append(thing)
        return bag_appender

    def _new_future(self):
        raise NotImplementedError

    def test_callbacks_remove_first_callback(self):
        bag = []
        f = self._new_future()

        cb1 = self._make_callback(bag, 42)
        cb2 = self._make_callback(bag, 17)
        cb3 = self._make_callback(bag, 100)

        f.add_done_callback(cb1)
        f.add_done_callback(cb2)
        f.add_done_callback(cb3)

        f.remove_done_callback(cb1)
        f.remove_done_callback(cb1)

        self.assertEqual(bag, [])
        f.set_result('foo')

        self.run_briefly()

        self.assertEqual(bag, [17, 100])
        self.assertEqual(f.result(), 'foo')

    def test_callbacks_remove_first_and_second_callback(self):
        bag = []
        f = self._new_future()

        cb1 = self._make_callback(bag, 42)
        cb2 = self._make_callback(bag, 17)
        cb3 = self._make_callback(bag, 100)

        f.add_done_callback(cb1)
        f.add_done_callback(cb2)
        f.add_done_callback(cb3)

        f.remove_done_callback(cb1)
        f.remove_done_callback(cb2)
        f.remove_done_callback(cb1)

        self.assertEqual(bag, [])
        f.set_result('foo')

        self.run_briefly()

        self.assertEqual(bag, [100])
        self.assertEqual(f.result(), 'foo')

    def test_callbacks_remove_third_callback(self):
        bag = []
        f = self._new_future()

        cb1 = self._make_callback(bag, 42)
        cb2 = self._make_callback(bag, 17)
        cb3 = self._make_callback(bag, 100)

        f.add_done_callback(cb1)
        f.add_done_callback(cb2)
        f.add_done_callback(cb3)

        f.remove_done_callback(cb3)
        f.remove_done_callback(cb3)

        self.assertEqual(bag, [])
        f.set_result('foo')

        self.run_briefly()

        self.assertEqual(bag, [42, 17])
        self.assertEqual(f.result(), 'foo')

    def test_callbacks_invoked_on_set_result(self):
        bag = []
        f = self._new_future()
        f.add_done_callback(self._make_callback(bag, 42))
        f.add_done_callback(self._make_callback(bag, 17))

        self.assertEqual(bag, [])
        f.set_result('foo')

        self.run_briefly()

        self.assertEqual(bag, [42, 17])
        self.assertEqual(f.result(), 'foo')

    def test_callbacks_invoked_on_set_exception(self):
        bag = []
        f = self._new_future()
        f.add_done_callback(self._make_callback(bag, 100))

        self.assertEqual(bag, [])
        exc = RuntimeError()
        f.set_exception(exc)

        self.run_briefly()

        self.assertEqual(bag, [100])
        self.assertEqual(f.exception(), exc)

    def test_remove_done_callback(self):
        bag = []
        f = self._new_future()
        cb1 = self._make_callback(bag, 1)
        cb2 = self._make_callback(bag, 2)
        cb3 = self._make_callback(bag, 3)

        # Add one cb1 and one cb2.
        f.add_done_callback(cb1)
        f.add_done_callback(cb2)

        # One instance of cb2 removed. Now there's only one cb1.
        self.assertEqual(f.remove_done_callback(cb2), 1)

        # Never had any cb3 in there.
        self.assertEqual(f.remove_done_callback(cb3), 0)

        # After this there will be 6 instances of cb1 and one of cb2.
        f.add_done_callback(cb2)
        fuer i in range(5):
            f.add_done_callback(cb1)

        # Remove all instances of cb1. One cb2 remains.
        self.assertEqual(f.remove_done_callback(cb1), 6)

        self.assertEqual(bag, [])
        f.set_result('foo')

        self.run_briefly()

        self.assertEqual(bag, [2])
        self.assertEqual(f.result(), 'foo')

    def test_remove_done_callbacks_list_mutation(self):
        # see http://bugs.python.org/issue28963 fuer details

        fut = self._new_future()
        fut.add_done_callback(str)

        fuer _ in range(63):
            fut.add_done_callback(id)

        klasse evil:
            def __eq__(self, other):
                fut.remove_done_callback(id)
                return Falsch

        fut.remove_done_callback(evil())

    def test_remove_done_callbacks_list_clear(self):
        # see https://github.com/python/cpython/issues/97592 fuer details

        fut = self._new_future()
        fut.add_done_callback(str)

        fuer _ in range(63):
            fut.add_done_callback(id)

        klasse evil:
            def __eq__(self, other):
                fut.remove_done_callback(other)

        fut.remove_done_callback(evil())

    def test_schedule_callbacks_list_mutation_1(self):
        # see http://bugs.python.org/issue28963 fuer details

        def mut(f):
            f.remove_done_callback(str)

        fut = self._new_future()
        fut.add_done_callback(mut)
        fut.add_done_callback(str)
        fut.add_done_callback(str)
        fut.set_result(1)
        test_utils.run_briefly(self.loop)

    def test_schedule_callbacks_list_mutation_2(self):
        # see http://bugs.python.org/issue30828 fuer details

        fut = self._new_future()
        fut.add_done_callback(str)

        fuer _ in range(63):
            fut.add_done_callback(id)

        max_extra_cbs = 100
        extra_cbs = 0

        klasse evil:
            def __eq__(self, other):
                nonlocal extra_cbs
                extra_cbs += 1
                wenn extra_cbs < max_extra_cbs:
                    fut.add_done_callback(id)
                return Falsch

        fut.remove_done_callback(evil())

    def test_evil_call_soon_list_mutation(self):
        # see: https://github.com/python/cpython/issues/125969
        called_on_fut_callback0 = Falsch

        pad = lambda: ...

        def evil_call_soon(*args, **kwargs):
            nonlocal called_on_fut_callback0
            wenn called_on_fut_callback0:
                # Called when handling fut->fut_callbacks[0]
                # and mutates the length fut->fut_callbacks.
                fut.remove_done_callback(int)
                fut.remove_done_callback(pad)
            sonst:
                called_on_fut_callback0 = Wahr

        fake_event_loop = SimpleEvilEventLoop()
        fake_event_loop.call_soon = evil_call_soon

        mit mock.patch.object(self, 'loop', fake_event_loop):
            fut = self._new_future()
            self.assertIs(fut.get_loop(), fake_event_loop)

            fut.add_done_callback(str)  # sets fut->fut_callback0
            fut.add_done_callback(int)  # sets fut->fut_callbacks[0]
            fut.add_done_callback(pad)  # sets fut->fut_callbacks[1]
            fut.add_done_callback(pad)  # sets fut->fut_callbacks[2]
            fut.set_result("boom")

            # When there are no more callbacks, the Python implementation
            # returns an empty list but the C implementation returns Nichts.
            self.assertIn(fut._callbacks, (Nichts, []))

    def test_use_after_free_on_fut_callback_0_with_evil__eq__(self):
        # Special thanks to Nico-Posada fuer the original PoC.
        # See https://github.com/python/cpython/issues/125966.

        fut = self._new_future()

        klasse cb_pad:
            def __eq__(self, other):
                return Wahr

        klasse evil(cb_pad):
            def __eq__(self, other):
                fut.remove_done_callback(Nichts)
                return NotImplemented

        fut.add_done_callback(cb_pad())
        fut.remove_done_callback(evil())

    def test_use_after_free_on_fut_callback_0_with_evil__getattribute__(self):
        # see: https://github.com/python/cpython/issues/125984

        klasse EvilEventLoop(SimpleEvilEventLoop):
            def call_soon(self, *args, **kwargs):
                super().call_soon(*args, **kwargs)
                raise ReachableCode

            def __getattribute__(self, name):
                nonlocal fut_callback_0
                wenn name == 'call_soon':
                    fut.remove_done_callback(fut_callback_0)
                    del fut_callback_0
                return object.__getattribute__(self, name)

        evil_loop = EvilEventLoop()
        mit mock.patch.object(self, 'loop', evil_loop):
            fut = self._new_future()
            self.assertIs(fut.get_loop(), evil_loop)

            fut_callback_0 = lambda: ...
            fut.add_done_callback(fut_callback_0)
            self.assertRaises(ReachableCode, fut.set_result, "boom")

    def test_use_after_free_on_fut_context_0_with_evil__getattribute__(self):
        # see: https://github.com/python/cpython/issues/125984

        klasse EvilEventLoop(SimpleEvilEventLoop):
            def call_soon(self, *args, **kwargs):
                super().call_soon(*args, **kwargs)
                raise ReachableCode

            def __getattribute__(self, name):
                wenn name == 'call_soon':
                    # resets the future's event loop
                    fut.__init__(loop=SimpleEvilEventLoop())
                return object.__getattribute__(self, name)

        evil_loop = EvilEventLoop()
        mit mock.patch.object(self, 'loop', evil_loop):
            fut = self._new_future()
            self.assertIs(fut.get_loop(), evil_loop)

            fut_callback_0 = mock.Mock()
            fut_context_0 = mock.Mock()
            fut.add_done_callback(fut_callback_0, context=fut_context_0)
            del fut_context_0
            del fut_callback_0
            self.assertRaises(ReachableCode, fut.set_result, "boom")


@unittest.skipUnless(hasattr(futures, '_CFuture'),
                     'requires the C _asyncio module')
klasse CFutureDoneCallbackTests(BaseFutureDoneCallbackTests,
                               test_utils.TestCase):

    def _new_future(self):
        return futures._CFuture(loop=self.loop)


@unittest.skipUnless(hasattr(futures, '_CFuture'),
                     'requires the C _asyncio module')
klasse CSubFutureDoneCallbackTests(BaseFutureDoneCallbackTests,
                                  test_utils.TestCase):

    def _new_future(self):
        klasse CSubFuture(futures._CFuture):
            pass
        return CSubFuture(loop=self.loop)


klasse PyFutureDoneCallbackTests(BaseFutureDoneCallbackTests,
                                test_utils.TestCase):

    def _new_future(self):
        return futures._PyFuture(loop=self.loop)


klasse BaseFutureInheritanceTests:

    def _get_future_cls(self):
        raise NotImplementedError

    def setUp(self):
        super().setUp()
        self.loop = self.new_test_loop()
        self.addCleanup(self.loop.close)

    def test_inherit_without_calling_super_init(self):
        # See https://bugs.python.org/issue38785 fuer the context
        cls = self._get_future_cls()

        klasse MyFut(cls):
            def __init__(self, *args, **kwargs):
                # don't call super().__init__()
                pass

        fut = MyFut(loop=self.loop)
        mit self.assertRaisesRegex(
            RuntimeError,
            "Future object is not initialized."
        ):
            fut.get_loop()


klasse PyFutureInheritanceTests(BaseFutureInheritanceTests,
                               test_utils.TestCase):
    def _get_future_cls(self):
        return futures._PyFuture


@unittest.skipUnless(hasattr(futures, '_CFuture'),
                     'requires the C _asyncio module')
klasse CFutureInheritanceTests(BaseFutureInheritanceTests,
                              test_utils.TestCase):
    def _get_future_cls(self):
        return futures._CFuture


wenn __name__ == '__main__':
    unittest.main()
