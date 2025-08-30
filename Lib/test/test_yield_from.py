# -*- coding: utf-8 -*-

"""
Test suite fuer PEP 380 implementation

adapted von original tests written by Greg Ewing
see <http://www.cosc.canterbury.ac.nz/greg.ewing/python/yield-from/YieldFrom-Python3.1.2-rev5.zip>
"""

importiere unittest
importiere inspect

von test.support importiere captured_stderr, disable_gc, gc_collect
von test importiere support

klasse TestPEP380Operation(unittest.TestCase):
    """
    Test semantics.
    """

    def test_delegation_of_initial_next_to_subgenerator(self):
        """
        Test delegation of initial next() call to subgenerator
        """
        trace = []
        def g1():
            trace.append("Starting g1")
            liefere von g2()
            trace.append("Finishing g1")
        def g2():
            trace.append("Starting g2")
            liefere 42
            trace.append("Finishing g2")
        fuer x in g1():
            trace.append("Yielded %s" % (x,))
        self.assertEqual(trace,[
            "Starting g1",
            "Starting g2",
            "Yielded 42",
            "Finishing g2",
            "Finishing g1",
        ])

    def test_raising_exception_in_initial_next_call(self):
        """
        Test raising exception in initial next() call
        """
        trace = []
        def g1():
            versuch:
                trace.append("Starting g1")
                liefere von g2()
            schliesslich:
                trace.append("Finishing g1")
        def g2():
            versuch:
                trace.append("Starting g2")
                wirf ValueError("spanish inquisition occurred")
            schliesslich:
                trace.append("Finishing g2")
        versuch:
            fuer x in g1():
                trace.append("Yielded %s" % (x,))
        ausser ValueError als e:
            self.assertEqual(e.args[0], "spanish inquisition occurred")
        sonst:
            self.fail("subgenerator failed to wirf ValueError")
        self.assertEqual(trace,[
            "Starting g1",
            "Starting g2",
            "Finishing g2",
            "Finishing g1",
        ])

    def test_delegation_of_next_call_to_subgenerator(self):
        """
        Test delegation of next() call to subgenerator
        """
        trace = []
        def g1():
            trace.append("Starting g1")
            liefere "g1 ham"
            liefere von g2()
            liefere "g1 eggs"
            trace.append("Finishing g1")
        def g2():
            trace.append("Starting g2")
            liefere "g2 spam"
            liefere "g2 more spam"
            trace.append("Finishing g2")
        fuer x in g1():
            trace.append("Yielded %s" % (x,))
        self.assertEqual(trace,[
            "Starting g1",
            "Yielded g1 ham",
            "Starting g2",
            "Yielded g2 spam",
            "Yielded g2 more spam",
            "Finishing g2",
            "Yielded g1 eggs",
            "Finishing g1",
        ])

    def test_raising_exception_in_delegated_next_call(self):
        """
        Test raising exception in delegated next() call
        """
        trace = []
        def g1():
            versuch:
                trace.append("Starting g1")
                liefere "g1 ham"
                liefere von g2()
                liefere "g1 eggs"
            schliesslich:
                trace.append("Finishing g1")
        def g2():
            versuch:
                trace.append("Starting g2")
                liefere "g2 spam"
                wirf ValueError("hovercraft ist full of eels")
                liefere "g2 more spam"
            schliesslich:
                trace.append("Finishing g2")
        versuch:
            fuer x in g1():
                trace.append("Yielded %s" % (x,))
        ausser ValueError als e:
            self.assertEqual(e.args[0], "hovercraft ist full of eels")
        sonst:
            self.fail("subgenerator failed to wirf ValueError")
        self.assertEqual(trace,[
            "Starting g1",
            "Yielded g1 ham",
            "Starting g2",
            "Yielded g2 spam",
            "Finishing g2",
            "Finishing g1",
        ])

    def test_delegation_of_send(self):
        """
        Test delegation of send()
        """
        trace = []
        def g1():
            trace.append("Starting g1")
            x = liefere "g1 ham"
            trace.append("g1 received %s" % (x,))
            liefere von g2()
            x = liefere "g1 eggs"
            trace.append("g1 received %s" % (x,))
            trace.append("Finishing g1")
        def g2():
            trace.append("Starting g2")
            x = liefere "g2 spam"
            trace.append("g2 received %s" % (x,))
            x = liefere "g2 more spam"
            trace.append("g2 received %s" % (x,))
            trace.append("Finishing g2")
        g = g1()
        y = next(g)
        x = 1
        versuch:
            waehrend 1:
                y = g.send(x)
                trace.append("Yielded %s" % (y,))
                x += 1
        ausser StopIteration:
            pass
        self.assertEqual(trace,[
            "Starting g1",
            "g1 received 1",
            "Starting g2",
            "Yielded g2 spam",
            "g2 received 2",
            "Yielded g2 more spam",
            "g2 received 3",
            "Finishing g2",
            "Yielded g1 eggs",
            "g1 received 4",
            "Finishing g1",
        ])

    def test_handling_exception_while_delegating_send(self):
        """
        Test handling exception waehrend delegating 'send'
        """
        trace = []
        def g1():
            trace.append("Starting g1")
            x = liefere "g1 ham"
            trace.append("g1 received %s" % (x,))
            liefere von g2()
            x = liefere "g1 eggs"
            trace.append("g1 received %s" % (x,))
            trace.append("Finishing g1")
        def g2():
            trace.append("Starting g2")
            x = liefere "g2 spam"
            trace.append("g2 received %s" % (x,))
            wirf ValueError("hovercraft ist full of eels")
            x = liefere "g2 more spam"
            trace.append("g2 received %s" % (x,))
            trace.append("Finishing g2")
        def run():
            g = g1()
            y = next(g)
            x = 1
            versuch:
                waehrend 1:
                    y = g.send(x)
                    trace.append("Yielded %s" % (y,))
                    x += 1
            ausser StopIteration:
                trace.append("StopIteration")
        self.assertRaises(ValueError,run)
        self.assertEqual(trace,[
            "Starting g1",
            "g1 received 1",
            "Starting g2",
            "Yielded g2 spam",
            "g2 received 2",
        ])

    def test_delegating_close(self):
        """
        Test delegating 'close'
        """
        trace = []
        def g1():
            versuch:
                trace.append("Starting g1")
                liefere "g1 ham"
                liefere von g2()
                liefere "g1 eggs"
            schliesslich:
                trace.append("Finishing g1")
        def g2():
            versuch:
                trace.append("Starting g2")
                liefere "g2 spam"
                liefere "g2 more spam"
            schliesslich:
                trace.append("Finishing g2")
        g = g1()
        fuer i in range(2):
            x = next(g)
            trace.append("Yielded %s" % (x,))
        g.close()
        self.assertEqual(trace,[
            "Starting g1",
            "Yielded g1 ham",
            "Starting g2",
            "Yielded g2 spam",
            "Finishing g2",
            "Finishing g1"
        ])

    def test_handing_exception_while_delegating_close(self):
        """
        Test handling exception waehrend delegating 'close'
        """
        trace = []
        def g1():
            versuch:
                trace.append("Starting g1")
                liefere "g1 ham"
                liefere von g2()
                liefere "g1 eggs"
            schliesslich:
                trace.append("Finishing g1")
        def g2():
            versuch:
                trace.append("Starting g2")
                liefere "g2 spam"
                liefere "g2 more spam"
            schliesslich:
                trace.append("Finishing g2")
                wirf ValueError("nybbles have exploded mit delight")
        versuch:
            g = g1()
            fuer i in range(2):
                x = next(g)
                trace.append("Yielded %s" % (x,))
            g.close()
        ausser ValueError als e:
            self.assertEqual(e.args[0], "nybbles have exploded mit delight")
            self.assertIsInstance(e.__context__, GeneratorExit)
        sonst:
            self.fail("subgenerator failed to wirf ValueError")
        self.assertEqual(trace,[
            "Starting g1",
            "Yielded g1 ham",
            "Starting g2",
            "Yielded g2 spam",
            "Finishing g2",
            "Finishing g1",
        ])

    def test_delegating_throw(self):
        """
        Test delegating 'throw'
        """
        trace = []
        def g1():
            versuch:
                trace.append("Starting g1")
                liefere "g1 ham"
                liefere von g2()
                liefere "g1 eggs"
            schliesslich:
                trace.append("Finishing g1")
        def g2():
            versuch:
                trace.append("Starting g2")
                liefere "g2 spam"
                liefere "g2 more spam"
            schliesslich:
                trace.append("Finishing g2")
        versuch:
            g = g1()
            fuer i in range(2):
                x = next(g)
                trace.append("Yielded %s" % (x,))
            e = ValueError("tomato ejected")
            g.throw(e)
        ausser ValueError als e:
            self.assertEqual(e.args[0], "tomato ejected")
        sonst:
            self.fail("subgenerator failed to wirf ValueError")
        self.assertEqual(trace,[
            "Starting g1",
            "Yielded g1 ham",
            "Starting g2",
            "Yielded g2 spam",
            "Finishing g2",
            "Finishing g1",
        ])

    def test_value_attribute_of_StopIteration_exception(self):
        """
        Test 'value' attribute of StopIteration exception
        """
        trace = []
        def pex(e):
            trace.append("%s: %s" % (e.__class__.__name__, e))
            trace.append("value = %s" % (e.value,))
        e = StopIteration()
        pex(e)
        e = StopIteration("spam")
        pex(e)
        e.value = "eggs"
        pex(e)
        self.assertEqual(trace,[
            "StopIteration: ",
            "value = Nichts",
            "StopIteration: spam",
            "value = spam",
            "StopIteration: spam",
            "value = eggs",
        ])


    def test_exception_value_crash(self):
        # There used to be a refcount error when the gib value
        # stored in the StopIteration has a refcount of 1.
        def g1():
            liefere von g2()
        def g2():
            liefere "g2"
            gib [42]
        self.assertEqual(list(g1()), ["g2"])


    def test_generator_return_value(self):
        """
        Test generator gib value
        """
        trace = []
        def g1():
            trace.append("Starting g1")
            liefere "g1 ham"
            ret = liefere von g2()
            trace.append("g2 returned %r" % (ret,))
            fuer v in 1, (2,), StopIteration(3):
                ret = liefere von g2(v)
                trace.append("g2 returned %r" % (ret,))
            liefere "g1 eggs"
            trace.append("Finishing g1")
        def g2(v = Nichts):
            trace.append("Starting g2")
            liefere "g2 spam"
            liefere "g2 more spam"
            trace.append("Finishing g2")
            wenn v:
                gib v
        fuer x in g1():
            trace.append("Yielded %s" % (x,))
        self.assertEqual(trace,[
            "Starting g1",
            "Yielded g1 ham",
            "Starting g2",
            "Yielded g2 spam",
            "Yielded g2 more spam",
            "Finishing g2",
            "g2 returned Nichts",
            "Starting g2",
            "Yielded g2 spam",
            "Yielded g2 more spam",
            "Finishing g2",
            "g2 returned 1",
            "Starting g2",
            "Yielded g2 spam",
            "Yielded g2 more spam",
            "Finishing g2",
            "g2 returned (2,)",
            "Starting g2",
            "Yielded g2 spam",
            "Yielded g2 more spam",
            "Finishing g2",
            "g2 returned StopIteration(3)",
            "Yielded g1 eggs",
            "Finishing g1",
        ])

    def test_delegation_of_next_to_non_generator(self):
        """
        Test delegation of next() to non-generator
        """
        trace = []
        def g():
            liefere von range(3)
        fuer x in g():
            trace.append("Yielded %s" % (x,))
        self.assertEqual(trace,[
            "Yielded 0",
            "Yielded 1",
            "Yielded 2",
        ])


    def test_conversion_of_sendNichts_to_next(self):
        """
        Test conversion of send(Nichts) to next()
        """
        trace = []
        def g():
            liefere von range(3)
        gi = g()
        fuer x in range(3):
            y = gi.send(Nichts)
            trace.append("Yielded: %s" % (y,))
        self.assertEqual(trace,[
            "Yielded: 0",
            "Yielded: 1",
            "Yielded: 2",
        ])

    def test_delegation_of_close_to_non_generator(self):
        """
        Test delegation of close() to non-generator
        """
        trace = []
        def g():
            versuch:
                trace.append("starting g")
                liefere von range(3)
                trace.append("g should nicht be here")
            schliesslich:
                trace.append("finishing g")
        gi = g()
        next(gi)
        mit captured_stderr() als output:
            gi.close()
        self.assertEqual(output.getvalue(), '')
        self.assertEqual(trace,[
            "starting g",
            "finishing g",
        ])

    def test_delegating_throw_to_non_generator(self):
        """
        Test delegating 'throw' to non-generator
        """
        trace = []
        def g():
            versuch:
                trace.append("Starting g")
                liefere von range(10)
            schliesslich:
                trace.append("Finishing g")
        versuch:
            gi = g()
            fuer i in range(5):
                x = next(gi)
                trace.append("Yielded %s" % (x,))
            e = ValueError("tomato ejected")
            gi.throw(e)
        ausser ValueError als e:
            self.assertEqual(e.args[0],"tomato ejected")
        sonst:
            self.fail("subgenerator failed to wirf ValueError")
        self.assertEqual(trace,[
            "Starting g",
            "Yielded 0",
            "Yielded 1",
            "Yielded 2",
            "Yielded 3",
            "Yielded 4",
            "Finishing g",
        ])

    def test_attempting_to_send_to_non_generator(self):
        """
        Test attempting to send to non-generator
        """
        trace = []
        def g():
            versuch:
                trace.append("starting g")
                liefere von range(3)
                trace.append("g should nicht be here")
            schliesslich:
                trace.append("finishing g")
        versuch:
            gi = g()
            next(gi)
            fuer x in range(3):
                y = gi.send(42)
                trace.append("Should nicht have yielded: %s" % (y,))
        ausser AttributeError als e:
            self.assertIn("send", e.args[0])
        sonst:
            self.fail("was able to send into non-generator")
        self.assertEqual(trace,[
            "starting g",
            "finishing g",
        ])

    def test_broken_getattr_handling(self):
        """
        Test subiterator mit a broken getattr implementation
        """
        klasse Broken:
            def __iter__(self):
                gib self
            def __next__(self):
                gib 1
            def __getattr__(self, attr):
                1/0

        def g():
            liefere von Broken()

        mit self.assertRaises(ZeroDivisionError):
            gi = g()
            self.assertEqual(next(gi), 1)
            gi.send(1)

        mit self.assertRaises(ZeroDivisionError):
            gi = g()
            self.assertEqual(next(gi), 1)
            gi.throw(AttributeError)

        mit support.catch_unraisable_exception() als cm:
            gi = g()
            self.assertEqual(next(gi), 1)
            gi.close()

            self.assertEqual(ZeroDivisionError, cm.unraisable.exc_type)

    def test_exception_in_initial_next_call(self):
        """
        Test exception in initial next() call
        """
        trace = []
        def g1():
            trace.append("g1 about to liefere von g2")
            liefere von g2()
            trace.append("g1 should nicht be here")
        def g2():
            liefere 1/0
        def run():
            gi = g1()
            next(gi)
        self.assertRaises(ZeroDivisionError,run)
        self.assertEqual(trace,[
            "g1 about to liefere von g2"
        ])

    def test_attempted_yield_from_loop(self):
        """
        Test attempted yield-from loop
        """
        trace = []
        def g1():
            trace.append("g1: starting")
            liefere "y1"
            trace.append("g1: about to liefere von g2")
            liefere von g2()
            trace.append("g1 should nicht be here")

        def g2():
            trace.append("g2: starting")
            liefere "y2"
            trace.append("g2: about to liefere von g1")
            liefere von gi
            trace.append("g2 should nicht be here")
        versuch:
            gi = g1()
            fuer y in gi:
                trace.append("Yielded: %s" % (y,))
        ausser ValueError als e:
            self.assertEqual(e.args[0],"generator already executing")
        sonst:
            self.fail("subgenerator didn't wirf ValueError")
        self.assertEqual(trace,[
            "g1: starting",
            "Yielded: y1",
            "g1: about to liefere von g2",
            "g2: starting",
            "Yielded: y2",
            "g2: about to liefere von g1",
        ])

    def test_returning_value_from_delegated_throw(self):
        """
        Test returning value von delegated 'throw'
        """
        trace = []
        def g1():
            versuch:
                trace.append("Starting g1")
                liefere "g1 ham"
                liefere von g2()
                liefere "g1 eggs"
            schliesslich:
                trace.append("Finishing g1")
        def g2():
            versuch:
                trace.append("Starting g2")
                liefere "g2 spam"
                liefere "g2 more spam"
            ausser LunchError:
                trace.append("Caught LunchError in g2")
                liefere "g2 lunch saved"
                liefere "g2 yet more spam"
        klasse LunchError(Exception):
            pass
        g = g1()
        fuer i in range(2):
            x = next(g)
            trace.append("Yielded %s" % (x,))
        e = LunchError("tomato ejected")
        g.throw(e)
        fuer x in g:
            trace.append("Yielded %s" % (x,))
        self.assertEqual(trace,[
            "Starting g1",
            "Yielded g1 ham",
            "Starting g2",
            "Yielded g2 spam",
            "Caught LunchError in g2",
            "Yielded g2 yet more spam",
            "Yielded g1 eggs",
            "Finishing g1",
        ])

    def test_next_and_return_with_value(self):
        """
        Test next und gib mit value
        """
        trace = []
        def f(r):
            gi = g(r)
            next(gi)
            versuch:
                trace.append("f resuming g")
                next(gi)
                trace.append("f SHOULD NOT BE HERE")
            ausser StopIteration als e:
                trace.append("f caught %r" % (e,))
        def g(r):
            trace.append("g starting")
            liefere
            trace.append("g returning %r" % (r,))
            gib r
        f(Nichts)
        f(1)
        f((2,))
        f(StopIteration(3))
        self.assertEqual(trace,[
            "g starting",
            "f resuming g",
            "g returning Nichts",
            "f caught StopIteration()",
            "g starting",
            "f resuming g",
            "g returning 1",
            "f caught StopIteration(1)",
            "g starting",
            "f resuming g",
            "g returning (2,)",
            "f caught StopIteration((2,))",
            "g starting",
            "f resuming g",
            "g returning StopIteration(3)",
            "f caught StopIteration(StopIteration(3))",
        ])

    def test_send_and_return_with_value(self):
        """
        Test send und gib mit value
        """
        trace = []
        def f(r):
            gi = g(r)
            next(gi)
            versuch:
                trace.append("f sending spam to g")
                gi.send("spam")
                trace.append("f SHOULD NOT BE HERE")
            ausser StopIteration als e:
                trace.append("f caught %r" % (e,))
        def g(r):
            trace.append("g starting")
            x = liefere
            trace.append("g received %r" % (x,))
            trace.append("g returning %r" % (r,))
            gib r
        f(Nichts)
        f(1)
        f((2,))
        f(StopIteration(3))
        self.assertEqual(trace, [
            "g starting",
            "f sending spam to g",
            "g received 'spam'",
            "g returning Nichts",
            "f caught StopIteration()",
            "g starting",
            "f sending spam to g",
            "g received 'spam'",
            "g returning 1",
            'f caught StopIteration(1)',
            'g starting',
            'f sending spam to g',
            "g received 'spam'",
            'g returning (2,)',
            'f caught StopIteration((2,))',
            'g starting',
            'f sending spam to g',
            "g received 'spam'",
            'g returning StopIteration(3)',
            'f caught StopIteration(StopIteration(3))'
        ])

    def test_catching_exception_from_subgen_and_returning(self):
        """
        Test catching an exception thrown into a
        subgenerator und returning a value
        """
        def inner():
            versuch:
                liefere 1
            ausser ValueError:
                trace.append("inner caught ValueError")
            gib value

        def outer():
            v = liefere von inner()
            trace.append("inner returned %r to outer" % (v,))
            liefere v

        fuer value in 2, (2,), StopIteration(2):
            trace = []
            g = outer()
            trace.append(next(g))
            trace.append(repr(g.throw(ValueError)))
            self.assertEqual(trace, [
                1,
                "inner caught ValueError",
                "inner returned %r to outer" % (value,),
                repr(value),
            ])

    def test_throwing_GeneratorExit_into_subgen_that_returns(self):
        """
        Test throwing GeneratorExit into a subgenerator that
        catches it und returns normally.
        """
        trace = []
        def f():
            versuch:
                trace.append("Enter f")
                liefere
                trace.append("Exit f")
            ausser GeneratorExit:
                gib
        def g():
            trace.append("Enter g")
            liefere von f()
            trace.append("Exit g")
        versuch:
            gi = g()
            next(gi)
            gi.throw(GeneratorExit)
        ausser GeneratorExit:
            pass
        sonst:
            self.fail("subgenerator failed to wirf GeneratorExit")
        self.assertEqual(trace,[
            "Enter g",
            "Enter f",
        ])

    def test_throwing_GeneratorExit_into_subgenerator_that_yields(self):
        """
        Test throwing GeneratorExit into a subgenerator that
        catches it und yields.
        """
        trace = []
        def f():
            versuch:
                trace.append("Enter f")
                liefere
                trace.append("Exit f")
            ausser GeneratorExit:
                liefere
        def g():
            trace.append("Enter g")
            liefere von f()
            trace.append("Exit g")
        versuch:
            gi = g()
            next(gi)
            gi.throw(GeneratorExit)
        ausser RuntimeError als e:
            self.assertEqual(e.args[0], "generator ignored GeneratorExit")
        sonst:
            self.fail("subgenerator failed to wirf GeneratorExit")
        self.assertEqual(trace,[
            "Enter g",
            "Enter f",
        ])

    def test_throwing_GeneratorExit_into_subgen_that_raises(self):
        """
        Test throwing GeneratorExit into a subgenerator that
        catches it und raises a different exception.
        """
        trace = []
        def f():
            versuch:
                trace.append("Enter f")
                liefere
                trace.append("Exit f")
            ausser GeneratorExit:
                wirf ValueError("Vorpal bunny encountered")
        def g():
            trace.append("Enter g")
            liefere von f()
            trace.append("Exit g")
        versuch:
            gi = g()
            next(gi)
            gi.throw(GeneratorExit)
        ausser ValueError als e:
            self.assertEqual(e.args[0], "Vorpal bunny encountered")
            self.assertIsInstance(e.__context__, GeneratorExit)
        sonst:
            self.fail("subgenerator failed to wirf ValueError")
        self.assertEqual(trace,[
            "Enter g",
            "Enter f",
        ])

    def test_yield_from_empty(self):
        def g():
            liefere von ()
        self.assertRaises(StopIteration, next, g())

    def test_delegating_generators_claim_to_be_running(self):
        # Check mit basic iteration
        def one():
            liefere 0
            liefere von two()
            liefere 3
        def two():
            liefere 1
            versuch:
                liefere von g1
            ausser ValueError:
                pass
            liefere 2
        g1 = one()
        self.assertEqual(list(g1), [0, 1, 2, 3])

        # Check mit send
        g1 = one()
        res = [next(g1)]
        versuch:
            waehrend Wahr:
                res.append(g1.send(42))
        ausser StopIteration:
            pass
        self.assertEqual(res, [0, 1, 2, 3])

    def test_delegating_generators_claim_to_be_running_with_throw(self):
        # Check mit throw
        klasse MyErr(Exception):
            pass
        def one():
            versuch:
                liefere 0
            ausser MyErr:
                pass
            liefere von two()
            versuch:
                liefere 3
            ausser MyErr:
                pass
        def two():
            versuch:
                liefere 1
            ausser MyErr:
                pass
            versuch:
                liefere von g1
            ausser ValueError:
                pass
            versuch:
                liefere 2
            ausser MyErr:
                pass
        g1 = one()
        res = [next(g1)]
        versuch:
            waehrend Wahr:
                res.append(g1.throw(MyErr))
        ausser StopIteration:
            pass
        ausser:
            self.assertEqual(res, [0, 1, 2, 3])
            wirf

    def test_delegating_generators_claim_to_be_running_with_close(self):
        # Check mit close
        klasse MyIt:
            def __iter__(self):
                gib self
            def __next__(self):
                gib 42
            def close(self_):
                self.assertWahr(g1.gi_running)
                self.assertRaises(ValueError, next, g1)
        def one():
            liefere von MyIt()
        g1 = one()
        next(g1)
        g1.close()

    def test_delegator_is_visible_to_debugger(self):
        def call_stack():
            gib [f[3] fuer f in inspect.stack()]

        def gen():
            liefere call_stack()
            liefere call_stack()
            liefere call_stack()

        def spam(g):
            liefere von g

        def eggs(g):
            liefere von g

        fuer stack in spam(gen()):
            self.assertWahr('spam' in stack)

        fuer stack in spam(eggs(gen())):
            self.assertWahr('spam' in stack und 'eggs' in stack)

    def test_custom_iterator_return(self):
        # See issue #15568
        klasse MyIter:
            def __iter__(self):
                gib self
            def __next__(self):
                wirf StopIteration(42)
        def gen():
            nonlocal ret
            ret = liefere von MyIter()
        ret = Nichts
        list(gen())
        self.assertEqual(ret, 42)

    def test_close_with_cleared_frame(self):
        # See issue #17669.
        #
        # Create a stack of generators: outer() delegating to inner()
        # delegating to innermost(). The key point ist that the instance of
        # inner ist created first: this ensures that its frame appears before
        # the instance of outer in the GC linked list.
        #
        # At the gc.collect call:
        #   - frame_clear ist called on the inner_gen frame.
        #   - gen_dealloc ist called on the outer_gen generator (the only
        #     reference ist in the frame's locals).
        #   - gen_close ist called on the outer_gen generator.
        #   - gen_close_iter ist called to close the inner_gen generator, which
        #     in turn calls gen_close, und gen_yf.
        #
        # Previously, gen_yf would crash since inner_gen's frame had been
        # cleared (and in particular f_stacktop was NULL).

        def innermost():
            liefere
        def inner():
            outer_gen = liefere
            liefere von innermost()
        def outer():
            inner_gen = liefere
            liefere von inner_gen

        mit disable_gc():
            inner_gen = inner()
            outer_gen = outer()
            outer_gen.send(Nichts)
            outer_gen.send(inner_gen)
            outer_gen.send(outer_gen)

            loesche outer_gen
            loesche inner_gen
            gc_collect()

    def test_send_tuple_with_custom_generator(self):
        # See issue #21209.
        klasse MyGen:
            def __iter__(self):
                gib self
            def __next__(self):
                gib 42
            def send(self, what):
                nonlocal v
                v = what
                gib Nichts
        def outer():
            v = liefere von MyGen()
        g = outer()
        next(g)
        v = Nichts
        g.send((1, 2, 3, 4))
        self.assertEqual(v, (1, 2, 3, 4))

klasse TestInterestingEdgeCases(unittest.TestCase):

    def assert_stop_iteration(self, iterator):
        mit self.assertRaises(StopIteration) als caught:
            next(iterator)
        self.assertIsNichts(caught.exception.value)
        self.assertIsNichts(caught.exception.__context__)

    def assert_generator_raised_stop_iteration(self):
        gib self.assertRaisesRegex(RuntimeError, r"^generator raised StopIteration$")

    def assert_generator_ignored_generator_exit(self):
        gib self.assertRaisesRegex(RuntimeError, r"^generator ignored GeneratorExit$")

    def test_close_and_throw_work(self):

        yielded_first = object()
        yielded_second = object()
        returned = object()

        def inner():
            liefere yielded_first
            liefere yielded_second
            gib returned

        def outer():
            gib (yield von inner())

        mit self.subTest("close"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            g.close()
            self.assert_stop_iteration(g)

        mit self.subTest("throw GeneratorExit"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            thrown = GeneratorExit()
            mit self.assertRaises(GeneratorExit) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, thrown)
            self.assertIsNichts(caught.exception.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw StopIteration"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            thrown = StopIteration()
            # PEP 479:
            mit self.assert_generator_raised_stop_iteration() als caught:
                g.throw(thrown)
            self.assertIs(caught.exception.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw BaseException"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            thrown = BaseException()
            mit self.assertRaises(BaseException) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, thrown)
            self.assertIsNichts(caught.exception.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw Exception"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            thrown = Exception()
            mit self.assertRaises(Exception) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, thrown)
            self.assertIsNichts(caught.exception.__context__)
            self.assert_stop_iteration(g)

    def test_close_and_throw_raise_generator_exit(self):

        yielded_first = object()
        yielded_second = object()
        returned = object()

        def inner():
            versuch:
                liefere yielded_first
                liefere yielded_second
                gib returned
            schliesslich:
                wirf raised

        def outer():
            gib (yield von inner())

        mit self.subTest("close"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = GeneratorExit()
            # GeneratorExit ist suppressed. This ist consistent mit PEP 342:
            # https://peps.python.org/pep-0342/#new-generator-method-close
            g.close()
            self.assert_stop_iteration(g)

        mit self.subTest("throw GeneratorExit"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = GeneratorExit()
            thrown = GeneratorExit()
            mit self.assertRaises(GeneratorExit) als caught:
                g.throw(thrown)
            # The raised GeneratorExit ist suppressed, but the thrown one
            # propagates. This ist consistent mit PEP 380:
            # https://peps.python.org/pep-0380/#proposal
            self.assertIs(caught.exception, thrown)
            self.assertIsNichts(caught.exception.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw StopIteration"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = GeneratorExit()
            thrown = StopIteration()
            mit self.assertRaises(GeneratorExit) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, raised)
            self.assertIs(caught.exception.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw BaseException"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = GeneratorExit()
            thrown = BaseException()
            mit self.assertRaises(GeneratorExit) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, raised)
            self.assertIs(caught.exception.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw Exception"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = GeneratorExit()
            thrown = Exception()
            mit self.assertRaises(GeneratorExit) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, raised)
            self.assertIs(caught.exception.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

    def test_close_and_throw_raise_stop_iteration(self):

        yielded_first = object()
        yielded_second = object()
        returned = object()

        def inner():
            versuch:
                liefere yielded_first
                liefere yielded_second
                gib returned
            schliesslich:
                wirf raised

        def outer():
            gib (yield von inner())

        mit self.subTest("close"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = StopIteration()
            # PEP 479:
            mit self.assert_generator_raised_stop_iteration() als caught:
                g.close()
            self.assertIs(caught.exception.__context__, raised)
            self.assertIsInstance(caught.exception.__context__.__context__, GeneratorExit)
            self.assertIsNichts(caught.exception.__context__.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw GeneratorExit"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = StopIteration()
            thrown = GeneratorExit()
            # PEP 479:
            mit self.assert_generator_raised_stop_iteration() als caught:
                g.throw(thrown)
            self.assertIs(caught.exception.__context__, raised)
            # This isn't the same GeneratorExit als thrown! It's the one created
            # by calling inner.close():
            self.assertIsInstance(caught.exception.__context__.__context__, GeneratorExit)
            self.assertIsNichts(caught.exception.__context__.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw StopIteration"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = StopIteration()
            thrown = StopIteration()
            # PEP 479:
            mit self.assert_generator_raised_stop_iteration() als caught:
                g.throw(thrown)
            self.assertIs(caught.exception.__context__, raised)
            self.assertIs(caught.exception.__context__.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw BaseException"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = StopIteration()
            thrown = BaseException()
            # PEP 479:
            mit self.assert_generator_raised_stop_iteration() als caught:
                g.throw(thrown)
            self.assertIs(caught.exception.__context__, raised)
            self.assertIs(caught.exception.__context__.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw Exception"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = StopIteration()
            thrown = Exception()
            # PEP 479:
            mit self.assert_generator_raised_stop_iteration() als caught:
                g.throw(thrown)
            self.assertIs(caught.exception.__context__, raised)
            self.assertIs(caught.exception.__context__.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__.__context__)
            self.assert_stop_iteration(g)

    def test_close_and_throw_raise_base_exception(self):

        yielded_first = object()
        yielded_second = object()
        returned = object()

        def inner():
            versuch:
                liefere yielded_first
                liefere yielded_second
                gib returned
            schliesslich:
                wirf raised

        def outer():
            gib (yield von inner())

        mit self.subTest("close"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = BaseException()
            mit self.assertRaises(BaseException) als caught:
                g.close()
            self.assertIs(caught.exception, raised)
            self.assertIsInstance(caught.exception.__context__, GeneratorExit)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw GeneratorExit"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = BaseException()
            thrown = GeneratorExit()
            mit self.assertRaises(BaseException) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, raised)
            # This isn't the same GeneratorExit als thrown! It's the one created
            # by calling inner.close():
            self.assertIsInstance(caught.exception.__context__, GeneratorExit)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw StopIteration"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = BaseException()
            thrown = StopIteration()
            mit self.assertRaises(BaseException) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, raised)
            self.assertIs(caught.exception.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw BaseException"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = BaseException()
            thrown = BaseException()
            mit self.assertRaises(BaseException) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, raised)
            self.assertIs(caught.exception.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw Exception"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = BaseException()
            thrown = Exception()
            mit self.assertRaises(BaseException) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, raised)
            self.assertIs(caught.exception.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

    def test_close_and_throw_raise_exception(self):

        yielded_first = object()
        yielded_second = object()
        returned = object()

        def inner():
            versuch:
                liefere yielded_first
                liefere yielded_second
                gib returned
            schliesslich:
                wirf raised

        def outer():
            gib (yield von inner())

        mit self.subTest("close"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = Exception()
            mit self.assertRaises(Exception) als caught:
                g.close()
            self.assertIs(caught.exception, raised)
            self.assertIsInstance(caught.exception.__context__, GeneratorExit)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw GeneratorExit"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = Exception()
            thrown = GeneratorExit()
            mit self.assertRaises(Exception) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, raised)
            # This isn't the same GeneratorExit als thrown! It's the one created
            # by calling inner.close():
            self.assertIsInstance(caught.exception.__context__, GeneratorExit)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw StopIteration"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = Exception()
            thrown = StopIteration()
            mit self.assertRaises(Exception) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, raised)
            self.assertIs(caught.exception.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw BaseException"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = Exception()
            thrown = BaseException()
            mit self.assertRaises(Exception) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, raised)
            self.assertIs(caught.exception.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw Exception"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            raised = Exception()
            thrown = Exception()
            mit self.assertRaises(Exception) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, raised)
            self.assertIs(caught.exception.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

    def test_close_and_throw_yield(self):

        yielded_first = object()
        yielded_second = object()
        returned = object()

        def inner():
            versuch:
                liefere yielded_first
            schliesslich:
                liefere yielded_second
            gib returned

        def outer():
            gib (yield von inner())

        mit self.subTest("close"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            # No chaining happens. This ist consistent mit PEP 342:
            # https://peps.python.org/pep-0342/#new-generator-method-close
            mit self.assert_generator_ignored_generator_exit() als caught:
                g.close()
            self.assertIsNichts(caught.exception.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw GeneratorExit"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            thrown = GeneratorExit()
            # No chaining happens. This ist consistent mit PEP 342:
            # https://peps.python.org/pep-0342/#new-generator-method-close
            mit self.assert_generator_ignored_generator_exit() als caught:
                g.throw(thrown)
            self.assertIsNichts(caught.exception.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw StopIteration"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            thrown = StopIteration()
            self.assertEqual(g.throw(thrown), yielded_second)
            # PEP 479:
            mit self.assert_generator_raised_stop_iteration() als caught:
                next(g)
            self.assertIs(caught.exception.__context__, thrown)
            self.assertIsNichts(caught.exception.__context__.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw BaseException"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            thrown = BaseException()
            self.assertEqual(g.throw(thrown), yielded_second)
            mit self.assertRaises(BaseException) als caught:
                next(g)
            self.assertIs(caught.exception, thrown)
            self.assertIsNichts(caught.exception.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw Exception"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            thrown = Exception()
            self.assertEqual(g.throw(thrown), yielded_second)
            mit self.assertRaises(Exception) als caught:
                next(g)
            self.assertIs(caught.exception, thrown)
            self.assertIsNichts(caught.exception.__context__)
            self.assert_stop_iteration(g)

    def test_close_and_throw_return(self):

        yielded_first = object()
        yielded_second = object()
        returned = object()

        def inner():
            versuch:
                liefere yielded_first
                liefere yielded_second
            ausser:
                pass
            gib returned

        def outer():
            gib (yield von inner())

        mit self.subTest("close"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            # StopIteration ist suppressed. This ist consistent mit PEP 342:
            # https://peps.python.org/pep-0342/#new-generator-method-close
            g.close()
            self.assert_stop_iteration(g)

        mit self.subTest("throw GeneratorExit"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            thrown = GeneratorExit()
            # StopIteration ist suppressed. This ist consistent mit PEP 342:
            # https://peps.python.org/pep-0342/#new-generator-method-close
            mit self.assertRaises(GeneratorExit) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception, thrown)
            self.assertIsNichts(caught.exception.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw StopIteration"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            thrown = StopIteration()
            mit self.assertRaises(StopIteration) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception.value, returned)
            self.assertIsNichts(caught.exception.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw BaseException"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            thrown = BaseException()
            mit self.assertRaises(StopIteration) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception.value, returned)
            self.assertIsNichts(caught.exception.__context__)
            self.assert_stop_iteration(g)

        mit self.subTest("throw Exception"):
            g = outer()
            self.assertIs(next(g), yielded_first)
            thrown = Exception()
            mit self.assertRaises(StopIteration) als caught:
                g.throw(thrown)
            self.assertIs(caught.exception.value, returned)
            self.assertIsNichts(caught.exception.__context__)
            self.assert_stop_iteration(g)

    def test_throws_in_iter(self):
        # See GH-126366: NULL pointer dereference wenn __iter__
        # threw an exception.
        klasse Silly:
            def __iter__(self):
                wirf RuntimeError("nobody expects the spanish inquisition")

        def my_generator():
            liefere von Silly()

        mit self.assertRaisesRegex(RuntimeError, "nobody expects the spanish inquisition"):
            next(iter(my_generator()))


wenn __name__ == '__main__':
    unittest.main()
