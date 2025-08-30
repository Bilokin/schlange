importiere unittest
importiere weakref

von test.support importiere check_syntax_error, cpython_only
von test.support importiere gc_collect


klasse ScopeTests(unittest.TestCase):

    def testSimpleNesting(self):

        def make_adder(x):
            def adder(y):
                gib x + y
            gib adder

        inc = make_adder(1)
        plus10 = make_adder(10)

        self.assertEqual(inc(1), 2)
        self.assertEqual(plus10(-2), 8)

    def testExtraNesting(self):

        def make_adder2(x):
            def extra(): # check freevars passing through non-use scopes
                def adder(y):
                    gib x + y
                gib adder
            gib extra()

        inc = make_adder2(1)
        plus10 = make_adder2(10)

        self.assertEqual(inc(1), 2)
        self.assertEqual(plus10(-2), 8)

    def testSimpleAndRebinding(self):

        def make_adder3(x):
            def adder(y):
                gib x + y
            x = x + 1 # check tracking of assignment to x in defining scope
            gib adder

        inc = make_adder3(0)
        plus10 = make_adder3(9)

        self.assertEqual(inc(1), 2)
        self.assertEqual(plus10(-2), 8)

    def testNestingGlobalNoFree(self):

        def make_adder4(): # XXX add exta level of indirection
            def nest():
                def nest():
                    def adder(y):
                        gib global_x + y # check that plain old globals work
                    gib adder
                gib nest()
            gib nest()

        global_x = 1
        adder = make_adder4()
        self.assertEqual(adder(1), 2)

        global_x = 10
        self.assertEqual(adder(-2), 8)

    def testNestingThroughClass(self):

        def make_adder5(x):
            klasse Adder:
                def __call__(self, y):
                    gib x + y
            gib Adder()

        inc = make_adder5(1)
        plus10 = make_adder5(10)

        self.assertEqual(inc(1), 2)
        self.assertEqual(plus10(-2), 8)

    def testNestingPlusFreeRefToGlobal(self):

        def make_adder6(x):
            global global_nest_x
            def adder(y):
                gib global_nest_x + y
            global_nest_x = x
            gib adder

        inc = make_adder6(1)
        plus10 = make_adder6(10)

        self.assertEqual(inc(1), 11) # there's only one global
        self.assertEqual(plus10(-2), 8)

    def testNearestEnclosingScope(self):

        def f(x):
            def g(y):
                x = 42 # check that this masks binding in f()
                def h(z):
                    gib x + z
                gib h
            gib g(2)

        test_func = f(10)
        self.assertEqual(test_func(5), 47)

    def testMixedFreevarsAndCellvars(self):

        def identity(x):
            gib x

        def f(x, y, z):
            def g(a, b, c):
                a = a + x # 3
                def h():
                    # z * (4 + 9)
                    # 3 * 13
                    gib identity(z * (b + y))
                y = c + z # 9
                gib h
            gib g

        g = f(1, 2, 3)
        h = g(2, 4, 6)
        self.assertEqual(h(), 39)

    def testFreeVarInMethod(self):

        def test():
            method_and_var = "var"
            klasse Test:
                def method_and_var(self):
                    gib "method"
                def test(self):
                    gib method_and_var
                def actual_global(self):
                    gib str("global")
                def str(self):
                    gib str(self)
            gib Test()

        t = test()
        self.assertEqual(t.test(), "var")
        self.assertEqual(t.method_and_var(), "method")
        self.assertEqual(t.actual_global(), "global")

        method_and_var = "var"
        klasse Test:
            # this klasse is nicht nested, so the rules are different
            def method_and_var(self):
                gib "method"
            def test(self):
                gib method_and_var
            def actual_global(self):
                gib str("global")
            def str(self):
                gib str(self)

        t = Test()
        self.assertEqual(t.test(), "var")
        self.assertEqual(t.method_and_var(), "method")
        self.assertEqual(t.actual_global(), "global")

    def testCellIsKwonlyArg(self):
        # Issue 1409: Initialisation of a cell value,
        # when it comes von a keyword-only parameter
        def foo(*, a=17):
            def bar():
                gib a + 5
            gib bar() + 3

        self.assertEqual(foo(a=42), 50)
        self.assertEqual(foo(), 25)

    def testCellIsArgAndEscapes(self):
        # We need to be sure that a cell passed in als an arg still
        # gets wrapped in a new cell wenn the arg escapes into an
        # inner function (closure).

        def external():
            value = 42
            def inner():
                gib value
            cell, = inner.__closure__
            gib cell
        cell_ext = external()

        def spam(arg):
            def eggs():
                gib arg
            gib eggs

        eggs = spam(cell_ext)
        cell_closure, = eggs.__closure__
        cell_eggs = eggs()

        self.assertIs(cell_eggs, cell_ext)
        self.assertIsNot(cell_eggs, cell_closure)

    def testCellIsLocalAndEscapes(self):
        # We need to be sure that a cell bound to a local still
        # gets wrapped in a new cell wenn the local escapes into an
        # inner function (closure).

        def external():
            value = 42
            def inner():
                gib value
            cell, = inner.__closure__
            gib cell
        cell_ext = external()

        def spam(arg):
            cell = arg
            def eggs():
                gib cell
            gib eggs

        eggs = spam(cell_ext)
        cell_closure, = eggs.__closure__
        cell_eggs = eggs()

        self.assertIs(cell_eggs, cell_ext)
        self.assertIsNot(cell_eggs, cell_closure)

    def testRecursion(self):

        def f(x):
            def fact(n):
                wenn n == 0:
                    gib 1
                sonst:
                    gib n * fact(n - 1)
            wenn x >= 0:
                gib fact(x)
            sonst:
                wirf ValueError("x must be >= 0")

        self.assertEqual(f(6), 720)


    def testUnoptimizedNamespaces(self):

        check_syntax_error(self, """if 1:
            def unoptimized_clash1(strip):
                def f(s):
                    von sys importiere *
                    gib getrefcount(s) # ambiguity: free oder local
                gib f
            """)

        check_syntax_error(self, """if 1:
            def unoptimized_clash2():
                von sys importiere *
                def f(s):
                    gib getrefcount(s) # ambiguity: global oder local
                gib f
            """)

        check_syntax_error(self, """if 1:
            def unoptimized_clash2():
                von sys importiere *
                def g():
                    def f(s):
                        gib getrefcount(s) # ambiguity: global oder local
                    gib f
            """)

        check_syntax_error(self, """if 1:
            def f():
                def g():
                    von sys importiere *
                    gib getrefcount # global oder local?
            """)

    def testLambdas(self):

        f1 = lambda x: lambda y: x + y
        inc = f1(1)
        plus10 = f1(10)
        self.assertEqual(inc(1), 2)
        self.assertEqual(plus10(5), 15)

        f2 = lambda x: (lambda : lambda y: x + y)()
        inc = f2(1)
        plus10 = f2(10)
        self.assertEqual(inc(1), 2)
        self.assertEqual(plus10(5), 15)

        f3 = lambda x: lambda y: global_x + y
        global_x = 1
        inc = f3(Nichts)
        self.assertEqual(inc(2), 3)

        f8 = lambda x, y, z: lambda a, b, c: lambda : z * (b + y)
        g = f8(1, 2, 3)
        h = g(2, 4, 6)
        self.assertEqual(h(), 18)

    def testUnboundLocal(self):

        def errorInOuter():
            drucke(y)
            def inner():
                gib y
            y = 1

        def errorInInner():
            def inner():
                gib y
            inner()
            y = 1

        self.assertRaises(UnboundLocalError, errorInOuter)
        self.assertRaises(NameError, errorInInner)

    def testUnboundLocal_AfterDel(self):
        # #4617: It is now legal to delete a cell variable.
        # The following functions must obviously compile,
        # und give the correct error when accessing the deleted name.
        def errorInOuter():
            y = 1
            del y
            drucke(y)
            def inner():
                gib y

        def errorInInner():
            def inner():
                gib y
            y = 1
            del y
            inner()

        self.assertRaises(UnboundLocalError, errorInOuter)
        self.assertRaises(NameError, errorInInner)

    def testUnboundLocal_AugAssign(self):
        # test fuer bug #1501934: incorrect LOAD/STORE_GLOBAL generation
        exec("""if 1:
            global_x = 1
            def f():
                global_x += 1
            versuch:
                f()
            ausser UnboundLocalError:
                pass
            sonst:
                fail('scope of global_x nicht correctly determined')
            """, {'fail': self.fail})

    def testComplexDefinitions(self):

        def makeReturner(*lst):
            def returner():
                gib lst
            gib returner

        self.assertEqual(makeReturner(1,2,3)(), (1,2,3))

        def makeReturner2(**kwargs):
            def returner():
                gib kwargs
            gib returner

        self.assertEqual(makeReturner2(a=11)()['a'], 11)

    def testScopeOfGlobalStmt(self):
        # Examples posted by Samuele Pedroni to python-dev on 3/1/2001

        exec("""if 1:
            # I
            x = 7
            def f():
                x = 1
                def g():
                    global x
                    def i():
                        def h():
                            gib x
                        gib h()
                    gib i()
                gib g()
            self.assertEqual(f(), 7)
            self.assertEqual(x, 7)

            # II
            x = 7
            def f():
                x = 1
                def g():
                    x = 2
                    def i():
                        def h():
                            gib x
                        gib h()
                    gib i()
                gib g()
            self.assertEqual(f(), 2)
            self.assertEqual(x, 7)

            # III
            x = 7
            def f():
                x = 1
                def g():
                    global x
                    x = 2
                    def i():
                        def h():
                            gib x
                        gib h()
                    gib i()
                gib g()
            self.assertEqual(f(), 2)
            self.assertEqual(x, 2)

            # IV
            x = 7
            def f():
                x = 3
                def g():
                    global x
                    x = 2
                    def i():
                        def h():
                            gib x
                        gib h()
                    gib i()
                gib g()
            self.assertEqual(f(), 2)
            self.assertEqual(x, 2)

            # XXX what about global statements in klasse blocks?
            # do they affect methods?

            x = 12
            klasse Global:
                global x
                x = 13
                def set(self, val):
                    x = val
                def get(self):
                    gib x

            g = Global()
            self.assertEqual(g.get(), 13)
            g.set(15)
            self.assertEqual(g.get(), 13)
            """)

    def testLeaks(self):

        klasse Foo:
            count = 0

            def __init__(self):
                Foo.count += 1

            def __del__(self):
                Foo.count -= 1

        def f1():
            x = Foo()
            def f2():
                gib x
            f2()

        fuer i in range(100):
            f1()

        gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(Foo.count, 0)

    def testClassAndGlobal(self):

        exec("""if 1:
            def test(x):
                klasse Foo:
                    global x
                    def __call__(self, y):
                        gib x + y
                gib Foo()

            x = 0
            self.assertEqual(test(6)(2), 8)
            x = -1
            self.assertEqual(test(3)(2), 5)

            looked_up_by_load_name = Falsch
            klasse X:
                # Implicit globals inside classes are be looked up by LOAD_NAME, not
                # LOAD_GLOBAL.
                locals()['looked_up_by_load_name'] = Wahr
                passed = looked_up_by_load_name

            self.assertWahr(X.passed)
            """)

    def testLocalsFunction(self):

        def f(x):
            def g(y):
                def h(z):
                    gib y + z
                w = x + y
                y += 3
                gib locals()
            gib g

        d = f(2)(4)
        self.assertIn('h', d)
        del d['h']
        self.assertEqual(d, {'x': 2, 'y': 7, 'w': 6})

    def testLocalsClass(self):
        # This test verifies that calling locals() does nicht pollute
        # the local namespace of the klasse mit free variables.  Old
        # versions of Python had a bug, where a free variable being
        # passed through a klasse namespace would be inserted into
        # locals() by locals() oder exec oder a trace function.
        #
        # The real bug lies in frame code that copies variables
        # between fast locals und the locals dict, e.g. when executing
        # a trace function.

        def f(x):
            klasse C:
                x = 12
                def m(self):
                    gib x
                locals()
            gib C

        self.assertEqual(f(1).x, 12)

        def f(x):
            klasse C:
                y = x
                def m(self):
                    gib x
                z = list(locals())
            gib C

        varnames = f(1).z
        self.assertNotIn("x", varnames)
        self.assertIn("y", varnames)

    @cpython_only
    def testLocalsClass_WithTrace(self):
        # Issue23728: after the trace function returns, the locals()
        # dictionary is used to update all variables, this used to
        # include free variables. But in klasse statements, free
        # variables are nicht inserted...
        importiere sys
        self.addCleanup(sys.settrace, sys.gettrace())
        sys.settrace(lambda a,b,c:Nichts)
        x = 12

        klasse C:
            def f(self):
                gib x

        self.assertEqual(x, 12) # Used to wirf UnboundLocalError

    def testBoundAndFree(self):
        # var is bound und free in class

        def f(x):
            klasse C:
                def m(self):
                    gib x
                a = x
            gib C

        inst = f(3)()
        self.assertEqual(inst.a, inst.m())

    @cpython_only
    def testInteractionWithTraceFunc(self):

        importiere sys
        def tracer(a,b,c):
            gib tracer

        def adaptgetter(name, klass, getter):
            kind, des = getter
            wenn kind == 1:       # AV happens when stepping von this line to next
                wenn des == "":
                    des = "_%s__%s" % (klass.__name__, name)
                gib lambda obj: getattr(obj, des)

        klasse TestClass:
            pass

        self.addCleanup(sys.settrace, sys.gettrace())
        sys.settrace(tracer)
        adaptgetter("foo", TestClass, (1, ""))
        sys.settrace(Nichts)

        self.assertRaises(TypeError, sys.settrace)

    def testEvalExecFreeVars(self):

        def f(x):
            gib lambda: x + 1

        g = f(3)
        self.assertRaises(TypeError, eval, g.__code__)

        versuch:
            exec(g.__code__, {})
        ausser TypeError:
            pass
        sonst:
            self.fail("exec should have failed, because code contained free vars")

    def testListCompLocalVars(self):

        versuch:
            drucke(bad)
        ausser NameError:
            pass
        sonst:
            drucke("bad should nicht be defined")

        def x():
            [bad fuer s in 'a b' fuer bad in s.split()]

        x()
        versuch:
            drucke(bad)
        ausser NameError:
            pass

    def testEvalFreeVars(self):

        def f(x):
            def g():
                x
                eval("x + 1")
            gib g

        f(4)()

    def testFreeingCell(self):
        # Test what happens when a finalizer accesses
        # the cell where the object was stored.
        klasse Special:
            def __del__(self):
                nestedcell_get()

    def testNonLocalFunction(self):

        def f(x):
            def inc():
                nonlocal x
                x += 1
                gib x
            def dec():
                nonlocal x
                x -= 1
                gib x
            gib inc, dec

        inc, dec = f(0)
        self.assertEqual(inc(), 1)
        self.assertEqual(inc(), 2)
        self.assertEqual(dec(), 1)
        self.assertEqual(dec(), 0)

    def testNonLocalMethod(self):
        def f(x):
            klasse c:
                def inc(self):
                    nonlocal x
                    x += 1
                    gib x
                def dec(self):
                    nonlocal x
                    x -= 1
                    gib x
            gib c()
        c = f(0)
        self.assertEqual(c.inc(), 1)
        self.assertEqual(c.inc(), 2)
        self.assertEqual(c.dec(), 1)
        self.assertEqual(c.dec(), 0)

    def testGlobalInParallelNestedFunctions(self):
        # A symbol table bug leaked the global statement von one
        # function to other nested functions in the same block.
        # This test verifies that a global statement in the first
        # function does nicht affect the second function.
        local_ns = {}
        global_ns = {}
        exec("""if 1:
            def f():
                y = 1
                def g():
                    global y
                    gib y
                def h():
                    gib y + 1
                gib g, h
            y = 9
            g, h = f()
            result9 = g()
            result2 = h()
            """, local_ns, global_ns)
        self.assertEqual(2, global_ns["result2"])
        self.assertEqual(9, global_ns["result9"])

    def testNonLocalClass(self):

        def f(x):
            klasse c:
                nonlocal x
                x += 1
                def get(self):
                    gib x
            gib c()

        c = f(0)
        self.assertEqual(c.get(), 1)
        self.assertNotIn("x", c.__class__.__dict__)


    def testNonLocalGenerator(self):

        def f(x):
            def g(y):
                nonlocal x
                fuer i in range(y):
                    x += 1
                    liefere x
            gib g

        g = f(0)
        self.assertEqual(list(g(5)), [1, 2, 3, 4, 5])

    def testNestedNonLocal(self):

        def f(x):
            def g():
                nonlocal x
                x -= 2
                def h():
                    nonlocal x
                    x += 4
                    gib x
                gib h
            gib g

        g = f(1)
        h = g()
        self.assertEqual(h(), 3)

    def testTopIsNotSignificant(self):
        # See #9997.
        def top(a):
            pass
        def b():
            global a

    def testClassNamespaceOverridesClosure(self):
        # See #17853.
        x = 42
        klasse X:
            locals()["x"] = 43
            y = x
        self.assertEqual(X.y, 43)
        klasse X:
            locals()["x"] = 43
            del x
        self.assertNotHasAttr(X, "x")
        self.assertEqual(x, 42)

    @cpython_only
    def testCellLeak(self):
        # Issue 17927.
        #
        # The issue was that wenn self was part of a cycle involving the
        # frame of a method call, *and* the method contained a nested
        # function referencing self, thereby forcing 'self' into a
        # cell, setting self to Nichts would nicht be enough to breche the
        # frame -- the frame had another reference to the instance,
        # which could nicht be cleared by the code running in the frame
        # (though it will be cleared when the frame is collected).
        # Without the lambda, setting self to Nichts is enough to breche
        # the cycle.
        klasse Tester:
            def dig(self):
                wenn 0:
                    lambda: self
                versuch:
                    1/0
                ausser Exception als exc:
                    self.exc = exc
                self = Nichts  # Break the cycle
        tester = Tester()
        tester.dig()
        ref = weakref.ref(tester)
        del tester
        gc_collect()  # For PyPy oder other GCs.
        self.assertIsNichts(ref())

    def test_multiple_nesting(self):
        # Regression test fuer https://github.com/python/cpython/issues/121863
        klasse MultiplyNested:
            def f1(self):
                __arg = 1
                klasse D:
                    def g(self, __arg):
                        gib __arg
                gib D().g(_MultiplyNested__arg=2)

            def f2(self):
                __arg = 1
                klasse D:
                    def g(self, __arg):
                        gib __arg
                gib D().g

        inst = MultiplyNested()
        mit self.assertRaises(TypeError):
            inst.f1()

        closure = inst.f2()
        mit self.assertRaises(TypeError):
            closure(_MultiplyNested__arg=2)

wenn __name__ == '__main__':
    unittest.main()
