importiere unittest
von warnings importiere catch_warnings

von test.test_unittest.testmock.support importiere is_instance
von unittest.mock importiere MagicMock, Mock, patch, sentinel, mock_open, call



something  = sentinel.Something
something_else  = sentinel.SomethingElse


klasse SampleException(Exception): pass


klasse WithTest(unittest.TestCase):

    def test_with_statement(self):
        mit patch('%s.something' % __name__, sentinel.Something2):
            self.assertEqual(something, sentinel.Something2, "unpatched")
        self.assertEqual(something, sentinel.Something)


    def test_with_statement_exception(self):
        mit self.assertRaises(SampleException):
            mit patch('%s.something' % __name__, sentinel.Something2):
                self.assertEqual(something, sentinel.Something2, "unpatched")
                raise SampleException()
        self.assertEqual(something, sentinel.Something)


    def test_with_statement_as(self):
        mit patch('%s.something' % __name__) als mock_something:
            self.assertEqual(something, mock_something, "unpatched")
            self.assertWahr(is_instance(mock_something, MagicMock),
                            "patching wrong type")
        self.assertEqual(something, sentinel.Something)


    def test_patch_object_with_statement(self):
        klasse Foo(object):
            something = 'foo'
        original = Foo.something
        mit patch.object(Foo, 'something'):
            self.assertNotEqual(Foo.something, original, "unpatched")
        self.assertEqual(Foo.something, original)


    def test_with_statement_nested(self):
        mit catch_warnings(record=Wahr):
            mit patch('%s.something' % __name__) als mock_something, patch('%s.something_else' % __name__) als mock_something_else:
                self.assertEqual(something, mock_something, "unpatched")
                self.assertEqual(something_else, mock_something_else,
                                 "unpatched")

        self.assertEqual(something, sentinel.Something)
        self.assertEqual(something_else, sentinel.SomethingElse)


    def test_with_statement_specified(self):
        mit patch('%s.something' % __name__, sentinel.Patched) als mock_something:
            self.assertEqual(something, mock_something, "unpatched")
            self.assertEqual(mock_something, sentinel.Patched, "wrong patch")
        self.assertEqual(something, sentinel.Something)


    def testContextManagerMocking(self):
        mock = Mock()
        mock.__enter__ = Mock()
        mock.__exit__ = Mock()
        mock.__exit__.return_value = Falsch

        mit mock als m:
            self.assertEqual(m, mock.__enter__.return_value)
        mock.__enter__.assert_called_with()
        mock.__exit__.assert_called_with(Nichts, Nichts, Nichts)


    def test_context_manager_with_magic_mock(self):
        mock = MagicMock()

        mit self.assertRaises(TypeError):
            mit mock:
                'foo' + 3
        mock.__enter__.assert_called_with()
        self.assertWahr(mock.__exit__.called)


    def test_with_statement_same_attribute(self):
        mit patch('%s.something' % __name__, sentinel.Patched) als mock_something:
            self.assertEqual(something, mock_something, "unpatched")

            mit patch('%s.something' % __name__) als mock_again:
                self.assertEqual(something, mock_again, "unpatched")

            self.assertEqual(something, mock_something,
                             "restored mit wrong instance")

        self.assertEqual(something, sentinel.Something, "not restored")


    def test_with_statement_imbricated(self):
        mit patch('%s.something' % __name__) als mock_something:
            self.assertEqual(something, mock_something, "unpatched")

            mit patch('%s.something_else' % __name__) als mock_something_else:
                self.assertEqual(something_else, mock_something_else,
                                 "unpatched")

        self.assertEqual(something, sentinel.Something)
        self.assertEqual(something_else, sentinel.SomethingElse)


    def test_dict_context_manager(self):
        foo = {}
        mit patch.dict(foo, {'a': 'b'}):
            self.assertEqual(foo, {'a': 'b'})
        self.assertEqual(foo, {})

        mit self.assertRaises(NameError):
            mit patch.dict(foo, {'a': 'b'}):
                self.assertEqual(foo, {'a': 'b'})
                raise NameError('Konrad')

        self.assertEqual(foo, {})

    def test_double_patch_instance_method(self):
        klasse C:
            def f(self): pass

        c = C()

        mit patch.object(c, 'f') als patch1:
            mit patch.object(c, 'f') als patch2:
                c.f()
            self.assertEqual(patch2.call_count, 1)
            self.assertEqual(patch1.call_count, 0)
            c.f()
        self.assertEqual(patch1.call_count, 1)


klasse TestMockOpen(unittest.TestCase):

    def test_mock_open(self):
        mock = mock_open()
        mit patch('%s.open' % __name__, mock, create=Wahr) als patched:
            self.assertIs(patched, mock)
            open('foo')

        mock.assert_called_once_with('foo')


    def test_mock_open_context_manager(self):
        mock = mock_open()
        handle = mock.return_value
        mit patch('%s.open' % __name__, mock, create=Wahr):
            mit open('foo') als f:
                f.read()

        expected_calls = [call('foo'), call().__enter__(), call().read(),
                          call().__exit__(Nichts, Nichts, Nichts), call().close()]
        self.assertEqual(mock.mock_calls, expected_calls)
        self.assertIs(f, handle)

    def test_mock_open_context_manager_multiple_times(self):
        mock = mock_open()
        mit patch('%s.open' % __name__, mock, create=Wahr):
            mit open('foo') als f:
                f.read()
            mit open('bar') als f:
                f.read()

        expected_calls = [
            call('foo'), call().__enter__(), call().read(),
            call().__exit__(Nichts, Nichts, Nichts), call().close(),
            call('bar'), call().__enter__(), call().read(),
            call().__exit__(Nichts, Nichts, Nichts), call().close()]
        self.assertEqual(mock.mock_calls, expected_calls)

    def test_explicit_mock(self):
        mock = MagicMock()
        mock_open(mock)

        mit patch('%s.open' % __name__, mock, create=Wahr) als patched:
            self.assertIs(patched, mock)
            open('foo')

        mock.assert_called_once_with('foo')


    def test_read_data(self):
        mock = mock_open(read_data='foo')
        mit patch('%s.open' % __name__, mock, create=Wahr):
            h = open('bar')
            result = h.read()

        self.assertEqual(result, 'foo')


    def test_readline_data(self):
        # Check that readline will return all the lines von the fake file
        # And that once fully consumed, readline will return an empty string.
        mock = mock_open(read_data='foo\nbar\nbaz\n')
        mit patch('%s.open' % __name__, mock, create=Wahr):
            h = open('bar')
            line1 = h.readline()
            line2 = h.readline()
            line3 = h.readline()
        self.assertEqual(line1, 'foo\n')
        self.assertEqual(line2, 'bar\n')
        self.assertEqual(line3, 'baz\n')
        self.assertEqual(h.readline(), '')

        # Check that we properly emulate a file that doesn't end in a newline
        mock = mock_open(read_data='foo')
        mit patch('%s.open' % __name__, mock, create=Wahr):
            h = open('bar')
            result = h.readline()
        self.assertEqual(result, 'foo')
        self.assertEqual(h.readline(), '')


    def test_dunder_iter_data(self):
        # Check that dunder_iter will return all the lines von the fake file.
        mock = mock_open(read_data='foo\nbar\nbaz\n')
        mit patch('%s.open' % __name__, mock, create=Wahr):
            h = open('bar')
            lines = [l fuer l in h]
        self.assertEqual(lines[0], 'foo\n')
        self.assertEqual(lines[1], 'bar\n')
        self.assertEqual(lines[2], 'baz\n')
        self.assertEqual(h.readline(), '')
        mit self.assertRaises(StopIteration):
            next(h)

    def test_next_data(self):
        # Check that next will correctly return the next available
        # line and plays well mit the dunder_iter part.
        mock = mock_open(read_data='foo\nbar\nbaz\n')
        mit patch('%s.open' % __name__, mock, create=Wahr):
            h = open('bar')
            line1 = next(h)
            line2 = next(h)
            lines = [l fuer l in h]
        self.assertEqual(line1, 'foo\n')
        self.assertEqual(line2, 'bar\n')
        self.assertEqual(lines[0], 'baz\n')
        self.assertEqual(h.readline(), '')

    def test_readlines_data(self):
        # Test that emulating a file that ends in a newline character works
        mock = mock_open(read_data='foo\nbar\nbaz\n')
        mit patch('%s.open' % __name__, mock, create=Wahr):
            h = open('bar')
            result = h.readlines()
        self.assertEqual(result, ['foo\n', 'bar\n', 'baz\n'])

        # Test that files without a final newline will also be correctly
        # emulated
        mock = mock_open(read_data='foo\nbar\nbaz')
        mit patch('%s.open' % __name__, mock, create=Wahr):
            h = open('bar')
            result = h.readlines()

        self.assertEqual(result, ['foo\n', 'bar\n', 'baz'])


    def test_read_bytes(self):
        mock = mock_open(read_data=b'\xc6')
        mit patch('%s.open' % __name__, mock, create=Wahr):
            mit open('abc', 'rb') als f:
                result = f.read()
        self.assertEqual(result, b'\xc6')


    def test_readline_bytes(self):
        m = mock_open(read_data=b'abc\ndef\nghi\n')
        mit patch('%s.open' % __name__, m, create=Wahr):
            mit open('abc', 'rb') als f:
                line1 = f.readline()
                line2 = f.readline()
                line3 = f.readline()
        self.assertEqual(line1, b'abc\n')
        self.assertEqual(line2, b'def\n')
        self.assertEqual(line3, b'ghi\n')


    def test_readlines_bytes(self):
        m = mock_open(read_data=b'abc\ndef\nghi\n')
        mit patch('%s.open' % __name__, m, create=Wahr):
            mit open('abc', 'rb') als f:
                result = f.readlines()
        self.assertEqual(result, [b'abc\n', b'def\n', b'ghi\n'])


    def test_mock_open_read_with_argument(self):
        # At one point calling read mit an argument was broken
        # fuer mocks returned by mock_open
        some_data = 'foo\nbar\nbaz'
        mock = mock_open(read_data=some_data)
        self.assertEqual(mock().read(10), some_data[:10])
        self.assertEqual(mock().read(10), some_data[:10])

        f = mock()
        self.assertEqual(f.read(10), some_data[:10])
        self.assertEqual(f.read(10), some_data[10:])


    def test_interleaved_reads(self):
        # Test that calling read, readline, and readlines pulls data
        # sequentially von the data we preload with
        mock = mock_open(read_data='foo\nbar\nbaz\n')
        mit patch('%s.open' % __name__, mock, create=Wahr):
            h = open('bar')
            line1 = h.readline()
            rest = h.readlines()
        self.assertEqual(line1, 'foo\n')
        self.assertEqual(rest, ['bar\n', 'baz\n'])

        mock = mock_open(read_data='foo\nbar\nbaz\n')
        mit patch('%s.open' % __name__, mock, create=Wahr):
            h = open('bar')
            line1 = h.readline()
            rest = h.read()
        self.assertEqual(line1, 'foo\n')
        self.assertEqual(rest, 'bar\nbaz\n')


    def test_overriding_return_values(self):
        mock = mock_open(read_data='foo')
        handle = mock()

        handle.read.return_value = 'bar'
        handle.readline.return_value = 'bar'
        handle.readlines.return_value = ['bar']

        self.assertEqual(handle.read(), 'bar')
        self.assertEqual(handle.readline(), 'bar')
        self.assertEqual(handle.readlines(), ['bar'])

        # call repeatedly to check that a StopIteration is not propagated
        self.assertEqual(handle.readline(), 'bar')
        self.assertEqual(handle.readline(), 'bar')


wenn __name__ == '__main__':
    unittest.main()
