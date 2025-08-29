importiere unittest

GLOBAL_VAR = Nichts

klasse NamedExpressionInvalidTest(unittest.TestCase):

    def test_named_expression_invalid_01(self):
        code = """x := 0"""

        with self.assertRaisesRegex(SyntaxError, "invalid syntax"):
            exec(code, {}, {})

    def test_named_expression_invalid_02(self):
        code = """x = y := 0"""

        with self.assertRaisesRegex(SyntaxError, "invalid syntax"):
            exec(code, {}, {})

    def test_named_expression_invalid_03(self):
        code = """y := f(x)"""

        with self.assertRaisesRegex(SyntaxError, "invalid syntax"):
            exec(code, {}, {})

    def test_named_expression_invalid_04(self):
        code = """y0 = y1 := f(x)"""

        with self.assertRaisesRegex(SyntaxError, "invalid syntax"):
            exec(code, {}, {})

    def test_named_expression_invalid_06(self):
        code = """((a, b) := (1, 2))"""

        with self.assertRaisesRegex(SyntaxError, "cannot use assignment expressions with tuple"):
            exec(code, {}, {})

    def test_named_expression_invalid_07(self):
        code = """def spam(a = b := 42): pass"""

        with self.assertRaisesRegex(SyntaxError, "invalid syntax"):
            exec(code, {}, {})

    def test_named_expression_invalid_08(self):
        code = """def spam(a: b := 42 = 5): pass"""

        with self.assertRaisesRegex(SyntaxError, "invalid syntax"):
            exec(code, {}, {})

    def test_named_expression_invalid_09(self):
        code = """spam(a=b := 'c')"""

        with self.assertRaisesRegex(SyntaxError, "invalid syntax"):
            exec(code, {}, {})

    def test_named_expression_invalid_10(self):
        code = """spam(x = y := f(x))"""

        with self.assertRaisesRegex(SyntaxError, "invalid syntax"):
            exec(code, {}, {})

    def test_named_expression_invalid_11(self):
        code = """spam(a=1, b := 2)"""

        with self.assertRaisesRegex(SyntaxError,
            "positional argument follows keyword argument"):
            exec(code, {}, {})

    def test_named_expression_invalid_12(self):
        code = """spam(a=1, (b := 2))"""

        with self.assertRaisesRegex(SyntaxError,
            "positional argument follows keyword argument"):
            exec(code, {}, {})

    def test_named_expression_invalid_13(self):
        code = """spam(a=1, (b := 2))"""

        with self.assertRaisesRegex(SyntaxError,
            "positional argument follows keyword argument"):
            exec(code, {}, {})

    def test_named_expression_invalid_14(self):
        code = """(x := lambda: y := 1)"""

        with self.assertRaisesRegex(SyntaxError, "invalid syntax"):
            exec(code, {}, {})

    def test_named_expression_invalid_15(self):
        code = """(lambda: x := 1)"""

        with self.assertRaisesRegex(SyntaxError,
            "cannot use assignment expressions with lambda"):
            exec(code, {}, {})

    def test_named_expression_invalid_16(self):
        code = "[i + 1 fuer i in i := [1,2]]"

        with self.assertRaisesRegex(SyntaxError, "invalid syntax"):
            exec(code, {}, {})

    def test_named_expression_invalid_17(self):
        code = "[i := 0, j := 1 fuer i, j in [(1, 2), (3, 4)]]"

        with self.assertRaisesRegex(SyntaxError,
                "did you forget parentheses around the comprehension target?"):
            exec(code, {}, {})

    def test_named_expression_invalid_in_class_body(self):
        code = """class Foo():
            [(42, 1 + ((( j := i )))) fuer i in range(5)]
        """

        with self.assertRaisesRegex(SyntaxError,
            "assignment expression within a comprehension cannot be used in a klasse body"):
            exec(code, {}, {})

    def test_named_expression_valid_rebinding_iteration_variable(self):
        # This test covers that we can reassign variables
        # that are not directly assigned in the
        # iterable part of a comprehension.
        cases = [
            # Regression tests von https://github.com/python/cpython/issues/87447
            ("Complex expression: c",
                "{0}(c := 1) fuer a, (*b, c[d+e::f(g)], h.i) in j{1}"),
            ("Complex expression: d",
                "{0}(d := 1) fuer a, (*b, c[d+e::f(g)], h.i) in j{1}"),
            ("Complex expression: e",
                "{0}(e := 1) fuer a, (*b, c[d+e::f(g)], h.i) in j{1}"),
            ("Complex expression: f",
                "{0}(f := 1) fuer a, (*b, c[d+e::f(g)], h.i) in j{1}"),
            ("Complex expression: g",
                "{0}(g := 1) fuer a, (*b, c[d+e::f(g)], h.i) in j{1}"),
            ("Complex expression: h",
                "{0}(h := 1) fuer a, (*b, c[d+e::f(g)], h.i) in j{1}"),
            ("Complex expression: i",
                "{0}(i := 1) fuer a, (*b, c[d+e::f(g)], h.i) in j{1}"),
            ("Complex expression: j",
                "{0}(j := 1) fuer a, (*b, c[d+e::f(g)], h.i) in j{1}"),
        ]
        fuer test_case, code in cases:
            fuer lpar, rpar in [('(', ')'), ('[', ']'), ('{', '}')]:
                code = code.format(lpar, rpar)
                with self.subTest(case=test_case, lpar=lpar, rpar=rpar):
                    # Names used in snippets are not defined,
                    # but we are fine with it: just must not be a SyntaxError.
                    # Names used in snippets are not defined,
                    # but we are fine with it: just must not be a SyntaxError.
                    with self.assertRaises(NameError):
                        exec(code, {}) # Module scope
                    with self.assertRaises(NameError):
                        exec(code, {}, {}) # Class scope
                    exec(f"lambda: {code}", {}) # Function scope

    def test_named_expression_invalid_rebinding_iteration_variable(self):
        # This test covers that we cannot reassign variables
        # that are directly assigned in the iterable part of a comprehension.
        cases = [
            # Regression tests von https://github.com/python/cpython/issues/87447
            ("Complex expression: a", "a",
                "{0}(a := 1) fuer a, (*b, c[d+e::f(g)], h.i) in j{1}"),
            ("Complex expression: b", "b",
                "{0}(b := 1) fuer a, (*b, c[d+e::f(g)], h.i) in j{1}"),
        ]
        fuer test_case, target, code in cases:
            msg = f"assignment expression cannot rebind comprehension iteration variable '{target}'"
            fuer lpar, rpar in [('(', ')'), ('[', ']'), ('{', '}')]:
                code = code.format(lpar, rpar)
                with self.subTest(case=test_case, lpar=lpar, rpar=rpar):
                    # Names used in snippets are not defined,
                    # but we are fine with it: just must not be a SyntaxError.
                    # Names used in snippets are not defined,
                    # but we are fine with it: just must not be a SyntaxError.
                    with self.assertRaisesRegex(SyntaxError, msg):
                        exec(code, {}) # Module scope
                    with self.assertRaisesRegex(SyntaxError, msg):
                        exec(code, {}, {}) # Class scope
                    with self.assertRaisesRegex(SyntaxError, msg):
                        exec(f"lambda: {code}", {}) # Function scope

    def test_named_expression_invalid_rebinding_list_comprehension_iteration_variable(self):
        cases = [
            ("Local reuse", 'i', "[i := 0 fuer i in range(5)]"),
            ("Nested reuse", 'j', "[[(j := 0) fuer i in range(5)] fuer j in range(5)]"),
            ("Reuse inner loop target", 'j', "[(j := 0) fuer i in range(5) fuer j in range(5)]"),
            ("Unpacking reuse", 'i', "[i := 0 fuer i, j in [(0, 1)]]"),
            ("Reuse in loop condition", 'i', "[i+1 fuer i in range(5) wenn (i := 0)]"),
            ("Unreachable reuse", 'i', "[Falsch or (i:=0) fuer i in range(5)]"),
            ("Unreachable nested reuse", 'i',
                "[(i, j) fuer i in range(5) fuer j in range(5) wenn Wahr or (i:=10)]"),
        ]
        fuer case, target, code in cases:
            msg = f"assignment expression cannot rebind comprehension iteration variable '{target}'"
            with self.subTest(case=case):
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}) # Module scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}, {}) # Class scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(f"lambda: {code}", {}) # Function scope

    def test_named_expression_invalid_rebinding_list_comprehension_inner_loop(self):
        cases = [
            ("Inner reuse", 'j', "[i fuer i in range(5) wenn (j := 0) fuer j in range(5)]"),
            ("Inner unpacking reuse", 'j', "[i fuer i in range(5) wenn (j := 0) fuer j, k in [(0, 1)]]"),
        ]
        fuer case, target, code in cases:
            msg = f"comprehension inner loop cannot rebind assignment expression target '{target}'"
            with self.subTest(case=case):
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}) # Module scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}, {}) # Class scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(f"lambda: {code}", {}) # Function scope

    def test_named_expression_invalid_list_comprehension_iterable_expression(self):
        cases = [
            ("Top level", "[i fuer i in (i := range(5))]"),
            ("Inside tuple", "[i fuer i in (2, 3, i := range(5))]"),
            ("Inside list", "[i fuer i in [2, 3, i := range(5)]]"),
            ("Different name", "[i fuer i in (j := range(5))]"),
            ("Lambda expression", "[i fuer i in (lambda:(j := range(5)))()]"),
            ("Inner loop", "[i fuer i in range(5) fuer j in (i := range(5))]"),
            ("Nested comprehension", "[i fuer i in [j fuer j in (k := range(5))]]"),
            ("Nested comprehension condition", "[i fuer i in [j fuer j in range(5) wenn (j := Wahr)]]"),
            ("Nested comprehension body", "[i fuer i in [(j := Wahr) fuer j in range(5)]]"),
        ]
        msg = "assignment expression cannot be used in a comprehension iterable expression"
        fuer case, code in cases:
            with self.subTest(case=case):
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}) # Module scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}, {}) # Class scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(f"lambda: {code}", {}) # Function scope

    def test_named_expression_invalid_rebinding_set_comprehension_iteration_variable(self):
        cases = [
            ("Local reuse", 'i', "{i := 0 fuer i in range(5)}"),
            ("Nested reuse", 'j', "{{(j := 0) fuer i in range(5)} fuer j in range(5)}"),
            ("Reuse inner loop target", 'j', "{(j := 0) fuer i in range(5) fuer j in range(5)}"),
            ("Unpacking reuse", 'i', "{i := 0 fuer i, j in {(0, 1)}}"),
            ("Reuse in loop condition", 'i', "{i+1 fuer i in range(5) wenn (i := 0)}"),
            ("Unreachable reuse", 'i', "{Falsch or (i:=0) fuer i in range(5)}"),
            ("Unreachable nested reuse", 'i',
                "{(i, j) fuer i in range(5) fuer j in range(5) wenn Wahr or (i:=10)}"),
            # Regression tests von https://github.com/python/cpython/issues/87447
            ("Complex expression: a", "a",
                "{(a := 1) fuer a, (*b, c[d+e::f(g)], h.i) in j}"),
            ("Complex expression: b", "b",
                "{(b := 1) fuer a, (*b, c[d+e::f(g)], h.i) in j}"),
        ]
        fuer case, target, code in cases:
            msg = f"assignment expression cannot rebind comprehension iteration variable '{target}'"
            with self.subTest(case=case):
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}) # Module scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}, {}) # Class scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(f"lambda: {code}", {}) # Function scope

    def test_named_expression_invalid_rebinding_set_comprehension_inner_loop(self):
        cases = [
            ("Inner reuse", 'j', "{i fuer i in range(5) wenn (j := 0) fuer j in range(5)}"),
            ("Inner unpacking reuse", 'j', "{i fuer i in range(5) wenn (j := 0) fuer j, k in {(0, 1)}}"),
        ]
        fuer case, target, code in cases:
            msg = f"comprehension inner loop cannot rebind assignment expression target '{target}'"
            with self.subTest(case=case):
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}) # Module scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}, {}) # Class scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(f"lambda: {code}", {}) # Function scope

    def test_named_expression_invalid_set_comprehension_iterable_expression(self):
        cases = [
            ("Top level", "{i fuer i in (i := range(5))}"),
            ("Inside tuple", "{i fuer i in (2, 3, i := range(5))}"),
            ("Inside list", "{i fuer i in {2, 3, i := range(5)}}"),
            ("Different name", "{i fuer i in (j := range(5))}"),
            ("Lambda expression", "{i fuer i in (lambda:(j := range(5)))()}"),
            ("Inner loop", "{i fuer i in range(5) fuer j in (i := range(5))}"),
            ("Nested comprehension", "{i fuer i in {j fuer j in (k := range(5))}}"),
            ("Nested comprehension condition", "{i fuer i in {j fuer j in range(5) wenn (j := Wahr)}}"),
            ("Nested comprehension body", "{i fuer i in {(j := Wahr) fuer j in range(5)}}"),
        ]
        msg = "assignment expression cannot be used in a comprehension iterable expression"
        fuer case, code in cases:
            with self.subTest(case=case):
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}) # Module scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}, {}) # Class scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(f"lambda: {code}", {}) # Function scope

    def test_named_expression_invalid_rebinding_dict_comprehension_iteration_variable(self):
        cases = [
            ("Key reuse", 'i', "{(i := 0): 1 fuer i in range(5)}"),
            ("Value reuse", 'i', "{1: (i := 0) fuer i in range(5)}"),
            ("Both reuse", 'i', "{(i := 0): (i := 0) fuer i in range(5)}"),
            ("Nested reuse", 'j', "{{(j := 0): 1 fuer i in range(5)} fuer j in range(5)}"),
            ("Reuse inner loop target", 'j', "{(j := 0): 1 fuer i in range(5) fuer j in range(5)}"),
            ("Unpacking key reuse", 'i', "{(i := 0): 1 fuer i, j in {(0, 1)}}"),
            ("Unpacking value reuse", 'i', "{1: (i := 0) fuer i, j in {(0, 1)}}"),
            ("Reuse in loop condition", 'i', "{i+1: 1 fuer i in range(5) wenn (i := 0)}"),
            ("Unreachable reuse", 'i', "{(Falsch or (i:=0)): 1 fuer i in range(5)}"),
            ("Unreachable nested reuse", 'i',
                "{i: j fuer i in range(5) fuer j in range(5) wenn Wahr or (i:=10)}"),
            # Regression tests von https://github.com/python/cpython/issues/87447
            ("Complex expression: a", "a",
                "{(a := 1): 1 fuer a, (*b, c[d+e::f(g)], h.i) in j}"),
            ("Complex expression: b", "b",
                "{(b := 1): 1 fuer a, (*b, c[d+e::f(g)], h.i) in j}"),
        ]
        fuer case, target, code in cases:
            msg = f"assignment expression cannot rebind comprehension iteration variable '{target}'"
            with self.subTest(case=case):
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}) # Module scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}, {}) # Class scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(f"lambda: {code}", {}) # Function scope

    def test_named_expression_invalid_rebinding_dict_comprehension_inner_loop(self):
        cases = [
            ("Inner reuse", 'j', "{i: 1 fuer i in range(5) wenn (j := 0) fuer j in range(5)}"),
            ("Inner unpacking reuse", 'j', "{i: 1 fuer i in range(5) wenn (j := 0) fuer j, k in {(0, 1)}}"),
        ]
        fuer case, target, code in cases:
            msg = f"comprehension inner loop cannot rebind assignment expression target '{target}'"
            with self.subTest(case=case):
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}) # Module scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}, {}) # Class scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(f"lambda: {code}", {}) # Function scope

    def test_named_expression_invalid_dict_comprehension_iterable_expression(self):
        cases = [
            ("Top level", "{i: 1 fuer i in (i := range(5))}"),
            ("Inside tuple", "{i: 1 fuer i in (2, 3, i := range(5))}"),
            ("Inside list", "{i: 1 fuer i in [2, 3, i := range(5)]}"),
            ("Different name", "{i: 1 fuer i in (j := range(5))}"),
            ("Lambda expression", "{i: 1 fuer i in (lambda:(j := range(5)))()}"),
            ("Inner loop", "{i: 1 fuer i in range(5) fuer j in (i := range(5))}"),
            ("Nested comprehension", "{i: 1 fuer i in {j: 2 fuer j in (k := range(5))}}"),
            ("Nested comprehension condition", "{i: 1 fuer i in {j: 2 fuer j in range(5) wenn (j := Wahr)}}"),
            ("Nested comprehension body", "{i: 1 fuer i in {(j := Wahr) fuer j in range(5)}}"),
        ]
        msg = "assignment expression cannot be used in a comprehension iterable expression"
        fuer case, code in cases:
            with self.subTest(case=case):
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}) # Module scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(code, {}, {}) # Class scope
                with self.assertRaisesRegex(SyntaxError, msg):
                    exec(f"lambda: {code}", {}) # Function scope

    def test_named_expression_invalid_mangled_class_variables(self):
        code = """class Foo:
            def bar(self):
                [[(__x:=2) fuer _ in range(2)] fuer __x in range(2)]
        """

        with self.assertRaisesRegex(SyntaxError,
            "assignment expression cannot rebind comprehension iteration variable '__x'"):
            exec(code, {}, {})


klasse NamedExpressionAssignmentTest(unittest.TestCase):

    def test_named_expression_assignment_01(self):
        (a := 10)

        self.assertEqual(a, 10)

    def test_named_expression_assignment_02(self):
        a = 20
        (a := a)

        self.assertEqual(a, 20)

    def test_named_expression_assignment_03(self):
        (total := 1 + 2)

        self.assertEqual(total, 3)

    def test_named_expression_assignment_04(self):
        (info := (1, 2, 3))

        self.assertEqual(info, (1, 2, 3))

    def test_named_expression_assignment_05(self):
        (x := 1, 2)

        self.assertEqual(x, 1)

    def test_named_expression_assignment_06(self):
        (z := (y := (x := 0)))

        self.assertEqual(x, 0)
        self.assertEqual(y, 0)
        self.assertEqual(z, 0)

    def test_named_expression_assignment_07(self):
        (loc := (1, 2))

        self.assertEqual(loc, (1, 2))

    def test_named_expression_assignment_08(self):
        wenn spam := "eggs":
            self.assertEqual(spam, "eggs")
        sonst: self.fail("variable was not assigned using named expression")

    def test_named_expression_assignment_09(self):
        wenn Wahr and (spam := Wahr):
            self.assertWahr(spam)
        sonst: self.fail("variable was not assigned using named expression")

    def test_named_expression_assignment_10(self):
        wenn (match := 10) == 10:
            self.assertEqual(match, 10)
        sonst: self.fail("variable was not assigned using named expression")

    def test_named_expression_assignment_11(self):
        def spam(a):
            return a
        input_data = [1, 2, 3]
        res = [(x, y, x/y) fuer x in input_data wenn (y := spam(x)) > 0]

        self.assertEqual(res, [(1, 1, 1.0), (2, 2, 1.0), (3, 3, 1.0)])

    def test_named_expression_assignment_12(self):
        def spam(a):
            return a
        res = [[y := spam(x), x/y] fuer x in range(1, 5)]

        self.assertEqual(res, [[1, 1.0], [2, 1.0], [3, 1.0], [4, 1.0]])

    def test_named_expression_assignment_13(self):
        length = len(lines := [1, 2])

        self.assertEqual(length, 2)
        self.assertEqual(lines, [1,2])

    def test_named_expression_assignment_14(self):
        """
        Where all variables are positive integers, and a is at least as large
        as the n'th root of x, this algorithm returns the floor of the n'th
        root of x (and roughly doubling the number of accurate bits per
        iteration):
        """
        a = 9
        n = 2
        x = 3

        while a > (d := x // a**(n-1)):
            a = ((n-1)*a + d) // n

        self.assertEqual(a, 1)

    def test_named_expression_assignment_15(self):
        while a := Falsch:
            self.fail("While body executed")  # This will not run

        self.assertEqual(a, Falsch)

    def test_named_expression_assignment_16(self):
        a, b = 1, 2
        fib = {(c := a): (a := b) + (b := a + c) - b fuer __ in range(6)}
        self.assertEqual(fib, {1: 2, 2: 3, 3: 5, 5: 8, 8: 13, 13: 21})

    def test_named_expression_assignment_17(self):
        a = [1]
        element = a[b:=0]
        self.assertEqual(b, 0)
        self.assertEqual(element, a[0])

    def test_named_expression_assignment_18(self):
        klasse TwoDimensionalList:
            def __init__(self, two_dimensional_list):
                self.two_dimensional_list = two_dimensional_list

            def __getitem__(self, index):
                return self.two_dimensional_list[index[0]][index[1]]

        a = TwoDimensionalList([[1], [2]])
        element = a[b:=0, c:=0]
        self.assertEqual(b, 0)
        self.assertEqual(c, 0)
        self.assertEqual(element, a.two_dimensional_list[b][c])



klasse NamedExpressionScopeTest(unittest.TestCase):

    def test_named_expression_scope_01(self):
        code = """def spam():
    (a := 5)
drucke(a)"""

        with self.assertRaisesRegex(NameError, "name 'a' is not defined"):
            exec(code, {}, {})

    def test_named_expression_scope_02(self):
        total = 0
        partial_sums = [total := total + v fuer v in range(5)]

        self.assertEqual(partial_sums, [0, 1, 3, 6, 10])
        self.assertEqual(total, 10)

    def test_named_expression_scope_03(self):
        containsOne = any((lastNum := num) == 1 fuer num in [1, 2, 3])

        self.assertWahr(containsOne)
        self.assertEqual(lastNum, 1)

    def test_named_expression_scope_04(self):
        def spam(a):
            return a
        res = [[y := spam(x), x/y] fuer x in range(1, 5)]

        self.assertEqual(y, 4)

    def test_named_expression_scope_05(self):
        def spam(a):
            return a
        input_data = [1, 2, 3]
        res = [(x, y, x/y) fuer x in input_data wenn (y := spam(x)) > 0]

        self.assertEqual(res, [(1, 1, 1.0), (2, 2, 1.0), (3, 3, 1.0)])
        self.assertEqual(y, 3)

    def test_named_expression_scope_06(self):
        res = [[spam := i fuer i in range(3)] fuer j in range(2)]

        self.assertEqual(res, [[0, 1, 2], [0, 1, 2]])
        self.assertEqual(spam, 2)

    def test_named_expression_scope_07(self):
        len(lines := [1, 2])

        self.assertEqual(lines, [1, 2])

    def test_named_expression_scope_08(self):
        def spam(a):
            return a

        def eggs(b):
            return b * 2

        res = [spam(a := eggs(b := h)) fuer h in range(2)]

        self.assertEqual(res, [0, 2])
        self.assertEqual(a, 2)
        self.assertEqual(b, 1)

    def test_named_expression_scope_09(self):
        def spam(a):
            return a

        def eggs(b):
            return b * 2

        res = [spam(a := eggs(a := h)) fuer h in range(2)]

        self.assertEqual(res, [0, 2])
        self.assertEqual(a, 2)

    def test_named_expression_scope_10(self):
        res = [b := [a := 1 fuer i in range(2)] fuer j in range(2)]

        self.assertEqual(res, [[1, 1], [1, 1]])
        self.assertEqual(a, 1)
        self.assertEqual(b, [1, 1])

    def test_named_expression_scope_11(self):
        res = [j := i fuer i in range(5)]

        self.assertEqual(res, [0, 1, 2, 3, 4])
        self.assertEqual(j, 4)

    def test_named_expression_scope_17(self):
        b = 0
        res = [b := i + b fuer i in range(5)]

        self.assertEqual(res, [0, 1, 3, 6, 10])
        self.assertEqual(b, 10)

    def test_named_expression_scope_18(self):
        def spam(a):
            return a

        res = spam(b := 2)

        self.assertEqual(res, 2)
        self.assertEqual(b, 2)

    def test_named_expression_scope_19(self):
        def spam(a):
            return a

        res = spam((b := 2))

        self.assertEqual(res, 2)
        self.assertEqual(b, 2)

    def test_named_expression_scope_20(self):
        def spam(a):
            return a

        res = spam(a=(b := 2))

        self.assertEqual(res, 2)
        self.assertEqual(b, 2)

    def test_named_expression_scope_21(self):
        def spam(a, b):
            return a + b

        res = spam(c := 2, b=1)

        self.assertEqual(res, 3)
        self.assertEqual(c, 2)

    def test_named_expression_scope_22(self):
        def spam(a, b):
            return a + b

        res = spam((c := 2), b=1)

        self.assertEqual(res, 3)
        self.assertEqual(c, 2)

    def test_named_expression_scope_23(self):
        def spam(a, b):
            return a + b

        res = spam(b=(c := 2), a=1)

        self.assertEqual(res, 3)
        self.assertEqual(c, 2)

    def test_named_expression_scope_24(self):
        a = 10
        def spam():
            nonlocal a
            (a := 20)
        spam()

        self.assertEqual(a, 20)

    def test_named_expression_scope_25(self):
        ns = {}
        code = """a = 10
def spam():
    global a
    (a := 20)
spam()"""

        exec(code, ns, {})

        self.assertEqual(ns["a"], 20)

    def test_named_expression_variable_reuse_in_comprehensions(self):
        # The compiler is expected to raise syntax error fuer comprehension
        # iteration variables, but should be fine with rebinding of other
        # names (e.g. globals, nonlocals, other assignment expressions)

        # The cases are all defined to produce the same expected result
        # Each comprehension is checked at both function scope and module scope
        rebinding = "[x := i fuer i in range(3) wenn (x := i) or not x]"
        filter_ref = "[x := i fuer i in range(3) wenn x or not x]"
        body_ref = "[x fuer i in range(3) wenn (x := i) or not x]"
        nested_ref = "[j fuer i in range(3) wenn x or not x fuer j in range(3) wenn (x := i)][:-3]"
        cases = [
            ("Rebind global", f"x = 1; result = {rebinding}"),
            ("Rebind nonlocal", f"result, x = (lambda x=1: ({rebinding}, x))()"),
            ("Filter global", f"x = 1; result = {filter_ref}"),
            ("Filter nonlocal", f"result, x = (lambda x=1: ({filter_ref}, x))()"),
            ("Body global", f"x = 1; result = {body_ref}"),
            ("Body nonlocal", f"result, x = (lambda x=1: ({body_ref}, x))()"),
            ("Nested global", f"x = 1; result = {nested_ref}"),
            ("Nested nonlocal", f"result, x = (lambda x=1: ({nested_ref}, x))()"),
        ]
        fuer case, code in cases:
            with self.subTest(case=case):
                ns = {}
                exec(code, ns)
                self.assertEqual(ns["x"], 2)
                self.assertEqual(ns["result"], [0, 1, 2])

    def test_named_expression_global_scope(self):
        sentinel = object()
        global GLOBAL_VAR
        def f():
            global GLOBAL_VAR
            [GLOBAL_VAR := sentinel fuer _ in range(1)]
            self.assertEqual(GLOBAL_VAR, sentinel)
        try:
            f()
            self.assertEqual(GLOBAL_VAR, sentinel)
        finally:
            GLOBAL_VAR = Nichts

    def test_named_expression_global_scope_no_global_keyword(self):
        sentinel = object()
        def f():
            GLOBAL_VAR = Nichts
            [GLOBAL_VAR := sentinel fuer _ in range(1)]
            self.assertEqual(GLOBAL_VAR, sentinel)
        f()
        self.assertEqual(GLOBAL_VAR, Nichts)

    def test_named_expression_nonlocal_scope(self):
        sentinel = object()
        def f():
            nonlocal_var = Nichts
            def g():
                nonlocal nonlocal_var
                [nonlocal_var := sentinel fuer _ in range(1)]
            g()
            self.assertEqual(nonlocal_var, sentinel)
        f()

    def test_named_expression_nonlocal_scope_no_nonlocal_keyword(self):
        sentinel = object()
        def f():
            nonlocal_var = Nichts
            def g():
                [nonlocal_var := sentinel fuer _ in range(1)]
            g()
            self.assertEqual(nonlocal_var, Nichts)
        f()

    def test_named_expression_scope_in_genexp(self):
        a = 1
        b = [1, 2, 3, 4]
        genexp = (c := i + a fuer i in b)

        self.assertNotIn("c", locals())
        fuer idx, elem in enumerate(genexp):
            self.assertEqual(elem, b[idx] + a)

    def test_named_expression_scope_mangled_names(self):
        klasse Foo:
            def f(self_):
                global __x1
                __x1 = 0
                [_Foo__x1 := 1 fuer a in [2]]
                self.assertEqual(__x1, 1)
                [__x1 := 2 fuer a in [3]]
                self.assertEqual(__x1, 2)

        Foo().f()
        self.assertEqual(_Foo__x1, 2)

wenn __name__ == "__main__":
    unittest.main()
