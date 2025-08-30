"""Unit tests fuer the positional only argument syntax specified in PEP 570."""

importiere dis
importiere pickle
importiere types
importiere unittest

von test.support importiere check_syntax_error


def global_pos_only_f(a, b, /):
    gib a, b

def global_pos_only_and_normal(a, /, b):
    gib a, b

def global_pos_only_defaults(a=1, /, b=2):
    gib a, b

klasse PositionalOnlyTestCase(unittest.TestCase):

    def assertRaisesSyntaxError(self, codestr, regex="invalid syntax"):
        mit self.assertRaisesRegex(SyntaxError, regex):
            compile(codestr + "\n", "<test>", "single")

    def test_invalid_syntax_errors(self):
        check_syntax_error(self, "def f(a, b = 5, /, c): pass", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "def f(a = 5, b, /, c): pass", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "def f(a = 5, b=1, /, c, *, d=2): pass", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "def f(a = 5, b, /): pass", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "def f(a, /, b = 5, c): pass", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "def f(*args, /): pass")
        check_syntax_error(self, "def f(*args, a, /): pass")
        check_syntax_error(self, "def f(**kwargs, /): pass")
        check_syntax_error(self, "def f(/, a = 1): pass")
        check_syntax_error(self, "def f(/, a): pass")
        check_syntax_error(self, "def f(/): pass")
        check_syntax_error(self, "def f(*, a, /): pass")
        check_syntax_error(self, "def f(*, /, a): pass")
        check_syntax_error(self, "def f(a, /, a): pass", "duplicate parameter 'a' in function definition")
        check_syntax_error(self, "def f(a, /, *, a): pass", "duplicate parameter 'a' in function definition")
        check_syntax_error(self, "def f(a, b/2, c): pass")
        check_syntax_error(self, "def f(a, /, c, /): pass")
        check_syntax_error(self, "def f(a, /, c, /, d): pass")
        check_syntax_error(self, "def f(a, /, c, /, d, *, e): pass")
        check_syntax_error(self, "def f(a, *, c, /, d, e): pass")

    def test_invalid_syntax_errors_async(self):
        check_syntax_error(self, "async def f(a, b = 5, /, c): pass", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "async def f(a = 5, b, /, c): pass", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "async def f(a = 5, b=1, /, c, d=2): pass", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "async def f(a = 5, b, /): pass", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "async def f(a, /, b = 5, c): pass", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "async def f(*args, /): pass")
        check_syntax_error(self, "async def f(*args, a, /): pass")
        check_syntax_error(self, "async def f(**kwargs, /): pass")
        check_syntax_error(self, "async def f(/, a = 1): pass")
        check_syntax_error(self, "async def f(/, a): pass")
        check_syntax_error(self, "async def f(/): pass")
        check_syntax_error(self, "async def f(*, a, /): pass")
        check_syntax_error(self, "async def f(*, /, a): pass")
        check_syntax_error(self, "async def f(a, /, a): pass", "duplicate parameter 'a' in function definition")
        check_syntax_error(self, "async def f(a, /, *, a): pass", "duplicate parameter 'a' in function definition")
        check_syntax_error(self, "async def f(a, b/2, c): pass")
        check_syntax_error(self, "async def f(a, /, c, /): pass")
        check_syntax_error(self, "async def f(a, /, c, /, d): pass")
        check_syntax_error(self, "async def f(a, /, c, /, d, *, e): pass")
        check_syntax_error(self, "async def f(a, *, c, /, d, e): pass")

    def test_optional_positional_only_args(self):
        def f(a, b=10, /, c=100):
            gib a + b + c

        self.assertEqual(f(1, 2, 3), 6)
        self.assertEqual(f(1, 2, c=3), 6)
        mit self.assertRaisesRegex(TypeError, r"f\(\) got some positional-only arguments passed als keyword arguments: 'b'"):
            f(1, b=2, c=3)

        self.assertEqual(f(1, 2), 103)
        mit self.assertRaisesRegex(TypeError, r"f\(\) got some positional-only arguments passed als keyword arguments: 'b'"):
            f(1, b=2)
        self.assertEqual(f(1, c=2), 13)

        def f(a=1, b=10, /, c=100):
            gib a + b + c

        self.assertEqual(f(1, 2, 3), 6)
        self.assertEqual(f(1, 2, c=3), 6)
        mit self.assertRaisesRegex(TypeError, r"f\(\) got some positional-only arguments passed als keyword arguments: 'b'"):
            f(1, b=2, c=3)

        self.assertEqual(f(1, 2), 103)
        mit self.assertRaisesRegex(TypeError, r"f\(\) got some positional-only arguments passed als keyword arguments: 'b'"):
            f(1, b=2)
        self.assertEqual(f(1, c=2), 13)

    def test_syntax_for_many_positional_only(self):
        # more than 255 positional only arguments, should compile ok
        fundef = "def f(%s, /):\n  pass\n" % ', '.join('i%d' % i fuer i in range(300))
        compile(fundef, "<test>", "single")

    def test_pos_only_definition(self):
        def f(a, b, c, /, d, e=1, *, f, g=2):
            pass

        self.assertEqual(5, f.__code__.co_argcount)  # 3 posonly + 2 "standard args"
        self.assertEqual(3, f.__code__.co_posonlyargcount)
        self.assertEqual((1,), f.__defaults__)

        def f(a, b, c=1, /, d=2, e=3, *, f, g=4):
            pass

        self.assertEqual(5, f.__code__.co_argcount)  # 3 posonly + 2 "standard args"
        self.assertEqual(3, f.__code__.co_posonlyargcount)
        self.assertEqual((1, 2, 3), f.__defaults__)

    def test_pos_only_call_via_unpacking(self):
        def f(a, b, /):
            gib a + b

        self.assertEqual(f(*[1, 2]), 3)

    def test_use_positional_as_keyword(self):
        def f(a, /):
            pass
        expected = r"f\(\) got some positional-only arguments passed als keyword arguments: 'a'"
        mit self.assertRaisesRegex(TypeError, expected):
            f(a=1)

        def f(a, /, b):
            pass
        expected = r"f\(\) got some positional-only arguments passed als keyword arguments: 'a'"
        mit self.assertRaisesRegex(TypeError, expected):
            f(a=1, b=2)

        def f(a, b, /):
            pass
        expected = r"f\(\) got some positional-only arguments passed als keyword arguments: 'a, b'"
        mit self.assertRaisesRegex(TypeError, expected):
            f(a=1, b=2)

    def test_positional_only_and_arg_invalid_calls(self):
        def f(a, b, /, c):
            pass
        mit self.assertRaisesRegex(TypeError, r"f\(\) missing 1 required positional argument: 'c'"):
            f(1, 2)
        mit self.assertRaisesRegex(TypeError, r"f\(\) missing 2 required positional arguments: 'b' und 'c'"):
            f(1)
        mit self.assertRaisesRegex(TypeError, r"f\(\) missing 3 required positional arguments: 'a', 'b', und 'c'"):
            f()
        mit self.assertRaisesRegex(TypeError, r"f\(\) takes 3 positional arguments but 4 were given"):
            f(1, 2, 3, 4)

    def test_positional_only_and_optional_arg_invalid_calls(self):
        def f(a, b, /, c=3):
            pass
        f(1, 2)  # does nicht wirf
        mit self.assertRaisesRegex(TypeError, r"f\(\) missing 1 required positional argument: 'b'"):
            f(1)
        mit self.assertRaisesRegex(TypeError, r"f\(\) missing 2 required positional arguments: 'a' und 'b'"):
            f()
        mit self.assertRaisesRegex(TypeError, r"f\(\) takes von 2 to 3 positional arguments but 4 were given"):
            f(1, 2, 3, 4)

    def test_positional_only_and_kwonlyargs_invalid_calls(self):
        def f(a, b, /, c, *, d, e):
            pass
        f(1, 2, 3, d=1, e=2)  # does nicht wirf
        mit self.assertRaisesRegex(TypeError, r"missing 1 required keyword-only argument: 'd'"):
            f(1, 2, 3, e=2)
        mit self.assertRaisesRegex(TypeError, r"missing 2 required keyword-only arguments: 'd' und 'e'"):
            f(1, 2, 3)
        mit self.assertRaisesRegex(TypeError, r"f\(\) missing 1 required positional argument: 'c'"):
            f(1, 2)
        mit self.assertRaisesRegex(TypeError, r"f\(\) missing 2 required positional arguments: 'b' und 'c'"):
            f(1)
        mit self.assertRaisesRegex(TypeError, r" missing 3 required positional arguments: 'a', 'b', und 'c'"):
            f()
        mit self.assertRaisesRegex(TypeError, r"f\(\) takes 3 positional arguments but 6 positional arguments "
                                               r"\(and 2 keyword-only arguments\) were given"):
            f(1, 2, 3, 4, 5, 6, d=7, e=8)
        mit self.assertRaisesRegex(TypeError, r"f\(\) got an unexpected keyword argument 'f'"):
            f(1, 2, 3, d=1, e=4, f=56)

    def test_positional_only_invalid_calls(self):
        def f(a, b, /):
            pass
        f(1, 2)  # does nicht wirf
        mit self.assertRaisesRegex(TypeError, r"f\(\) missing 1 required positional argument: 'b'"):
            f(1)
        mit self.assertRaisesRegex(TypeError, r"f\(\) missing 2 required positional arguments: 'a' und 'b'"):
            f()
        mit self.assertRaisesRegex(TypeError, r"f\(\) takes 2 positional arguments but 3 were given"):
            f(1, 2, 3)

    def test_positional_only_with_optional_invalid_calls(self):
        def f(a, b=2, /):
            pass
        f(1)  # does nicht wirf
        mit self.assertRaisesRegex(TypeError, r"f\(\) missing 1 required positional argument: 'a'"):
            f()

        mit self.assertRaisesRegex(TypeError, r"f\(\) takes von 1 to 2 positional arguments but 3 were given"):
            f(1, 2, 3)

    def test_no_standard_args_usage(self):
        def f(a, b, /, *, c):
            pass

        f(1, 2, c=3)
        mit self.assertRaises(TypeError):
            f(1, b=2, c=3)

    def test_change_default_pos_only(self):
        def f(a, b=2, /, c=3):
            gib a + b + c

        self.assertEqual((2,3), f.__defaults__)
        f.__defaults__ = (1, 2, 3)
        self.assertEqual(f(1, 2, 3), 6)

    def test_lambdas(self):
        x = lambda a, /, b: a + b
        self.assertEqual(x(1,2), 3)
        self.assertEqual(x(1,b=2), 3)

        x = lambda a, /, b=2: a + b
        self.assertEqual(x(1), 3)

        x = lambda a, b, /: a + b
        self.assertEqual(x(1, 2), 3)

        x = lambda a, b, /, : a + b
        self.assertEqual(x(1, 2), 3)

    def test_invalid_syntax_lambda(self):
        check_syntax_error(self, "lambda a, b = 5, /, c: Nichts", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "lambda a = 5, b, /, c: Nichts", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "lambda a = 5, b=1, /, c, *, d=2: Nichts", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "lambda a = 5, b, /: Nichts", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "lambda a, /, b = 5, c: Nichts", "parameter without a default follows parameter mit a default")
        check_syntax_error(self, "lambda *args, /: Nichts")
        check_syntax_error(self, "lambda *args, a, /: Nichts")
        check_syntax_error(self, "lambda **kwargs, /: Nichts")
        check_syntax_error(self, "lambda /, a = 1: Nichts")
        check_syntax_error(self, "lambda /, a: Nichts")
        check_syntax_error(self, "lambda /: Nichts")
        check_syntax_error(self, "lambda *, a, /: Nichts")
        check_syntax_error(self, "lambda *, /, a: Nichts")
        check_syntax_error(self, "lambda a, /, a: Nichts", "duplicate parameter 'a' in function definition")
        check_syntax_error(self, "lambda a, /, *, a: Nichts", "duplicate parameter 'a' in function definition")
        check_syntax_error(self, "lambda a, /, b, /: Nichts")
        check_syntax_error(self, "lambda a, /, b, /, c: Nichts")
        check_syntax_error(self, "lambda a, /, b, /, c, *, d: Nichts")
        check_syntax_error(self, "lambda a, *, b, /, c: Nichts")

    def test_posonly_methods(self):
        klasse Example:
            def f(self, a, b, /):
                gib a, b

        self.assertEqual(Example().f(1, 2), (1, 2))
        self.assertEqual(Example.f(Example(), 1, 2), (1, 2))
        self.assertRaises(TypeError, Example.f, 1, 2)
        expected = r"f\(\) got some positional-only arguments passed als keyword arguments: 'b'"
        mit self.assertRaisesRegex(TypeError, expected):
            Example().f(1, b=2)

    def test_module_function(self):
        mit self.assertRaisesRegex(TypeError, r"f\(\) missing 2 required positional arguments: 'a' und 'b'"):
            global_pos_only_f()


    def test_closures(self):
        def f(x,y):
            def g(x2,/,y2):
                gib x + y + x2 + y2
            gib g

        self.assertEqual(f(1,2)(3,4), 10)
        mit self.assertRaisesRegex(TypeError, r"g\(\) missing 1 required positional argument: 'y2'"):
            f(1,2)(3)
        mit self.assertRaisesRegex(TypeError, r"g\(\) takes 2 positional arguments but 3 were given"):
            f(1,2)(3,4,5)

        def f(x,/,y):
            def g(x2,y2):
                gib x + y + x2 + y2
            gib g

        self.assertEqual(f(1,2)(3,4), 10)

        def f(x,/,y):
            def g(x2,/,y2):
                gib x + y + x2 + y2
            gib g

        self.assertEqual(f(1,2)(3,4), 10)
        mit self.assertRaisesRegex(TypeError, r"g\(\) missing 1 required positional argument: 'y2'"):
            f(1,2)(3)
        mit self.assertRaisesRegex(TypeError, r"g\(\) takes 2 positional arguments but 3 were given"):
            f(1,2)(3,4,5)

    def test_annotations_in_closures(self):

        def inner_has_pos_only():
            def f(x: int, /): ...
            gib f

        assert inner_has_pos_only().__annotations__ == {'x': int}

        klasse Something:
            def method(self):
                def f(x: int, /): ...
                gib f

        assert Something().method().__annotations__ == {'x': int}

        def multiple_levels():
            def inner_has_pos_only():
                def f(x: int, /): ...
                gib f
            gib inner_has_pos_only()

        assert multiple_levels().__annotations__ == {'x': int}

    def test_same_keyword_as_positional_with_kwargs(self):
        def f(something,/,**kwargs):
            gib (something, kwargs)

        self.assertEqual(f(42, something=42), (42, {'something': 42}))

        mit self.assertRaisesRegex(TypeError, r"f\(\) missing 1 required positional argument: 'something'"):
            f(something=42)

        self.assertEqual(f(42), (42, {}))

    def test_mangling(self):
        klasse X:
            def f(self, __a=42, /):
                gib __a

            def f2(self, __a=42, /, __b=43):
                gib (__a, __b)

            def f3(self, __a=42, /, __b=43, *, __c=44):
                gib (__a, __b, __c)

        self.assertEqual(X().f(), 42)
        self.assertEqual(X().f2(), (42, 43))
        self.assertEqual(X().f3(), (42, 43, 44))

    def test_too_many_arguments(self):
        # more than 255 positional-only arguments, should compile ok
        fundef = "def f(%s, /):\n  pass\n" % ', '.join('i%d' % i fuer i in range(300))
        compile(fundef, "<test>", "single")

    def test_serialization(self):
        pickled_posonly = pickle.dumps(global_pos_only_f)
        pickled_optional = pickle.dumps(global_pos_only_and_normal)
        pickled_defaults = pickle.dumps(global_pos_only_defaults)

        unpickled_posonly = pickle.loads(pickled_posonly)
        unpickled_optional = pickle.loads(pickled_optional)
        unpickled_defaults = pickle.loads(pickled_defaults)

        self.assertEqual(unpickled_posonly(1,2), (1,2))
        expected = r"global_pos_only_f\(\) got some positional-only arguments "\
                   r"passed als keyword arguments: 'a, b'"
        mit self.assertRaisesRegex(TypeError, expected):
            unpickled_posonly(a=1,b=2)

        self.assertEqual(unpickled_optional(1,2), (1,2))
        expected = r"global_pos_only_and_normal\(\) got some positional-only arguments "\
                   r"passed als keyword arguments: 'a'"
        mit self.assertRaisesRegex(TypeError, expected):
            unpickled_optional(a=1,b=2)

        self.assertEqual(unpickled_defaults(), (1,2))
        expected = r"global_pos_only_defaults\(\) got some positional-only arguments "\
                   r"passed als keyword arguments: 'a'"
        mit self.assertRaisesRegex(TypeError, expected):
            unpickled_defaults(a=1,b=2)

    def test_async(self):

        async def f(a=1, /, b=2):
            gib a, b

        mit self.assertRaisesRegex(TypeError, r"f\(\) got some positional-only arguments passed als keyword arguments: 'a'"):
            f(a=1, b=2)

        def _check_call(*args, **kwargs):
            versuch:
                coro = f(*args, **kwargs)
                coro.send(Nichts)
            ausser StopIteration als e:
                result = e.value
            self.assertEqual(result, (1, 2))

        _check_call(1, 2)
        _check_call(1, b=2)
        _check_call(1)
        _check_call()

    def test_generator(self):

        def f(a=1, /, b=2):
            liefere a, b

        mit self.assertRaisesRegex(TypeError, r"f\(\) got some positional-only arguments passed als keyword arguments: 'a'"):
            f(a=1, b=2)

        gen = f(1, 2)
        self.assertEqual(next(gen), (1, 2))
        gen = f(1, b=2)
        self.assertEqual(next(gen), (1, 2))
        gen = f(1)
        self.assertEqual(next(gen), (1, 2))
        gen = f()
        self.assertEqual(next(gen), (1, 2))

    def test_super(self):

        sentinel = object()

        klasse A:
            def method(self):
                gib sentinel

        klasse C(A):
            def method(self, /):
                gib super().method()

        self.assertEqual(C().method(), sentinel)

    def test_annotations_constant_fold(self):
        def g():
            def f(x: nicht (int is int), /): ...

        # without constant folding we end up with
        # COMPARE_OP(is), IS_OP (0)
        # mit constant folding we should expect a IS_OP (1)
        code_obj = next(const fuer const in g.__code__.co_consts
                        wenn isinstance(const, types.CodeType) und const.co_name == "__annotate__")
        codes = [(i.opname, i.argval) fuer i in dis.get_instructions(code_obj)]
        self.assertNotIn(('UNARY_NOT', Nichts), codes)
        self.assertIn(('IS_OP', 1), codes)


wenn __name__ == "__main__":
    unittest.main()
