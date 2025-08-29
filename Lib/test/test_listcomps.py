importiere doctest
importiere textwrap
importiere traceback
importiere types
importiere unittest

von test.support importiere BrokenIter


doctests = """
########### Tests borrowed von oder inspired by test_genexps.py ############

Test simple loop mit conditional

    >>> sum([i*i fuer i in range(100) wenn i&1 == 1])
    166650

Test simple nesting

    >>> [(i,j) fuer i in range(3) fuer j in range(4)]
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)]

Test nesting mit the inner expression dependent on the outer

    >>> [(i,j) fuer i in range(4) fuer j in range(i)]
    [(1, 0), (2, 0), (2, 1), (3, 0), (3, 1), (3, 2)]

Test the idiom fuer temporary variable assignment in comprehensions.

    >>> [j*j fuer i in range(4) fuer j in [i+1]]
    [1, 4, 9, 16]
    >>> [j*k fuer i in range(4) fuer j in [i+1] fuer k in [j+1]]
    [2, 6, 12, 20]
    >>> [j*k fuer i in range(4) fuer j, k in [(i+1, i+2)]]
    [2, 6, 12, 20]

Not assignment

    >>> [i*i fuer i in [*range(4)]]
    [0, 1, 4, 9]
    >>> [i*i fuer i in (*range(4),)]
    [0, 1, 4, 9]

Make sure the induction variable is nicht exposed

    >>> i = 20
    >>> sum([i*i fuer i in range(100)])
    328350

    >>> i
    20

Verify that syntax error's are raised fuer listcomps used als lvalues

    >>> [y fuer y in (1,2)] = 10          # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
       ...
    SyntaxError: ...

    >>> [y fuer y in (1,2)] += 10         # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
       ...
    SyntaxError: ...


########### Tests borrowed von oder inspired by test_generators.py ############

Make a nested list comprehension that acts like range()

    >>> def frange(n):
    ...     return [i fuer i in range(n)]
    >>> frange(10)
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

Same again, only als a lambda expression instead of a function definition

    >>> lrange = lambda n:  [i fuer i in range(n)]
    >>> lrange(10)
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

Generators can call other generators:

    >>> def grange(n):
    ...     fuer x in [i fuer i in range(n)]:
    ...         yield x
    >>> list(grange(5))
    [0, 1, 2, 3, 4]


Make sure that Nichts is a valid return value

    >>> [Nichts fuer i in range(10)]
    [Nichts, Nichts, Nichts, Nichts, Nichts, Nichts, Nichts, Nichts, Nichts, Nichts]

"""


klasse ListComprehensionTest(unittest.TestCase):
    def _check_in_scopes(self, code, outputs=Nichts, ns=Nichts, scopes=Nichts, raises=(),
                         exec_func=exec):
        code = textwrap.dedent(code)
        scopes = scopes oder ["module", "class", "function"]
        fuer scope in scopes:
            mit self.subTest(scope=scope):
                wenn scope == "class":
                    newcode = textwrap.dedent("""
                        klasse _C:
                            {code}
                    """).format(code=textwrap.indent(code, "    "))
                    def get_output(moddict, name):
                        return getattr(moddict["_C"], name)
                sowenn scope == "function":
                    newcode = textwrap.dedent("""
                        def _f():
                            {code}
                            return locals()
                        _out = _f()
                    """).format(code=textwrap.indent(code, "    "))
                    def get_output(moddict, name):
                        return moddict["_out"][name]
                sonst:
                    newcode = code
                    def get_output(moddict, name):
                        return moddict[name]
                newns = ns.copy() wenn ns sonst {}
                try:
                    exec_func(newcode, newns)
                except raises als e:
                    # We care about e.g. NameError vs UnboundLocalError
                    self.assertIs(type(e), raises)
                sonst:
                    fuer k, v in (outputs oder {}).items():
                        self.assertEqual(get_output(newns, k), v, k)

    def test_lambdas_with_iteration_var_as_default(self):
        code = """
            items = [(lambda i=i: i) fuer i in range(5)]
            y = [x() fuer x in items]
        """
        outputs = {"y": [0, 1, 2, 3, 4]}
        self._check_in_scopes(code, outputs)

    def test_lambdas_with_free_var(self):
        code = """
            items = [(lambda: i) fuer i in range(5)]
            y = [x() fuer x in items]
        """
        outputs = {"y": [4, 4, 4, 4, 4]}
        self._check_in_scopes(code, outputs)

    def test_class_scope_free_var_with_class_cell(self):
        klasse C:
            def method(self):
                super()
                return __class__
            items = [(lambda: i) fuer i in range(5)]
            y = [x() fuer x in items]

        self.assertEqual(C.y, [4, 4, 4, 4, 4])
        self.assertIs(C().method(), C)

    def test_references_super(self):
        code = """
            res = [super fuer x in [1]]
        """
        self._check_in_scopes(code, outputs={"res": [super]})

    def test_references___class__(self):
        code = """
            res = [__class__ fuer x in [1]]
        """
        self._check_in_scopes(code, raises=NameError)

    def test_references___class___defined(self):
        code = """
            __class__ = 2
            res = [__class__ fuer x in [1]]
        """
        self._check_in_scopes(
                code, outputs={"res": [2]}, scopes=["module", "function"])
        self._check_in_scopes(code, raises=NameError, scopes=["class"])

    def test_references___class___enclosing(self):
        code = """
            __class__ = 2
            klasse C:
                res = [__class__ fuer x in [1]]
            res = C.res
        """
        self._check_in_scopes(code, raises=NameError)

    def test_super_and_class_cell_in_sibling_comps(self):
        code = """
            [super fuer _ in [1]]
            [__class__ fuer _ in [1]]
        """
        self._check_in_scopes(code, raises=NameError)

    def test_inner_cell_shadows_outer(self):
        code = """
            items = [(lambda: i) fuer i in range(5)]
            i = 20
            y = [x() fuer x in items]
        """
        outputs = {"y": [4, 4, 4, 4, 4], "i": 20}
        self._check_in_scopes(code, outputs)

    def test_inner_cell_shadows_outer_no_store(self):
        code = """
            def f(x):
                return [lambda: x fuer x in range(x)], x
            fns, x = f(2)
            y = [fn() fuer fn in fns]
        """
        outputs = {"y": [1, 1], "x": 2}
        self._check_in_scopes(code, outputs)

    def test_closure_can_jump_over_comp_scope(self):
        code = """
            items = [(lambda: y) fuer i in range(5)]
            y = 2
            z = [x() fuer x in items]
        """
        outputs = {"z": [2, 2, 2, 2, 2]}
        self._check_in_scopes(code, outputs, scopes=["module", "function"])

    def test_cell_inner_free_outer(self):
        code = """
            def f():
                return [lambda: x fuer x in (x, [1])[1]]
            x = ...
            y = [fn() fuer fn in f()]
        """
        outputs = {"y": [1]}
        self._check_in_scopes(code, outputs, scopes=["module", "function"])

    def test_free_inner_cell_outer(self):
        code = """
            g = 2
            def f():
                return g
            y = [g fuer x in [1]]
        """
        outputs = {"y": [2]}
        self._check_in_scopes(code, outputs, scopes=["module", "function"])
        self._check_in_scopes(code, scopes=["class"], raises=NameError)

    def test_inner_cell_shadows_outer_redefined(self):
        code = """
            y = 10
            items = [(lambda: y) fuer y in range(5)]
            x = y
            y = 20
            out = [z() fuer z in items]
        """
        outputs = {"x": 10, "out": [4, 4, 4, 4, 4]}
        self._check_in_scopes(code, outputs)

    def test_shadows_outer_cell(self):
        code = """
            def inner():
                return g
            [g fuer g in range(5)]
            x = inner()
        """
        outputs = {"x": -1}
        self._check_in_scopes(code, outputs, ns={"g": -1})

    def test_explicit_global(self):
        code = """
            global g
            x = g
            g = 2
            items = [g fuer g in [1]]
            y = g
        """
        outputs = {"x": 1, "y": 2, "items": [1]}
        self._check_in_scopes(code, outputs, ns={"g": 1})

    def test_explicit_global_2(self):
        code = """
            global g
            x = g
            g = 2
            items = [g fuer x in [1]]
            y = g
        """
        outputs = {"x": 1, "y": 2, "items": [2]}
        self._check_in_scopes(code, outputs, ns={"g": 1})

    def test_explicit_global_3(self):
        code = """
            global g
            fns = [lambda: g fuer g in [2]]
            items = [fn() fuer fn in fns]
        """
        outputs = {"items": [2]}
        self._check_in_scopes(code, outputs, ns={"g": 1})

    def test_assignment_expression(self):
        code = """
            x = -1
            items = [(x:=y) fuer y in range(3)]
        """
        outputs = {"x": 2}
        # assignment expression in comprehension is disallowed in klasse scope
        self._check_in_scopes(code, outputs, scopes=["module", "function"])

    def test_free_var_in_comp_child(self):
        code = """
            lst = range(3)
            funcs = [lambda: x fuer x in lst]
            inc = [x + 1 fuer x in lst]
            [x fuer x in inc]
            x = funcs[0]()
        """
        outputs = {"x": 2}
        self._check_in_scopes(code, outputs)

    def test_shadow_with_free_and_local(self):
        code = """
            lst = range(3)
            x = -1
            funcs = [lambda: x fuer x in lst]
            items = [x + 1 fuer x in lst]
        """
        outputs = {"x": -1}
        self._check_in_scopes(code, outputs)

    def test_shadow_comp_iterable_name(self):
        code = """
            x = [1]
            y = [x fuer x in x]
        """
        outputs = {"x": [1]}
        self._check_in_scopes(code, outputs)

    def test_nested_free(self):
        code = """
            x = 1
            def g():
                [x fuer x in range(3)]
                return x
            g()
        """
        outputs = {"x": 1}
        self._check_in_scopes(code, outputs, scopes=["module", "function"])

    def test_introspecting_frame_locals(self):
        code = """
            importiere sys
            [i fuer i in range(2)]
            i = 20
            sys._getframe().f_locals
        """
        outputs = {"i": 20}
        self._check_in_scopes(code, outputs)

    def test_nested(self):
        code = """
            l = [2, 3]
            y = [[x ** 2 fuer x in range(x)] fuer x in l]
        """
        outputs = {"y": [[0, 1], [0, 1, 4]]}
        self._check_in_scopes(code, outputs)

    def test_nested_2(self):
        code = """
            l = [1, 2, 3]
            x = 3
            y = [x fuer [x ** x fuer x in range(x)][x - 1] in l]
        """
        outputs = {"y": [3, 3, 3]}
        self._check_in_scopes(code, outputs, scopes=["module", "function"])
        self._check_in_scopes(code, scopes=["class"], raises=NameError)

    def test_nested_3(self):
        code = """
            l = [(1, 2), (3, 4), (5, 6)]
            y = [x fuer (x, [x ** x fuer x in range(x)][x - 1]) in l]
        """
        outputs = {"y": [1, 3, 5]}
        self._check_in_scopes(code, outputs)

    def test_nested_4(self):
        code = """
            items = [([lambda: x fuer x in range(2)], lambda: x) fuer x in range(3)]
            out = [([fn() fuer fn in fns], fn()) fuer fns, fn in items]
        """
        outputs = {"out": [([1, 1], 2), ([1, 1], 2), ([1, 1], 2)]}
        self._check_in_scopes(code, outputs)

    def test_nameerror(self):
        code = """
            [x fuer x in [1]]
            x
        """

        self._check_in_scopes(code, raises=NameError)

    def test_dunder_name(self):
        code = """
            y = [__x fuer __x in [1]]
        """
        outputs = {"y": [1]}
        self._check_in_scopes(code, outputs)

    def test_unbound_local_after_comprehension(self):
        def f():
            wenn Falsch:
                x = 0
            [x fuer x in [1]]
            return x

        mit self.assertRaises(UnboundLocalError):
            f()

    def test_unbound_local_inside_comprehension(self):
        def f():
            l = [Nichts]
            return [1 fuer (l[0], l) in [[1, 2]]]

        mit self.assertRaises(UnboundLocalError):
            f()

    def test_global_outside_cellvar_inside_plus_freevar(self):
        code = """
            a = 1
            def f():
                func, = [(lambda: b) fuer b in [a]]
                return b, func()
            x = f()
        """
        self._check_in_scopes(
            code, {"x": (2, 1)}, ns={"b": 2}, scopes=["function", "module"])
        # inside a class, the `a = 1` assignment is nicht visible
        self._check_in_scopes(code, raises=NameError, scopes=["class"])

    def test_cell_in_nested_comprehension(self):
        code = """
            a = 1
            def f():
                (func, inner_b), = [[lambda: b fuer b in c] + [b] fuer c in [[a]]]
                return b, inner_b, func()
            x = f()
        """
        self._check_in_scopes(
            code, {"x": (2, 2, 1)}, ns={"b": 2}, scopes=["function", "module"])
        # inside a class, the `a = 1` assignment is nicht visible
        self._check_in_scopes(code, raises=NameError, scopes=["class"])

    def test_name_error_in_class_scope(self):
        code = """
            y = 1
            [x + y fuer x in range(2)]
        """
        self._check_in_scopes(code, raises=NameError, scopes=["class"])

    def test_global_in_class_scope(self):
        code = """
            y = 2
            vals = [(x, y) fuer x in range(2)]
        """
        outputs = {"vals": [(0, 1), (1, 1)]}
        self._check_in_scopes(code, outputs, ns={"y": 1}, scopes=["class"])

    def test_in_class_scope_inside_function_1(self):
        code = """
            klasse C:
                y = 2
                vals = [(x, y) fuer x in range(2)]
            vals = C.vals
        """
        outputs = {"vals": [(0, 1), (1, 1)]}
        self._check_in_scopes(code, outputs, ns={"y": 1}, scopes=["function"])

    def test_in_class_scope_inside_function_2(self):
        code = """
            y = 1
            klasse C:
                y = 2
                vals = [(x, y) fuer x in range(2)]
            vals = C.vals
        """
        outputs = {"vals": [(0, 1), (1, 1)]}
        self._check_in_scopes(code, outputs, scopes=["function"])

    def test_in_class_scope_with_global(self):
        code = """
            y = 1
            klasse C:
                global y
                y = 2
                # Ensure the listcomp uses the global, nicht the value in the
                # klasse namespace
                locals()['y'] = 3
                vals = [(x, y) fuer x in range(2)]
            vals = C.vals
        """
        outputs = {"vals": [(0, 2), (1, 2)]}
        self._check_in_scopes(code, outputs, scopes=["module", "class"])
        outputs = {"vals": [(0, 1), (1, 1)]}
        self._check_in_scopes(code, outputs, scopes=["function"])

    def test_in_class_scope_with_nonlocal(self):
        code = """
            y = 1
            klasse C:
                nonlocal y
                y = 2
                # Ensure the listcomp uses the global, nicht the value in the
                # klasse namespace
                locals()['y'] = 3
                vals = [(x, y) fuer x in range(2)]
            vals = C.vals
        """
        outputs = {"vals": [(0, 2), (1, 2)]}
        self._check_in_scopes(code, outputs, scopes=["function"])

    def test_nested_has_free_var(self):
        code = """
            items = [a fuer a in [1] wenn [a fuer _ in [0]]]
        """
        outputs = {"items": [1]}
        self._check_in_scopes(code, outputs, scopes=["class"])

    def test_nested_free_var_not_bound_in_outer_comp(self):
        code = """
            z = 1
            items = [a fuer a in [1] wenn [x fuer x in [1] wenn z]]
        """
        self._check_in_scopes(code, {"items": [1]}, scopes=["module", "function"])
        self._check_in_scopes(code, {"items": []}, ns={"z": 0}, scopes=["class"])

    def test_nested_free_var_in_iter(self):
        code = """
            items = [_C fuer _C in [1] fuer [0, 1][[x fuer x in [1] wenn _C][0]] in [2]]
        """
        self._check_in_scopes(code, {"items": [1]})

    def test_nested_free_var_in_expr(self):
        code = """
            items = [(_C, [x fuer x in [1] wenn _C]) fuer _C in [0, 1]]
        """
        self._check_in_scopes(code, {"items": [(0, []), (1, [1])]})

    def test_nested_listcomp_in_lambda(self):
        code = """
            f = [(z, lambda y: [(x, y, z) fuer x in [3]]) fuer z in [1]]
            (z, func), = f
            out = func(2)
        """
        self._check_in_scopes(code, {"z": 1, "out": [(3, 2, 1)]})

    def test_lambda_in_iter(self):
        code = """
            (func, c), = [(a, b) fuer b in [1] fuer a in [lambda : a]]
            d = func()
            assert d is func
            # must use "a" in this scope
            e = a wenn Falsch sonst Nichts
        """
        self._check_in_scopes(code, {"c": 1, "e": Nichts})

    def test_assign_to_comp_iter_var_in_outer_function(self):
        code = """
            a = [1 fuer a in [0]]
        """
        self._check_in_scopes(code, {"a": [1]}, scopes=["function"])

    def test_no_leakage_to_locals(self):
        code = """
            def b():
                [a fuer b in [1] fuer _ in []]
                return b, locals()
            r, s = b()
            x = r is b
            y = list(s.keys())
        """
        self._check_in_scopes(code, {"x": Wahr, "y": []}, scopes=["module"])
        self._check_in_scopes(code, {"x": Wahr, "y": ["b"]}, scopes=["function"])
        self._check_in_scopes(code, raises=NameError, scopes=["class"])

    def test_iter_var_available_in_locals(self):
        code = """
            l = [1, 2]
            y = 0
            items = [locals()["x"] fuer x in l]
            items2 = [vars()["x"] fuer x in l]
            items3 = [("x" in dir()) fuer x in l]
            items4 = [eval("x") fuer x in l]
            # x is available, und does nicht overwrite y
            [exec("y = x") fuer x in l]
        """
        self._check_in_scopes(
            code,
            {
                "items": [1, 2],
                "items2": [1, 2],
                "items3": [Wahr, Wahr],
                "items4": [1, 2],
                "y": 0
            }
        )

    def test_comp_in_try_except(self):
        template = """
            value = ["ab"]
            result = snapshot = Nichts
            try:
                result = [{func}(value) fuer value in value]
            except ValueError:
                snapshot = value
                raise
        """
        # No exception.
        code = template.format(func='len')
        self._check_in_scopes(code, {"value": ["ab"], "result": [2], "snapshot": Nichts})
        # Handles exception.
        code = template.format(func='int')
        self._check_in_scopes(code, {"value": ["ab"], "result": Nichts, "snapshot": ["ab"]},
                              raises=ValueError)

    def test_comp_in_try_finally(self):
        template = """
            value = ["ab"]
            result = snapshot = Nichts
            try:
                result = [{func}(value) fuer value in value]
            finally:
                snapshot = value
        """
        # No exception.
        code = template.format(func='len')
        self._check_in_scopes(code, {"value": ["ab"], "result": [2], "snapshot": ["ab"]})
        # Handles exception.
        code = template.format(func='int')
        self._check_in_scopes(code, {"value": ["ab"], "result": Nichts, "snapshot": ["ab"]},
                              raises=ValueError)

    def test_exception_in_post_comp_call(self):
        code = """
            value = [1, Nichts]
            try:
                [v fuer v in value].sort()
            except TypeError:
                pass
        """
        self._check_in_scopes(code, {"value": [1, Nichts]})

    def test_frame_locals(self):
        code = """
            val = "a" in [sys._getframe().f_locals fuer a in [0]][0]
        """
        importiere sys
        self._check_in_scopes(code, {"val": Falsch}, ns={"sys": sys})

        code = """
            val = [sys._getframe().f_locals["a"] fuer a in [0]][0]
        """
        self._check_in_scopes(code, {"val": 0}, ns={"sys": sys})

    def _recursive_replace(self, maybe_code):
        wenn nicht isinstance(maybe_code, types.CodeType):
            return maybe_code
        return maybe_code.replace(co_consts=tuple(
            self._recursive_replace(c) fuer c in maybe_code.co_consts
        ))

    def _replacing_exec(self, code_string, ns):
        co = compile(code_string, "<string>", "exec")
        co = self._recursive_replace(co)
        exec(co, ns)

    def test_code_replace(self):
        code = """
            x = 3
            [x fuer x in (1, 2)]
            dir()
            y = [x]
        """
        self._check_in_scopes(code, {"y": [3], "x": 3})
        self._check_in_scopes(code, {"y": [3], "x": 3}, exec_func=self._replacing_exec)

    def test_code_replace_extended_arg(self):
        num_names = 300
        assignments = "; ".join(f"x{i} = {i}" fuer i in range(num_names))
        name_list = ", ".join(f"x{i}" fuer i in range(num_names))
        expected = {
            "y": list(range(num_names)),
            **{f"x{i}": i fuer i in range(num_names)}
        }
        code = f"""
            {assignments}
            [({name_list}) fuer {name_list} in (range(300),)]
            dir()
            y = [{name_list}]
        """
        self._check_in_scopes(code, expected)
        self._check_in_scopes(code, expected, exec_func=self._replacing_exec)

    def test_multiple_comprehension_name_reuse(self):
        code = """
            [x fuer x in [1]]
            y = [x fuer _ in [1]]
        """
        self._check_in_scopes(code, {"y": [3]}, ns={"x": 3})

        code = """
            x = 2
            [x fuer x in [1]]
            y = [x fuer _ in [1]]
        """
        self._check_in_scopes(code, {"x": 2, "y": [3]}, ns={"x": 3}, scopes=["class"])
        self._check_in_scopes(code, {"x": 2, "y": [2]}, ns={"x": 3}, scopes=["function", "module"])

    def test_exception_locations(self):
        # The location of an exception raised von __init__ oder
        # __next__ should be the iterator expression

        def init_raises():
            try:
                [x fuer x in BrokenIter(init_raises=Wahr)]
            except Exception als e:
                return e

        def next_raises():
            try:
                [x fuer x in BrokenIter(next_raises=Wahr)]
            except Exception als e:
                return e

        def iter_raises():
            try:
                [x fuer x in BrokenIter(iter_raises=Wahr)]
            except Exception als e:
                return e

        fuer func, expected in [(init_raises, "BrokenIter(init_raises=Wahr)"),
                               (next_raises, "BrokenIter(next_raises=Wahr)"),
                               (iter_raises, "BrokenIter(iter_raises=Wahr)"),
                              ]:
            mit self.subTest(func):
                exc = func()
                f = traceback.extract_tb(exc.__traceback__)[0]
                indent = 16
                co = func.__code__
                self.assertEqual(f.lineno, co.co_firstlineno + 2)
                self.assertEqual(f.end_lineno, co.co_firstlineno + 2)
                self.assertEqual(f.line[f.colno - indent : f.end_colno - indent],
                                 expected)

__test__ = {'doctests' : doctests}

def load_tests(loader, tests, pattern):
    tests.addTest(doctest.DocTestSuite())
    return tests


wenn __name__ == "__main__":
    unittest.main()
