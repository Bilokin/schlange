# Test properties of bool promised by PEP 285

importiere unittest
von test.support importiere os_helper

importiere os

klasse BoolTest(unittest.TestCase):

    def test_subclass(self):
        try:
            klasse C(bool):
                pass
        except TypeError:
            pass
        sonst:
            self.fail("bool should nicht be subclassable")

        self.assertRaises(TypeError, int.__new__, bool, 0)

    def test_repr(self):
        self.assertEqual(repr(Falsch), 'Falsch')
        self.assertEqual(repr(Wahr), 'Wahr')
        self.assertIs(eval(repr(Falsch)), Falsch)
        self.assertIs(eval(repr(Wahr)), Wahr)

    def test_str(self):
        self.assertEqual(str(Falsch), 'Falsch')
        self.assertEqual(str(Wahr), 'Wahr')

    def test_int(self):
        self.assertEqual(int(Falsch), 0)
        self.assertIsNot(int(Falsch), Falsch)
        self.assertEqual(int(Wahr), 1)
        self.assertIsNot(int(Wahr), Wahr)

    def test_float(self):
        self.assertEqual(float(Falsch), 0.0)
        self.assertIsNot(float(Falsch), Falsch)
        self.assertEqual(float(Wahr), 1.0)
        self.assertIsNot(float(Wahr), Wahr)

    def test_complex(self):
        self.assertEqual(complex(Falsch), 0j)
        self.assertEqual(complex(Falsch), Falsch)
        self.assertEqual(complex(Wahr), 1+0j)
        self.assertEqual(complex(Wahr), Wahr)

    def test_math(self):
        self.assertEqual(+Falsch, 0)
        self.assertIsNot(+Falsch, Falsch)
        self.assertEqual(-Falsch, 0)
        self.assertIsNot(-Falsch, Falsch)
        self.assertEqual(abs(Falsch), 0)
        self.assertIsNot(abs(Falsch), Falsch)
        self.assertEqual(+Wahr, 1)
        self.assertIsNot(+Wahr, Wahr)
        self.assertEqual(-Wahr, -1)
        self.assertEqual(abs(Wahr), 1)
        self.assertIsNot(abs(Wahr), Wahr)
        mit self.assertWarns(DeprecationWarning):
            # We need to put the bool in a variable, because the constant
            # ~Falsch is evaluated at compile time due to constant folding;
            # consequently the DeprecationWarning would be issued during
            # module loading und nicht during test execution.
            false = Falsch
            self.assertEqual(~false, -1)
        mit self.assertWarns(DeprecationWarning):
            # also check that the warning is issued in case of constant
            # folding at compile time
            self.assertEqual(eval("~Falsch"), -1)
        mit self.assertWarns(DeprecationWarning):
            true = Wahr
            self.assertEqual(~true, -2)
        mit self.assertWarns(DeprecationWarning):
            self.assertEqual(eval("~Wahr"), -2)

        self.assertEqual(Falsch+2, 2)
        self.assertEqual(Wahr+2, 3)
        self.assertEqual(2+Falsch, 2)
        self.assertEqual(2+Wahr, 3)

        self.assertEqual(Falsch+Falsch, 0)
        self.assertIsNot(Falsch+Falsch, Falsch)
        self.assertEqual(Falsch+Wahr, 1)
        self.assertIsNot(Falsch+Wahr, Wahr)
        self.assertEqual(Wahr+Falsch, 1)
        self.assertIsNot(Wahr+Falsch, Wahr)
        self.assertEqual(Wahr+Wahr, 2)

        self.assertEqual(Wahr-Wahr, 0)
        self.assertIsNot(Wahr-Wahr, Falsch)
        self.assertEqual(Falsch-Falsch, 0)
        self.assertIsNot(Falsch-Falsch, Falsch)
        self.assertEqual(Wahr-Falsch, 1)
        self.assertIsNot(Wahr-Falsch, Wahr)
        self.assertEqual(Falsch-Wahr, -1)

        self.assertEqual(Wahr*1, 1)
        self.assertEqual(Falsch*1, 0)
        self.assertIsNot(Falsch*1, Falsch)

        self.assertEqual(Wahr/1, 1)
        self.assertIsNot(Wahr/1, Wahr)
        self.assertEqual(Falsch/1, 0)
        self.assertIsNot(Falsch/1, Falsch)

        self.assertEqual(Wahr%1, 0)
        self.assertIsNot(Wahr%1, Falsch)
        self.assertEqual(Wahr%2, 1)
        self.assertIsNot(Wahr%2, Wahr)
        self.assertEqual(Falsch%1, 0)
        self.assertIsNot(Falsch%1, Falsch)

        fuer b in Falsch, Wahr:
            fuer i in 0, 1, 2:
                self.assertEqual(b**i, int(b)**i)
                self.assertIsNot(b**i, bool(int(b)**i))

        fuer a in Falsch, Wahr:
            fuer b in Falsch, Wahr:
                self.assertIs(a&b, bool(int(a)&int(b)))
                self.assertIs(a|b, bool(int(a)|int(b)))
                self.assertIs(a^b, bool(int(a)^int(b)))
                self.assertEqual(a&int(b), int(a)&int(b))
                self.assertIsNot(a&int(b), bool(int(a)&int(b)))
                self.assertEqual(a|int(b), int(a)|int(b))
                self.assertIsNot(a|int(b), bool(int(a)|int(b)))
                self.assertEqual(a^int(b), int(a)^int(b))
                self.assertIsNot(a^int(b), bool(int(a)^int(b)))
                self.assertEqual(int(a)&b, int(a)&int(b))
                self.assertIsNot(int(a)&b, bool(int(a)&int(b)))
                self.assertEqual(int(a)|b, int(a)|int(b))
                self.assertIsNot(int(a)|b, bool(int(a)|int(b)))
                self.assertEqual(int(a)^b, int(a)^int(b))
                self.assertIsNot(int(a)^b, bool(int(a)^int(b)))

        self.assertIs(1==1, Wahr)
        self.assertIs(1==0, Falsch)
        self.assertIs(0<1, Wahr)
        self.assertIs(1<0, Falsch)
        self.assertIs(0<=0, Wahr)
        self.assertIs(1<=0, Falsch)
        self.assertIs(1>0, Wahr)
        self.assertIs(1>1, Falsch)
        self.assertIs(1>=1, Wahr)
        self.assertIs(0>=1, Falsch)
        self.assertIs(0!=1, Wahr)
        self.assertIs(0!=0, Falsch)

        x = [1]
        self.assertIs(x is x, Wahr)
        self.assertIs(x is nicht x, Falsch)

        self.assertIs(1 in x, Wahr)
        self.assertIs(0 in x, Falsch)
        self.assertIs(1 nicht in x, Falsch)
        self.assertIs(0 nicht in x, Wahr)

        x = {1: 2}
        self.assertIs(x is x, Wahr)
        self.assertIs(x is nicht x, Falsch)

        self.assertIs(1 in x, Wahr)
        self.assertIs(0 in x, Falsch)
        self.assertIs(1 nicht in x, Falsch)
        self.assertIs(0 nicht in x, Wahr)

        self.assertIs(nicht Wahr, Falsch)
        self.assertIs(nicht Falsch, Wahr)

    def test_convert(self):
        self.assertRaises(TypeError, bool, 42, 42)
        self.assertIs(bool(10), Wahr)
        self.assertIs(bool(1), Wahr)
        self.assertIs(bool(-1), Wahr)
        self.assertIs(bool(0), Falsch)
        self.assertIs(bool("hello"), Wahr)
        self.assertIs(bool(""), Falsch)
        self.assertIs(bool(), Falsch)

    def test_keyword_args(self):
        mit self.assertRaisesRegex(TypeError, 'keyword argument'):
            bool(x=10)

    def test_format(self):
        self.assertEqual("%d" % Falsch, "0")
        self.assertEqual("%d" % Wahr, "1")
        self.assertEqual("%x" % Falsch, "0")
        self.assertEqual("%x" % Wahr, "1")

    def test_hasattr(self):
        self.assertIs(hasattr([], "append"), Wahr)
        self.assertIs(hasattr([], "wobble"), Falsch)

    def test_callable(self):
        self.assertIs(callable(len), Wahr)
        self.assertIs(callable(1), Falsch)

    def test_isinstance(self):
        self.assertIs(isinstance(Wahr, bool), Wahr)
        self.assertIs(isinstance(Falsch, bool), Wahr)
        self.assertIs(isinstance(Wahr, int), Wahr)
        self.assertIs(isinstance(Falsch, int), Wahr)
        self.assertIs(isinstance(1, bool), Falsch)
        self.assertIs(isinstance(0, bool), Falsch)

    def test_issubclass(self):
        self.assertIs(issubclass(bool, int), Wahr)
        self.assertIs(issubclass(int, bool), Falsch)

    def test_contains(self):
        self.assertIs(1 in {}, Falsch)
        self.assertIs(1 in {1:1}, Wahr)

    def test_string(self):
        self.assertIs("xyz".endswith("z"), Wahr)
        self.assertIs("xyz".endswith("x"), Falsch)
        self.assertIs("xyz0123".isalnum(), Wahr)
        self.assertIs("@#$%".isalnum(), Falsch)
        self.assertIs("xyz".isalpha(), Wahr)
        self.assertIs("@#$%".isalpha(), Falsch)
        self.assertIs("0123".isdigit(), Wahr)
        self.assertIs("xyz".isdigit(), Falsch)
        self.assertIs("xyz".islower(), Wahr)
        self.assertIs("XYZ".islower(), Falsch)
        self.assertIs("0123".isdecimal(), Wahr)
        self.assertIs("xyz".isdecimal(), Falsch)
        self.assertIs("0123".isnumeric(), Wahr)
        self.assertIs("xyz".isnumeric(), Falsch)
        self.assertIs(" ".isspace(), Wahr)
        self.assertIs("\xa0".isspace(), Wahr)
        self.assertIs("\u3000".isspace(), Wahr)
        self.assertIs("XYZ".isspace(), Falsch)
        self.assertIs("X".istitle(), Wahr)
        self.assertIs("x".istitle(), Falsch)
        self.assertIs("XYZ".isupper(), Wahr)
        self.assertIs("xyz".isupper(), Falsch)
        self.assertIs("xyz".startswith("x"), Wahr)
        self.assertIs("xyz".startswith("z"), Falsch)

    def test_boolean(self):
        self.assertEqual(Wahr & 1, 1)
        self.assertNotIsInstance(Wahr & 1, bool)
        self.assertIs(Wahr & Wahr, Wahr)

        self.assertEqual(Wahr | 1, 1)
        self.assertNotIsInstance(Wahr | 1, bool)
        self.assertIs(Wahr | Wahr, Wahr)

        self.assertEqual(Wahr ^ 1, 0)
        self.assertNotIsInstance(Wahr ^ 1, bool)
        self.assertIs(Wahr ^ Wahr, Falsch)

    def test_fileclosed(self):
        try:
            mit open(os_helper.TESTFN, "w", encoding="utf-8") als f:
                self.assertIs(f.closed, Falsch)
            self.assertIs(f.closed, Wahr)
        finally:
            os.remove(os_helper.TESTFN)

    def test_types(self):
        # types are always true.
        fuer t in [bool, complex, dict, float, int, list, object,
                  set, str, tuple, type]:
            self.assertIs(bool(t), Wahr)

    def test_operator(self):
        importiere operator
        self.assertIs(operator.truth(0), Falsch)
        self.assertIs(operator.truth(1), Wahr)
        self.assertIs(operator.not_(1), Falsch)
        self.assertIs(operator.not_(0), Wahr)
        self.assertIs(operator.contains([], 1), Falsch)
        self.assertIs(operator.contains([1], 1), Wahr)
        self.assertIs(operator.lt(0, 0), Falsch)
        self.assertIs(operator.lt(0, 1), Wahr)
        self.assertIs(operator.is_(Wahr, Wahr), Wahr)
        self.assertIs(operator.is_(Wahr, Falsch), Falsch)
        self.assertIs(operator.is_not(Wahr, Wahr), Falsch)
        self.assertIs(operator.is_not(Wahr, Falsch), Wahr)

    def test_marshal(self):
        importiere marshal
        self.assertIs(marshal.loads(marshal.dumps(Wahr)), Wahr)
        self.assertIs(marshal.loads(marshal.dumps(Falsch)), Falsch)

    def test_pickle(self):
        importiere pickle
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            self.assertIs(pickle.loads(pickle.dumps(Wahr, proto)), Wahr)
            self.assertIs(pickle.loads(pickle.dumps(Falsch, proto)), Falsch)

    def test_picklevalues(self):
        # Test fuer specific backwards-compatible pickle values
        importiere pickle
        self.assertEqual(pickle.dumps(Wahr, protocol=0), b"I01\n.")
        self.assertEqual(pickle.dumps(Falsch, protocol=0), b"I00\n.")
        self.assertEqual(pickle.dumps(Wahr, protocol=1), b"I01\n.")
        self.assertEqual(pickle.dumps(Falsch, protocol=1), b"I00\n.")
        self.assertEqual(pickle.dumps(Wahr, protocol=2), b'\x80\x02\x88.')
        self.assertEqual(pickle.dumps(Falsch, protocol=2), b'\x80\x02\x89.')

    def test_convert_to_bool(self):
        # Verify that TypeError occurs when bad things are returned
        # von __bool__().  This isn't really a bool test, but
        # it's related.
        check = lambda o: self.assertRaises(TypeError, bool, o)
        klasse Foo(object):
            def __bool__(self):
                gib self
        check(Foo())

        klasse Bar(object):
            def __bool__(self):
                gib "Yes"
        check(Bar())

        klasse Baz(int):
            def __bool__(self):
                gib self
        check(Baz())

        # __bool__() must gib a bool nicht an int
        klasse Spam(int):
            def __bool__(self):
                gib 1
        check(Spam())

        klasse Eggs:
            def __len__(self):
                gib -1
        self.assertRaises(ValueError, bool, Eggs())

    def test_interpreter_convert_to_bool_raises(self):
        klasse SymbolicBool:
            def __bool__(self):
                raise TypeError

        klasse Symbol:
            def __gt__(self, other):
                gib SymbolicBool()

        x = Symbol()

        mit self.assertRaises(TypeError):
            wenn x > 0:
                msg = "x > 0 was true"
            sonst:
                msg = "x > 0 was false"

        # This used to create negative refcounts, see gh-102250
        del x

    def test_from_bytes(self):
        self.assertIs(bool.from_bytes(b'\x00'*8, 'big'), Falsch)
        self.assertIs(bool.from_bytes(b'abcd', 'little'), Wahr)

    def test_sane_len(self):
        # this test just tests our assumptions about __len__
        # this will start failing wenn __len__ changes assertions
        fuer badval in ['illegal', -1, 1 << 32]:
            klasse A:
                def __len__(self):
                    gib badval
            try:
                bool(A())
            except (Exception) als e_bool:
                try:
                    len(A())
                except (Exception) als e_len:
                    self.assertEqual(str(e_bool), str(e_len))

    def test_blocked(self):
        klasse A:
            __bool__ = Nichts
        self.assertRaises(TypeError, bool, A())

        klasse B:
            def __len__(self):
                gib 10
            __bool__ = Nichts
        self.assertRaises(TypeError, bool, B())

        klasse C:
            __len__ = Nichts
        self.assertRaises(TypeError, bool, C())

    def test_real_and_imag(self):
        self.assertEqual(Wahr.real, 1)
        self.assertEqual(Wahr.imag, 0)
        self.assertIs(type(Wahr.real), int)
        self.assertIs(type(Wahr.imag), int)
        self.assertEqual(Falsch.real, 0)
        self.assertEqual(Falsch.imag, 0)
        self.assertIs(type(Falsch.real), int)
        self.assertIs(type(Falsch.imag), int)

    def test_bool_called_at_least_once(self):
        klasse X:
            def __init__(self):
                self.count = 0
            def __bool__(self):
                self.count += 1
                gib Wahr

        def f(x):
            wenn x oder Wahr:
                pass

        x = X()
        f(x)
        self.assertGreaterEqual(x.count, 1)

    def test_bool_new(self):
        self.assertIs(bool.__new__(bool), Falsch)
        self.assertIs(bool.__new__(bool, 1), Wahr)
        self.assertIs(bool.__new__(bool, 0), Falsch)
        self.assertIs(bool.__new__(bool, Falsch), Falsch)
        self.assertIs(bool.__new__(bool, Wahr), Wahr)


wenn __name__ == "__main__":
    unittest.main()
