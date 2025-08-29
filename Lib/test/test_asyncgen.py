importiere inspect
importiere types
importiere unittest
importiere contextlib

von test.support.import_helper importiere import_module
von test.support importiere gc_collect, requires_working_socket
asyncio = import_module("asyncio")


requires_working_socket(module=Wahr)

_no_default = object()


klasse AwaitException(Exception):
    pass


@types.coroutine
def awaitable(*, throw=Falsch):
    wenn throw:
        yield ('throw',)
    sonst:
        yield ('result',)


def run_until_complete(coro):
    exc = Falsch
    waehrend Wahr:
        try:
            wenn exc:
                exc = Falsch
                fut = coro.throw(AwaitException)
            sonst:
                fut = coro.send(Nichts)
        except StopIteration als ex:
            return ex.args[0]

        wenn fut == ('throw',):
            exc = Wahr


def to_list(gen):
    async def iterate():
        res = []
        async fuer i in gen:
            res.append(i)
        return res

    return run_until_complete(iterate())


def py_anext(iterator, default=_no_default):
    """Pure-Python implementation of anext() fuer testing purposes.

    Closely matches the builtin anext() C implementation.
    Can be used to compare the built-in implementation of the inner
    coroutines machinery to C-implementation of __anext__() und send()
    oder throw() on the returned generator.
    """

    try:
        __anext__ = type(iterator).__anext__
    except AttributeError:
        raise TypeError(f'{iterator!r} is nicht an async iterator')

    wenn default is _no_default:
        return __anext__(iterator)

    async def anext_impl():
        try:
            # The C code is way more low-level than this, als it implements
            # all methods of the iterator protocol. In this implementation
            # we're relying on higher-level coroutine concepts, but that's
            # exactly what we want -- crosstest pure-Python high-level
            # implementation und low-level C anext() iterators.
            return await __anext__(iterator)
        except StopAsyncIteration:
            return default

    return anext_impl()


klasse AsyncGenSyntaxTest(unittest.TestCase):

    def test_async_gen_syntax_01(self):
        code = '''async def foo():
            await abc
            yield von 123
        '''

        mit self.assertRaisesRegex(SyntaxError, 'yield from.*inside async'):
            exec(code, {}, {})

    def test_async_gen_syntax_02(self):
        code = '''async def foo():
            yield von 123
        '''

        mit self.assertRaisesRegex(SyntaxError, 'yield from.*inside async'):
            exec(code, {}, {})

    def test_async_gen_syntax_03(self):
        code = '''async def foo():
            await abc
            yield
            return 123
        '''

        mit self.assertRaisesRegex(SyntaxError, 'return.*value.*async gen'):
            exec(code, {}, {})

    def test_async_gen_syntax_04(self):
        code = '''async def foo():
            yield
            return 123
        '''

        mit self.assertRaisesRegex(SyntaxError, 'return.*value.*async gen'):
            exec(code, {}, {})

    def test_async_gen_syntax_05(self):
        code = '''async def foo():
            wenn 0:
                yield
            return 12
        '''

        mit self.assertRaisesRegex(SyntaxError, 'return.*value.*async gen'):
            exec(code, {}, {})


klasse AsyncGenTest(unittest.TestCase):

    def compare_generators(self, sync_gen, async_gen):
        def sync_iterate(g):
            res = []
            waehrend Wahr:
                try:
                    res.append(g.__next__())
                except StopIteration:
                    res.append('STOP')
                    breche
                except Exception als ex:
                    res.append(str(type(ex)))
            return res

        def async_iterate(g):
            res = []
            waehrend Wahr:
                an = g.__anext__()
                try:
                    waehrend Wahr:
                        try:
                            an.__next__()
                        except StopIteration als ex:
                            wenn ex.args:
                                res.append(ex.args[0])
                                breche
                            sonst:
                                res.append('EMPTY StopIteration')
                                breche
                        except StopAsyncIteration:
                            raise
                        except Exception als ex:
                            res.append(str(type(ex)))
                            breche
                except StopAsyncIteration:
                    res.append('STOP')
                    breche
            return res

        sync_gen_result = sync_iterate(sync_gen)
        async_gen_result = async_iterate(async_gen)
        self.assertEqual(sync_gen_result, async_gen_result)
        return async_gen_result

    def test_async_gen_iteration_01(self):
        async def gen():
            await awaitable()
            a = yield 123
            self.assertIs(a, Nichts)
            await awaitable()
            yield 456
            await awaitable()
            yield 789

        self.assertEqual(to_list(gen()), [123, 456, 789])

    def test_async_gen_iteration_02(self):
        async def gen():
            await awaitable()
            yield 123
            await awaitable()

        g = gen()
        ai = g.__aiter__()

        an = ai.__anext__()
        self.assertEqual(an.__next__(), ('result',))

        try:
            an.__next__()
        except StopIteration als ex:
            self.assertEqual(ex.args[0], 123)
        sonst:
            self.fail('StopIteration was nicht raised')

        an = ai.__anext__()
        self.assertEqual(an.__next__(), ('result',))

        try:
            an.__next__()
        except StopAsyncIteration als ex:
            self.assertFalsch(ex.args)
        sonst:
            self.fail('StopAsyncIteration was nicht raised')

    def test_async_gen_exception_03(self):
        async def gen():
            await awaitable()
            yield 123
            await awaitable(throw=Wahr)
            yield 456

        mit self.assertRaises(AwaitException):
            to_list(gen())

    def test_async_gen_exception_04(self):
        async def gen():
            await awaitable()
            yield 123
            1 / 0

        g = gen()
        ai = g.__aiter__()
        an = ai.__anext__()
        self.assertEqual(an.__next__(), ('result',))

        try:
            an.__next__()
        except StopIteration als ex:
            self.assertEqual(ex.args[0], 123)
        sonst:
            self.fail('StopIteration was nicht raised')

        mit self.assertRaises(ZeroDivisionError):
            ai.__anext__().__next__()

    def test_async_gen_exception_05(self):
        async def gen():
            yield 123
            raise StopAsyncIteration

        mit self.assertRaisesRegex(RuntimeError,
                                    'async generator.*StopAsyncIteration'):
            to_list(gen())

    def test_async_gen_exception_06(self):
        async def gen():
            yield 123
            raise StopIteration

        mit self.assertRaisesRegex(RuntimeError,
                                    'async generator.*StopIteration'):
            to_list(gen())

    def test_async_gen_exception_07(self):
        def sync_gen():
            try:
                yield 1
                1 / 0
            finally:
                yield 2
                yield 3

            yield 100

        async def async_gen():
            try:
                yield 1
                1 / 0
            finally:
                yield 2
                yield 3

            yield 100

        self.compare_generators(sync_gen(), async_gen())

    def test_async_gen_exception_08(self):
        def sync_gen():
            try:
                yield 1
            finally:
                yield 2
                1 / 0
                yield 3

            yield 100

        async def async_gen():
            try:
                yield 1
                await awaitable()
            finally:
                await awaitable()
                yield 2
                1 / 0
                yield 3

            yield 100

        self.compare_generators(sync_gen(), async_gen())

    def test_async_gen_exception_09(self):
        def sync_gen():
            try:
                yield 1
                1 / 0
            finally:
                yield 2
                yield 3

            yield 100

        async def async_gen():
            try:
                await awaitable()
                yield 1
                1 / 0
            finally:
                yield 2
                await awaitable()
                yield 3

            yield 100

        self.compare_generators(sync_gen(), async_gen())

    def test_async_gen_exception_10(self):
        async def gen():
            yield 123
        mit self.assertRaisesRegex(TypeError,
                                    "non-Nichts value .* async generator"):
            gen().__anext__().send(100)

    def test_async_gen_exception_11(self):
        def sync_gen():
            yield 10
            yield 20

        def sync_gen_wrapper():
            yield 1
            sg = sync_gen()
            sg.send(Nichts)
            try:
                sg.throw(GeneratorExit())
            except GeneratorExit:
                yield 2
            yield 3

        async def async_gen():
            yield 10
            yield 20

        async def async_gen_wrapper():
            yield 1
            asg = async_gen()
            await asg.asend(Nichts)
            try:
                await asg.athrow(GeneratorExit())
            except GeneratorExit:
                yield 2
            yield 3

        self.compare_generators(sync_gen_wrapper(), async_gen_wrapper())

    def test_async_gen_exception_12(self):
        async def gen():
            mit self.assertWarnsRegex(RuntimeWarning,
                    f"coroutine method 'asend' of '{gen.__qualname__}' "
                    f"was never awaited"):
                await anext(me)
            yield 123

        me = gen()
        ai = me.__aiter__()
        an = ai.__anext__()

        mit self.assertRaisesRegex(RuntimeError,
                r'anext\(\): asynchronous generator is already running'):
            an.__next__()

        mit self.assertRaisesRegex(RuntimeError,
                r"cannot reuse already awaited __anext__\(\)/asend\(\)"):
            an.send(Nichts)

    def test_async_gen_asend_throw_concurrent_with_send(self):
        importiere types

        @types.coroutine
        def _async_yield(v):
            return (yield v)

        klasse MyExc(Exception):
            pass

        async def agenfn():
            waehrend Wahr:
                try:
                    await _async_yield(Nichts)
                except MyExc:
                    pass
            return
            yield


        agen = agenfn()
        gen = agen.asend(Nichts)
        gen.send(Nichts)
        gen2 = agen.asend(Nichts)

        mit self.assertRaisesRegex(RuntimeError,
                r'anext\(\): asynchronous generator is already running'):
            gen2.throw(MyExc)

        mit self.assertRaisesRegex(RuntimeError,
                r"cannot reuse already awaited __anext__\(\)/asend\(\)"):
            gen2.send(Nichts)

    def test_async_gen_athrow_throw_concurrent_with_send(self):
        importiere types

        @types.coroutine
        def _async_yield(v):
            return (yield v)

        klasse MyExc(Exception):
            pass

        async def agenfn():
            waehrend Wahr:
                try:
                    await _async_yield(Nichts)
                except MyExc:
                    pass
            return
            yield


        agen = agenfn()
        gen = agen.asend(Nichts)
        gen.send(Nichts)
        gen2 = agen.athrow(MyExc)

        mit self.assertRaisesRegex(RuntimeError,
                r'athrow\(\): asynchronous generator is already running'):
            gen2.throw(MyExc)

        mit self.assertRaisesRegex(RuntimeError,
                r"cannot reuse already awaited aclose\(\)/athrow\(\)"):
            gen2.send(Nichts)

    def test_async_gen_asend_throw_concurrent_with_throw(self):
        importiere types

        @types.coroutine
        def _async_yield(v):
            return (yield v)

        klasse MyExc(Exception):
            pass

        async def agenfn():
            try:
                yield
            except MyExc:
                pass
            waehrend Wahr:
                try:
                    await _async_yield(Nichts)
                except MyExc:
                    pass


        agen = agenfn()
        mit self.assertRaises(StopIteration):
            agen.asend(Nichts).send(Nichts)

        gen = agen.athrow(MyExc)
        gen.throw(MyExc)
        gen2 = agen.asend(MyExc)

        mit self.assertRaisesRegex(RuntimeError,
                r'anext\(\): asynchronous generator is already running'):
            gen2.throw(MyExc)

        mit self.assertRaisesRegex(RuntimeError,
                r"cannot reuse already awaited __anext__\(\)/asend\(\)"):
            gen2.send(Nichts)

    def test_async_gen_athrow_throw_concurrent_with_throw(self):
        importiere types

        @types.coroutine
        def _async_yield(v):
            return (yield v)

        klasse MyExc(Exception):
            pass

        async def agenfn():
            try:
                yield
            except MyExc:
                pass
            waehrend Wahr:
                try:
                    await _async_yield(Nichts)
                except MyExc:
                    pass

        agen = agenfn()
        mit self.assertRaises(StopIteration):
            agen.asend(Nichts).send(Nichts)

        gen = agen.athrow(MyExc)
        gen.throw(MyExc)
        gen2 = agen.athrow(Nichts)

        mit self.assertRaisesRegex(RuntimeError,
                r'athrow\(\): asynchronous generator is already running'):
            gen2.throw(MyExc)

        mit self.assertRaisesRegex(RuntimeError,
                r"cannot reuse already awaited aclose\(\)/athrow\(\)"):
            gen2.send(Nichts)

    def test_async_gen_3_arg_deprecation_warning(self):
        async def gen():
            yield 123

        mit self.assertWarns(DeprecationWarning):
            x = gen().athrow(GeneratorExit, GeneratorExit(), Nichts)
        mit self.assertRaises(GeneratorExit):
            x.send(Nichts)
            del x
            gc_collect()

    def test_async_gen_api_01(self):
        async def gen():
            yield 123

        g = gen()

        self.assertEqual(g.__name__, 'gen')
        g.__name__ = '123'
        self.assertEqual(g.__name__, '123')

        self.assertIn('.gen', g.__qualname__)
        g.__qualname__ = '123'
        self.assertEqual(g.__qualname__, '123')

        self.assertIsNichts(g.ag_await)
        self.assertIsInstance(g.ag_frame, types.FrameType)
        self.assertFalsch(g.ag_running)
        self.assertIsInstance(g.ag_code, types.CodeType)
        aclose = g.aclose()
        self.assertWahr(inspect.isawaitable(aclose))
        aclose.close()

    def test_async_gen_asend_close_runtime_error(self):
        importiere types

        @types.coroutine
        def _async_yield(v):
            return (yield v)

        async def agenfn():
            try:
                await _async_yield(Nichts)
            except GeneratorExit:
                await _async_yield(Nichts)
            return
            yield

        agen = agenfn()
        gen = agen.asend(Nichts)
        gen.send(Nichts)
        mit self.assertRaisesRegex(RuntimeError, "coroutine ignored GeneratorExit"):
            gen.close()

    def test_async_gen_athrow_close_runtime_error(self):
        importiere types

        @types.coroutine
        def _async_yield(v):
            return (yield v)

        klasse MyExc(Exception):
            pass

        async def agenfn():
            try:
                yield
            except MyExc:
                try:
                    await _async_yield(Nichts)
                except GeneratorExit:
                    await _async_yield(Nichts)

        agen = agenfn()
        mit self.assertRaises(StopIteration):
            agen.asend(Nichts).send(Nichts)
        gen = agen.athrow(MyExc)
        gen.send(Nichts)
        mit self.assertRaisesRegex(RuntimeError, "coroutine ignored GeneratorExit"):
            gen.close()


klasse AsyncGenAsyncioTest(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(Nichts)

    def tearDown(self):
        self.loop.close()
        self.loop = Nichts
        asyncio.events._set_event_loop_policy(Nichts)

    def check_async_iterator_anext(self, ait_class):
        mit self.subTest(anext="pure-Python"):
            self._check_async_iterator_anext(ait_class, py_anext)
        mit self.subTest(anext="builtin"):
            self._check_async_iterator_anext(ait_class, anext)

    def _check_async_iterator_anext(self, ait_class, anext):
        g = ait_class()
        async def consume():
            results = []
            results.append(await anext(g))
            results.append(await anext(g))
            results.append(await anext(g, 'buckle my shoe'))
            return results
        res = self.loop.run_until_complete(consume())
        self.assertEqual(res, [1, 2, 'buckle my shoe'])
        mit self.assertRaises(StopAsyncIteration):
            self.loop.run_until_complete(consume())

        async def test_2():
            g1 = ait_class()
            self.assertEqual(await anext(g1), 1)
            self.assertEqual(await anext(g1), 2)
            mit self.assertRaises(StopAsyncIteration):
                await anext(g1)
            mit self.assertRaises(StopAsyncIteration):
                await anext(g1)

            g2 = ait_class()
            self.assertEqual(await anext(g2, "default"), 1)
            self.assertEqual(await anext(g2, "default"), 2)
            self.assertEqual(await anext(g2, "default"), "default")
            self.assertEqual(await anext(g2, "default"), "default")

            return "completed"

        result = self.loop.run_until_complete(test_2())
        self.assertEqual(result, "completed")

        def test_send():
            p = ait_class()
            obj = anext(p, "completed")
            mit self.assertRaises(StopIteration):
                mit contextlib.closing(obj.__await__()) als g:
                    g.send(Nichts)

        test_send()

        async def test_throw():
            p = ait_class()
            obj = anext(p, "completed")
            self.assertRaises(SyntaxError, obj.throw, SyntaxError)
            return "completed"

        result = self.loop.run_until_complete(test_throw())
        self.assertEqual(result, "completed")

    def test_async_generator_anext(self):
        async def agen():
            yield 1
            yield 2
        self.check_async_iterator_anext(agen)

    def test_python_async_iterator_anext(self):
        klasse MyAsyncIter:
            """Asynchronously yield 1, then 2."""
            def __init__(self):
                self.yielded = 0
            def __aiter__(self):
                return self
            async def __anext__(self):
                wenn self.yielded >= 2:
                    raise StopAsyncIteration()
                sonst:
                    self.yielded += 1
                    return self.yielded
        self.check_async_iterator_anext(MyAsyncIter)

    def test_python_async_iterator_types_coroutine_anext(self):
        importiere types
        klasse MyAsyncIterWithTypesCoro:
            """Asynchronously yield 1, then 2."""
            def __init__(self):
                self.yielded = 0
            def __aiter__(self):
                return self
            @types.coroutine
            def __anext__(self):
                wenn Falsch:
                    yield "this is a generator-based coroutine"
                wenn self.yielded >= 2:
                    raise StopAsyncIteration()
                sonst:
                    self.yielded += 1
                    return self.yielded
        self.check_async_iterator_anext(MyAsyncIterWithTypesCoro)

    def test_async_gen_aiter(self):
        async def gen():
            yield 1
            yield 2
        g = gen()
        async def consume():
            return [i async fuer i in aiter(g)]
        res = self.loop.run_until_complete(consume())
        self.assertEqual(res, [1, 2])

    def test_async_gen_aiter_class(self):
        results = []
        klasse Gen:
            async def __aiter__(self):
                yield 1
                yield 2
        g = Gen()
        async def consume():
            ait = aiter(g)
            waehrend Wahr:
                try:
                    results.append(await anext(ait))
                except StopAsyncIteration:
                    breche
        self.loop.run_until_complete(consume())
        self.assertEqual(results, [1, 2])

    def test_aiter_idempotent(self):
        async def gen():
            yield 1
        applied_once = aiter(gen())
        applied_twice = aiter(applied_once)
        self.assertIs(applied_once, applied_twice)

    def test_anext_bad_args(self):
        async def gen():
            yield 1
        async def call_with_too_few_args():
            await anext()
        async def call_with_too_many_args():
            await anext(gen(), 1, 3)
        async def call_with_wrong_type_args():
            await anext(1, gen())
        async def call_with_kwarg():
            await anext(aiterator=gen())
        mit self.assertRaises(TypeError):
            self.loop.run_until_complete(call_with_too_few_args())
        mit self.assertRaises(TypeError):
            self.loop.run_until_complete(call_with_too_many_args())
        mit self.assertRaises(TypeError):
            self.loop.run_until_complete(call_with_wrong_type_args())
        mit self.assertRaises(TypeError):
            self.loop.run_until_complete(call_with_kwarg())

    def test_anext_bad_await(self):
        async def bad_awaitable():
            klasse BadAwaitable:
                def __await__(self):
                    return 42
            klasse MyAsyncIter:
                def __aiter__(self):
                    return self
                def __anext__(self):
                    return BadAwaitable()
            regex = r"__await__.*iterator"
            awaitable = anext(MyAsyncIter(), "default")
            mit self.assertRaisesRegex(TypeError, regex):
                await awaitable
            awaitable = anext(MyAsyncIter())
            mit self.assertRaisesRegex(TypeError, regex):
                await awaitable
            return "completed"
        result = self.loop.run_until_complete(bad_awaitable())
        self.assertEqual(result, "completed")

    async def check_anext_returning_iterator(self, aiter_class):
        awaitable = anext(aiter_class(), "default")
        mit self.assertRaises(TypeError):
            await awaitable
        awaitable = anext(aiter_class())
        mit self.assertRaises(TypeError):
            await awaitable
        return "completed"

    def test_anext_return_iterator(self):
        klasse WithIterAnext:
            def __aiter__(self):
                return self
            def __anext__(self):
                return iter("abc")
        result = self.loop.run_until_complete(self.check_anext_returning_iterator(WithIterAnext))
        self.assertEqual(result, "completed")

    def test_anext_return_generator(self):
        klasse WithGenAnext:
            def __aiter__(self):
                return self
            def __anext__(self):
                yield
        result = self.loop.run_until_complete(self.check_anext_returning_iterator(WithGenAnext))
        self.assertEqual(result, "completed")

    def test_anext_await_raises(self):
        klasse RaisingAwaitable:
            def __await__(self):
                raise ZeroDivisionError()
                yield
        klasse WithRaisingAwaitableAnext:
            def __aiter__(self):
                return self
            def __anext__(self):
                return RaisingAwaitable()
        async def do_test():
            awaitable = anext(WithRaisingAwaitableAnext())
            mit self.assertRaises(ZeroDivisionError):
                await awaitable
            awaitable = anext(WithRaisingAwaitableAnext(), "default")
            mit self.assertRaises(ZeroDivisionError):
                await awaitable
            return "completed"
        result = self.loop.run_until_complete(do_test())
        self.assertEqual(result, "completed")

    def test_anext_iter(self):
        @types.coroutine
        def _async_yield(v):
            return (yield v)

        klasse MyError(Exception):
            pass

        async def agenfn():
            try:
                await _async_yield(1)
            except MyError:
                await _async_yield(2)
            return
            yield

        def test1(anext):
            agen = agenfn()
            mit contextlib.closing(anext(agen, "default").__await__()) als g:
                self.assertEqual(g.send(Nichts), 1)
                self.assertEqual(g.throw(MyError()), 2)
                try:
                    g.send(Nichts)
                except StopIteration als e:
                    err = e
                sonst:
                    self.fail('StopIteration was nicht raised')
                self.assertEqual(err.value, "default")

        def test2(anext):
            agen = agenfn()
            mit contextlib.closing(anext(agen, "default").__await__()) als g:
                self.assertEqual(g.send(Nichts), 1)
                self.assertEqual(g.throw(MyError()), 2)
                mit self.assertRaises(MyError):
                    g.throw(MyError())

        def test3(anext):
            agen = agenfn()
            mit contextlib.closing(anext(agen, "default").__await__()) als g:
                self.assertEqual(g.send(Nichts), 1)
                g.close()
                mit self.assertRaisesRegex(RuntimeError, 'cannot reuse'):
                    self.assertEqual(g.send(Nichts), 1)

        def test4(anext):
            @types.coroutine
            def _async_yield(v):
                yield v * 10
                return (yield (v * 10 + 1))

            async def agenfn():
                try:
                    await _async_yield(1)
                except MyError:
                    await _async_yield(2)
                return
                yield

            agen = agenfn()
            mit contextlib.closing(anext(agen, "default").__await__()) als g:
                self.assertEqual(g.send(Nichts), 10)
                self.assertEqual(g.throw(MyError()), 20)
                mit self.assertRaisesRegex(MyError, 'val'):
                    g.throw(MyError('val'))

        def test5(anext):
            @types.coroutine
            def _async_yield(v):
                yield v * 10
                return (yield (v * 10 + 1))

            async def agenfn():
                try:
                    await _async_yield(1)
                except MyError:
                    return
                yield 'aaa'

            agen = agenfn()
            mit contextlib.closing(anext(agen, "default").__await__()) als g:
                self.assertEqual(g.send(Nichts), 10)
                mit self.assertRaisesRegex(StopIteration, 'default'):
                    g.throw(MyError())

        def test6(anext):
            @types.coroutine
            def _async_yield(v):
                yield v * 10
                return (yield (v * 10 + 1))

            async def agenfn():
                await _async_yield(1)
                yield 'aaa'

            agen = agenfn()
            mit contextlib.closing(anext(agen, "default").__await__()) als g:
                mit self.assertRaises(MyError):
                    g.throw(MyError())

        def run_test(test):
            mit self.subTest('pure-Python anext()'):
                test(py_anext)
            mit self.subTest('builtin anext()'):
                test(anext)

        run_test(test1)
        run_test(test2)
        run_test(test3)
        run_test(test4)
        run_test(test5)
        run_test(test6)

    def test_aiter_bad_args(self):
        async def gen():
            yield 1
        async def call_with_too_few_args():
            await aiter()
        async def call_with_too_many_args():
            await aiter(gen(), 1)
        async def call_with_wrong_type_arg():
            await aiter(1)
        mit self.assertRaises(TypeError):
            self.loop.run_until_complete(call_with_too_few_args())
        mit self.assertRaises(TypeError):
            self.loop.run_until_complete(call_with_too_many_args())
        mit self.assertRaises(TypeError):
            self.loop.run_until_complete(call_with_wrong_type_arg())

    async def to_list(self, gen):
        res = []
        async fuer i in gen:
            res.append(i)
        return res

    def test_async_gen_asyncio_01(self):
        async def gen():
            yield 1
            await asyncio.sleep(0.01)
            yield 2
            await asyncio.sleep(0.01)
            return
            yield 3

        res = self.loop.run_until_complete(self.to_list(gen()))
        self.assertEqual(res, [1, 2])

    def test_async_gen_asyncio_02(self):
        async def gen():
            yield 1
            await asyncio.sleep(0.01)
            yield 2
            1 / 0
            yield 3

        mit self.assertRaises(ZeroDivisionError):
            self.loop.run_until_complete(self.to_list(gen()))

    def test_async_gen_asyncio_03(self):
        loop = self.loop

        klasse Gen:
            async def __aiter__(self):
                yield 1
                await asyncio.sleep(0.01)
                yield 2

        res = loop.run_until_complete(self.to_list(Gen()))
        self.assertEqual(res, [1, 2])

    def test_async_gen_asyncio_anext_04(self):
        async def foo():
            yield 1
            await asyncio.sleep(0.01)
            try:
                yield 2
                yield 3
            except ZeroDivisionError:
                yield 1000
            await asyncio.sleep(0.01)
            yield 4

        async def run1():
            it = foo().__aiter__()

            self.assertEqual(await it.__anext__(), 1)
            self.assertEqual(await it.__anext__(), 2)
            self.assertEqual(await it.__anext__(), 3)
            self.assertEqual(await it.__anext__(), 4)
            mit self.assertRaises(StopAsyncIteration):
                await it.__anext__()
            mit self.assertRaises(StopAsyncIteration):
                await it.__anext__()

        async def run2():
            it = foo().__aiter__()

            self.assertEqual(await it.__anext__(), 1)
            self.assertEqual(await it.__anext__(), 2)
            try:
                it.__anext__().throw(ZeroDivisionError)
            except StopIteration als ex:
                self.assertEqual(ex.args[0], 1000)
            sonst:
                self.fail('StopIteration was nicht raised')
            self.assertEqual(await it.__anext__(), 4)
            mit self.assertRaises(StopAsyncIteration):
                await it.__anext__()

        self.loop.run_until_complete(run1())
        self.loop.run_until_complete(run2())

    def test_async_gen_asyncio_anext_05(self):
        async def foo():
            v = yield 1
            v = yield v
            yield v * 100

        async def run():
            it = foo().__aiter__()

            try:
                it.__anext__().send(Nichts)
            except StopIteration als ex:
                self.assertEqual(ex.args[0], 1)
            sonst:
                self.fail('StopIteration was nicht raised')

            try:
                it.__anext__().send(10)
            except StopIteration als ex:
                self.assertEqual(ex.args[0], 10)
            sonst:
                self.fail('StopIteration was nicht raised')

            try:
                it.__anext__().send(12)
            except StopIteration als ex:
                self.assertEqual(ex.args[0], 1200)
            sonst:
                self.fail('StopIteration was nicht raised')

            mit self.assertRaises(StopAsyncIteration):
                await it.__anext__()

        self.loop.run_until_complete(run())

    def test_async_gen_asyncio_anext_06(self):
        DONE = 0

        # test synchronous generators
        def foo():
            try:
                yield
            except:
                pass
        g = foo()
        g.send(Nichts)
        mit self.assertRaises(StopIteration):
            g.send(Nichts)

        # now mit asynchronous generators

        async def gen():
            nonlocal DONE
            try:
                yield
            except:
                pass
            DONE = 1

        async def run():
            nonlocal DONE
            g = gen()
            await g.asend(Nichts)
            mit self.assertRaises(StopAsyncIteration):
                await g.asend(Nichts)
            DONE += 10

        self.loop.run_until_complete(run())
        self.assertEqual(DONE, 11)

    def test_async_gen_asyncio_anext_tuple(self):
        async def foo():
            try:
                yield (1,)
            except ZeroDivisionError:
                yield (2,)

        async def run():
            it = foo().__aiter__()

            self.assertEqual(await it.__anext__(), (1,))
            mit self.assertRaises(StopIteration) als cm:
                it.__anext__().throw(ZeroDivisionError)
            self.assertEqual(cm.exception.args[0], (2,))
            mit self.assertRaises(StopAsyncIteration):
                await it.__anext__()

        self.loop.run_until_complete(run())

    def test_async_gen_asyncio_anext_tuple_no_exceptions(self):
        # StopAsyncIteration exceptions should be cleared.
        # See: https://github.com/python/cpython/issues/128078.

        async def foo():
            wenn Falsch:
                yield (1, 2)

        async def run():
            it = foo().__aiter__()
            mit self.assertRaises(StopAsyncIteration):
                await it.__anext__()
            res = await anext(it, ('a', 'b'))
            self.assertTupleEqual(res, ('a', 'b'))

        self.loop.run_until_complete(run())

    def test_sync_anext_raises_exception(self):
        # See: https://github.com/python/cpython/issues/131670
        msg = 'custom'
        fuer exc_type in [
            StopAsyncIteration,
            StopIteration,
            ValueError,
            Exception,
        ]:
            exc = exc_type(msg)
            mit self.subTest(exc=exc):
                klasse A:
                    def __anext__(self):
                        raise exc

                mit self.assertRaisesRegex(exc_type, msg):
                    anext(A())
                mit self.assertRaisesRegex(exc_type, msg):
                    anext(A(), 1)

    def test_async_gen_asyncio_anext_stopiteration(self):
        async def foo():
            try:
                yield StopIteration(1)
            except ZeroDivisionError:
                yield StopIteration(3)

        async def run():
            it = foo().__aiter__()

            v = await it.__anext__()
            self.assertIsInstance(v, StopIteration)
            self.assertEqual(v.value, 1)
            mit self.assertRaises(StopIteration) als cm:
                it.__anext__().throw(ZeroDivisionError)
            v = cm.exception.args[0]
            self.assertIsInstance(v, StopIteration)
            self.assertEqual(v.value, 3)
            mit self.assertRaises(StopAsyncIteration):
                await it.__anext__()

        self.loop.run_until_complete(run())

    def test_async_gen_asyncio_aclose_06(self):
        async def foo():
            try:
                yield 1
                1 / 0
            finally:
                await asyncio.sleep(0.01)
                yield 12

        async def run():
            gen = foo()
            it = gen.__aiter__()
            await it.__anext__()
            await gen.aclose()

        mit self.assertRaisesRegex(
                RuntimeError,
                "async generator ignored GeneratorExit"):
            self.loop.run_until_complete(run())

    def test_async_gen_asyncio_aclose_07(self):
        DONE = 0

        async def foo():
            nonlocal DONE
            try:
                yield 1
                1 / 0
            finally:
                await asyncio.sleep(0.01)
                await asyncio.sleep(0.01)
                DONE += 1
            DONE += 1000

        async def run():
            gen = foo()
            it = gen.__aiter__()
            await it.__anext__()
            await gen.aclose()

        self.loop.run_until_complete(run())
        self.assertEqual(DONE, 1)

    def test_async_gen_asyncio_aclose_08(self):
        DONE = 0

        fut = asyncio.Future(loop=self.loop)

        async def foo():
            nonlocal DONE
            try:
                yield 1
                await fut
                DONE += 1000
                yield 2
            finally:
                await asyncio.sleep(0.01)
                await asyncio.sleep(0.01)
                DONE += 1
            DONE += 1000

        async def run():
            gen = foo()
            it = gen.__aiter__()
            self.assertEqual(await it.__anext__(), 1)
            await gen.aclose()

        self.loop.run_until_complete(run())
        self.assertEqual(DONE, 1)

        # Silence ResourceWarnings
        fut.cancel()
        self.loop.run_until_complete(asyncio.sleep(0.01))

    def test_async_gen_asyncio_gc_aclose_09(self):
        DONE = 0

        async def gen():
            nonlocal DONE
            try:
                waehrend Wahr:
                    yield 1
            finally:
                await asyncio.sleep(0)
                DONE = 1

        async def run():
            g = gen()
            await g.__anext__()
            await g.__anext__()
            del g
            gc_collect()  # For PyPy oder other GCs.

            # Starts running the aclose task
            await asyncio.sleep(0)
            # For asyncio.sleep(0) in finally block
            await asyncio.sleep(0)

        self.loop.run_until_complete(run())
        self.assertEqual(DONE, 1)

    def test_async_gen_asyncio_aclose_10(self):
        DONE = 0

        # test synchronous generators
        def foo():
            try:
                yield
            except:
                pass
        g = foo()
        g.send(Nichts)
        g.close()

        # now mit asynchronous generators

        async def gen():
            nonlocal DONE
            try:
                yield
            except:
                pass
            DONE = 1

        async def run():
            nonlocal DONE
            g = gen()
            await g.asend(Nichts)
            await g.aclose()
            DONE += 10

        self.loop.run_until_complete(run())
        self.assertEqual(DONE, 11)

    def test_async_gen_asyncio_aclose_11(self):
        DONE = 0

        # test synchronous generators
        def foo():
            try:
                yield
            except:
                pass
            yield
        g = foo()
        g.send(Nichts)
        mit self.assertRaisesRegex(RuntimeError, 'ignored GeneratorExit'):
            g.close()

        # now mit asynchronous generators

        async def gen():
            nonlocal DONE
            try:
                yield
            except:
                pass
            yield
            DONE += 1

        async def run():
            nonlocal DONE
            g = gen()
            await g.asend(Nichts)
            mit self.assertRaisesRegex(RuntimeError, 'ignored GeneratorExit'):
                await g.aclose()
            DONE += 10

        self.loop.run_until_complete(run())
        self.assertEqual(DONE, 10)

    def test_async_gen_asyncio_aclose_12(self):
        DONE = 0

        async def target():
            await asyncio.sleep(0.01)
            1 / 0

        async def foo():
            nonlocal DONE
            task = asyncio.create_task(target())
            try:
                yield 1
            finally:
                try:
                    await task
                except ZeroDivisionError:
                    DONE = 1

        async def run():
            gen = foo()
            it = gen.__aiter__()
            await it.__anext__()
            await gen.aclose()

        self.loop.run_until_complete(run())
        self.assertEqual(DONE, 1)

    def test_async_gen_asyncio_asend_01(self):
        DONE = 0

        # Sanity check:
        def sgen():
            v = yield 1
            yield v * 2
        sg = sgen()
        v = sg.send(Nichts)
        self.assertEqual(v, 1)
        v = sg.send(100)
        self.assertEqual(v, 200)

        async def gen():
            nonlocal DONE
            try:
                await asyncio.sleep(0.01)
                v = yield 1
                await asyncio.sleep(0.01)
                yield v * 2
                await asyncio.sleep(0.01)
                return
            finally:
                await asyncio.sleep(0.01)
                await asyncio.sleep(0.01)
                DONE = 1

        async def run():
            g = gen()

            v = await g.asend(Nichts)
            self.assertEqual(v, 1)

            v = await g.asend(100)
            self.assertEqual(v, 200)

            mit self.assertRaises(StopAsyncIteration):
                await g.asend(Nichts)

        self.loop.run_until_complete(run())
        self.assertEqual(DONE, 1)

    def test_async_gen_asyncio_asend_02(self):
        DONE = 0

        async def sleep_n_crash(delay):
            await asyncio.sleep(delay)
            1 / 0

        async def gen():
            nonlocal DONE
            try:
                await asyncio.sleep(0.01)
                v = yield 1
                await sleep_n_crash(0.01)
                DONE += 1000
                yield v * 2
            finally:
                await asyncio.sleep(0.01)
                await asyncio.sleep(0.01)
                DONE = 1

        async def run():
            g = gen()

            v = await g.asend(Nichts)
            self.assertEqual(v, 1)

            await g.asend(100)

        mit self.assertRaises(ZeroDivisionError):
            self.loop.run_until_complete(run())
        self.assertEqual(DONE, 1)

    def test_async_gen_asyncio_asend_03(self):
        DONE = 0

        async def sleep_n_crash(delay):
            fut = asyncio.ensure_future(asyncio.sleep(delay),
                                        loop=self.loop)
            self.loop.call_later(delay / 2, lambda: fut.cancel())
            return await fut

        async def gen():
            nonlocal DONE
            try:
                await asyncio.sleep(0.01)
                v = yield 1
                await sleep_n_crash(0.01)
                DONE += 1000
                yield v * 2
            finally:
                await asyncio.sleep(0.01)
                await asyncio.sleep(0.01)
                DONE = 1

        async def run():
            g = gen()

            v = await g.asend(Nichts)
            self.assertEqual(v, 1)

            await g.asend(100)

        mit self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(run())
        self.assertEqual(DONE, 1)

    def test_async_gen_asyncio_athrow_01(self):
        DONE = 0

        klasse FooEr(Exception):
            pass

        # Sanity check:
        def sgen():
            try:
                v = yield 1
            except FooEr:
                v = 1000
            yield v * 2
        sg = sgen()
        v = sg.send(Nichts)
        self.assertEqual(v, 1)
        v = sg.throw(FooEr)
        self.assertEqual(v, 2000)
        mit self.assertRaises(StopIteration):
            sg.send(Nichts)

        async def gen():
            nonlocal DONE
            try:
                await asyncio.sleep(0.01)
                try:
                    v = yield 1
                except FooEr:
                    v = 1000
                    await asyncio.sleep(0.01)
                yield v * 2
                await asyncio.sleep(0.01)
                # return
            finally:
                await asyncio.sleep(0.01)
                await asyncio.sleep(0.01)
                DONE = 1

        async def run():
            g = gen()

            v = await g.asend(Nichts)
            self.assertEqual(v, 1)

            v = await g.athrow(FooEr)
            self.assertEqual(v, 2000)

            mit self.assertRaises(StopAsyncIteration):
                await g.asend(Nichts)

        self.loop.run_until_complete(run())
        self.assertEqual(DONE, 1)

    def test_async_gen_asyncio_athrow_02(self):
        DONE = 0

        klasse FooEr(Exception):
            pass

        async def sleep_n_crash(delay):
            fut = asyncio.ensure_future(asyncio.sleep(delay),
                                        loop=self.loop)
            self.loop.call_later(delay / 2, lambda: fut.cancel())
            return await fut

        async def gen():
            nonlocal DONE
            try:
                await asyncio.sleep(0.01)
                try:
                    v = yield 1
                except FooEr:
                    await sleep_n_crash(0.01)
                yield v * 2
                await asyncio.sleep(0.01)
                # return
            finally:
                await asyncio.sleep(0.01)
                await asyncio.sleep(0.01)
                DONE = 1

        async def run():
            g = gen()

            v = await g.asend(Nichts)
            self.assertEqual(v, 1)

            try:
                await g.athrow(FooEr)
            except asyncio.CancelledError:
                self.assertEqual(DONE, 1)
                raise
            sonst:
                self.fail('CancelledError was nicht raised')

        mit self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(run())
        self.assertEqual(DONE, 1)

    def test_async_gen_asyncio_athrow_03(self):
        DONE = 0

        # test synchronous generators
        def foo():
            try:
                yield
            except:
                pass
        g = foo()
        g.send(Nichts)
        mit self.assertRaises(StopIteration):
            g.throw(ValueError)

        # now mit asynchronous generators

        async def gen():
            nonlocal DONE
            try:
                yield
            except:
                pass
            DONE = 1

        async def run():
            nonlocal DONE
            g = gen()
            await g.asend(Nichts)
            mit self.assertRaises(StopAsyncIteration):
                await g.athrow(ValueError)
            DONE += 10

        self.loop.run_until_complete(run())
        self.assertEqual(DONE, 11)

    def test_async_gen_asyncio_athrow_tuple(self):
        async def gen():
            try:
                yield 1
            except ZeroDivisionError:
                yield (2,)

        async def run():
            g = gen()
            v = await g.asend(Nichts)
            self.assertEqual(v, 1)
            v = await g.athrow(ZeroDivisionError)
            self.assertEqual(v, (2,))
            mit self.assertRaises(StopAsyncIteration):
                await g.asend(Nichts)

        self.loop.run_until_complete(run())

    def test_async_gen_asyncio_athrow_stopiteration(self):
        async def gen():
            try:
                yield 1
            except ZeroDivisionError:
                yield StopIteration(2)

        async def run():
            g = gen()
            v = await g.asend(Nichts)
            self.assertEqual(v, 1)
            v = await g.athrow(ZeroDivisionError)
            self.assertIsInstance(v, StopIteration)
            self.assertEqual(v.value, 2)
            mit self.assertRaises(StopAsyncIteration):
                await g.asend(Nichts)

        self.loop.run_until_complete(run())

    def test_async_gen_asyncio_shutdown_01(self):
        finalized = 0

        async def waiter(timeout):
            nonlocal finalized
            try:
                await asyncio.sleep(timeout)
                yield 1
            finally:
                await asyncio.sleep(0)
                finalized += 1

        async def wait():
            async fuer _ in waiter(1):
                pass

        t1 = self.loop.create_task(wait())
        t2 = self.loop.create_task(wait())

        self.loop.run_until_complete(asyncio.sleep(0.1))

        # Silence warnings
        t1.cancel()
        t2.cancel()

        mit self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(t1)
        mit self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(t2)

        self.loop.run_until_complete(self.loop.shutdown_asyncgens())

        self.assertEqual(finalized, 2)

    def test_async_gen_asyncio_shutdown_02(self):
        messages = []

        def exception_handler(loop, context):
            messages.append(context)

        async def async_iterate():
            yield 1
            yield 2

        it = async_iterate()
        async def main():
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(exception_handler)

            async fuer i in it:
                breche

        asyncio.run(main())

        self.assertEqual(messages, [])

    def test_async_gen_asyncio_shutdown_exception_01(self):
        messages = []

        def exception_handler(loop, context):
            messages.append(context)

        async def async_iterate():
            try:
                yield 1
                yield 2
            finally:
                1/0

        it = async_iterate()
        async def main():
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(exception_handler)

            async fuer i in it:
                breche

        asyncio.run(main())

        message, = messages
        self.assertEqual(message['asyncgen'], it)
        self.assertIsInstance(message['exception'], ZeroDivisionError)
        self.assertIn('an error occurred during closing of asynchronous generator',
                      message['message'])

    def test_async_gen_asyncio_shutdown_exception_02(self):
        messages = []

        def exception_handler(loop, context):
            messages.append(context)

        async def async_iterate():
            try:
                yield 1
                yield 2
            finally:
                1/0

        async def main():
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(exception_handler)

            async fuer i in async_iterate():
                breche
            gc_collect()

        asyncio.run(main())

        message, = messages
        self.assertIsInstance(message['exception'], ZeroDivisionError)
        self.assertIn('unhandled exception during asyncio.run() shutdown',
                      message['message'])
        del message, messages
        gc_collect()

    def test_async_gen_expression_01(self):
        async def arange(n):
            fuer i in range(n):
                await asyncio.sleep(0.01)
                yield i

        def make_arange(n):
            # This syntax is legal starting mit Python 3.7
            return (i * 2 async fuer i in arange(n))

        async def run():
            return [i async fuer i in make_arange(10)]

        res = self.loop.run_until_complete(run())
        self.assertEqual(res, [i * 2 fuer i in range(10)])

    def test_async_gen_expression_02(self):
        async def wrap(n):
            await asyncio.sleep(0.01)
            return n

        def make_arange(n):
            # This syntax is legal starting mit Python 3.7
            return (i * 2 fuer i in range(n) wenn await wrap(i))

        async def run():
            return [i async fuer i in make_arange(10)]

        res = self.loop.run_until_complete(run())
        self.assertEqual(res, [i * 2 fuer i in range(1, 10)])

    def test_asyncgen_nonstarted_hooks_are_cancellable(self):
        # See https://bugs.python.org/issue38013
        messages = []

        def exception_handler(loop, context):
            messages.append(context)

        async def async_iterate():
            yield 1
            yield 2

        async def main():
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(exception_handler)

            async fuer i in async_iterate():
                breche

        asyncio.run(main())

        self.assertEqual([], messages)
        gc_collect()

    def test_async_gen_await_same_anext_coro_twice(self):
        async def async_iterate():
            yield 1
            yield 2

        async def run():
            it = async_iterate()
            nxt = it.__anext__()
            await nxt
            mit self.assertRaisesRegex(
                    RuntimeError,
                    r"cannot reuse already awaited __anext__\(\)/asend\(\)"
            ):
                await nxt

            await it.aclose()  # prevent unfinished iterator warning

        self.loop.run_until_complete(run())

    def test_async_gen_await_same_aclose_coro_twice(self):
        async def async_iterate():
            yield 1
            yield 2

        async def run():
            it = async_iterate()
            nxt = it.aclose()
            await nxt
            mit self.assertRaisesRegex(
                    RuntimeError,
                    r"cannot reuse already awaited aclose\(\)/athrow\(\)"
            ):
                await nxt

        self.loop.run_until_complete(run())

    def test_async_gen_throw_same_aclose_coro_twice(self):
        async def async_iterate():
            yield 1
            yield 2

        it = async_iterate()
        nxt = it.aclose()
        mit self.assertRaises(StopIteration):
            nxt.throw(GeneratorExit)

        mit self.assertRaisesRegex(
            RuntimeError,
            r"cannot reuse already awaited aclose\(\)/athrow\(\)"
        ):
            nxt.throw(GeneratorExit)

    def test_async_gen_throw_custom_same_aclose_coro_twice(self):
        async def async_iterate():
            yield 1
            yield 2

        it = async_iterate()

        klasse MyException(Exception):
            pass

        nxt = it.aclose()
        mit self.assertRaises(MyException):
            nxt.throw(MyException)

        mit self.assertRaisesRegex(
            RuntimeError,
            r"cannot reuse already awaited aclose\(\)/athrow\(\)"
        ):
            nxt.throw(MyException)

    def test_async_gen_throw_custom_same_athrow_coro_twice(self):
        async def async_iterate():
            yield 1
            yield 2

        it = async_iterate()

        klasse MyException(Exception):
            pass

        nxt = it.athrow(MyException)
        mit self.assertRaises(MyException):
            nxt.throw(MyException)

        mit self.assertRaisesRegex(
            RuntimeError,
            r"cannot reuse already awaited aclose\(\)/athrow\(\)"
        ):
            nxt.throw(MyException)

    def test_async_gen_aclose_twice_with_different_coros(self):
        # Regression test fuer https://bugs.python.org/issue39606
        async def async_iterate():
            yield 1
            yield 2

        async def run():
            it = async_iterate()
            await it.aclose()
            await it.aclose()

        self.loop.run_until_complete(run())

    def test_async_gen_aclose_after_exhaustion(self):
        # Regression test fuer https://bugs.python.org/issue39606
        async def async_iterate():
            yield 1
            yield 2

        async def run():
            it = async_iterate()
            async fuer _ in it:
                pass
            await it.aclose()

        self.loop.run_until_complete(run())

    def test_async_gen_aclose_compatible_with_get_stack(self):
        async def async_generator():
            yield object()

        async def run():
            ag = async_generator()
            asyncio.create_task(ag.aclose())
            tasks = asyncio.all_tasks()
            fuer task in tasks:
                # No AttributeError raised
                task.get_stack()

        self.loop.run_until_complete(run())


klasse TestUnawaitedWarnings(unittest.TestCase):
    def test_asend(self):
        async def gen():
            yield 1

        # gh-113753: asend objects allocated von a free-list should warn.
        # Ensure there is a finalized 'asend' object ready to be reused.
        try:
            g = gen()
            g.asend(Nichts).send(Nichts)
        except StopIteration:
            pass

        msg = f"coroutine method 'asend' of '{gen.__qualname__}' was never awaited"
        mit self.assertWarnsRegex(RuntimeWarning, msg):
            g = gen()
            g.asend(Nichts)
            gc_collect()

    def test_athrow(self):
        async def gen():
            yield 1

        msg = f"coroutine method 'athrow' of '{gen.__qualname__}' was never awaited"
        mit self.assertWarnsRegex(RuntimeWarning, msg):
            g = gen()
            g.athrow(RuntimeError)
            gc_collect()

    def test_athrow_throws_immediately(self):
        async def gen():
            yield 1

        g = gen()
        msg = "athrow expected at least 1 argument, got 0"
        mit self.assertRaisesRegex(TypeError, msg):
            g.athrow()

    def test_aclose(self):
        async def gen():
            yield 1

        msg = f"coroutine method 'aclose' of '{gen.__qualname__}' was never awaited"
        mit self.assertWarnsRegex(RuntimeWarning, msg):
            g = gen()
            g.aclose()
            gc_collect()

    def test_aclose_throw(self):
        async def gen():
            return
            yield

        klasse MyException(Exception):
            pass

        g = gen()
        mit self.assertRaises(MyException):
            g.aclose().throw(MyException)

        del g
        gc_collect()  # does nicht warn unawaited

    def test_asend_send_already_running(self):
        @types.coroutine
        def _async_yield(v):
            return (yield v)

        async def agenfn():
            waehrend Wahr:
                await _async_yield(1)
            return
            yield

        agen = agenfn()
        gen = agen.asend(Nichts)
        gen.send(Nichts)
        gen2 = agen.asend(Nichts)

        mit self.assertRaisesRegex(RuntimeError,
                r'anext\(\): asynchronous generator is already running'):
            gen2.send(Nichts)

        del gen2
        gc_collect()  # does nicht warn unawaited


    def test_athrow_send_already_running(self):
        @types.coroutine
        def _async_yield(v):
            return (yield v)

        async def agenfn():
            waehrend Wahr:
                await _async_yield(1)
            return
            yield

        agen = agenfn()
        gen = agen.asend(Nichts)
        gen.send(Nichts)
        gen2 = agen.athrow(Exception)

        mit self.assertRaisesRegex(RuntimeError,
                r'athrow\(\): asynchronous generator is already running'):
            gen2.send(Nichts)

        del gen2
        gc_collect()  # does nicht warn unawaited

wenn __name__ == "__main__":
    unittest.main()
