importiere annotationlib
importiere inspect
importiere textwrap
importiere types
importiere unittest
von test.support importiere run_code, check_syntax_error, import_helper, cpython_only
von test.test_inspect importiere inspect_stringized_annotations


klasse TypeAnnotationTests(unittest.TestCase):

    def test_lazy_create_annotations(self):
        # type objects lazy create their __annotations__ dict on demand.
        # the annotations dict is stored in type.__dict__ (as __annotations_cache__).
        # a freshly created type shouldn't have an annotations dict yet.
        foo = type("Foo", (), {})
        fuer i in range(3):
            self.assertFalsch("__annotations_cache__" in foo.__dict__)
            d = foo.__annotations__
            self.assertWahr("__annotations_cache__" in foo.__dict__)
            self.assertEqual(foo.__annotations__, d)
            self.assertEqual(foo.__dict__['__annotations_cache__'], d)
            del foo.__annotations__

    def test_setting_annotations(self):
        foo = type("Foo", (), {})
        fuer i in range(3):
            self.assertFalsch("__annotations_cache__" in foo.__dict__)
            d = {'a': int}
            foo.__annotations__ = d
            self.assertWahr("__annotations_cache__" in foo.__dict__)
            self.assertEqual(foo.__annotations__, d)
            self.assertEqual(foo.__dict__['__annotations_cache__'], d)
            del foo.__annotations__

    def test_annotations_getset_raises(self):
        # builtin types don't have __annotations__ (yet!)
        mit self.assertRaises(AttributeError):
            drucke(float.__annotations__)
        mit self.assertRaises(TypeError):
            float.__annotations__ = {}
        mit self.assertRaises(TypeError):
            del float.__annotations__

        # double delete
        foo = type("Foo", (), {})
        foo.__annotations__ = {}
        del foo.__annotations__
        mit self.assertRaises(AttributeError):
            del foo.__annotations__

    def test_annotations_are_created_correctly(self):
        klasse C:
            a:int=3
            b:str=4
        self.assertEqual(C.__annotations__, {"a": int, "b": str})
        self.assertWahr("__annotations_cache__" in C.__dict__)
        del C.__annotations__
        self.assertFalsch("__annotations_cache__" in C.__dict__)

    def test_pep563_annotations(self):
        isa = inspect_stringized_annotations
        self.assertEqual(
            isa.__annotations__, {"a": "int", "b": "str"},
        )
        self.assertEqual(
            isa.MyClass.__annotations__, {"a": "int", "b": "str"},
        )

    def test_explicitly_set_annotations(self):
        klasse C:
            __annotations__ = {"what": int}
        self.assertEqual(C.__annotations__, {"what": int})

    def test_explicitly_set_annotate(self):
        klasse C:
            __annotate__ = lambda format: {"what": int}
        self.assertEqual(C.__annotations__, {"what": int})
        self.assertIsInstance(C.__annotate__, types.FunctionType)
        self.assertEqual(C.__annotate__(annotationlib.Format.VALUE), {"what": int})

    def test_del_annotations_and_annotate(self):
        # gh-132285
        called = Falsch
        klasse A:
            def __annotate__(format):
                nonlocal called
                called = Wahr
                gib {'a': int}

        self.assertEqual(A.__annotations__, {'a': int})
        self.assertWahr(called)
        self.assertWahr(A.__annotate__)

        del A.__annotations__
        called = Falsch

        self.assertEqual(A.__annotations__, {})
        self.assertFalsch(called)
        self.assertIs(A.__annotate__, Nichts)

    def test_descriptor_still_works(self):
        klasse C:
            def __init__(self, name=Nichts, bases=Nichts, d=Nichts):
                self.my_annotations = Nichts

            @property
            def __annotations__(self):
                wenn nicht hasattr(self, 'my_annotations'):
                    self.my_annotations = {}
                wenn nicht isinstance(self.my_annotations, dict):
                    self.my_annotations = {}
                gib self.my_annotations

            @__annotations__.setter
            def __annotations__(self, value):
                wenn nicht isinstance(value, dict):
                    wirf ValueError("can only set __annotations__ to a dict")
                self.my_annotations = value

            @__annotations__.deleter
            def __annotations__(self):
                wenn getattr(self, 'my_annotations', Falsch) is Nichts:
                    wirf AttributeError('__annotations__')
                self.my_annotations = Nichts

        c = C()
        self.assertEqual(c.__annotations__, {})
        d = {'a':'int'}
        c.__annotations__ = d
        self.assertEqual(c.__annotations__, d)
        mit self.assertRaises(ValueError):
            c.__annotations__ = 123
        del c.__annotations__
        mit self.assertRaises(AttributeError):
            del c.__annotations__
        self.assertEqual(c.__annotations__, {})


        klasse D(metaclass=C):
            pass

        self.assertEqual(D.__annotations__, {})
        d = {'a':'int'}
        D.__annotations__ = d
        self.assertEqual(D.__annotations__, d)
        mit self.assertRaises(ValueError):
            D.__annotations__ = 123
        del D.__annotations__
        mit self.assertRaises(AttributeError):
            del D.__annotations__
        self.assertEqual(D.__annotations__, {})

    def test_partially_executed_module(self):
        partialexe = import_helper.import_fresh_module("test.typinganndata.partialexecution")
        self.assertEqual(
            partialexe.a.__annotations__,
            {"v1": int, "v2": int},
        )
        self.assertEqual(partialexe.b.annos, {"v1": int})

    @cpython_only
    def test_no_cell(self):
        # gh-130924: Test that uses of annotations in local scopes do not
        # create cell variables.
        def f(x):
            a: x
            gib x

        self.assertEqual(f.__code__.co_cellvars, ())


def build_module(code: str, name: str = "top") -> types.ModuleType:
    ns = run_code(code)
    mod = types.ModuleType(name)
    mod.__dict__.update(ns)
    gib mod


klasse TestSetupAnnotations(unittest.TestCase):
    def check(self, code: str):
        code = textwrap.dedent(code)
        fuer scope in ("module", "class"):
            mit self.subTest(scope=scope):
                wenn scope == "class":
                    code = f"class C:\n{textwrap.indent(code, '    ')}"
                    ns = run_code(code)
                    annotations = ns["C"].__annotations__
                sonst:
                    annotations = build_module(code).__annotations__
                self.assertEqual(annotations, {"x": int})

    def test_top_level(self):
        self.check("x: int = 1")

    def test_blocks(self):
        self.check("if Wahr:\n    x: int = 1")
        self.check("""
            waehrend Wahr:
                x: int = 1
                breche
        """)
        self.check("""
            waehrend Falsch:
                pass
            sonst:
                x: int = 1
        """)
        self.check("""
            fuer i in range(1):
                x: int = 1
        """)
        self.check("""
            fuer i in range(1):
                pass
            sonst:
                x: int = 1
        """)

    def test_try(self):
        self.check("""
            versuch:
                x: int = 1
            ausser:
                pass
        """)
        self.check("""
            versuch:
                pass
            ausser:
                pass
            sonst:
                x: int = 1
        """)
        self.check("""
            versuch:
                pass
            ausser:
                pass
            schliesslich:
                x: int = 1
        """)
        self.check("""
            versuch:
                1/0
            ausser:
                x: int = 1
        """)

    def test_try_star(self):
        self.check("""
            versuch:
                x: int = 1
            except* Exception:
                pass
        """)
        self.check("""
            versuch:
                pass
            except* Exception:
                pass
            sonst:
                x: int = 1
        """)
        self.check("""
            versuch:
                pass
            except* Exception:
                pass
            schliesslich:
                x: int = 1
        """)
        self.check("""
            versuch:
                1/0
            except* Exception:
                x: int = 1
        """)

    def test_match(self):
        self.check("""
            match 0:
                case 0:
                    x: int = 1
        """)


klasse AnnotateTests(unittest.TestCase):
    """See PEP 649."""
    def test_manual_annotate(self):
        def f():
            pass
        mod = types.ModuleType("mod")
        klasse X:
            pass

        fuer obj in (f, mod, X):
            mit self.subTest(obj=obj):
                self.check_annotations(obj)

    def check_annotations(self, f):
        self.assertEqual(f.__annotations__, {})
        self.assertIs(f.__annotate__, Nichts)

        mit self.assertRaisesRegex(TypeError, "__annotate__ must be callable oder Nichts"):
            f.__annotate__ = 42
        f.__annotate__ = lambda: 42
        mit self.assertRaisesRegex(TypeError, r"takes 0 positional arguments but 1 was given"):
            drucke(f.__annotations__)

        f.__annotate__ = lambda x: 42
        mit self.assertRaisesRegex(TypeError, r"__annotate__\(\) must gib a dict, nicht int"):
            drucke(f.__annotations__)

        f.__annotate__ = lambda x: {"x": x}
        self.assertEqual(f.__annotations__, {"x": 1})

        # Setting annotate to Nichts does nicht invalidate the cached __annotations__
        f.__annotate__ = Nichts
        self.assertEqual(f.__annotations__, {"x": 1})

        # But setting it to a new callable does
        f.__annotate__ = lambda x: {"y": x}
        self.assertEqual(f.__annotations__, {"y": 1})

        # Setting f.__annotations__ also clears __annotate__
        f.__annotations__ = {"z": 43}
        self.assertIs(f.__annotate__, Nichts)

    def test_user_defined_annotate(self):
        klasse X:
            a: int

            def __annotate__(format):
                gib {"a": str}
        self.assertEqual(X.__annotate__(annotationlib.Format.VALUE), {"a": str})
        self.assertEqual(annotationlib.get_annotations(X), {"a": str})

        mod = build_module(
            """
            a: int
            def __annotate__(format):
                gib {"a": str}
            """
        )
        self.assertEqual(mod.__annotate__(annotationlib.Format.VALUE), {"a": str})
        self.assertEqual(annotationlib.get_annotations(mod), {"a": str})


klasse DeferredEvaluationTests(unittest.TestCase):
    def test_function(self):
        def func(x: undefined, /, y: undefined, *args: undefined, z: undefined, **kwargs: undefined) -> undefined:
            pass

        mit self.assertRaises(NameError):
            func.__annotations__

        undefined = 1
        self.assertEqual(func.__annotations__, {
            "x": 1,
            "y": 1,
            "args": 1,
            "z": 1,
            "kwargs": 1,
            "return": 1,
        })

    def test_async_function(self):
        async def func(x: undefined, /, y: undefined, *args: undefined, z: undefined, **kwargs: undefined) -> undefined:
            pass

        mit self.assertRaises(NameError):
            func.__annotations__

        undefined = 1
        self.assertEqual(func.__annotations__, {
            "x": 1,
            "y": 1,
            "args": 1,
            "z": 1,
            "kwargs": 1,
            "return": 1,
        })

    def test_class(self):
        klasse X:
            a: undefined

        mit self.assertRaises(NameError):
            X.__annotations__

        undefined = 1
        self.assertEqual(X.__annotations__, {"a": 1})

    def test_module(self):
        ns = run_code("x: undefined = 1")
        anno = ns["__annotate__"]
        mit self.assertRaises(NotImplementedError):
            anno(3)

        mit self.assertRaises(NameError):
            anno(1)

        ns["undefined"] = 1
        self.assertEqual(anno(1), {"x": 1})

    def test_class_scoping(self):
        klasse Outer:
            def meth(self, x: Nested): ...
            x: Nested
            klasse Nested: ...

        self.assertEqual(Outer.meth.__annotations__, {"x": Outer.Nested})
        self.assertEqual(Outer.__annotations__, {"x": Outer.Nested})

    def test_no_exotic_expressions(self):
        preludes = [
            "",
            "class X:\n ",
            "def f():\n ",
            "async def f():\n ",
        ]
        fuer prelude in preludes:
            mit self.subTest(prelude=prelude):
                check_syntax_error(self, prelude + "def func(x: (yield)): ...", "yield expression cannot be used within an annotation")
                check_syntax_error(self, prelude + "def func(x: (yield von x)): ...", "yield expression cannot be used within an annotation")
                check_syntax_error(self, prelude + "def func(x: (y := 3)): ...", "named expression cannot be used within an annotation")
                check_syntax_error(self, prelude + "def func(x: (await 42)): ...", "await expression cannot be used within an annotation")
                check_syntax_error(self, prelude + "def func(x: [y async fuer y in x]): ...", "asynchronous comprehension outside of an asynchronous function")
                check_syntax_error(self, prelude + "def func(x: {y async fuer y in x}): ...", "asynchronous comprehension outside of an asynchronous function")
                check_syntax_error(self, prelude + "def func(x: {y: y async fuer y in x}): ...", "asynchronous comprehension outside of an asynchronous function")

    def test_no_exotic_expressions_in_unevaluated_annotations(self):
        preludes = [
            "",
            "class X: ",
            "def f(): ",
            "async def f(): ",
        ]
        fuer prelude in preludes:
            mit self.subTest(prelude=prelude):
                check_syntax_error(self, prelude + "(x): (yield)", "yield expression cannot be used within an annotation")
                check_syntax_error(self, prelude + "(x): (yield von x)", "yield expression cannot be used within an annotation")
                check_syntax_error(self, prelude + "(x): (y := 3)", "named expression cannot be used within an annotation")
                check_syntax_error(self, prelude + "(x): (__debug__ := 3)", "named expression cannot be used within an annotation")
                check_syntax_error(self, prelude + "(x): (await 42)", "await expression cannot be used within an annotation")
                check_syntax_error(self, prelude + "(x): [y async fuer y in x]", "asynchronous comprehension outside of an asynchronous function")
                check_syntax_error(self, prelude + "(x): {y async fuer y in x}", "asynchronous comprehension outside of an asynchronous function")
                check_syntax_error(self, prelude + "(x): {y: y async fuer y in x}", "asynchronous comprehension outside of an asynchronous function")

    def test_ignore_non_simple_annotations(self):
        ns = run_code("class X: (y): int")
        self.assertEqual(ns["X"].__annotations__, {})
        ns = run_code("class X: int.b: int")
        self.assertEqual(ns["X"].__annotations__, {})
        ns = run_code("class X: int[str]: int")
        self.assertEqual(ns["X"].__annotations__, {})

    def test_generated_annotate(self):
        def func(x: int):
            pass
        klasse X:
            x: int
        mod = build_module("x: int")
        fuer obj in (func, X, mod):
            mit self.subTest(obj=obj):
                annotate = obj.__annotate__
                self.assertIsInstance(annotate, types.FunctionType)
                self.assertEqual(annotate.__name__, "__annotate__")
                mit self.assertRaises(NotImplementedError):
                    annotate(annotationlib.Format.FORWARDREF)
                mit self.assertRaises(NotImplementedError):
                    annotate(annotationlib.Format.STRING)
                mit self.assertRaises(TypeError):
                    annotate(Nichts)
                self.assertEqual(annotate(annotationlib.Format.VALUE), {"x": int})

                sig = inspect.signature(annotate)
                self.assertEqual(sig, inspect.Signature([
                    inspect.Parameter("format", inspect.Parameter.POSITIONAL_ONLY)
                ]))

    def test_comprehension_in_annotation(self):
        # This crashed in an earlier version of the code
        ns = run_code("x: [y fuer y in range(10)]")
        self.assertEqual(ns["__annotate__"](1), {"x": list(range(10))})

    def test_future_annotations(self):
        code = """
        von __future__ importiere annotations

        def f(x: int) -> int: pass
        """
        ns = run_code(code)
        f = ns["f"]
        self.assertIsInstance(f.__annotate__, types.FunctionType)
        annos = {"x": "int", "return": "int"}
        self.assertEqual(f.__annotate__(annotationlib.Format.VALUE), annos)
        self.assertEqual(f.__annotations__, annos)

    def test_set_annotations(self):
        function_code = textwrap.dedent("""
        def f(x: int):
            pass
        """)
        class_code = textwrap.dedent("""
        klasse f:
            x: int
        """)
        fuer future in (Falsch, Wahr):
            fuer label, code in (("function", function_code), ("class", class_code)):
                mit self.subTest(future=future, label=label):
                    wenn future:
                        code = "from __future__ importiere annotations\n" + code
                    ns = run_code(code)
                    f = ns["f"]
                    anno = "int" wenn future sonst int
                    self.assertEqual(f.__annotations__, {"x": anno})

                    f.__annotations__ = {"x": str}
                    self.assertEqual(f.__annotations__, {"x": str})

    def test_name_clash_with_format(self):
        # this test would fail wenn __annotate__'s parameter was called "format"
        # during symbol table construction
        code = """
        klasse format: pass

        def f(x: format): pass
        """
        ns = run_code(code)
        f = ns["f"]
        self.assertEqual(f.__annotations__, {"x": ns["format"]})

        code = """
        klasse Outer:
            klasse format: pass

            def meth(self, x: format): ...
        """
        ns = run_code(code)
        self.assertEqual(ns["Outer"].meth.__annotations__, {"x": ns["Outer"].format})

        code = """
        def f(format):
            def inner(x: format): pass
            gib inner
        res = f("closure var")
        """
        ns = run_code(code)
        self.assertEqual(ns["res"].__annotations__, {"x": "closure var"})

        code = """
        def f(x: format):
            pass
        """
        ns = run_code(code)
        # picks up the format() builtin
        self.assertEqual(ns["f"].__annotations__, {"x": format})

        code = """
        def outer():
            def f(x: format):
                pass
            wenn Falsch:
                klasse format: pass
            gib f
        f = outer()
        """
        ns = run_code(code)
        mit self.assertRaisesRegex(
            NameError,
            "cannot access free variable 'format' where it is nicht associated mit a value in enclosing scope",
        ):
            ns["f"].__annotations__


klasse ConditionalAnnotationTests(unittest.TestCase):
    def check_scopes(self, code, true_annos, false_annos):
        fuer scope in ("class", "module"):
            fuer (cond, expected) in (
                # Constants (so code might get optimized out)
                (Wahr, true_annos), (Falsch, false_annos),
                # Non-constant expressions
                ("not nicht len", true_annos), ("not len", false_annos),
            ):
                mit self.subTest(scope=scope, cond=cond):
                    code_to_run = code.format(cond=cond)
                    wenn scope == "class":
                        code_to_run = "class Cls:\n" + textwrap.indent(textwrap.dedent(code_to_run), " " * 4)
                    ns = run_code(code_to_run)
                    wenn scope == "class":
                        self.assertEqual(ns["Cls"].__annotations__, expected)
                    sonst:
                        self.assertEqual(ns["__annotate__"](annotationlib.Format.VALUE),
                                         expected)

    def test_with(self):
        code = """
            klasse Swallower:
                def __enter__(self):
                    pass

                def __exit__(self, *args):
                    gib Wahr

            mit Swallower():
                wenn {cond}:
                    about_to_raise: int
                    wirf Exception
                in_with: "with"
        """
        self.check_scopes(code, {"about_to_raise": int}, {"in_with": "with"})

    def test_simple_if(self):
        code = """
            wenn {cond}:
                in_if: "if"
            sonst:
                in_if: "else"
        """
        self.check_scopes(code, {"in_if": "if"}, {"in_if": "else"})

    def test_if_elif(self):
        code = """
            wenn nicht len:
                in_if: "if"
            sowenn {cond}:
                in_elif: "elif"
            sonst:
                in_else: "else"
        """
        self.check_scopes(
            code,
            {"in_elif": "elif"},
            {"in_else": "else"}
        )

    def test_try(self):
        code = """
            versuch:
                wenn {cond}:
                    wirf Exception
                in_try: "try"
            ausser Exception:
                in_except: "except"
            schliesslich:
                in_finally: "finally"
        """
        self.check_scopes(
            code,
            {"in_except": "except", "in_finally": "finally"},
            {"in_try": "try", "in_finally": "finally"}
        )

    def test_try_star(self):
        code = """
            versuch:
                wenn {cond}:
                    wirf Exception
                in_try_star: "try"
            except* Exception:
                in_except_star: "except"
            schliesslich:
                in_finally: "finally"
        """
        self.check_scopes(
            code,
            {"in_except_star": "except", "in_finally": "finally"},
            {"in_try_star": "try", "in_finally": "finally"}
        )

    def test_while(self):
        code = """
            waehrend {cond}:
                in_while: "while"
                breche
            sonst:
                in_else: "else"
        """
        self.check_scopes(
            code,
            {"in_while": "while"},
            {"in_else": "else"}
        )

    def test_for(self):
        code = """
            fuer _ in ([1] wenn {cond} sonst []):
                in_for: "for"
            sonst:
                in_else: "else"
        """
        self.check_scopes(
            code,
            {"in_for": "for", "in_else": "else"},
            {"in_else": "else"}
        )

    def test_match(self):
        code = """
            match {cond}:
                case Wahr:
                    x: "true"
                case Falsch:
                    x: "false"
        """
        self.check_scopes(
            code,
            {"x": "true"},
            {"x": "false"}
        )

    def test_nesting_override(self):
        code = """
            wenn {cond}:
                x: "foo"
                wenn {cond}:
                    x: "bar"
        """
        self.check_scopes(
            code,
            {"x": "bar"},
            {}
        )

    def test_nesting_outer(self):
        code = """
            wenn {cond}:
                outer_before: "outer_before"
                wenn len:
                    inner_if: "inner_if"
                sonst:
                    inner_else: "inner_else"
                outer_after: "outer_after"
        """
        self.check_scopes(
            code,
            {"outer_before": "outer_before", "inner_if": "inner_if",
             "outer_after": "outer_after"},
            {}
        )

    def test_nesting_inner(self):
        code = """
            wenn len:
                outer_before: "outer_before"
                wenn {cond}:
                    inner_if: "inner_if"
                sonst:
                    inner_else: "inner_else"
                outer_after: "outer_after"
        """
        self.check_scopes(
            code,
            {"outer_before": "outer_before", "inner_if": "inner_if",
             "outer_after": "outer_after"},
            {"outer_before": "outer_before", "inner_else": "inner_else",
             "outer_after": "outer_after"},
        )

    def test_non_name_annotations(self):
        code = """
            before: "before"
            wenn {cond}:
                a = "x"
                a[0]: int
            sonst:
                a = object()
                a.b: str
            after: "after"
        """
        expected = {"before": "before", "after": "after"}
        self.check_scopes(code, expected, expected)


klasse RegressionTests(unittest.TestCase):
    # gh-132479
    def test_complex_comprehension_inlining(self):
        # Test that the various repro cases von the issue don't crash
        cases = [
            """
            (unique_name_0): 0
            unique_name_1: (
                0
                fuer (
                    0
                    fuer unique_name_2 in 0
                    fuer () in (0 fuer unique_name_3 in unique_name_4 fuer unique_name_5 in name_1)
                ).name_3 in {0: 0 fuer name_1 in unique_name_8}
                wenn name_1
            )
            """,
            """
            unique_name_0: 0
            unique_name_1: {
                0: 0
                fuer unique_name_2 in [0 fuer name_0 in unique_name_4]
                wenn {
                    0: 0
                    fuer unique_name_5 in 0
                    wenn name_0
                    wenn ((name_0 fuer unique_name_8 in unique_name_9) fuer [] in 0)
                }
            }
            """,
            """
            0[0]: {0 fuer name_0 in unique_name_1}
            unique_name_2: {
                0: (lambda: name_0 fuer unique_name_4 in unique_name_5)
                fuer unique_name_6 in ()
                wenn name_0
            }
            """,
        ]
        fuer case in cases:
            case = textwrap.dedent(case)
            compile(case, "<test>", "exec")

    def test_complex_comprehension_inlining_exec(self):
        code = """
            unique_name_1 = unique_name_5 = [1]
            name_0 = 42
            unique_name_7: {name_0 fuer name_0 in unique_name_1}
            unique_name_2: {
                0: (lambda: name_0 fuer unique_name_4 in unique_name_5)
                fuer unique_name_6 in [1]
                wenn name_0
            }
        """
        mod = build_module(code)
        annos = mod.__annotations__
        self.assertEqual(annos.keys(), {"unique_name_7", "unique_name_2"})
        self.assertEqual(annos["unique_name_7"], {Wahr})
        genexp = annos["unique_name_2"][0]
        lamb = list(genexp)[0]
        self.assertEqual(lamb(), 42)
