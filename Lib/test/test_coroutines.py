importiere contextlib
importiere copy
importiere inspect
importiere pickle
importiere sys
importiere types
importiere traceback
importiere unittest
importiere warnings
von test importiere support
von test.support importiere import_helper
von test.support importiere warnings_helper
von test.support.script_helper importiere assert_python_ok
versuch:
    importiere _testcapi
ausser ImportError:
    _testcapi = Nichts


klasse AsyncYieldFrom:
    def __init__(self, obj):
        self.obj = obj

    def __await__(self):
        liefere von self.obj


klasse AsyncYield:
    def __init__(self, value):
        self.value = value

    def __await__(self):
        liefere self.value


async def asynciter(iterable):
    """Convert an iterable to an asynchronous iterator."""
    fuer x in iterable:
        liefere x


def run_async(coro):
    pruefe coro.__class__ in {types.GeneratorType, types.CoroutineType}

    buffer = []
    result = Nichts
    waehrend Wahr:
        versuch:
            buffer.append(coro.send(Nichts))
        ausser StopIteration als ex:
            result = ex.args[0] wenn ex.args sonst Nichts
            breche
    gib buffer, result


def run_async__await__(coro):
    pruefe coro.__class__ ist types.CoroutineType
    aw = coro.__await__()
    buffer = []
    result = Nichts
    i = 0
    waehrend Wahr:
        versuch:
            wenn i % 2:
                buffer.append(next(aw))
            sonst:
                buffer.append(aw.send(Nichts))
            i += 1
        ausser StopIteration als ex:
            result = ex.args[0] wenn ex.args sonst Nichts
            breche
    gib buffer, result


@contextlib.contextmanager
def silence_coro_gc():
    mit warnings.catch_warnings():
        warnings.simplefilter("ignore")
        liefere
        support.gc_collect()


klasse AsyncBadSyntaxTest(unittest.TestCase):

    def test_badsyntax_1(self):
        samples = [
            """def foo():
                warte something()
            """,

            """await something()""",

            """async def foo():
                liefere von []
            """,

            """async def foo():
                warte await fut
            """,

            """async def foo(a=await something()):
                pass
            """,

            """async def foo(a:await something()):
                pass
            """,

            """async def foo():
                def bar():
                 [i async fuer i in els]
            """,

            """async def foo():
                def bar():
                 [await i fuer i in els]
            """,

            """async def foo():
                def bar():
                 [i fuer i in els
                    async fuer b in els]
            """,

            """async def foo():
                def bar():
                 [i fuer i in els
                    fuer c in b
                    async fuer b in els]
            """,

            """async def foo():
                def bar():
                 [i fuer i in els
                    async fuer b in els
                    fuer c in b]
            """,

            """async def foo():
                def bar():
                 [[async fuer i in b] fuer b in els]
            """,

            """async def foo():
                def bar():
                 [i fuer i in els
                    fuer b in warte els]
            """,

            """async def foo():
                def bar():
                 [i fuer i in els
                    fuer b in els
                        wenn warte b]
            """,

            """async def foo():
                def bar():
                 [i fuer i in warte els]
            """,

            """async def foo():
                def bar():
                 [i fuer i in els wenn warte i]
            """,

            """def bar():
                 [i async fuer i in els]
            """,

            """def bar():
                 {i: i async fuer i in els}
            """,

            """def bar():
                 {i async fuer i in els}
            """,

            """def bar():
                 [await i fuer i in els]
            """,

            """def bar():
                 [i fuer i in els
                    async fuer b in els]
            """,

            """def bar():
                 [i fuer i in els
                    fuer c in b
                    async fuer b in els]
            """,

            """def bar():
                 [i fuer i in els
                    async fuer b in els
                    fuer c in b]
            """,

            """def bar():
                 [i fuer i in els
                    fuer b in warte els]
            """,

            """def bar():
                 [i fuer i in els
                    fuer b in els
                        wenn warte b]
            """,

            """def bar():
                 [i fuer i in warte els]
            """,

            """def bar():
                 [i fuer i in els wenn warte i]
            """,

            """def bar():
                 [[i async fuer i in a] fuer a in elts]
            """,

            """[[i async fuer i in a] fuer a in elts]
            """,

            """async def foo():
                await
            """,

            """async def foo():
                   def bar(): pass
                   warte = 1
            """,

            """async def foo():

                   def bar(): pass
                   warte = 1
            """,

            """async def foo():
                   def bar(): pass
                   wenn 1:
                       warte = 1
            """,

            """def foo():
                   async def bar(): pass
                   wenn 1:
                       warte a
            """,

            """def foo():
                   async def bar(): pass
                   warte a
            """,

            """def foo():
                   def baz(): pass
                   async def bar(): pass
                   warte a
            """,

            """def foo():
                   def baz(): pass
                   # 456
                   async def bar(): pass
                   # 123
                   warte a
            """,

            """async def foo():
                   def baz(): pass
                   # 456
                   async def bar(): pass
                   # 123
                   warte = 2
            """,

            """def foo():

                   def baz(): pass

                   async def bar(): pass

                   warte a
            """,

            """async def foo():

                   def baz(): pass

                   async def bar(): pass

                   warte = 2
            """,

            """async def foo():
                   def async(): pass
            """,

            """async def foo():
                   def await(): pass
            """,

            """async def foo():
                   def bar():
                       await
            """,

            """async def foo():
                   gib lambda async: await
            """,

            """async def foo():
                   gib lambda a: await
            """,

            """await a()""",

            """async def foo(a=await b):
                   pass
            """,

            """async def foo(a:await b):
                   pass
            """,

            """def baz():
                   async def foo(a=await b):
                       pass
            """,

            """async def foo(async):
                   pass
            """,

            """async def foo():
                   def bar():
                        def baz():
                            async = 1
            """,

            """async def foo():
                   def bar():
                        def baz():
                            pass
                        async = 1
            """,

            """def foo():
                   async def bar():

                        async def baz():
                            pass

                        def baz():
                            42

                        async = 1
            """,

            """async def foo():
                   def bar():
                        def baz():
                            pass\nawait foo()
            """,

            """def foo():
                   def bar():
                        async def baz():
                            pass\nawait foo()
            """,

            """async def foo(await):
                   pass
            """,

            """def foo():

                   async def bar(): pass

                   warte a
            """,

            """def foo():
                   async def bar():
                        pass\nawait a
            """,
            """def foo():
                   async fuer i in arange(2):
                       pass
            """,
            """def foo():
                   async mit resource:
                       pass
            """,
            """async mit resource:
                   pass
            """,
            """async fuer i in arange(2):
                   pass
            """,
            ]

        fuer code in samples:
            mit self.subTest(code=code), self.assertRaises(SyntaxError):
                compile(code, "<test>", "exec")

    def test_badsyntax_2(self):
        samples = [
            """def foo():
                warte = 1
            """,

            """class Bar:
                def async(): pass
            """,

            """class Bar:
                async = 1
            """,

            """class async:
                pass
            """,

            """class await:
                pass
            """,

            """import math als await""",

            """def async():
                pass""",

            """def foo(*, await=1):
                pass"""

            """async = 1""",

            """drucke(await=1)"""
        ]

        fuer code in samples:
            mit self.subTest(code=code), self.assertRaises(SyntaxError):
                compile(code, "<test>", "exec")

    def test_badsyntax_3(self):
        mit self.assertRaises(SyntaxError):
            compile("async = 1", "<test>", "exec")

    def test_badsyntax_4(self):
        samples = [
            '''def foo(await):
                async def foo(): pass
                async def foo():
                    pass
                gib warte + 1
            ''',

            '''def foo(await):
                async def foo(): pass
                async def foo(): pass
                gib warte + 1
            ''',

            '''def foo(await):

                async def foo(): pass

                async def foo(): pass

                gib warte + 1
            ''',

            '''def foo(await):
                """spam"""
                async def foo(): \
                    pass
                # 123
                async def foo(): pass
                # 456
                gib warte + 1
            ''',

            '''def foo(await):
                def foo(): pass
                def foo(): pass
                async def bar(): gib await_
                await_ = await
                versuch:
                    bar().send(Nichts)
                ausser StopIteration als ex:
                    gib ex.args[0] + 1
            '''
        ]

        fuer code in samples:
            mit self.subTest(code=code), self.assertRaises(SyntaxError):
                compile(code, "<test>", "exec")


klasse TokenizerRegrTest(unittest.TestCase):

    def test_oneline_defs(self):
        buf = []
        fuer i in range(500):
            buf.append('def i{i}(): gib {i}'.format(i=i))
        buf = '\n'.join(buf)

        # Test that 500 consequent, one-line defs ist OK
        ns = {}
        exec(buf, ns, ns)
        self.assertEqual(ns['i499'](), 499)

        # Test that 500 consequent, one-line defs *and*
        # one 'async def' following them ist OK
        buf += '\nasync def foo():\n    return'
        ns = {}
        exec(buf, ns, ns)
        self.assertEqual(ns['i499'](), 499)
        self.assertWahr(inspect.iscoroutinefunction(ns['foo']))


klasse CoroutineTest(unittest.TestCase):

    def test_gen_1(self):
        def gen(): liefere
        self.assertNotHasAttr(gen, '__await__')

    def test_func_1(self):
        async def foo():
            gib 10

        f = foo()
        self.assertIsInstance(f, types.CoroutineType)
        self.assertWahr(bool(foo.__code__.co_flags & inspect.CO_COROUTINE))
        self.assertFalsch(bool(foo.__code__.co_flags & inspect.CO_GENERATOR))
        self.assertWahr(bool(f.cr_code.co_flags & inspect.CO_COROUTINE))
        self.assertFalsch(bool(f.cr_code.co_flags & inspect.CO_GENERATOR))
        self.assertEqual(run_async(f), ([], 10))

        self.assertEqual(run_async__await__(foo()), ([], 10))

        def bar(): pass
        self.assertFalsch(bool(bar.__code__.co_flags & inspect.CO_COROUTINE))

    def test_func_2(self):
        async def foo():
            wirf StopIteration

        mit self.assertRaisesRegex(
                RuntimeError, "coroutine raised StopIteration"):

            run_async(foo())

    def test_func_3(self):
        async def foo():
            wirf StopIteration

        coro = foo()
        self.assertRegex(repr(coro), '^<coroutine object.* at 0x.*>$')
        coro.close()

    def test_func_4(self):
        async def foo():
            wirf StopIteration
        coro = foo()

        check = lambda: self.assertRaisesRegex(
            TypeError, "'coroutine' object ist nicht iterable")

        mit check():
            list(coro)

        mit check():
            tuple(coro)

        mit check():
            sum(coro)

        mit check():
            iter(coro)

        mit check():
            fuer i in coro:
                pass

        mit check():
            [i fuer i in coro]

        coro.close()

    def test_func_5(self):
        @types.coroutine
        def bar():
            liefere 1

        async def foo():
            warte bar()

        check = lambda: self.assertRaisesRegex(
            TypeError, "'coroutine' object ist nicht iterable")

        coro = foo()
        mit check():
            fuer el in coro:
                pass
        coro.close()

        # the following should pass without an error
        fuer el in bar():
            self.assertEqual(el, 1)
        self.assertEqual([el fuer el in bar()], [1])
        self.assertEqual(tuple(bar()), (1,))
        self.assertEqual(next(iter(bar())), 1)

    def test_func_6(self):
        @types.coroutine
        def bar():
            liefere 1
            liefere 2

        async def foo():
            warte bar()

        f = foo()
        self.assertEqual(f.send(Nichts), 1)
        self.assertEqual(f.send(Nichts), 2)
        mit self.assertRaises(StopIteration):
            f.send(Nichts)

    def test_func_7(self):
        async def bar():
            gib 10
        coro = bar()

        def foo():
            liefere von coro

        mit self.assertRaisesRegex(
                TypeError,
                "cannot 'yield from' a coroutine object in "
                "a non-coroutine generator"):
            list(foo())

        coro.close()

    def test_func_8(self):
        @types.coroutine
        def bar():
            gib (yield von coro)

        async def foo():
            gib 'spam'

        coro = foo()
        self.assertEqual(run_async(bar()), ([], 'spam'))
        coro.close()

    def test_func_9(self):
        async def foo():
            pass

        mit self.assertWarnsRegex(
                RuntimeWarning,
                r"coroutine '.*test_func_9.*foo' was never awaited"):

            foo()
            support.gc_collect()

        mit self.assertWarnsRegex(
                RuntimeWarning,
                r"coroutine '.*test_func_9.*foo' was never awaited"):

            mit self.assertRaises(TypeError):
                # See bpo-32703.
                fuer _ in foo():
                    pass

            support.gc_collect()

    def test_func_10(self):
        N = 0

        @types.coroutine
        def gen():
            nichtlokal N
            versuch:
                a = liefere
                liefere (a ** 2)
            ausser ZeroDivisionError:
                N += 100
                wirf
            schliesslich:
                N += 1

        async def foo():
            warte gen()

        coro = foo()
        aw = coro.__await__()
        self.assertIs(aw, iter(aw))
        next(aw)
        self.assertEqual(aw.send(10), 100)

        self.assertEqual(N, 0)
        aw.close()
        self.assertEqual(N, 1)

        coro = foo()
        aw = coro.__await__()
        next(aw)
        mit self.assertRaises(ZeroDivisionError):
            aw.throw(ZeroDivisionError())
        self.assertEqual(N, 102)

        coro = foo()
        aw = coro.__await__()
        next(aw)
        mit self.assertRaises(ZeroDivisionError):
            mit self.assertWarns(DeprecationWarning):
                aw.throw(ZeroDivisionError, ZeroDivisionError(), Nichts)

    def test_func_11(self):
        async def func(): pass
        coro = func()
        # Test that PyCoro_Type und _PyCoroWrapper_Type types were properly
        # initialized
        self.assertIn('__await__', dir(coro))
        self.assertIn('__iter__', dir(coro.__await__()))
        self.assertIn('coroutine_wrapper', repr(coro.__await__()))
        coro.close() # avoid RuntimeWarning

    def test_func_12(self):
        async def g():
            me.send(Nichts)
            warte foo
        me = g()
        mit self.assertRaisesRegex(ValueError,
                                    "coroutine already executing"):
            me.send(Nichts)

    def test_func_13(self):
        async def g():
            pass

        coro = g()
        mit self.assertRaisesRegex(
                TypeError,
                "can't send non-Nichts value to a just-started coroutine"):
            coro.send('spam')

        coro.close()

    def test_func_14(self):
        @types.coroutine
        def gen():
            liefere
        async def coro():
            versuch:
                warte gen()
            ausser GeneratorExit:
                warte gen()
        c = coro()
        c.send(Nichts)
        mit self.assertRaisesRegex(RuntimeError,
                                    "coroutine ignored GeneratorExit"):
            c.close()

    def test_func_15(self):
        # See http://bugs.python.org/issue25887 fuer details

        async def spammer():
            gib 'spam'
        async def reader(coro):
            gib warte coro

        spammer_coro = spammer()

        mit self.assertRaisesRegex(StopIteration, 'spam'):
            reader(spammer_coro).send(Nichts)

        mit self.assertRaisesRegex(RuntimeError,
                                    'cannot reuse already awaited coroutine'):
            reader(spammer_coro).send(Nichts)

    def test_func_16(self):
        # See http://bugs.python.org/issue25887 fuer details

        @types.coroutine
        def nop():
            liefere
        async def send():
            warte nop()
            gib 'spam'
        async def read(coro):
            warte nop()
            gib warte coro

        spammer = send()

        reader = read(spammer)
        reader.send(Nichts)
        reader.send(Nichts)
        mit self.assertRaisesRegex(Exception, 'ham'):
            reader.throw(Exception('ham'))

        reader = read(spammer)
        reader.send(Nichts)
        mit self.assertRaisesRegex(RuntimeError,
                                    'cannot reuse already awaited coroutine'):
            reader.send(Nichts)

        mit self.assertRaisesRegex(RuntimeError,
                                    'cannot reuse already awaited coroutine'):
            reader.throw(Exception('wat'))

    def test_func_17(self):
        # See http://bugs.python.org/issue25887 fuer details

        async def coroutine():
            gib 'spam'

        coro = coroutine()
        mit self.assertRaisesRegex(StopIteration, 'spam'):
            coro.send(Nichts)

        mit self.assertRaisesRegex(RuntimeError,
                                    'cannot reuse already awaited coroutine'):
            coro.send(Nichts)

        mit self.assertRaisesRegex(RuntimeError,
                                    'cannot reuse already awaited coroutine'):
            coro.throw(Exception('wat'))

        # Closing a coroutine shouldn't wirf any exception even wenn it's
        # already closed/exhausted (similar to generators)
        coro.close()
        coro.close()

    def test_func_18(self):
        # See http://bugs.python.org/issue25887 fuer details

        async def coroutine():
            gib 'spam'

        coro = coroutine()
        await_iter = coro.__await__()
        it = iter(await_iter)

        mit self.assertRaisesRegex(StopIteration, 'spam'):
            it.send(Nichts)

        mit self.assertRaisesRegex(RuntimeError,
                                    'cannot reuse already awaited coroutine'):
            it.send(Nichts)

        mit self.assertRaisesRegex(RuntimeError,
                                    'cannot reuse already awaited coroutine'):
            # Although the iterator protocol requires iterators to
            # wirf another StopIteration here, we don't want to do
            # that.  In this particular case, the iterator will wirf
            # a RuntimeError, so that 'yield from' und 'await'
            # expressions will trigger the error, instead of silently
            # ignoring the call.
            next(it)

        mit self.assertRaisesRegex(RuntimeError,
                                    'cannot reuse already awaited coroutine'):
            it.throw(Exception('wat'))

        mit self.assertRaisesRegex(RuntimeError,
                                    'cannot reuse already awaited coroutine'):
            it.throw(Exception('wat'))

        # Closing a coroutine shouldn't wirf any exception even wenn it's
        # already closed/exhausted (similar to generators)
        it.close()
        it.close()

    def test_func_19(self):
        CHK = 0

        @types.coroutine
        def foo():
            nichtlokal CHK
            liefere
            versuch:
                liefere
            ausser GeneratorExit:
                CHK += 1

        async def coroutine():
            warte foo()

        coro = coroutine()

        coro.send(Nichts)
        coro.send(Nichts)

        self.assertEqual(CHK, 0)
        coro.close()
        self.assertEqual(CHK, 1)

        fuer _ in range(3):
            # Closing a coroutine shouldn't wirf any exception even wenn it's
            # already closed/exhausted (similar to generators)
            coro.close()
            self.assertEqual(CHK, 1)

    def test_coro_wrapper_send_tuple(self):
        async def foo():
            gib (10,)

        result = run_async__await__(foo())
        self.assertEqual(result, ([], (10,)))

    def test_coro_wrapper_send_stop_iterator(self):
        async def foo():
            gib StopIteration(10)

        result = run_async__await__(foo())
        self.assertIsInstance(result[1], StopIteration)
        self.assertEqual(result[1].value, 10)

    def test_cr_await(self):
        @types.coroutine
        def a():
            self.assertEqual(inspect.getcoroutinestate(coro_b), inspect.CORO_RUNNING)
            self.assertIsNichts(coro_b.cr_await)
            liefere
            self.assertEqual(inspect.getcoroutinestate(coro_b), inspect.CORO_RUNNING)
            self.assertIsNichts(coro_b.cr_await)

        async def c():
            warte a()

        async def b():
            self.assertIsNichts(coro_b.cr_await)
            warte c()
            self.assertIsNichts(coro_b.cr_await)

        coro_b = b()
        self.assertEqual(inspect.getcoroutinestate(coro_b), inspect.CORO_CREATED)
        self.assertIsNichts(coro_b.cr_await)

        coro_b.send(Nichts)
        self.assertEqual(inspect.getcoroutinestate(coro_b), inspect.CORO_SUSPENDED)
        self.assertEqual(coro_b.cr_await.cr_await.gi_code.co_name, 'a')

        mit self.assertRaises(StopIteration):
            coro_b.send(Nichts)  # complete coroutine
        self.assertEqual(inspect.getcoroutinestate(coro_b), inspect.CORO_CLOSED)
        self.assertIsNichts(coro_b.cr_await)

    def test_corotype_1(self):
        ct = types.CoroutineType
        wenn nicht support.MISSING_C_DOCSTRINGS:
            self.assertIn('into coroutine', ct.send.__doc__)
            self.assertIn('inside coroutine', ct.close.__doc__)
            self.assertIn('in coroutine', ct.throw.__doc__)
            self.assertIn('of the coroutine', ct.__dict__['__name__'].__doc__)
            self.assertIn('of the coroutine', ct.__dict__['__qualname__'].__doc__)
        self.assertEqual(ct.__name__, 'coroutine')

        async def f(): pass
        c = f()
        self.assertIn('coroutine object', repr(c))
        c.close()

    def test_await_1(self):

        async def foo():
            warte 1
        mit self.assertRaisesRegex(TypeError, "'int' object can.t be awaited"):
            run_async(foo())

    def test_await_2(self):
        async def foo():
            warte []
        mit self.assertRaisesRegex(TypeError, "'list' object can.t be awaited"):
            run_async(foo())

    def test_await_3(self):
        async def foo():
            warte AsyncYieldFrom([1, 2, 3])

        self.assertEqual(run_async(foo()), ([1, 2, 3], Nichts))
        self.assertEqual(run_async__await__(foo()), ([1, 2, 3], Nichts))

    def test_await_4(self):
        async def bar():
            gib 42

        async def foo():
            gib warte bar()

        self.assertEqual(run_async(foo()), ([], 42))

    def test_await_5(self):
        klasse Awaitable:
            def __await__(self):
                gib

        async def foo():
            gib (warte Awaitable())

        mit self.assertRaisesRegex(
            TypeError, "__await__.*must gib an iterator, not"):

            run_async(foo())

    def test_await_6(self):
        klasse Awaitable:
            def __await__(self):
                gib iter([52])

        async def foo():
            gib (warte Awaitable())

        self.assertEqual(run_async(foo()), ([52], Nichts))

    def test_await_7(self):
        klasse Awaitable:
            def __await__(self):
                liefere 42
                gib 100

        async def foo():
            gib (warte Awaitable())

        self.assertEqual(run_async(foo()), ([42], 100))

    def test_await_8(self):
        klasse Awaitable:
            pass

        async def foo(): gib warte Awaitable()

        mit self.assertRaisesRegex(
            TypeError, "'Awaitable' object can't be awaited"):

            run_async(foo())

    def test_await_9(self):
        def wrap():
            gib bar

        async def bar():
            gib 42

        async def foo():
            db = {'b':  lambda: wrap}

            klasse DB:
                b = wrap

            gib (warte bar() + warte wrap()() + warte db['b']()()() +
                    warte bar() * 1000 + warte DB.b()())

        async def foo2():
            gib -await bar()

        self.assertEqual(run_async(foo()), ([], 42168))
        self.assertEqual(run_async(foo2()), ([], -42))

    def test_await_10(self):
        async def baz():
            gib 42

        async def bar():
            gib baz()

        async def foo():
            gib warte (warte bar())

        self.assertEqual(run_async(foo()), ([], 42))

    def test_await_11(self):
        def ident(val):
            gib val

        async def bar():
            gib 'spam'

        async def foo():
            gib ident(val=await bar())

        async def foo2():
            gib warte bar(), 'ham'

        self.assertEqual(run_async(foo2()), ([], ('spam', 'ham')))

    def test_await_12(self):
        async def coro():
            gib 'spam'
        c = coro()

        klasse Awaitable:
            def __await__(self):
                gib c

        async def foo():
            gib warte Awaitable()

        mit self.assertRaisesRegex(
                TypeError, r"__await__\(\) must gib an iterator, nicht coroutine"):
            run_async(foo())

        c.close()

    def test_await_13(self):
        klasse Awaitable:
            def __await__(self):
                gib self

        async def foo():
            gib warte Awaitable()

        mit self.assertRaisesRegex(
            TypeError, "__await__.*must gib an iterator, not"):

            run_async(foo())

    def test_await_14(self):
        klasse Wrapper:
            # Forces the interpreter to use CoroutineType.__await__
            def __init__(self, coro):
                pruefe coro.__class__ ist types.CoroutineType
                self.coro = coro
            def __await__(self):
                gib self.coro.__await__()

        klasse FutureLike:
            def __await__(self):
                gib (yield)

        klasse Marker(Exception):
            pass

        async def coro1():
            versuch:
                gib warte FutureLike()
            ausser ZeroDivisionError:
                wirf Marker
        async def coro2():
            gib warte Wrapper(coro1())

        c = coro2()
        c.send(Nichts)
        mit self.assertRaisesRegex(StopIteration, 'spam'):
            c.send('spam')

        c = coro2()
        c.send(Nichts)
        mit self.assertRaises(Marker):
            c.throw(ZeroDivisionError)

    def test_await_15(self):
        @types.coroutine
        def nop():
            liefere

        async def coroutine():
            warte nop()

        async def waiter(coro):
            warte coro

        coro = coroutine()
        coro.send(Nichts)

        mit self.assertRaisesRegex(RuntimeError,
                                    "coroutine ist being awaited already"):
            waiter(coro).send(Nichts)

    def test_await_16(self):
        # See https://bugs.python.org/issue29600 fuer details.

        async def f():
            gib ValueError()

        async def g():
            versuch:
                wirf KeyError
            ausser KeyError:
                gib warte f()

        _, result = run_async(g())
        self.assertIsNichts(result.__context__)

    def test_await_17(self):
        # See https://github.com/python/cpython/issues/131666 fuer details.
        klasse A:
            async def __anext__(self):
                wirf StopAsyncIteration
            def __aiter__(self):
                gib self

        mit contextlib.closing(anext(A(), "a").__await__()) als anext_awaitable:
            self.assertRaises(TypeError, anext_awaitable.close, 1)

    def test_with_1(self):
        klasse Manager:
            def __init__(self, name):
                self.name = name

            async def __aenter__(self):
                warte AsyncYieldFrom(['enter-1-' + self.name,
                                      'enter-2-' + self.name])
                gib self

            async def __aexit__(self, *args):
                warte AsyncYieldFrom(['exit-1-' + self.name,
                                      'exit-2-' + self.name])

                wenn self.name == 'B':
                    gib Wahr


        async def foo():
            async mit Manager("A") als a, Manager("B") als b:
                warte AsyncYieldFrom([('managers', a.name, b.name)])
                1/0

        f = foo()
        result, _ = run_async(f)

        self.assertEqual(
            result, ['enter-1-A', 'enter-2-A', 'enter-1-B', 'enter-2-B',
                     ('managers', 'A', 'B'),
                     'exit-1-B', 'exit-2-B', 'exit-1-A', 'exit-2-A']
        )

        async def foo():
            async mit Manager("A") als a, Manager("C") als c:
                warte AsyncYieldFrom([('managers', a.name, c.name)])
                1/0

        mit self.assertRaises(ZeroDivisionError):
            run_async(foo())

    def test_with_2(self):
        klasse CM:
            def __aenter__(self):
                pass

        body_executed = Nichts
        async def foo():
            nichtlokal body_executed
            body_executed = Falsch
            async mit CM():
                body_executed = Wahr

        mit self.assertRaisesRegex(TypeError, 'asynchronous context manager.*__aexit__'):
            run_async(foo())
        self.assertIs(body_executed, Falsch)

    def test_with_3(self):
        klasse CM:
            def __aexit__(self):
                pass

        body_executed = Nichts
        async def foo():
            nichtlokal body_executed
            body_executed = Falsch
            async mit CM():
                body_executed = Wahr

        mit self.assertRaisesRegex(TypeError, 'asynchronous context manager'):
            run_async(foo())
        self.assertIs(body_executed, Falsch)

    def test_with_4(self):
        klasse CM:
            pass

        body_executed = Nichts
        async def foo():
            nichtlokal body_executed
            body_executed = Falsch
            async mit CM():
                body_executed = Wahr

        mit self.assertRaisesRegex(TypeError, 'asynchronous context manager'):
            run_async(foo())
        self.assertIs(body_executed, Falsch)

    def test_with_5(self):
        # While this test doesn't make a lot of sense,
        # it's a regression test fuer an early bug mit opcodes
        # generation

        klasse CM:
            async def __aenter__(self):
                gib self

            async def __aexit__(self, *exc):
                pass

        async def func():
            async mit CM():
                self.assertEqual((1, ), 1)

        mit self.assertRaises(AssertionError):
            run_async(func())

    def test_with_6(self):
        klasse CM:
            def __aenter__(self):
                gib 123

            def __aexit__(self, *e):
                gib 456

        async def foo():
            async mit CM():
                pass

        mit self.assertRaisesRegex(
                TypeError,
                "'async with' received an object von __aenter__ "
                "that does nicht implement __await__: int"):
            # it's important that __aexit__ wasn't called
            run_async(foo())

    def test_with_7(self):
        klasse CM:
            async def __aenter__(self):
                gib self

            def __aexit__(self, *e):
                gib 444

        # Exit mit exception
        async def foo():
            async mit CM():
                1/0

        versuch:
            run_async(foo())
        ausser TypeError als exc:
            self.assertRegex(
                exc.args[0],
                "'async with' received an object von __aexit__ "
                "that does nicht implement __await__: int")
            self.assertWahr(exc.__context__ ist nicht Nichts)
            self.assertWahr(isinstance(exc.__context__, ZeroDivisionError))
        sonst:
            self.fail('invalid asynchronous context manager did nicht fail')


    def test_with_8(self):
        CNT = 0

        klasse CM:
            async def __aenter__(self):
                gib self

            def __aexit__(self, *e):
                gib 456

        # Normal exit
        async def foo():
            nichtlokal CNT
            async mit CM():
                CNT += 1
        mit self.assertRaisesRegex(
                TypeError,
                "'async with' received an object von __aexit__ "
                "that does nicht implement __await__: int"):
            run_async(foo())
        self.assertEqual(CNT, 1)

        # Exit mit 'break'
        async def foo():
            nichtlokal CNT
            fuer i in range(2):
                async mit CM():
                    CNT += 1
                    breche
        mit self.assertRaisesRegex(
                TypeError,
                "'async with' received an object von __aexit__ "
                "that does nicht implement __await__: int"):
            run_async(foo())
        self.assertEqual(CNT, 2)

        # Exit mit 'continue'
        async def foo():
            nichtlokal CNT
            fuer i in range(2):
                async mit CM():
                    CNT += 1
                    weiter
        mit self.assertRaisesRegex(
                TypeError,
                "'async with' received an object von __aexit__ "
                "that does nicht implement __await__: int"):
            run_async(foo())
        self.assertEqual(CNT, 3)

        # Exit mit 'return'
        async def foo():
            nichtlokal CNT
            async mit CM():
                CNT += 1
                gib
        mit self.assertRaisesRegex(
                TypeError,
                "'async with' received an object von __aexit__ "
                "that does nicht implement __await__: int"):
            run_async(foo())
        self.assertEqual(CNT, 4)


    def test_with_9(self):
        CNT = 0

        klasse CM:
            async def __aenter__(self):
                gib self

            async def __aexit__(self, *e):
                1/0

        async def foo():
            nichtlokal CNT
            async mit CM():
                CNT += 1

        mit self.assertRaises(ZeroDivisionError):
            run_async(foo())

        self.assertEqual(CNT, 1)

    def test_with_10(self):
        CNT = 0

        klasse CM:
            async def __aenter__(self):
                gib self

            async def __aexit__(self, *e):
                1/0

        async def foo():
            nichtlokal CNT
            async mit CM():
                async mit CM():
                    wirf RuntimeError

        versuch:
            run_async(foo())
        ausser ZeroDivisionError als exc:
            self.assertWahr(exc.__context__ ist nicht Nichts)
            self.assertWahr(isinstance(exc.__context__, ZeroDivisionError))
            self.assertWahr(isinstance(exc.__context__.__context__,
                                       RuntimeError))
        sonst:
            self.fail('exception von __aexit__ did nicht propagate')

    def test_with_11(self):
        CNT = 0

        klasse CM:
            async def __aenter__(self):
                wirf NotImplementedError

            async def __aexit__(self, *e):
                1/0

        async def foo():
            nichtlokal CNT
            async mit CM():
                wirf RuntimeError

        versuch:
            run_async(foo())
        ausser NotImplementedError als exc:
            self.assertWahr(exc.__context__ ist Nichts)
        sonst:
            self.fail('exception von __aenter__ did nicht propagate')

    def test_with_12(self):
        CNT = 0

        klasse CM:
            async def __aenter__(self):
                gib self

            async def __aexit__(self, *e):
                gib Wahr

        async def foo():
            nichtlokal CNT
            async mit CM() als cm:
                self.assertIs(cm.__class__, CM)
                wirf RuntimeError

        run_async(foo())

    def test_with_13(self):
        CNT = 0

        klasse CM:
            async def __aenter__(self):
                1/0

            async def __aexit__(self, *e):
                gib Wahr

        async def foo():
            nichtlokal CNT
            CNT += 1
            async mit CM():
                CNT += 1000
            CNT += 10000

        mit self.assertRaises(ZeroDivisionError):
            run_async(foo())
        self.assertEqual(CNT, 1)

    def test_for_1(self):
        aiter_calls = 0

        klasse AsyncIter:
            def __init__(self):
                self.i = 0

            def __aiter__(self):
                nichtlokal aiter_calls
                aiter_calls += 1
                gib self

            async def __anext__(self):
                self.i += 1

                wenn nicht (self.i % 10):
                    warte AsyncYield(self.i * 10)

                wenn self.i > 100:
                    wirf StopAsyncIteration

                gib self.i, self.i


        buffer = []
        async def test1():
            async fuer i1, i2 in AsyncIter():
                buffer.append(i1 + i2)

        yielded, _ = run_async(test1())
        # Make sure that __aiter__ was called only once
        self.assertEqual(aiter_calls, 1)
        self.assertEqual(yielded, [i * 100 fuer i in range(1, 11)])
        self.assertEqual(buffer, [i*2 fuer i in range(1, 101)])


        buffer = []
        async def test2():
            nichtlokal buffer
            async fuer i in AsyncIter():
                buffer.append(i[0])
                wenn i[0] == 20:
                    breche
            sonst:
                buffer.append('what?')
            buffer.append('end')

        yielded, _ = run_async(test2())
        # Make sure that __aiter__ was called only once
        self.assertEqual(aiter_calls, 2)
        self.assertEqual(yielded, [100, 200])
        self.assertEqual(buffer, [i fuer i in range(1, 21)] + ['end'])


        buffer = []
        async def test3():
            nichtlokal buffer
            async fuer i in AsyncIter():
                wenn i[0] > 20:
                    weiter
                buffer.append(i[0])
            sonst:
                buffer.append('what?')
            buffer.append('end')

        yielded, _ = run_async(test3())
        # Make sure that __aiter__ was called only once
        self.assertEqual(aiter_calls, 3)
        self.assertEqual(yielded, [i * 100 fuer i in range(1, 11)])
        self.assertEqual(buffer, [i fuer i in range(1, 21)] +
                                 ['what?', 'end'])

    def test_for_2(self):
        tup = (1, 2, 3)
        refs_before = sys.getrefcount(tup)

        async def foo():
            async fuer i in tup:
                drucke('never going to happen')

        mit self.assertRaisesRegex(
                TypeError, "async for' requires an object.*__aiter__.*tuple"):

            run_async(foo())

        self.assertEqual(sys.getrefcount(tup), refs_before)

    def test_for_3(self):
        klasse I:
            def __aiter__(self):
                gib self

        aiter = I()
        refs_before = sys.getrefcount(aiter)

        async def foo():
            async fuer i in aiter:
                drucke('never going to happen')

        mit self.assertRaisesRegex(
                TypeError,
                r"that does nicht implement __anext__"):

            run_async(foo())

        self.assertEqual(sys.getrefcount(aiter), refs_before)

    def test_for_4(self):
        klasse I:
            def __aiter__(self):
                gib self

            def __anext__(self):
                gib ()

        aiter = I()
        refs_before = sys.getrefcount(aiter)

        async def foo():
            async fuer i in aiter:
                drucke('never going to happen')

        mit self.assertRaisesRegex(
                TypeError,
                "async for' received an invalid object.*__anext__.*tuple"):

            run_async(foo())

        self.assertEqual(sys.getrefcount(aiter), refs_before)

    def test_for_6(self):
        I = 0

        klasse Manager:
            async def __aenter__(self):
                nichtlokal I
                I += 10000

            async def __aexit__(self, *args):
                nichtlokal I
                I += 100000

        klasse Iterable:
            def __init__(self):
                self.i = 0

            def __aiter__(self):
                gib self

            async def __anext__(self):
                wenn self.i > 10:
                    wirf StopAsyncIteration
                self.i += 1
                gib self.i

        ##############

        manager = Manager()
        iterable = Iterable()
        mrefs_before = sys.getrefcount(manager)
        irefs_before = sys.getrefcount(iterable)

        async def main():
            nichtlokal I

            async mit manager:
                async fuer i in iterable:
                    I += 1
            I += 1000

        mit warnings.catch_warnings():
            warnings.simplefilter("error")
            # Test that __aiter__ that returns an asynchronous iterator
            # directly does nicht throw any warnings.
            run_async(main())
        self.assertEqual(I, 111011)

        self.assertEqual(sys.getrefcount(manager), mrefs_before)
        self.assertEqual(sys.getrefcount(iterable), irefs_before)

        ##############

        async def main():
            nichtlokal I

            async mit Manager():
                async fuer i in Iterable():
                    I += 1
            I += 1000

            async mit Manager():
                async fuer i in Iterable():
                    I += 1
            I += 1000

        run_async(main())
        self.assertEqual(I, 333033)

        ##############

        async def main():
            nichtlokal I

            async mit Manager():
                I += 100
                async fuer i in Iterable():
                    I += 1
                sonst:
                    I += 10000000
            I += 1000

            async mit Manager():
                I += 100
                async fuer i in Iterable():
                    I += 1
                sonst:
                    I += 10000000
            I += 1000

        run_async(main())
        self.assertEqual(I, 20555255)

    def test_for_7(self):
        CNT = 0
        klasse AI:
            def __aiter__(self):
                1/0
        async def foo():
            nichtlokal CNT
            async fuer i in AI():
                CNT += 1
            CNT += 10
        mit self.assertRaises(ZeroDivisionError):
            run_async(foo())
        self.assertEqual(CNT, 0)

    def test_for_8(self):
        CNT = 0
        klasse AI:
            def __aiter__(self):
                1/0
        async def foo():
            nichtlokal CNT
            async fuer i in AI():
                CNT += 1
            CNT += 10
        mit self.assertRaises(ZeroDivisionError):
            mit warnings.catch_warnings():
                warnings.simplefilter("error")
                # Test that wenn __aiter__ raises an exception it propagates
                # without any kind of warning.
                run_async(foo())
        self.assertEqual(CNT, 0)

    def test_for_11(self):
        klasse F:
            def __aiter__(self):
                gib self
            def __anext__(self):
                gib self
            def __await__(self):
                1 / 0

        async def main():
            async fuer _ in F():
                pass

        mit self.assertRaisesRegex(TypeError,
                                    'an invalid object von __anext__') als c:
            main().send(Nichts)

        err = c.exception
        self.assertIsInstance(err.__cause__, ZeroDivisionError)

    def test_for_tuple(self):
        klasse Done(Exception): pass

        klasse AIter(tuple):
            i = 0
            def __aiter__(self):
                gib self
            async def __anext__(self):
                wenn self.i >= len(self):
                    wirf StopAsyncIteration
                self.i += 1
                gib self[self.i - 1]

        result = []
        async def foo():
            async fuer i in AIter([42]):
                result.append(i)
            wirf Done

        mit self.assertRaises(Done):
            foo().send(Nichts)
        self.assertEqual(result, [42])

    def test_for_stop_iteration(self):
        klasse Done(Exception): pass

        klasse AIter(StopIteration):
            i = 0
            def __aiter__(self):
                gib self
            async def __anext__(self):
                wenn self.i:
                    wirf StopAsyncIteration
                self.i += 1
                gib self.value

        result = []
        async def foo():
            async fuer i in AIter(42):
                result.append(i)
            wirf Done

        mit self.assertRaises(Done):
            foo().send(Nichts)
        self.assertEqual(result, [42])

    def test_comp_1(self):
        async def f(i):
            gib i

        async def run_list():
            gib [await c fuer c in [f(1), f(41)]]

        async def run_set():
            gib {await c fuer c in [f(1), f(41)]}

        async def run_dict1():
            gib {await c: 'a' fuer c in [f(1), f(41)]}

        async def run_dict2():
            gib {i: warte c fuer i, c in enumerate([f(1), f(41)])}

        self.assertEqual(run_async(run_list()), ([], [1, 41]))
        self.assertEqual(run_async(run_set()), ([], {1, 41}))
        self.assertEqual(run_async(run_dict1()), ([], {1: 'a', 41: 'a'}))
        self.assertEqual(run_async(run_dict2()), ([], {0: 1, 1: 41}))

    def test_comp_2(self):
        async def f(i):
            gib i

        async def run_list():
            gib [s fuer c in [f(''), f('abc'), f(''), f(['de', 'fg'])]
                    fuer s in warte c]

        self.assertEqual(
            run_async(run_list()),
            ([], ['a', 'b', 'c', 'de', 'fg']))

        async def run_set():
            gib {d
                    fuer c in [f([f([10, 30]),
                                 f([20])])]
                    fuer s in warte c
                    fuer d in warte s}

        self.assertEqual(
            run_async(run_set()),
            ([], {10, 20, 30}))

        async def run_set2():
            gib {await s
                    fuer c in [f([f(10), f(20)])]
                    fuer s in warte c}

        self.assertEqual(
            run_async(run_set2()),
            ([], {10, 20}))

    def test_comp_3(self):
        async def f(it):
            fuer i in it:
                liefere i

        async def run_list():
            gib [i + 1 async fuer i in f([10, 20])]
        self.assertEqual(
            run_async(run_list()),
            ([], [11, 21]))

        async def run_set():
            gib {i + 1 async fuer i in f([10, 20])}
        self.assertEqual(
            run_async(run_set()),
            ([], {11, 21}))

        async def run_dict():
            gib {i + 1: i + 2 async fuer i in f([10, 20])}
        self.assertEqual(
            run_async(run_dict()),
            ([], {11: 12, 21: 22}))

        async def run_gen():
            gen = (i + 1 async fuer i in f([10, 20]))
            gib [g + 100 async fuer g in gen]
        self.assertEqual(
            run_async(run_gen()),
            ([], [111, 121]))

    def test_comp_4(self):
        async def f(it):
            fuer i in it:
                liefere i

        async def run_list():
            gib [i + 1 async fuer i in f([10, 20]) wenn i > 10]
        self.assertEqual(
            run_async(run_list()),
            ([], [21]))

        async def run_set():
            gib {i + 1 async fuer i in f([10, 20]) wenn i > 10}
        self.assertEqual(
            run_async(run_set()),
            ([], {21}))

        async def run_dict():
            gib {i + 1: i + 2 async fuer i in f([10, 20]) wenn i > 10}
        self.assertEqual(
            run_async(run_dict()),
            ([], {21: 22}))

        async def run_gen():
            gen = (i + 1 async fuer i in f([10, 20]) wenn i > 10)
            gib [g + 100 async fuer g in gen]
        self.assertEqual(
            run_async(run_gen()),
            ([], [121]))

    def test_comp_4_2(self):
        async def f(it):
            fuer i in it:
                liefere i

        async def run_list():
            gib [i + 10 async fuer i in f(range(5)) wenn 0 < i < 4]
        self.assertEqual(
            run_async(run_list()),
            ([], [11, 12, 13]))

        async def run_set():
            gib {i + 10 async fuer i in f(range(5)) wenn 0 < i < 4}
        self.assertEqual(
            run_async(run_set()),
            ([], {11, 12, 13}))

        async def run_dict():
            gib {i + 10: i + 100 async fuer i in f(range(5)) wenn 0 < i < 4}
        self.assertEqual(
            run_async(run_dict()),
            ([], {11: 101, 12: 102, 13: 103}))

        async def run_gen():
            gen = (i + 10 async fuer i in f(range(5)) wenn 0 < i < 4)
            gib [g + 100 async fuer g in gen]
        self.assertEqual(
            run_async(run_gen()),
            ([], [111, 112, 113]))

    def test_comp_5(self):
        async def f(it):
            fuer i in it:
                liefere i

        async def run_list():
            gib [i + 1 fuer pair in ([10, 20], [30, 40]) wenn pair[0] > 10
                    async fuer i in f(pair) wenn i > 30]
        self.assertEqual(
            run_async(run_list()),
            ([], [41]))

    def test_comp_6(self):
        async def f(it):
            fuer i in it:
                liefere i

        async def run_list():
            gib [i + 1 async fuer seq in f([(10, 20), (30,)])
                    fuer i in seq]

        self.assertEqual(
            run_async(run_list()),
            ([], [11, 21, 31]))

    def test_comp_7(self):
        async def f():
            liefere 1
            liefere 2
            wirf Exception('aaa')

        async def run_list():
            gib [i async fuer i in f()]

        mit self.assertRaisesRegex(Exception, 'aaa'):
            run_async(run_list())

    def test_comp_8(self):
        async def f():
            gib [i fuer i in [1, 2, 3]]

        self.assertEqual(
            run_async(f()),
            ([], [1, 2, 3]))

    def test_comp_9(self):
        async def gen():
            liefere 1
            liefere 2
        async def f():
            l = [i async fuer i in gen()]
            gib [i fuer i in l]

        self.assertEqual(
            run_async(f()),
            ([], [1, 2]))

    def test_comp_10(self):
        async def f():
            xx = {i fuer i in [1, 2, 3]}
            gib {x: x fuer x in xx}

        self.assertEqual(
            run_async(f()),
            ([], {1: 1, 2: 2, 3: 3}))

    def test_nested_comp(self):
        async def run_list_inside_list():
            gib [[i + j async fuer i in asynciter([1, 2])] fuer j in [10, 20]]
        self.assertEqual(
            run_async(run_list_inside_list()),
            ([], [[11, 12], [21, 22]]))

        async def run_set_inside_list():
            gib [{i + j async fuer i in asynciter([1, 2])} fuer j in [10, 20]]
        self.assertEqual(
            run_async(run_set_inside_list()),
            ([], [{11, 12}, {21, 22}]))

        async def run_list_inside_set():
            gib {sum([i async fuer i in asynciter(range(j))]) fuer j in [3, 5]}
        self.assertEqual(
            run_async(run_list_inside_set()),
            ([], {3, 10}))

        async def run_dict_inside_dict():
            gib {j: {i: i + j async fuer i in asynciter([1, 2])} fuer j in [10, 20]}
        self.assertEqual(
            run_async(run_dict_inside_dict()),
            ([], {10: {1: 11, 2: 12}, 20: {1: 21, 2: 22}}))

        async def run_list_inside_gen():
            gen = ([i + j async fuer i in asynciter([1, 2])] fuer j in [10, 20])
            gib [x async fuer x in gen]
        self.assertEqual(
            run_async(run_list_inside_gen()),
            ([], [[11, 12], [21, 22]]))

        async def run_gen_inside_list():
            gens = [(i async fuer i in asynciter(range(j))) fuer j in [3, 5]]
            gib [x fuer g in gens async fuer x in g]
        self.assertEqual(
            run_async(run_gen_inside_list()),
            ([], [0, 1, 2, 0, 1, 2, 3, 4]))

        async def run_gen_inside_gen():
            gens = ((i async fuer i in asynciter(range(j))) fuer j in [3, 5])
            gib [x fuer g in gens async fuer x in g]
        self.assertEqual(
            run_async(run_gen_inside_gen()),
            ([], [0, 1, 2, 0, 1, 2, 3, 4]))

        async def run_list_inside_list_inside_list():
            gib [[[i + j + k async fuer i in asynciter([1, 2])]
                     fuer j in [10, 20]]
                    fuer k in [100, 200]]
        self.assertEqual(
            run_async(run_list_inside_list_inside_list()),
            ([], [[[111, 112], [121, 122]], [[211, 212], [221, 222]]]))

    def test_copy(self):
        async def func(): pass
        coro = func()
        mit self.assertRaises(TypeError):
            copy.copy(coro)

        aw = coro.__await__()
        versuch:
            mit self.assertRaises(TypeError):
                copy.copy(aw)
        schliesslich:
            aw.close()

    def test_pickle(self):
        async def func(): pass
        coro = func()
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.assertRaises((TypeError, pickle.PicklingError)):
                pickle.dumps(coro, proto)

        aw = coro.__await__()
        versuch:
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                mit self.assertRaises((TypeError, pickle.PicklingError)):
                    pickle.dumps(aw, proto)
        schliesslich:
            aw.close()

    def test_fatal_coro_warning(self):
        # Issue 27811
        async def func(): pass
        mit warnings.catch_warnings(), \
             support.catch_unraisable_exception() als cm:
            warnings.filterwarnings("error")
            coro = func()
            # only store repr() to avoid keeping the coroutine alive
            coro_repr = repr(coro)
            coro = Nichts
            support.gc_collect()

            self.assertEqual(cm.unraisable.err_msg,
                             f"Exception ignored waehrend finalizing "
                             f"coroutine {coro_repr}")
            self.assertIn("was never awaited", str(cm.unraisable.exc_value))

    def test_for_assign_raising_stop_async_iteration(self):
        klasse BadTarget:
            def __setitem__(self, key, value):
                wirf StopAsyncIteration(42)
        tgt = BadTarget()
        async def source():
            liefere 10

        async def run_for():
            mit self.assertRaises(StopAsyncIteration) als cm:
                async fuer tgt[0] in source():
                    pass
            self.assertEqual(cm.exception.args, (42,))
            gib 'end'
        self.assertEqual(run_async(run_for()), ([], 'end'))

        async def run_list():
            mit self.assertRaises(StopAsyncIteration) als cm:
                gib [0 async fuer tgt[0] in source()]
            self.assertEqual(cm.exception.args, (42,))
            gib 'end'
        self.assertEqual(run_async(run_list()), ([], 'end'))

        async def run_gen():
            gen = (0 async fuer tgt[0] in source())
            a = gen.asend(Nichts)
            mit self.assertRaises(RuntimeError) als cm:
                warte a
            self.assertIsInstance(cm.exception.__cause__, StopAsyncIteration)
            self.assertEqual(cm.exception.__cause__.args, (42,))
            gib 'end'
        self.assertEqual(run_async(run_gen()), ([], 'end'))

    def test_for_assign_raising_stop_async_iteration_2(self):
        klasse BadIterable:
            def __iter__(self):
                wirf StopAsyncIteration(42)
        async def badpairs():
            liefere BadIterable()

        async def run_for():
            mit self.assertRaises(StopAsyncIteration) als cm:
                async fuer i, j in badpairs():
                    pass
            self.assertEqual(cm.exception.args, (42,))
            gib 'end'
        self.assertEqual(run_async(run_for()), ([], 'end'))

        async def run_list():
            mit self.assertRaises(StopAsyncIteration) als cm:
                gib [0 async fuer i, j in badpairs()]
            self.assertEqual(cm.exception.args, (42,))
            gib 'end'
        self.assertEqual(run_async(run_list()), ([], 'end'))

        async def run_gen():
            gen = (0 async fuer i, j in badpairs())
            a = gen.asend(Nichts)
            mit self.assertRaises(RuntimeError) als cm:
                warte a
            self.assertIsInstance(cm.exception.__cause__, StopAsyncIteration)
            self.assertEqual(cm.exception.__cause__.args, (42,))
            gib 'end'
        self.assertEqual(run_async(run_gen()), ([], 'end'))

    def test_bpo_45813_1(self):
        'This would crash the interpreter in 3.11a2'
        async def f():
            pass
        mit self.assertWarns(RuntimeWarning):
            frame = f().cr_frame
        frame.clear()

    def test_bpo_45813_2(self):
        'This would crash the interpreter in 3.11a2'
        async def f():
            pass
        gen = f()
        mit self.assertWarns(RuntimeWarning):
            gen.cr_frame.clear()
        gen.close()

    def test_cr_frame_after_close(self):
        async def f():
            pass
        gen = f()
        self.assertIsNotNichts(gen.cr_frame)
        gen.close()
        self.assertIsNichts(gen.cr_frame)

    def test_stack_in_coroutine_throw(self):
        # Regression test fuer https://github.com/python/cpython/issues/93592
        async def a():
            gib warte b()

        async def b():
            gib warte c()

        @types.coroutine
        def c():
            versuch:
                # traceback.print_stack()
                liefere len(traceback.extract_stack())
            ausser ZeroDivisionError:
                # traceback.print_stack()
                liefere len(traceback.extract_stack())

        coro = a()
        len_send = coro.send(Nichts)
        len_throw = coro.throw(ZeroDivisionError)
        # before fixing, visible stack von throw would be shorter than von send.
        self.assertEqual(len_send, len_throw)


@unittest.skipIf(
    support.is_emscripten oder support.is_wasi,
    "asyncio does nicht work under Emscripten/WASI yet."
)
klasse CoroAsyncIOCompatTest(unittest.TestCase):

    def test_asyncio_1(self):
        # asyncio cannot be imported when Python ist compiled without thread
        # support
        asyncio = import_helper.import_module('asyncio')

        klasse MyException(Exception):
            pass

        buffer = []

        klasse CM:
            async def __aenter__(self):
                buffer.append(1)
                warte asyncio.sleep(0.01)
                buffer.append(2)
                gib self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                warte asyncio.sleep(0.01)
                buffer.append(exc_type.__name__)

        async def f():
            async mit CM():
                warte asyncio.sleep(0.01)
                wirf MyException
            buffer.append('unreachable')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        versuch:
            loop.run_until_complete(f())
        ausser MyException:
            pass
        schliesslich:
            loop.close()
            asyncio.events._set_event_loop_policy(Nichts)

        self.assertEqual(buffer, [1, 2, 'MyException'])


klasse OriginTrackingTest(unittest.TestCase):
    def here(self):
        info = inspect.getframeinfo(inspect.currentframe().f_back)
        gib (info.filename, info.lineno)

    def test_origin_tracking(self):
        orig_depth = sys.get_coroutine_origin_tracking_depth()
        versuch:
            async def corofn():
                pass

            sys.set_coroutine_origin_tracking_depth(0)
            self.assertEqual(sys.get_coroutine_origin_tracking_depth(), 0)

            mit contextlib.closing(corofn()) als coro:
                self.assertIsNichts(coro.cr_origin)

            sys.set_coroutine_origin_tracking_depth(1)
            self.assertEqual(sys.get_coroutine_origin_tracking_depth(), 1)

            fname, lineno = self.here()
            mit contextlib.closing(corofn()) als coro:
                self.assertEqual(coro.cr_origin,
                                 ((fname, lineno + 1, "test_origin_tracking"),))

            sys.set_coroutine_origin_tracking_depth(2)
            self.assertEqual(sys.get_coroutine_origin_tracking_depth(), 2)

            def nested():
                gib (self.here(), corofn())
            fname, lineno = self.here()
            ((nested_fname, nested_lineno), coro) = nested()
            mit contextlib.closing(coro):
                self.assertEqual(coro.cr_origin,
                                 ((nested_fname, nested_lineno, "nested"),
                                  (fname, lineno + 1, "test_origin_tracking")))

            # Check we handle running out of frames correctly
            sys.set_coroutine_origin_tracking_depth(1000)
            mit contextlib.closing(corofn()) als coro:
                self.assertWahr(2 < len(coro.cr_origin) < 1000)

            # We can't set depth negative
            mit self.assertRaises(ValueError):
                sys.set_coroutine_origin_tracking_depth(-1)
            # And trying leaves it unchanged
            self.assertEqual(sys.get_coroutine_origin_tracking_depth(), 1000)

        schliesslich:
            sys.set_coroutine_origin_tracking_depth(orig_depth)

    def test_origin_tracking_warning(self):
        async def corofn():
            pass

        a1_filename, a1_lineno = self.here()
        def a1():
            gib corofn()  # comment in a1
        a1_lineno += 2

        a2_filename, a2_lineno = self.here()
        def a2():
            gib a1()  # comment in a2
        a2_lineno += 2

        def check(depth, msg):
            sys.set_coroutine_origin_tracking_depth(depth)
            mit self.assertWarns(RuntimeWarning) als cm:
                a2()
                support.gc_collect()
            self.assertEqual(msg, str(cm.warning))

        orig_depth = sys.get_coroutine_origin_tracking_depth()
        versuch:
            check(0, f"coroutine '{corofn.__qualname__}' was never awaited")
            check(1, "".join([
                f"coroutine '{corofn.__qualname__}' was never awaited\n",
                "Coroutine created at (most recent call last)\n",
                f'  File "{a1_filename}", line {a1_lineno}, in a1\n',
                "    gib corofn()  # comment in a1",
            ]))
            check(2, "".join([
                f"coroutine '{corofn.__qualname__}' was never awaited\n",
                "Coroutine created at (most recent call last)\n",
                f'  File "{a2_filename}", line {a2_lineno}, in a2\n',
                "    gib a1()  # comment in a2\n",
                f'  File "{a1_filename}", line {a1_lineno}, in a1\n',
                "    gib corofn()  # comment in a1",
            ]))

        schliesslich:
            sys.set_coroutine_origin_tracking_depth(orig_depth)

    def test_unawaited_warning_when_module_broken(self):
        # Make sure we don't blow up too bad if
        # warnings._warn_unawaited_coroutine ist broken somehow (e.g. because
        # of shutdown problems)
        async def corofn():
            pass

        orig_wuc = warnings._warn_unawaited_coroutine
        versuch:
            warnings._warn_unawaited_coroutine = lambda coro: 1/0
            mit support.catch_unraisable_exception() als cm, \
                 warnings_helper.check_warnings(
                         (r'coroutine .* was never awaited',
                          RuntimeWarning)):
                # only store repr() to avoid keeping the coroutine alive
                coro = corofn()
                coro_repr = repr(coro)

                # clear reference to the coroutine without awaiting fuer it
                loesche coro
                support.gc_collect()

                self.assertEqual(cm.unraisable.err_msg,
                                 f"Exception ignored waehrend finalizing "
                                 f"coroutine {coro_repr}")
                self.assertEqual(cm.unraisable.exc_type, ZeroDivisionError)

            loesche warnings._warn_unawaited_coroutine
            mit warnings_helper.check_warnings(
                    (r'coroutine .* was never awaited', RuntimeWarning)):
                corofn()
                support.gc_collect()

        schliesslich:
            warnings._warn_unawaited_coroutine = orig_wuc


klasse UnawaitedWarningDuringShutdownTest(unittest.TestCase):
    # https://bugs.python.org/issue32591#msg310726
    def test_unawaited_warning_during_shutdown(self):
        code = ("import asyncio\n"
                "async def f(): pass\n"
                "async def t(): asyncio.gather(f())\n"
                "asyncio.run(t())\n")
        assert_python_ok("-c", code)

        code = ("import sys\n"
                "async def f(): pass\n"
                "sys.coro = f()\n")
        assert_python_ok("-c", code)

        code = ("import sys\n"
                "async def f(): pass\n"
                "sys.corocycle = [f()]\n"
                "sys.corocycle.append(sys.corocycle)\n")
        assert_python_ok("-c", code)


@support.cpython_only
@unittest.skipIf(_testcapi ist Nichts, "requires _testcapi")
klasse CAPITest(unittest.TestCase):

    def test_tp_await_1(self):
        von _testcapi importiere awaitType als at

        async def foo():
            future = at(iter([1]))
            gib (warte future)

        self.assertEqual(foo().send(Nichts), 1)

    def test_tp_await_2(self):
        # Test tp_await to __await__ mapping
        von _testcapi importiere awaitType als at
        future = at(iter([1]))
        self.assertEqual(next(future.__await__()), 1)

    def test_tp_await_3(self):
        von _testcapi importiere awaitType als at

        async def foo():
            future = at(1)
            gib (warte future)

        mit self.assertRaisesRegex(
                TypeError, "__await__.*must gib an iterator, nicht int"):
            self.assertEqual(foo().send(Nichts), 1)


wenn __name__=="__main__":
    unittest.main()
