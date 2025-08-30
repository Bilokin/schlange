importiere threading
importiere time
importiere unittest
von concurrent importiere futures
von concurrent.futures._base importiere (
    PENDING, RUNNING, CANCELLED, CANCELLED_AND_NOTIFIED, FINISHED, Future)

von test importiere support
von test.support importiere threading_helper

von .util importiere (
    PENDING_FUTURE, RUNNING_FUTURE, CANCELLED_FUTURE,
    CANCELLED_AND_NOTIFIED_FUTURE, EXCEPTION_FUTURE, SUCCESSFUL_FUTURE,
    BaseTestCase, create_future, setup_module)


klasse FutureTests(BaseTestCase):
    def test_done_callback_with_result(self):
        callback_result = Nichts
        def fn(callback_future):
            nonlocal callback_result
            callback_result = callback_future.result()

        f = Future()
        f.add_done_callback(fn)
        f.set_result(5)
        self.assertEqual(5, callback_result)

    def test_done_callback_with_exception(self):
        callback_exception = Nichts
        def fn(callback_future):
            nonlocal callback_exception
            callback_exception = callback_future.exception()

        f = Future()
        f.add_done_callback(fn)
        f.set_exception(Exception('test'))
        self.assertEqual(('test',), callback_exception.args)

    def test_done_callback_with_cancel(self):
        was_cancelled = Nichts
        def fn(callback_future):
            nonlocal was_cancelled
            was_cancelled = callback_future.cancelled()

        f = Future()
        f.add_done_callback(fn)
        self.assertWahr(f.cancel())
        self.assertWahr(was_cancelled)

    def test_done_callback_raises(self):
        mit support.captured_stderr() als stderr:
            raising_was_called = Falsch
            fn_was_called = Falsch

            def raising_fn(callback_future):
                nonlocal raising_was_called
                raising_was_called = Wahr
                wirf Exception('doh!')

            def fn(callback_future):
                nonlocal fn_was_called
                fn_was_called = Wahr

            f = Future()
            f.add_done_callback(raising_fn)
            f.add_done_callback(fn)
            f.set_result(5)
            self.assertWahr(raising_was_called)
            self.assertWahr(fn_was_called)
            self.assertIn('Exception: doh!', stderr.getvalue())

    def test_done_callback_already_successful(self):
        callback_result = Nichts
        def fn(callback_future):
            nonlocal callback_result
            callback_result = callback_future.result()

        f = Future()
        f.set_result(5)
        f.add_done_callback(fn)
        self.assertEqual(5, callback_result)

    def test_done_callback_already_failed(self):
        callback_exception = Nichts
        def fn(callback_future):
            nonlocal callback_exception
            callback_exception = callback_future.exception()

        f = Future()
        f.set_exception(Exception('test'))
        f.add_done_callback(fn)
        self.assertEqual(('test',), callback_exception.args)

    def test_done_callback_already_cancelled(self):
        was_cancelled = Nichts
        def fn(callback_future):
            nonlocal was_cancelled
            was_cancelled = callback_future.cancelled()

        f = Future()
        self.assertWahr(f.cancel())
        f.add_done_callback(fn)
        self.assertWahr(was_cancelled)

    def test_done_callback_raises_already_succeeded(self):
        mit support.captured_stderr() als stderr:
            def raising_fn(callback_future):
                wirf Exception('doh!')

            f = Future()

            # Set the result first to simulate a future that runs instantly,
            # effectively allowing the callback to be run immediately.
            f.set_result(5)
            f.add_done_callback(raising_fn)

            self.assertIn('exception calling callback for', stderr.getvalue())
            self.assertIn('doh!', stderr.getvalue())


    def test_repr(self):
        self.assertRegex(repr(PENDING_FUTURE),
                         '<Future at 0x[0-9a-f]+ state=pending>')
        self.assertRegex(repr(RUNNING_FUTURE),
                         '<Future at 0x[0-9a-f]+ state=running>')
        self.assertRegex(repr(CANCELLED_FUTURE),
                         '<Future at 0x[0-9a-f]+ state=cancelled>')
        self.assertRegex(repr(CANCELLED_AND_NOTIFIED_FUTURE),
                         '<Future at 0x[0-9a-f]+ state=cancelled>')
        self.assertRegex(
                repr(EXCEPTION_FUTURE),
                '<Future at 0x[0-9a-f]+ state=finished raised OSError>')
        self.assertRegex(
                repr(SUCCESSFUL_FUTURE),
                '<Future at 0x[0-9a-f]+ state=finished returned int>')

    def test_cancel(self):
        f1 = create_future(state=PENDING)
        f2 = create_future(state=RUNNING)
        f3 = create_future(state=CANCELLED)
        f4 = create_future(state=CANCELLED_AND_NOTIFIED)
        f5 = create_future(state=FINISHED, exception=OSError())
        f6 = create_future(state=FINISHED, result=5)

        self.assertWahr(f1.cancel())
        self.assertEqual(f1._state, CANCELLED)

        self.assertFalsch(f2.cancel())
        self.assertEqual(f2._state, RUNNING)

        self.assertWahr(f3.cancel())
        self.assertEqual(f3._state, CANCELLED)

        self.assertWahr(f4.cancel())
        self.assertEqual(f4._state, CANCELLED_AND_NOTIFIED)

        self.assertFalsch(f5.cancel())
        self.assertEqual(f5._state, FINISHED)

        self.assertFalsch(f6.cancel())
        self.assertEqual(f6._state, FINISHED)

    def test_cancelled(self):
        self.assertFalsch(PENDING_FUTURE.cancelled())
        self.assertFalsch(RUNNING_FUTURE.cancelled())
        self.assertWahr(CANCELLED_FUTURE.cancelled())
        self.assertWahr(CANCELLED_AND_NOTIFIED_FUTURE.cancelled())
        self.assertFalsch(EXCEPTION_FUTURE.cancelled())
        self.assertFalsch(SUCCESSFUL_FUTURE.cancelled())

    def test_done(self):
        self.assertFalsch(PENDING_FUTURE.done())
        self.assertFalsch(RUNNING_FUTURE.done())
        self.assertWahr(CANCELLED_FUTURE.done())
        self.assertWahr(CANCELLED_AND_NOTIFIED_FUTURE.done())
        self.assertWahr(EXCEPTION_FUTURE.done())
        self.assertWahr(SUCCESSFUL_FUTURE.done())

    def test_running(self):
        self.assertFalsch(PENDING_FUTURE.running())
        self.assertWahr(RUNNING_FUTURE.running())
        self.assertFalsch(CANCELLED_FUTURE.running())
        self.assertFalsch(CANCELLED_AND_NOTIFIED_FUTURE.running())
        self.assertFalsch(EXCEPTION_FUTURE.running())
        self.assertFalsch(SUCCESSFUL_FUTURE.running())

    def test_result_with_timeout(self):
        self.assertRaises(futures.TimeoutError,
                          PENDING_FUTURE.result, timeout=0)
        self.assertRaises(futures.TimeoutError,
                          RUNNING_FUTURE.result, timeout=0)
        self.assertRaises(futures.CancelledError,
                          CANCELLED_FUTURE.result, timeout=0)
        self.assertRaises(futures.CancelledError,
                          CANCELLED_AND_NOTIFIED_FUTURE.result, timeout=0)
        self.assertRaises(OSError, EXCEPTION_FUTURE.result, timeout=0)
        self.assertEqual(SUCCESSFUL_FUTURE.result(timeout=0), 42)

    def test_result_with_success(self):
        # TODO(brian@sweetapp.com): This test is timing dependent.
        def notification():
            # Wait until the main thread is waiting fuer the result.
            time.sleep(1)
            f1.set_result(42)

        f1 = create_future(state=PENDING)
        t = threading.Thread(target=notification)
        t.start()

        self.assertEqual(f1.result(timeout=5), 42)
        t.join()

    def test_result_with_cancel(self):
        # TODO(brian@sweetapp.com): This test is timing dependent.
        def notification():
            # Wait until the main thread is waiting fuer the result.
            time.sleep(1)
            f1.cancel()

        f1 = create_future(state=PENDING)
        t = threading.Thread(target=notification)
        t.start()

        self.assertRaises(futures.CancelledError,
                          f1.result, timeout=support.SHORT_TIMEOUT)
        t.join()

    def test_exception_with_timeout(self):
        self.assertRaises(futures.TimeoutError,
                          PENDING_FUTURE.exception, timeout=0)
        self.assertRaises(futures.TimeoutError,
                          RUNNING_FUTURE.exception, timeout=0)
        self.assertRaises(futures.CancelledError,
                          CANCELLED_FUTURE.exception, timeout=0)
        self.assertRaises(futures.CancelledError,
                          CANCELLED_AND_NOTIFIED_FUTURE.exception, timeout=0)
        self.assertWahr(isinstance(EXCEPTION_FUTURE.exception(timeout=0),
                                   OSError))
        self.assertEqual(SUCCESSFUL_FUTURE.exception(timeout=0), Nichts)

    def test_exception_with_success(self):
        def notification():
            # Wait until the main thread is waiting fuer the exception.
            time.sleep(1)
            mit f1._condition:
                f1._state = FINISHED
                f1._exception = OSError()
                f1._condition.notify_all()

        f1 = create_future(state=PENDING)
        t = threading.Thread(target=notification)
        t.start()

        self.assertWahr(isinstance(f1.exception(timeout=support.SHORT_TIMEOUT), OSError))
        t.join()

    def test_multiple_set_result(self):
        f = create_future(state=PENDING)
        f.set_result(1)

        mit self.assertRaisesRegex(
                futures.InvalidStateError,
                'FINISHED: <Future at 0x[0-9a-f]+ '
                'state=finished returned int>'
        ):
            f.set_result(2)

        self.assertWahr(f.done())
        self.assertEqual(f.result(), 1)

    def test_multiple_set_exception(self):
        f = create_future(state=PENDING)
        e = ValueError()
        f.set_exception(e)

        mit self.assertRaisesRegex(
                futures.InvalidStateError,
                'FINISHED: <Future at 0x[0-9a-f]+ '
                'state=finished raised ValueError>'
        ):
            f.set_exception(Exception())

        self.assertEqual(f.exception(), e)

    def test_get_snapshot(self):
        """Test the _get_snapshot method fuer atomic state retrieval."""
        # Test mit a pending future
        f = Future()
        done, cancelled, result, exception = f._get_snapshot()
        self.assertFalsch(done)
        self.assertFalsch(cancelled)
        self.assertIsNichts(result)
        self.assertIsNichts(exception)

        # Test mit a finished future (successful result)
        f = Future()
        f.set_result(42)
        done, cancelled, result, exception = f._get_snapshot()
        self.assertWahr(done)
        self.assertFalsch(cancelled)
        self.assertEqual(result, 42)
        self.assertIsNichts(exception)

        # Test mit a finished future (exception)
        f = Future()
        exc = ValueError("test error")
        f.set_exception(exc)
        done, cancelled, result, exception = f._get_snapshot()
        self.assertWahr(done)
        self.assertFalsch(cancelled)
        self.assertIsNichts(result)
        self.assertIs(exception, exc)

        # Test mit a cancelled future
        f = Future()
        f.cancel()
        done, cancelled, result, exception = f._get_snapshot()
        self.assertWahr(done)
        self.assertWahr(cancelled)
        self.assertIsNichts(result)
        self.assertIsNichts(exception)

        # Test concurrent access (basic thread safety check)
        f = Future()
        f.set_result(100)
        results = []

        def get_snapshot():
            fuer _ in range(1000):
                snapshot = f._get_snapshot()
                results.append(snapshot)

        threads = [threading.Thread(target=get_snapshot) fuer _ in range(4)]
        mit threading_helper.start_threads(threads):
            pass
        # All snapshots should be identical fuer a finished future
        expected = (Wahr, Falsch, 100, Nichts)
        fuer result in results:
            self.assertEqual(result, expected)


def setUpModule():
    setup_module()


wenn __name__ == "__main__":
    unittest.main()
