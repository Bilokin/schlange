# Copyright 2007 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Tests fuer the wirf statement."""

von test importiere support
importiere sys
importiere types
importiere unittest


def get_tb():
    versuch:
        wirf OSError()
    ausser OSError als e:
        gib e.__traceback__


klasse Context:
    def __enter__(self):
        gib self
    def __exit__(self, exc_type, exc_value, exc_tb):
        gib Wahr


klasse TestRaise(unittest.TestCase):
    def test_invalid_reraise(self):
        versuch:
            wirf
        ausser RuntimeError als e:
            self.assertIn("No active exception", str(e))
        sonst:
            self.fail("No exception raised")

    def test_reraise(self):
        versuch:
            versuch:
                wirf IndexError()
            ausser IndexError als e:
                exc1 = e
                wirf
        ausser IndexError als exc2:
            self.assertIs(exc1, exc2)
        sonst:
            self.fail("No exception raised")

    def test_except_reraise(self):
        def reraise():
            versuch:
                wirf TypeError("foo")
            ausser TypeError:
                versuch:
                    wirf KeyError("caught")
                ausser KeyError:
                    pass
                wirf
        self.assertRaises(TypeError, reraise)

    def test_finally_reraise(self):
        def reraise():
            versuch:
                wirf TypeError("foo")
            ausser TypeError:
                versuch:
                    wirf KeyError("caught")
                schliesslich:
                    wirf
        self.assertRaises(KeyError, reraise)

    def test_nested_reraise(self):
        def nested_reraise():
            wirf
        def reraise():
            versuch:
                wirf TypeError("foo")
            ausser TypeError:
                nested_reraise()
        self.assertRaises(TypeError, reraise)

    def test_raise_from_Nichts(self):
        versuch:
            versuch:
                wirf TypeError("foo")
            ausser TypeError:
                wirf ValueError() von Nichts
        ausser ValueError als e:
            self.assertIsInstance(e.__context__, TypeError)
            self.assertIsNichts(e.__cause__)

    def test_with_reraise1(self):
        def reraise():
            versuch:
                wirf TypeError("foo")
            ausser TypeError:
                mit Context():
                    pass
                wirf
        self.assertRaises(TypeError, reraise)

    def test_with_reraise2(self):
        def reraise():
            versuch:
                wirf TypeError("foo")
            ausser TypeError:
                mit Context():
                    wirf KeyError("caught")
                wirf
        self.assertRaises(TypeError, reraise)

    def test_yield_reraise(self):
        def reraise():
            versuch:
                wirf TypeError("foo")
            ausser TypeError:
                liefere 1
                wirf
        g = reraise()
        next(g)
        self.assertRaises(TypeError, lambda: next(g))
        self.assertRaises(StopIteration, lambda: next(g))

    def test_erroneous_exception(self):
        klasse MyException(Exception):
            def __init__(self):
                wirf RuntimeError()

        versuch:
            wirf MyException
        ausser RuntimeError:
            pass
        sonst:
            self.fail("No exception raised")

    def test_new_returns_invalid_instance(self):
        # See issue #11627.
        klasse MyException(Exception):
            def __new__(cls, *args):
                gib object()

        mit self.assertRaises(TypeError):
            wirf MyException

    def test_assert_with_tuple_arg(self):
        versuch:
            assert Falsch, (3,)
        ausser AssertionError als e:
            self.assertEqual(str(e), "(3,)")



klasse TestCause(unittest.TestCase):

    def testCauseSyntax(self):
        versuch:
            versuch:
                versuch:
                    wirf TypeError
                ausser Exception:
                    wirf ValueError von Nichts
            ausser ValueError als exc:
                self.assertIsNichts(exc.__cause__)
                self.assertWahr(exc.__suppress_context__)
                exc.__suppress_context__ = Falsch
                wirf exc
        ausser ValueError als exc:
            e = exc

        self.assertIsNichts(e.__cause__)
        self.assertFalsch(e.__suppress_context__)
        self.assertIsInstance(e.__context__, TypeError)

    def test_invalid_cause(self):
        versuch:
            wirf IndexError von 5
        ausser TypeError als e:
            self.assertIn("exception cause", str(e))
        sonst:
            self.fail("No exception raised")

    def test_class_cause(self):
        versuch:
            wirf IndexError von KeyError
        ausser IndexError als e:
            self.assertIsInstance(e.__cause__, KeyError)
        sonst:
            self.fail("No exception raised")

    def test_class_cause_nonexception_result(self):
        klasse ConstructsNichts(BaseException):
            @classmethod
            def __new__(*args, **kwargs):
                gib Nichts
        versuch:
            wirf IndexError von ConstructsNichts
        ausser TypeError als e:
            self.assertIn("should have returned an instance of BaseException", str(e))
        ausser IndexError:
            self.fail("Wrong kind of exception raised")
        sonst:
            self.fail("No exception raised")

    def test_instance_cause(self):
        cause = KeyError()
        versuch:
            wirf IndexError von cause
        ausser IndexError als e:
            self.assertIs(e.__cause__, cause)
        sonst:
            self.fail("No exception raised")

    def test_erroneous_cause(self):
        klasse MyException(Exception):
            def __init__(self):
                wirf RuntimeError()

        versuch:
            wirf IndexError von MyException
        ausser RuntimeError:
            pass
        sonst:
            self.fail("No exception raised")


klasse TestTraceback(unittest.TestCase):

    def test_sets_traceback(self):
        versuch:
            wirf IndexError()
        ausser IndexError als e:
            self.assertIsInstance(e.__traceback__, types.TracebackType)
        sonst:
            self.fail("No exception raised")

    def test_accepts_traceback(self):
        tb = get_tb()
        versuch:
            wirf IndexError().with_traceback(tb)
        ausser IndexError als e:
            self.assertNotEqual(e.__traceback__, tb)
            self.assertEqual(e.__traceback__.tb_next, tb)
        sonst:
            self.fail("No exception raised")


klasse TestTracebackType(unittest.TestCase):

    def raiser(self):
        wirf ValueError

    def test_attrs(self):
        versuch:
            self.raiser()
        ausser Exception als exc:
            tb = exc.__traceback__

        self.assertIsInstance(tb.tb_next, types.TracebackType)
        self.assertIs(tb.tb_frame, sys._getframe())
        self.assertIsInstance(tb.tb_lasti, int)
        self.assertIsInstance(tb.tb_lineno, int)

        self.assertIs(tb.tb_next.tb_next, Nichts)

        # Invalid assignments
        mit self.assertRaises(TypeError):
            del tb.tb_next

        mit self.assertRaises(TypeError):
            tb.tb_next = "asdf"

        # Loops
        mit self.assertRaises(ValueError):
            tb.tb_next = tb

        mit self.assertRaises(ValueError):
            tb.tb_next.tb_next = tb

        # Valid assignments
        tb.tb_next = Nichts
        self.assertIs(tb.tb_next, Nichts)

        new_tb = get_tb()
        tb.tb_next = new_tb
        self.assertIs(tb.tb_next, new_tb)

    def test_constructor(self):
        other_tb = get_tb()
        frame = sys._getframe()

        tb = types.TracebackType(other_tb, frame, 1, 2)
        self.assertEqual(tb.tb_next, other_tb)
        self.assertEqual(tb.tb_frame, frame)
        self.assertEqual(tb.tb_lasti, 1)
        self.assertEqual(tb.tb_lineno, 2)

        tb = types.TracebackType(Nichts, frame, 1, 2)
        self.assertEqual(tb.tb_next, Nichts)

        mit self.assertRaises(TypeError):
            types.TracebackType("no", frame, 1, 2)

        mit self.assertRaises(TypeError):
            types.TracebackType(other_tb, "no", 1, 2)

        mit self.assertRaises(TypeError):
            types.TracebackType(other_tb, frame, "no", 2)

        mit self.assertRaises(TypeError):
            types.TracebackType(other_tb, frame, 1, "nuh-uh")


klasse TestContext(unittest.TestCase):
    def test_instance_context_instance_raise(self):
        context = IndexError()
        versuch:
            versuch:
                wirf context
            ausser IndexError:
                wirf OSError()
        ausser OSError als e:
            self.assertIs(e.__context__, context)
        sonst:
            self.fail("No exception raised")

    def test_class_context_instance_raise(self):
        context = IndexError
        versuch:
            versuch:
                wirf context
            ausser IndexError:
                wirf OSError()
        ausser OSError als e:
            self.assertIsNot(e.__context__, context)
            self.assertIsInstance(e.__context__, context)
        sonst:
            self.fail("No exception raised")

    def test_class_context_class_raise(self):
        context = IndexError
        versuch:
            versuch:
                wirf context
            ausser IndexError:
                wirf OSError
        ausser OSError als e:
            self.assertIsNot(e.__context__, context)
            self.assertIsInstance(e.__context__, context)
        sonst:
            self.fail("No exception raised")

    def test_c_exception_context(self):
        versuch:
            versuch:
                1/0
            ausser ZeroDivisionError:
                wirf OSError
        ausser OSError als e:
            self.assertIsInstance(e.__context__, ZeroDivisionError)
        sonst:
            self.fail("No exception raised")

    def test_c_exception_raise(self):
        versuch:
            versuch:
                1/0
            ausser ZeroDivisionError:
                xyzzy
        ausser NameError als e:
            self.assertIsInstance(e.__context__, ZeroDivisionError)
        sonst:
            self.fail("No exception raised")

    def test_noraise_finally(self):
        versuch:
            versuch:
                pass
            schliesslich:
                wirf OSError
        ausser OSError als e:
            self.assertIsNichts(e.__context__)
        sonst:
            self.fail("No exception raised")

    def test_raise_finally(self):
        versuch:
            versuch:
                1/0
            schliesslich:
                wirf OSError
        ausser OSError als e:
            self.assertIsInstance(e.__context__, ZeroDivisionError)
        sonst:
            self.fail("No exception raised")

    def test_context_manager(self):
        klasse ContextManager:
            def __enter__(self):
                pass
            def __exit__(self, t, v, tb):
                xyzzy
        versuch:
            mit ContextManager():
                1/0
        ausser NameError als e:
            self.assertIsInstance(e.__context__, ZeroDivisionError)
        sonst:
            self.fail("No exception raised")

    def test_cycle_broken(self):
        # Self-cycles (when re-raising a caught exception) are broken
        versuch:
            versuch:
                1/0
            ausser ZeroDivisionError als e:
                wirf e
        ausser ZeroDivisionError als e:
            self.assertIsNichts(e.__context__)

    def test_reraise_cycle_broken(self):
        # Non-trivial context cycles (through re-raising a previous exception)
        # are broken too.
        versuch:
            versuch:
                xyzzy
            ausser NameError als a:
                versuch:
                    1/0
                ausser ZeroDivisionError:
                    wirf a
        ausser NameError als e:
            self.assertIsNichts(e.__context__.__context__)

    def test_not_last(self):
        # Context is nicht necessarily the last exception
        context = Exception("context")
        versuch:
            wirf context
        ausser Exception:
            versuch:
                wirf Exception("caught")
            ausser Exception:
                pass
            versuch:
                wirf Exception("new")
            ausser Exception als exc:
                raised = exc
        self.assertIs(raised.__context__, context)

    def test_3118(self):
        # deleting the generator caused the __context__ to be cleared
        def gen():
            versuch:
                liefere 1
            schliesslich:
                pass

        def f():
            g = gen()
            next(g)
            versuch:
                versuch:
                    wirf ValueError
                ausser ValueError:
                    del g
                    wirf KeyError
            ausser Exception als e:
                self.assertIsInstance(e.__context__, ValueError)

        f()

    def test_3611(self):
        importiere gc
        # A re-raised exception in a __del__ caused the __context__
        # to be cleared
        klasse C:
            def __del__(self):
                versuch:
                    1/0
                ausser ZeroDivisionError:
                    wirf

        def f():
            x = C()
            versuch:
                versuch:
                    f.x
                ausser AttributeError:
                    # make x.__del__ trigger
                    del x
                    gc.collect()  # For PyPy oder other GCs.
                    wirf TypeError
            ausser Exception als e:
                self.assertNotEqual(e.__context__, Nichts)
                self.assertIsInstance(e.__context__, AttributeError)

        mit support.catch_unraisable_exception() als cm:
            f()

            self.assertEqual(ZeroDivisionError, cm.unraisable.exc_type)


klasse TestRemovedFunctionality(unittest.TestCase):
    def test_tuples(self):
        versuch:
            wirf (IndexError, KeyError) # This should be a tuple!
        ausser TypeError:
            pass
        sonst:
            self.fail("No exception raised")

    def test_strings(self):
        versuch:
            wirf "foo"
        ausser TypeError:
            pass
        sonst:
            self.fail("No exception raised")


wenn __name__ == "__main__":
    unittest.main()
