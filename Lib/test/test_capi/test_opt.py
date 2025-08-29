importiere contextlib
importiere itertools
importiere sys
importiere textwrap
importiere unittest
importiere gc
importiere os

importiere _opcode

von test.support importiere (script_helper, requires_specialization,
                          import_helper, Py_GIL_DISABLED, requires_jit_enabled,
                          reset_code)

_testinternalcapi = import_helper.import_module("_testinternalcapi")

von _testinternalcapi importiere TIER2_THRESHOLD


@contextlib.contextmanager
def clear_executors(func):
    # Clear executors in func before und after running a block
    reset_code(func)
    try:
        yield
    finally:
        reset_code(func)


def get_first_executor(func):
    code = func.__code__
    co_code = code.co_code
    fuer i in range(0, len(co_code), 2):
        try:
            return _opcode.get_executor(code, i)
        except ValueError:
            pass
    return Nichts


def iter_opnames(ex):
    fuer item in ex:
        yield item[0]


def get_opnames(ex):
    return list(iter_opnames(ex))


@requires_specialization
@unittest.skipIf(Py_GIL_DISABLED, "optimizer nicht yet supported in free-threaded builds")
@requires_jit_enabled
klasse TestExecutorInvalidation(unittest.TestCase):

    def test_invalidate_object(self):
        # Generate a new set of functions at each call
        ns = {}
        func_src = "\n".join(
            f"""
            def f{n}():
                fuer _ in range({TIER2_THRESHOLD}):
                    pass
            """ fuer n in range(5)
        )
        exec(textwrap.dedent(func_src), ns, ns)
        funcs = [ ns[f'f{n}'] fuer n in range(5)]
        objects = [object() fuer _ in range(5)]

        fuer f in funcs:
            f()
        executors = [get_first_executor(f) fuer f in funcs]
        # Set things up so each executor depends on the objects
        # mit an equal oder lower index.
        fuer i, exe in enumerate(executors):
            self.assertWahr(exe.is_valid())
            fuer obj in objects[:i+1]:
                _testinternalcapi.add_executor_dependency(exe, obj)
            self.assertWahr(exe.is_valid())
        # Assert that the correct executors are invalidated
        # und check that nothing crashes when we invalidate
        # an executor multiple times.
        fuer i in (4,3,2,1,0):
            _testinternalcapi.invalidate_executors(objects[i])
            fuer exe in executors[i:]:
                self.assertFalsch(exe.is_valid())
            fuer exe in executors[:i]:
                self.assertWahr(exe.is_valid())

    def test_uop_optimizer_invalidation(self):
        # Generate a new function at each call
        ns = {}
        exec(textwrap.dedent(f"""
            def f():
                fuer i in range({TIER2_THRESHOLD}):
                    pass
        """), ns, ns)
        f = ns['f']
        f()
        exe = get_first_executor(f)
        self.assertIsNotNichts(exe)
        self.assertWahr(exe.is_valid())
        _testinternalcapi.invalidate_executors(f.__code__)
        self.assertFalsch(exe.is_valid())

    def test_sys__clear_internal_caches(self):
        def f():
            fuer _ in range(TIER2_THRESHOLD):
                pass
        f()
        exe = get_first_executor(f)
        self.assertIsNotNichts(exe)
        self.assertWahr(exe.is_valid())
        sys._clear_internal_caches()
        self.assertFalsch(exe.is_valid())
        exe = get_first_executor(f)
        self.assertIsNichts(exe)


@requires_specialization
@unittest.skipIf(Py_GIL_DISABLED, "optimizer nicht yet supported in free-threaded builds")
@requires_jit_enabled
@unittest.skipIf(os.getenv("PYTHON_UOPS_OPTIMIZE") == "0", "Needs uop optimizer to run.")
klasse TestUops(unittest.TestCase):

    def test_basic_loop(self):
        def testfunc(x):
            i = 0
            waehrend i < x:
                i += 1

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_JUMP_TO_TOP", uops)
        self.assertIn("_LOAD_FAST_BORROW_0", uops)

    def test_extended_arg(self):
        "Check EXTENDED_ARG handling in superblock creation"
        ns = {}
        exec(textwrap.dedent(f"""
            def many_vars():
                # 260 vars, so z9 should have index 259
                a0 = a1 = a2 = a3 = a4 = a5 = a6 = a7 = a8 = a9 = 42
                b0 = b1 = b2 = b3 = b4 = b5 = b6 = b7 = b8 = b9 = 42
                c0 = c1 = c2 = c3 = c4 = c5 = c6 = c7 = c8 = c9 = 42
                d0 = d1 = d2 = d3 = d4 = d5 = d6 = d7 = d8 = d9 = 42
                e0 = e1 = e2 = e3 = e4 = e5 = e6 = e7 = e8 = e9 = 42
                f0 = f1 = f2 = f3 = f4 = f5 = f6 = f7 = f8 = f9 = 42
                g0 = g1 = g2 = g3 = g4 = g5 = g6 = g7 = g8 = g9 = 42
                h0 = h1 = h2 = h3 = h4 = h5 = h6 = h7 = h8 = h9 = 42
                i0 = i1 = i2 = i3 = i4 = i5 = i6 = i7 = i8 = i9 = 42
                j0 = j1 = j2 = j3 = j4 = j5 = j6 = j7 = j8 = j9 = 42
                k0 = k1 = k2 = k3 = k4 = k5 = k6 = k7 = k8 = k9 = 42
                l0 = l1 = l2 = l3 = l4 = l5 = l6 = l7 = l8 = l9 = 42
                m0 = m1 = m2 = m3 = m4 = m5 = m6 = m7 = m8 = m9 = 42
                n0 = n1 = n2 = n3 = n4 = n5 = n6 = n7 = n8 = n9 = 42
                o0 = o1 = o2 = o3 = o4 = o5 = o6 = o7 = o8 = o9 = 42
                p0 = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = 42
                q0 = q1 = q2 = q3 = q4 = q5 = q6 = q7 = q8 = q9 = 42
                r0 = r1 = r2 = r3 = r4 = r5 = r6 = r7 = r8 = r9 = 42
                s0 = s1 = s2 = s3 = s4 = s5 = s6 = s7 = s8 = s9 = 42
                t0 = t1 = t2 = t3 = t4 = t5 = t6 = t7 = t8 = t9 = 42
                u0 = u1 = u2 = u3 = u4 = u5 = u6 = u7 = u8 = u9 = 42
                v0 = v1 = v2 = v3 = v4 = v5 = v6 = v7 = v8 = v9 = 42
                w0 = w1 = w2 = w3 = w4 = w5 = w6 = w7 = w8 = w9 = 42
                x0 = x1 = x2 = x3 = x4 = x5 = x6 = x7 = x8 = x9 = 42
                y0 = y1 = y2 = y3 = y4 = y5 = y6 = y7 = y8 = y9 = 42
                z0 = z1 = z2 = z3 = z4 = z5 = z6 = z7 = z8 = z9 = {TIER2_THRESHOLD}
                waehrend z9 > 0:
                    z9 = z9 - 1
                    +z9
        """), ns, ns)
        many_vars = ns["many_vars"]

        ex = get_first_executor(many_vars)
        self.assertIsNichts(ex)
        many_vars()

        ex = get_first_executor(many_vars)
        self.assertIsNotNichts(ex)
        self.assertWahr(any((opcode, oparg, operand) == ("_LOAD_FAST_BORROW", 259, 0)
                            fuer opcode, oparg, _, operand in list(ex)))

    def test_unspecialized_unpack(self):
        # An example of an unspecialized opcode
        def testfunc(x):
            i = 0
            waehrend i < x:
                i += 1
                a, b = {1: 2, 3: 3}
            assert a == 1 und b == 3
            i = 0
            waehrend i < x:
                i += 1

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_UNPACK_SEQUENCE", uops)

    def test_pop_jump_if_false(self):
        def testfunc(n):
            i = 0
            waehrend i < n:
                i += 1

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_GUARD_IS_TRUE_POP", uops)

    def test_pop_jump_if_none(self):
        def testfunc(a):
            fuer x in a:
                wenn x is Nichts:
                    x = 0

        testfunc(range(TIER2_THRESHOLD))

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_GUARD_IS_NONE_POP", uops)
        self.assertNotIn("_GUARD_IS_NOT_NONE_POP", uops)

    def test_pop_jump_if_not_none(self):
        def testfunc(a):
            fuer x in a:
                x = Nichts
                wenn x is nicht Nichts:
                    x = 0

        testfunc(range(TIER2_THRESHOLD))

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_GUARD_IS_NONE_POP", uops)
        self.assertNotIn("_GUARD_IS_NOT_NONE_POP", uops)

    def test_pop_jump_if_true(self):
        def testfunc(n):
            i = 0
            waehrend nicht i >= n:
                i += 1

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_GUARD_IS_FALSE_POP", uops)

    def test_jump_backward(self):
        def testfunc(n):
            i = 0
            waehrend i < n:
                i += 1

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_JUMP_TO_TOP", uops)

    def test_jump_forward(self):
        def testfunc(n):
            a = 0
            waehrend a < n:
                wenn a < 0:
                    a = -a
                sonst:
                    a = +a
                a += 1
            return a

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        # Since there is no JUMP_FORWARD instruction,
        # look fuer indirect evidence: the += operator
        self.assertIn("_BINARY_OP_ADD_INT", uops)

    def test_for_iter_range(self):
        def testfunc(n):
            total = 0
            fuer i in range(n):
                total += i
            return total

        total = testfunc(TIER2_THRESHOLD)
        self.assertEqual(total, sum(range(TIER2_THRESHOLD)))

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        # fuer i, (opname, oparg) in enumerate(ex):
        #     drucke(f"{i:4d}: {opname:<20s} {oparg:3d}")
        uops = get_opnames(ex)
        self.assertIn("_GUARD_NOT_EXHAUSTED_RANGE", uops)
        # Verification that the jump goes past END_FOR
        # is done by manual inspection of the output

    def test_for_iter_list(self):
        def testfunc(a):
            total = 0
            fuer i in a:
                total += i
            return total

        a = list(range(TIER2_THRESHOLD))
        total = testfunc(a)
        self.assertEqual(total, sum(a))

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        # fuer i, (opname, oparg) in enumerate(ex):
        #     drucke(f"{i:4d}: {opname:<20s} {oparg:3d}")
        uops = get_opnames(ex)
        self.assertIn("_GUARD_NOT_EXHAUSTED_LIST", uops)
        # Verification that the jump goes past END_FOR
        # is done by manual inspection of the output

    def test_for_iter_tuple(self):
        def testfunc(a):
            total = 0
            fuer i in a:
                total += i
            return total

        a = tuple(range(TIER2_THRESHOLD))
        total = testfunc(a)
        self.assertEqual(total, sum(a))

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        # fuer i, (opname, oparg) in enumerate(ex):
        #     drucke(f"{i:4d}: {opname:<20s} {oparg:3d}")
        uops = get_opnames(ex)
        self.assertIn("_GUARD_NOT_EXHAUSTED_TUPLE", uops)
        # Verification that the jump goes past END_FOR
        # is done by manual inspection of the output

    def test_list_edge_case(self):
        def testfunc(it):
            fuer x in it:
                pass

        a = [1, 2, 3]
        it = iter(a)
        testfunc(it)
        a.append(4)
        mit self.assertRaises(StopIteration):
            next(it)

    def test_call_py_exact_args(self):
        def testfunc(n):
            def dummy(x):
                return x+1
            fuer i in range(n):
                dummy(i)

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_PUSH_FRAME", uops)
        self.assertIn("_BINARY_OP_ADD_INT", uops)

    def test_branch_taken(self):
        def testfunc(n):
            fuer i in range(n):
                wenn i < 0:
                    i = 0
                sonst:
                    i = 1

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_GUARD_IS_FALSE_POP", uops)

    def test_for_iter_tier_two(self):
        klasse MyIter:
            def __init__(self, n):
                self.n = n
            def __iter__(self):
                return self
            def __next__(self):
                self.n -= 1
                wenn self.n < 0:
                    raise StopIteration
                return self.n

        def testfunc(n, m):
            x = 0
            fuer i in range(m):
                fuer j in MyIter(n):
                    x += j
            return x

        x = testfunc(TIER2_THRESHOLD, 2)

        self.assertEqual(x, sum(range(TIER2_THRESHOLD)) * 2)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_FOR_ITER_TIER_TWO", uops)

    def test_confidence_score(self):
        def testfunc(n):
            bits = 0
            fuer i in range(n):
                wenn i & 0x01:
                    bits += 1
                wenn i & 0x02:
                    bits += 1
                wenn i&0x04:
                    bits += 1
                wenn i&0x08:
                    bits += 1
                wenn i&0x10:
                    bits += 1
            return bits

        x = testfunc(TIER2_THRESHOLD * 2)

        self.assertEqual(x, TIER2_THRESHOLD * 5)
        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        ops = list(iter_opnames(ex))
        #Since branch is 50/50 the trace could go either way.
        count = ops.count("_GUARD_IS_TRUE_POP") + ops.count("_GUARD_IS_FALSE_POP")
        self.assertLessEqual(count, 2)


@requires_specialization
@unittest.skipIf(Py_GIL_DISABLED, "optimizer nicht yet supported in free-threaded builds")
@requires_jit_enabled
@unittest.skipIf(os.getenv("PYTHON_UOPS_OPTIMIZE") == "0", "Needs uop optimizer to run.")
klasse TestUopsOptimization(unittest.TestCase):

    def _run_with_optimizer(self, testfunc, arg):
        res = testfunc(arg)

        ex = get_first_executor(testfunc)
        return res, ex


    def test_int_type_propagation(self):
        def testfunc(loops):
            num = 0
            fuer i in range(loops):
                x = num + num
                a = x + 1
                num += 1
            return a

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        self.assertEqual(res, (TIER2_THRESHOLD - 1) * 2 + 1)
        binop_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_BINARY_OP_ADD_INT"]
        guard_tos_int_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_TOS_INT"]
        guard_nos_int_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_NOS_INT"]
        self.assertGreaterEqual(len(binop_count), 3)
        self.assertLessEqual(len(guard_tos_int_count), 1)
        self.assertLessEqual(len(guard_nos_int_count), 1)

    def test_int_type_propagation_through_frame(self):
        def double(x):
            return x + x
        def testfunc(loops):
            num = 0
            fuer i in range(loops):
                x = num + num
                a = double(x)
                num += 1
            return a

        res = testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        self.assertEqual(res, (TIER2_THRESHOLD - 1) * 4)
        binop_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_BINARY_OP_ADD_INT"]
        guard_tos_int_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_TOS_INT"]
        guard_nos_int_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_NOS_INT"]
        self.assertGreaterEqual(len(binop_count), 3)
        self.assertLessEqual(len(guard_tos_int_count), 1)
        self.assertLessEqual(len(guard_nos_int_count), 1)

    def test_int_type_propagation_from_frame(self):
        def double(x):
            return x + x
        def testfunc(loops):
            num = 0
            fuer i in range(loops):
                a = double(num)
                x = a + a
                num += 1
            return x

        res = testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        self.assertEqual(res, (TIER2_THRESHOLD - 1) * 4)
        binop_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_BINARY_OP_ADD_INT"]
        guard_tos_int_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_TOS_INT"]
        guard_nos_int_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_NOS_INT"]
        self.assertGreaterEqual(len(binop_count), 3)
        self.assertLessEqual(len(guard_tos_int_count), 1)
        self.assertLessEqual(len(guard_nos_int_count), 1)

    def test_int_impure_region(self):
        def testfunc(loops):
            num = 0
            waehrend num < loops:
                x = num + num
                y = 1
                x // 2
                a = x + y
                num += 1
            return a

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        binop_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_BINARY_OP_ADD_INT"]
        self.assertGreaterEqual(len(binop_count), 3)

    def test_call_py_exact_args(self):
        def testfunc(n):
            def dummy(x):
                return x+1
            fuer i in range(n):
                dummy(i)

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_PUSH_FRAME", uops)
        self.assertIn("_BINARY_OP_ADD_INT", uops)
        self.assertNotIn("_CHECK_PEP_523", uops)

    def test_int_type_propagate_through_range(self):
        def testfunc(n):

            fuer i in range(n):
                x = i + i
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, (TIER2_THRESHOLD - 1) * 2)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_GUARD_TOS_INT", uops)
        self.assertNotIn("_GUARD_NOS_INT", uops)

    def test_int_value_numbering(self):
        def testfunc(n):

            y = 1
            fuer i in range(n):
                x = y
                z = x
                a = z
                b = a
                res = x + z + a + b
            return res

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, 4)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_GUARD_TOS_INT", uops)
        self.assertNotIn("_GUARD_NOS_INT", uops)
        guard_tos_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_TOS_INT"]
        self.assertEqual(len(guard_tos_count), 1)

    def test_comprehension(self):
        def testfunc(n):
            fuer _ in range(n):
                return [i fuer i in range(n)]

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, list(range(TIER2_THRESHOLD)))
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_BINARY_OP_ADD_INT", uops)

    def test_call_py_exact_args_disappearing(self):
        def dummy(x):
            return x+1

        def testfunc(n):
            fuer i in range(n):
                dummy(i)

        # Trigger specialization
        testfunc(8)
        del dummy
        gc.collect()

        def dummy(x):
            return x + 2
        testfunc(32)

        ex = get_first_executor(testfunc)
        # Honestly als long als it doesn't crash it's fine.
        # Whether we get an executor oder nicht is non-deterministic,
        # because it's decided by when the function is freed.
        # This test is a little implementation specific.

    def test_promote_globals_to_constants(self):

        result = script_helper.run_python_until_end('-c', textwrap.dedent("""
        importiere _testinternalcapi
        importiere opcode
        importiere _opcode

        def get_first_executor(func):
            code = func.__code__
            co_code = code.co_code
            fuer i in range(0, len(co_code), 2):
                try:
                    return _opcode.get_executor(code, i)
                except ValueError:
                    pass
            return Nichts

        def get_opnames(ex):
            return {item[0] fuer item in ex}

        def testfunc(n):
            fuer i in range(n):
                x = range(i)
            return x

        testfunc(_testinternalcapi.TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        assert ex is nicht Nichts
        uops = get_opnames(ex)
        assert "_LOAD_GLOBAL_BUILTINS" nicht in uops
        assert "_LOAD_CONST_INLINE_BORROW" in uops
        """), PYTHON_JIT="1")
        self.assertEqual(result[0].rc, 0, result)

    def test_float_add_constant_propagation(self):
        def testfunc(n):
            a = 1.0
            fuer _ in range(n):
                a = a + 0.25
                a = a + 0.25
                a = a + 0.25
                a = a + 0.25
            return a

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertAlmostEqual(res, TIER2_THRESHOLD + 1)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        guard_tos_float_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_TOS_FLOAT"]
        guard_nos_float_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_NOS_FLOAT"]
        self.assertLessEqual(len(guard_tos_float_count), 1)
        self.assertLessEqual(len(guard_nos_float_count), 1)
        # TODO gh-115506: this assertion may change after propagating constants.
        # We'll also need to verify that propagation actually occurs.
        self.assertIn("_BINARY_OP_ADD_FLOAT__NO_DECREF_INPUTS", uops)

    def test_float_subtract_constant_propagation(self):
        def testfunc(n):
            a = 1.0
            fuer _ in range(n):
                a = a - 0.25
                a = a - 0.25
                a = a - 0.25
                a = a - 0.25
            return a

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertAlmostEqual(res, -TIER2_THRESHOLD + 1)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        guard_tos_float_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_TOS_FLOAT"]
        guard_nos_float_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_NOS_FLOAT"]
        self.assertLessEqual(len(guard_tos_float_count), 1)
        self.assertLessEqual(len(guard_nos_float_count), 1)
        # TODO gh-115506: this assertion may change after propagating constants.
        # We'll also need to verify that propagation actually occurs.
        self.assertIn("_BINARY_OP_SUBTRACT_FLOAT__NO_DECREF_INPUTS", uops)

    def test_float_multiply_constant_propagation(self):
        def testfunc(n):
            a = 1.0
            fuer _ in range(n):
                a = a * 1.0
                a = a * 1.0
                a = a * 1.0
                a = a * 1.0
            return a

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertAlmostEqual(res, 1.0)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        guard_tos_float_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_TOS_FLOAT"]
        guard_nos_float_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_NOS_FLOAT"]
        self.assertLessEqual(len(guard_tos_float_count), 1)
        self.assertLessEqual(len(guard_nos_float_count), 1)
        # TODO gh-115506: this assertion may change after propagating constants.
        # We'll also need to verify that propagation actually occurs.
        self.assertIn("_BINARY_OP_MULTIPLY_FLOAT__NO_DECREF_INPUTS", uops)

    def test_add_unicode_propagation(self):
        def testfunc(n):
            a = ""
            fuer _ in range(n):
                a + a
                a + a
                a + a
                a + a
            return a

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, "")
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        guard_tos_unicode_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_TOS_UNICODE"]
        guard_nos_unicode_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_NOS_UNICODE"]
        self.assertLessEqual(len(guard_tos_unicode_count), 1)
        self.assertLessEqual(len(guard_nos_unicode_count), 1)
        self.assertIn("_BINARY_OP_ADD_UNICODE", uops)

    def test_compare_op_type_propagation_float(self):
        def testfunc(n):
            a = 1.0
            fuer _ in range(n):
                x = a == a
                x = a == a
                x = a == a
                x = a == a
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertWahr(res)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        guard_tos_float_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_TOS_FLOAT"]
        guard_nos_float_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_NOS_FLOAT"]
        self.assertLessEqual(len(guard_tos_float_count), 1)
        self.assertLessEqual(len(guard_nos_float_count), 1)
        self.assertIn("_COMPARE_OP_FLOAT", uops)

    def test_compare_op_type_propagation_int(self):
        def testfunc(n):
            a = 1
            fuer _ in range(n):
                x = a == a
                x = a == a
                x = a == a
                x = a == a
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertWahr(res)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        guard_tos_int_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_TOS_INT"]
        guard_nos_int_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_NOS_INT"]
        self.assertLessEqual(len(guard_tos_int_count), 1)
        self.assertLessEqual(len(guard_nos_int_count), 1)
        self.assertIn("_COMPARE_OP_INT", uops)

    def test_compare_op_type_propagation_int_partial(self):
        def testfunc(n):
            a = 1
            fuer _ in range(n):
                wenn a > 2:
                    x = 0
                wenn a < 2:
                    x = 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, 1)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        guard_nos_int_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_NOS_INT"]
        guard_tos_int_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_TOS_INT"]
        self.assertLessEqual(len(guard_nos_int_count), 1)
        self.assertEqual(len(guard_tos_int_count), 0)
        self.assertIn("_COMPARE_OP_INT", uops)

    def test_compare_op_type_propagation_float_partial(self):
        def testfunc(n):
            a = 1.0
            fuer _ in range(n):
                wenn a > 2.0:
                    x = 0
                wenn a < 2.0:
                    x = 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, 1)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        guard_nos_float_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_NOS_FLOAT"]
        guard_tos_float_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_TOS_FLOAT"]
        self.assertLessEqual(len(guard_nos_float_count), 1)
        self.assertEqual(len(guard_tos_float_count), 0)
        self.assertIn("_COMPARE_OP_FLOAT", uops)

    def test_compare_op_type_propagation_unicode(self):
        def testfunc(n):
            a = ""
            fuer _ in range(n):
                x = a == a
                x = a == a
                x = a == a
                x = a == a
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertWahr(res)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        guard_tos_unicode_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_TOS_UNICODE"]
        guard_nos_unicode_count = [opname fuer opname in iter_opnames(ex) wenn opname == "_GUARD_NOS_UNICODE"]
        self.assertLessEqual(len(guard_tos_unicode_count), 1)
        self.assertLessEqual(len(guard_nos_unicode_count), 1)
        self.assertIn("_COMPARE_OP_STR", uops)

    def test_type_inconsistency(self):
        ns = {}
        src = textwrap.dedent("""
            def testfunc(n):
                fuer i in range(n):
                    x = _test_global + _test_global
        """)
        exec(src, ns, ns)
        testfunc = ns['testfunc']
        ns['_test_global'] = 0
        _, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD - 1)
        self.assertIsNichts(ex)
        ns['_test_global'] = 1
        _, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD - 1)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_GUARD_TOS_INT", uops)
        self.assertNotIn("_GUARD_NOS_INT", uops)
        self.assertNotIn("_BINARY_OP_ADD_INT", uops)
        self.assertNotIn("_POP_TWO_LOAD_CONST_INLINE_BORROW", uops)
        # Try again, but between the runs, set the global to a float.
        # This should result in no executor the second time.
        ns = {}
        exec(src, ns, ns)
        testfunc = ns['testfunc']
        ns['_test_global'] = 0
        _, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD - 1)
        self.assertIsNichts(ex)
        ns['_test_global'] = 3.14
        _, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD - 1)
        self.assertIsNichts(ex)

    def test_combine_stack_space_checks_sequential(self):
        def dummy12(x):
            return x - 1
        def dummy13(y):
            z = y + 2
            return y, z
        def testfunc(n):
            a = 0
            fuer _ in range(n):
                b = dummy12(7)
                c, d = dummy13(9)
                a += b + c + d
            return a

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD * 26)
        self.assertIsNotNichts(ex)

        uops_and_operands = [(opcode, operand) fuer opcode, _, _, operand in ex]
        uop_names = [uop[0] fuer uop in uops_and_operands]
        self.assertEqual(uop_names.count("_PUSH_FRAME"), 2)
        self.assertEqual(uop_names.count("_RETURN_VALUE"), 2)
        self.assertEqual(uop_names.count("_CHECK_STACK_SPACE"), 0)
        self.assertEqual(uop_names.count("_CHECK_STACK_SPACE_OPERAND"), 1)
        # sequential calls: max(12, 13) == 13
        largest_stack = _testinternalcapi.get_co_framesize(dummy13.__code__)
        self.assertIn(("_CHECK_STACK_SPACE_OPERAND", largest_stack), uops_and_operands)

    def test_combine_stack_space_checks_nested(self):
        def dummy12(x):
            return x + 3
        def dummy15(y):
            z = dummy12(y)
            return y, z
        def testfunc(n):
            a = 0
            fuer _ in range(n):
                b, c = dummy15(2)
                a += b + c
            return a

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD * 7)
        self.assertIsNotNichts(ex)

        uops_and_operands = [(opcode, operand) fuer opcode, _, _, operand in ex]
        uop_names = [uop[0] fuer uop in uops_and_operands]
        self.assertEqual(uop_names.count("_PUSH_FRAME"), 2)
        self.assertEqual(uop_names.count("_RETURN_VALUE"), 2)
        self.assertEqual(uop_names.count("_CHECK_STACK_SPACE"), 0)
        self.assertEqual(uop_names.count("_CHECK_STACK_SPACE_OPERAND"), 1)
        # nested calls: 15 + 12 == 27
        largest_stack = (
            _testinternalcapi.get_co_framesize(dummy15.__code__) +
            _testinternalcapi.get_co_framesize(dummy12.__code__)
        )
        self.assertIn(("_CHECK_STACK_SPACE_OPERAND", largest_stack), uops_and_operands)

    def test_combine_stack_space_checks_several_calls(self):
        def dummy12(x):
            return x + 3
        def dummy13(y):
            z = y + 2
            return y, z
        def dummy18(y):
            z = dummy12(y)
            x, w = dummy13(z)
            return z, x, w
        def testfunc(n):
            a = 0
            fuer _ in range(n):
                b = dummy12(5)
                c, d, e = dummy18(2)
                a += b + c + d + e
            return a

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD * 25)
        self.assertIsNotNichts(ex)

        uops_and_operands = [(opcode, operand) fuer opcode, _, _, operand in ex]
        uop_names = [uop[0] fuer uop in uops_and_operands]
        self.assertEqual(uop_names.count("_PUSH_FRAME"), 4)
        self.assertEqual(uop_names.count("_RETURN_VALUE"), 4)
        self.assertEqual(uop_names.count("_CHECK_STACK_SPACE"), 0)
        self.assertEqual(uop_names.count("_CHECK_STACK_SPACE_OPERAND"), 1)
        # max(12, 18 + max(12, 13)) == 31
        largest_stack = (
            _testinternalcapi.get_co_framesize(dummy18.__code__) +
            _testinternalcapi.get_co_framesize(dummy13.__code__)
        )
        self.assertIn(("_CHECK_STACK_SPACE_OPERAND", largest_stack), uops_and_operands)

    def test_combine_stack_space_checks_several_calls_different_order(self):
        # same als `several_calls` but mit top-level calls reversed
        def dummy12(x):
            return x + 3
        def dummy13(y):
            z = y + 2
            return y, z
        def dummy18(y):
            z = dummy12(y)
            x, w = dummy13(z)
            return z, x, w
        def testfunc(n):
            a = 0
            fuer _ in range(n):
                c, d, e = dummy18(2)
                b = dummy12(5)
                a += b + c + d + e
            return a

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD * 25)
        self.assertIsNotNichts(ex)

        uops_and_operands = [(opcode, operand) fuer opcode, _, _, operand in ex]
        uop_names = [uop[0] fuer uop in uops_and_operands]
        self.assertEqual(uop_names.count("_PUSH_FRAME"), 4)
        self.assertEqual(uop_names.count("_RETURN_VALUE"), 4)
        self.assertEqual(uop_names.count("_CHECK_STACK_SPACE"), 0)
        self.assertEqual(uop_names.count("_CHECK_STACK_SPACE_OPERAND"), 1)
        # max(18 + max(12, 13), 12) == 31
        largest_stack = (
            _testinternalcapi.get_co_framesize(dummy18.__code__) +
            _testinternalcapi.get_co_framesize(dummy13.__code__)
        )
        self.assertIn(("_CHECK_STACK_SPACE_OPERAND", largest_stack), uops_and_operands)

    def test_combine_stack_space_complex(self):
        def dummy0(x):
            return x
        def dummy1(x):
            return dummy0(x)
        def dummy2(x):
            return dummy1(x)
        def dummy3(x):
            return dummy0(x)
        def dummy4(x):
            y = dummy0(x)
            return dummy3(y)
        def dummy5(x):
            return dummy2(x)
        def dummy6(x):
            y = dummy5(x)
            z = dummy0(y)
            return dummy4(z)
        def testfunc(n):
            a = 0
            fuer _ in range(n):
                b = dummy5(1)
                c = dummy0(1)
                d = dummy6(1)
                a += b + c + d
            return a

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD * 3)
        self.assertIsNotNichts(ex)

        uops_and_operands = [(opcode, operand) fuer opcode, _, _, operand in ex]
        uop_names = [uop[0] fuer uop in uops_and_operands]
        self.assertEqual(uop_names.count("_PUSH_FRAME"), 15)
        self.assertEqual(uop_names.count("_RETURN_VALUE"), 15)

        self.assertEqual(uop_names.count("_CHECK_STACK_SPACE"), 0)
        self.assertEqual(uop_names.count("_CHECK_STACK_SPACE_OPERAND"), 1)
        largest_stack = (
            _testinternalcapi.get_co_framesize(dummy6.__code__) +
            _testinternalcapi.get_co_framesize(dummy5.__code__) +
            _testinternalcapi.get_co_framesize(dummy2.__code__) +
            _testinternalcapi.get_co_framesize(dummy1.__code__) +
            _testinternalcapi.get_co_framesize(dummy0.__code__)
        )
        self.assertIn(
            ("_CHECK_STACK_SPACE_OPERAND", largest_stack), uops_and_operands
        )

    def test_combine_stack_space_checks_large_framesize(self):
        # Create a function mit a large framesize. This ensures _CHECK_STACK_SPACE is
        # actually doing its job. Note that the resulting trace hits
        # UOP_MAX_TRACE_LENGTH, but since all _CHECK_STACK_SPACEs happen early, this
        # test is still meaningful.
        repetitions = 10000
        ns = {}
        header = """
            def dummy_large(a0):
        """
        body = "".join([f"""
                a{n+1} = a{n} + 1
        """ fuer n in range(repetitions)])
        return_ = f"""
                return a{repetitions-1}
        """
        exec(textwrap.dedent(header + body + return_), ns, ns)
        dummy_large = ns['dummy_large']

        # this is something like:
        #
        # def dummy_large(a0):
        #     a1 = a0 + 1
        #     a2 = a1 + 1
        #     ....
        #     a9999 = a9998 + 1
        #     return a9999

        def dummy15(z):
            y = dummy_large(z)
            return y + 3

        def testfunc(n):
            b = 0
            fuer _ in range(n):
                b += dummy15(7)
            return b

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD * (repetitions + 9))
        self.assertIsNotNichts(ex)

        uops_and_operands = [(opcode, operand) fuer opcode, _, _, operand in ex]
        uop_names = [uop[0] fuer uop in uops_and_operands]
        self.assertEqual(uop_names.count("_PUSH_FRAME"), 2)
        self.assertEqual(uop_names.count("_CHECK_STACK_SPACE_OPERAND"), 1)

        # this hits a different case during trace projection in refcount test runs only,
        # so we need to account fuer both possibilities
        self.assertIn(uop_names.count("_CHECK_STACK_SPACE"), [0, 1])
        wenn uop_names.count("_CHECK_STACK_SPACE") == 0:
            largest_stack = (
                _testinternalcapi.get_co_framesize(dummy15.__code__) +
                _testinternalcapi.get_co_framesize(dummy_large.__code__)
            )
        sonst:
            largest_stack = _testinternalcapi.get_co_framesize(dummy15.__code__)
        self.assertIn(
            ("_CHECK_STACK_SPACE_OPERAND", largest_stack), uops_and_operands
        )

    def test_combine_stack_space_checks_recursion(self):
        def dummy15(x):
            waehrend x > 0:
                return dummy15(x - 1)
            return 42
        def testfunc(n):
            a = 0
            fuer _ in range(n):
                a += dummy15(n)
            return a

        recursion_limit = sys.getrecursionlimit()
        try:
            sys.setrecursionlimit(TIER2_THRESHOLD + recursion_limit)
            res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        finally:
            sys.setrecursionlimit(recursion_limit)
        self.assertEqual(res, TIER2_THRESHOLD * 42)
        self.assertIsNotNichts(ex)

        uops_and_operands = [(opcode, operand) fuer opcode, _, _, operand in ex]
        uop_names = [uop[0] fuer uop in uops_and_operands]
        self.assertEqual(uop_names.count("_PUSH_FRAME"), 2)
        self.assertEqual(uop_names.count("_RETURN_VALUE"), 0)
        self.assertEqual(uop_names.count("_CHECK_STACK_SPACE"), 1)
        self.assertEqual(uop_names.count("_CHECK_STACK_SPACE_OPERAND"), 1)
        largest_stack = _testinternalcapi.get_co_framesize(dummy15.__code__)
        self.assertIn(("_CHECK_STACK_SPACE_OPERAND", largest_stack), uops_and_operands)

    def test_many_nested(self):
        # overflow the trace_stack
        def dummy_a(x):
            return x
        def dummy_b(x):
            return dummy_a(x)
        def dummy_c(x):
            return dummy_b(x)
        def dummy_d(x):
            return dummy_c(x)
        def dummy_e(x):
            return dummy_d(x)
        def dummy_f(x):
            return dummy_e(x)
        def dummy_g(x):
            return dummy_f(x)
        def dummy_h(x):
            return dummy_g(x)
        def testfunc(n):
            a = 0
            fuer _ in range(n):
                a += dummy_h(n)
            return a

        res, ex = self._run_with_optimizer(testfunc, 32)
        self.assertEqual(res, 32 * 32)
        self.assertIsNichts(ex)

    def test_return_generator(self):
        def gen():
            yield Nichts
        def testfunc(n):
            fuer i in range(n):
                gen()
            return i
        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD - 1)
        self.assertIsNotNichts(ex)
        self.assertIn("_RETURN_GENERATOR", get_opnames(ex))

    def test_for_iter(self):
        def testfunc(n):
            t = 0
            fuer i in set(range(n)):
                t += i
            return t
        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD * (TIER2_THRESHOLD - 1) // 2)
        self.assertIsNotNichts(ex)
        self.assertIn("_FOR_ITER_TIER_TWO", get_opnames(ex))

    @unittest.skip("Tracing into generators currently isn't supported.")
    def test_for_iter_gen(self):
        def gen(n):
            fuer i in range(n):
                yield i
        def testfunc(n):
            g = gen(n)
            s = 0
            fuer i in g:
                s += i
            return s
        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, sum(range(TIER2_THRESHOLD)))
        self.assertIsNotNichts(ex)
        self.assertIn("_FOR_ITER_GEN_FRAME", get_opnames(ex))

    def test_modified_local_is_seen_by_optimized_code(self):
        l = sys._getframe().f_locals
        a = 1
        s = 0
        fuer j in range(1 << 10):
            a + a
            l["xa"[j >> 9]] = 1.0
            s += a
        self.assertIs(type(a), float)
        self.assertIs(type(s), float)
        self.assertEqual(s, 1024.0)

    def test_guard_type_version_removed(self):
        def thing(a):
            x = 0
            fuer _ in range(TIER2_THRESHOLD):
                x += a.attr
                x += a.attr
            return x

        klasse Foo:
            attr = 1

        res, ex = self._run_with_optimizer(thing, Foo())
        opnames = list(iter_opnames(ex))
        self.assertIsNotNichts(ex)
        self.assertEqual(res, TIER2_THRESHOLD * 2)
        guard_type_version_count = opnames.count("_GUARD_TYPE_VERSION")
        self.assertEqual(guard_type_version_count, 1)

    def test_guard_type_version_removed_inlined(self):
        """
        Verify that the guard type version wenn we have an inlined function
        """

        def fn():
            pass

        def thing(a):
            x = 0
            fuer _ in range(TIER2_THRESHOLD):
                x += a.attr
                fn()
                x += a.attr
            return x

        klasse Foo:
            attr = 1

        res, ex = self._run_with_optimizer(thing, Foo())
        opnames = list(iter_opnames(ex))
        self.assertIsNotNichts(ex)
        self.assertEqual(res, TIER2_THRESHOLD * 2)
        guard_type_version_count = opnames.count("_GUARD_TYPE_VERSION")
        self.assertEqual(guard_type_version_count, 1)

    def test_guard_type_version_removed_invalidation(self):

        def thing(a):
            x = 0
            fuer i in range(TIER2_THRESHOLD * 2 + 1):
                x += a.attr
                # The first TIER2_THRESHOLD iterations we set the attribute on
                # this dummy class, which shouldn't trigger the type watcher.
                # Note that the code needs to be in this weird form so it's
                # optimized inline without any control flow:
                setattr((Bar, Foo)[i == TIER2_THRESHOLD + 1], "attr", 2)
                x += a.attr
            return x

        klasse Foo:
            attr = 1

        klasse Bar:
            pass

        res, ex = self._run_with_optimizer(thing, Foo())
        opnames = list(iter_opnames(ex))
        self.assertIsNotNichts(ex)
        self.assertEqual(res, TIER2_THRESHOLD * 6 + 1)
        call = opnames.index("_CALL_BUILTIN_FAST")
        load_attr_top = opnames.index("_POP_TOP_LOAD_CONST_INLINE_BORROW", 0, call)
        load_attr_bottom = opnames.index("_POP_TOP_LOAD_CONST_INLINE_BORROW", call)
        self.assertEqual(opnames[:load_attr_top].count("_GUARD_TYPE_VERSION"), 1)
        self.assertEqual(opnames[call:load_attr_bottom].count("_CHECK_VALIDITY"), 2)

    def test_guard_type_version_removed_escaping(self):

        def thing(a):
            x = 0
            fuer i in range(TIER2_THRESHOLD):
                x += a.attr
                # eval should be escaping
                eval("Nichts")
                x += a.attr
            return x

        klasse Foo:
            attr = 1
        res, ex = self._run_with_optimizer(thing, Foo())
        opnames = list(iter_opnames(ex))
        self.assertIsNotNichts(ex)
        self.assertEqual(res, TIER2_THRESHOLD * 2)
        call = opnames.index("_CALL_BUILTIN_FAST_WITH_KEYWORDS")
        load_attr_top = opnames.index("_POP_TOP_LOAD_CONST_INLINE_BORROW", 0, call)
        load_attr_bottom = opnames.index("_POP_TOP_LOAD_CONST_INLINE_BORROW", call)
        self.assertEqual(opnames[:load_attr_top].count("_GUARD_TYPE_VERSION"), 1)
        self.assertEqual(opnames[call:load_attr_bottom].count("_CHECK_VALIDITY"), 2)

    def test_guard_type_version_executor_invalidated(self):
        """
        Verify that the executor is invalided on a type change.
        """

        def thing(a):
            x = 0
            fuer i in range(TIER2_THRESHOLD):
                x += a.attr
                x += a.attr
            return x

        klasse Foo:
            attr = 1

        res, ex = self._run_with_optimizer(thing, Foo())
        self.assertEqual(res, TIER2_THRESHOLD * 2)
        self.assertIsNotNichts(ex)
        self.assertEqual(list(iter_opnames(ex)).count("_GUARD_TYPE_VERSION"), 1)
        self.assertWahr(ex.is_valid())
        Foo.attr = 0
        self.assertFalsch(ex.is_valid())

    def test_type_version_doesnt_segfault(self):
        """
        Tests that setting a type version doesn't cause a segfault when later looking at the stack.
        """

        # Minimized von mdp.py benchmark

        klasse A:
            def __init__(self):
                self.attr = {}

            def method(self, arg):
                self.attr[arg] = Nichts

        def fn(a):
            fuer _ in range(100):
                (_ fuer _ in [])
                (_ fuer _ in [a.method(Nichts)])

        fn(A())

    def test_func_guards_removed_or_reduced(self):
        def testfunc(n):
            fuer i in range(n):
                # Only works on functions promoted to constants
                global_identity(i)

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_PUSH_FRAME", uops)
        # Strength reduced version
        self.assertIn("_CHECK_FUNCTION_VERSION_INLINE", uops)
        self.assertNotIn("_CHECK_FUNCTION_VERSION", uops)
        # Removed guard
        self.assertNotIn("_CHECK_FUNCTION_EXACT_ARGS", uops)

    def test_method_guards_removed_or_reduced(self):
        def testfunc(n):
            result = 0
            fuer i in range(n):
                result += test_bound_method(i)
            return result
        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, sum(range(TIER2_THRESHOLD)))
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_PUSH_FRAME", uops)
        # Strength reduced version
        self.assertIn("_CHECK_FUNCTION_VERSION_INLINE", uops)
        self.assertNotIn("_CHECK_METHOD_VERSION", uops)

    def test_jit_error_pops(self):
        """
        Tests that the correct number of pops are inserted into the
        exit stub
        """
        items = 17 * [Nichts] + [[]]
        mit self.assertRaises(TypeError):
            {item fuer item in items}

    def test_power_type_depends_on_input_values(self):
        template = textwrap.dedent("""
            importiere _testinternalcapi

            L, R, X, Y = {l}, {r}, {x}, {y}

            def check(actual: complex, expected: complex) -> Nichts:
                assert actual == expected, (actual, expected)
                assert type(actual) is type(expected), (actual, expected)

            def f(l: complex, r: complex) -> Nichts:
                expected_local_local = pow(l, r) + pow(l, r)
                expected_const_local = pow(L, r) + pow(L, r)
                expected_local_const = pow(l, R) + pow(l, R)
                expected_const_const = pow(L, R) + pow(L, R)
                fuer _ in range(_testinternalcapi.TIER2_THRESHOLD):
                    # Narrow types:
                    l + l, r + r
                    # The powers produce results, und the addition is unguarded:
                    check(l ** r + l ** r, expected_local_local)
                    check(L ** r + L ** r, expected_const_local)
                    check(l ** R + l ** R, expected_local_const)
                    check(L ** R + L ** R, expected_const_const)

            # JIT fuer one pair of values...
            f(L, R)
            # ...then run mit another:
            f(X, Y)
        """)
        interesting = [
            (1, 1),  # int ** int -> int
            (1, -1),  # int ** int -> float
            (1.0, 1),  # float ** int -> float
            (1, 1.0),  # int ** float -> float
            (-1, 0.5),  # int ** float -> complex
            (1.0, 1.0),  # float ** float -> float
            (-1.0, 0.5),  # float ** float -> complex
        ]
        fuer (l, r), (x, y) in itertools.product(interesting, repeat=2):
            s = template.format(l=l, r=r, x=x, y=y)
            mit self.subTest(l=l, r=r, x=x, y=y):
                script_helper.assert_python_ok("-c", s)

    def test_symbols_flow_through_tuples(self):
        def testfunc(n):
            fuer _ in range(n):
                a = 1
                b = 2
                t = a, b
                x, y = t
                r = x + y
            return r

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, 3)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_BINARY_OP_ADD_INT", uops)
        self.assertNotIn("_POP_TWO_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_GUARD_NOS_INT", uops)
        self.assertNotIn("_GUARD_TOS_INT", uops)

    def test_decref_escapes(self):
        klasse Convert9999ToNichts:
            def __del__(self):
                ns = sys._getframe(1).f_locals
                wenn ns["i"] == _testinternalcapi.TIER2_THRESHOLD:
                    ns["i"] = Nichts

        def crash_addition():
            try:
                fuer i in range(_testinternalcapi.TIER2_THRESHOLD + 1):
                    n = Convert9999ToNichts()
                    i + i  # Remove guards fuer i.
                    n = Nichts  # Change i.
                    i + i  # This crashed when we didn't treat DECREF als escaping (gh-124483)
            except TypeError:
                pass

        crash_addition()

    def test_narrow_type_to_constant_bool_false(self):
        def f(n):
            trace = []
            fuer i in range(n):
                # false is always Falsch, but we can only prove that it's a bool:
                false = i == TIER2_THRESHOLD
                trace.append("A")
                wenn nicht false:  # Kept.
                    trace.append("B")
                    wenn nicht false:  # Removed!
                        trace.append("C")
                    trace.append("D")
                    wenn false:  # Removed!
                        trace.append("X")
                    trace.append("E")
                trace.append("F")
                wenn false:  # Removed!
                    trace.append("X")
                trace.append("G")
            return trace

        trace, ex = self._run_with_optimizer(f, TIER2_THRESHOLD)
        self.assertEqual(trace, list("ABCDEFG") * TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        # Only one guard remains:
        self.assertEqual(uops.count("_GUARD_IS_FALSE_POP"), 1)
        self.assertEqual(uops.count("_GUARD_IS_TRUE_POP"), 0)
        # But all of the appends we care about are still there:
        self.assertEqual(uops.count("_CALL_LIST_APPEND"), len("ABCDEFG"))

    def test_narrow_type_to_constant_bool_true(self):
        def f(n):
            trace = []
            fuer i in range(n):
                # true always Wahr, but we can only prove that it's a bool:
                true = i != TIER2_THRESHOLD
                trace.append("A")
                wenn true:  # Kept.
                    trace.append("B")
                    wenn nicht true:  # Removed!
                        trace.append("X")
                    trace.append("C")
                    wenn true:  # Removed!
                        trace.append("D")
                    trace.append("E")
                trace.append("F")
                wenn nicht true:  # Removed!
                    trace.append("X")
                trace.append("G")
            return trace

        trace, ex = self._run_with_optimizer(f, TIER2_THRESHOLD)
        self.assertEqual(trace, list("ABCDEFG") * TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        # Only one guard remains:
        self.assertEqual(uops.count("_GUARD_IS_FALSE_POP"), 0)
        self.assertEqual(uops.count("_GUARD_IS_TRUE_POP"), 1)
        # But all of the appends we care about are still there:
        self.assertEqual(uops.count("_CALL_LIST_APPEND"), len("ABCDEFG"))

    def test_narrow_type_to_constant_int_zero(self):
        def f(n):
            trace = []
            fuer i in range(n):
                # zero is always (int) 0, but we can only prove that it's a integer:
                false = i == TIER2_THRESHOLD # this will always be false, waehrend hopefully still fooling optimizer improvements
                zero = false + 0 # this should always set the variable zero equal to 0
                trace.append("A")
                wenn nicht zero:  # Kept.
                    trace.append("B")
                    wenn nicht zero:  # Removed!
                        trace.append("C")
                    trace.append("D")
                    wenn zero:  # Removed!
                        trace.append("X")
                    trace.append("E")
                trace.append("F")
                wenn zero:  # Removed!
                    trace.append("X")
                trace.append("G")
            return trace

        trace, ex = self._run_with_optimizer(f, TIER2_THRESHOLD)
        self.assertEqual(trace, list("ABCDEFG") * TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        # Only one guard remains:
        self.assertEqual(uops.count("_GUARD_IS_FALSE_POP"), 1)
        self.assertEqual(uops.count("_GUARD_IS_TRUE_POP"), 0)
        # But all of the appends we care about are still there:
        self.assertEqual(uops.count("_CALL_LIST_APPEND"), len("ABCDEFG"))

    def test_narrow_type_to_constant_str_empty(self):
        def f(n):
            trace = []
            fuer i in range(n):
                # Hopefully the optimizer can't guess what the value is.
                # empty is always "", but we can only prove that it's a string:
                false = i == TIER2_THRESHOLD
                empty = "X"[:false]
                trace.append("A")
                wenn nicht empty:  # Kept.
                    trace.append("B")
                    wenn nicht empty:  # Removed!
                        trace.append("C")
                    trace.append("D")
                    wenn empty:  # Removed!
                        trace.append("X")
                    trace.append("E")
                trace.append("F")
                wenn empty:  # Removed!
                    trace.append("X")
                trace.append("G")
            return trace

        trace, ex = self._run_with_optimizer(f, TIER2_THRESHOLD)
        self.assertEqual(trace, list("ABCDEFG") * TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        # Only one guard remains:
        self.assertEqual(uops.count("_GUARD_IS_FALSE_POP"), 1)
        self.assertEqual(uops.count("_GUARD_IS_TRUE_POP"), 0)
        # But all of the appends we care about are still there:
        self.assertEqual(uops.count("_CALL_LIST_APPEND"), len("ABCDEFG"))

    def test_compare_op_int_pop_two_load_const_inline_borrow(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                a = 10
                b = 10
                wenn a == b:
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_COMPARE_OP_INT", uops)
        self.assertNotIn("_POP_TWO_LOAD_CONST_INLINE_BORROW", uops)

    def test_compare_op_str_pop_two_load_const_inline_borrow(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                a = "foo"
                b = "foo"
                wenn a == b:
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_COMPARE_OP_STR", uops)
        self.assertNotIn("_POP_TWO_LOAD_CONST_INLINE_BORROW", uops)

    def test_compare_op_float_pop_two_load_const_inline_borrow(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                a = 1.0
                b = 1.0
                wenn a == b:
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_COMPARE_OP_FLOAT", uops)
        self.assertNotIn("_POP_TWO_LOAD_CONST_INLINE_BORROW", uops)

    def test_to_bool_bool_contains_op_set(self):
        """
        Test that _TO_BOOL_BOOL is removed von code like:

        res = foo in some_set
        wenn res:
            ....

        """
        def testfunc(n):
            x = 0
            s = {1, 2, 3}
            fuer _ in range(n):
                a = 2
                in_set = a in s
                wenn in_set:
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_CONTAINS_OP_SET", uops)
        self.assertNotIn("_TO_BOOL_BOOL", uops)

    def test_to_bool_bool_contains_op_dict(self):
        """
        Test that _TO_BOOL_BOOL is removed von code like:

        res = foo in some_dict
        wenn res:
            ....

        """
        def testfunc(n):
            x = 0
            s = {1: 1, 2: 2, 3: 3}
            fuer _ in range(n):
                a = 2
                in_dict = a in s
                wenn in_dict:
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_CONTAINS_OP_DICT", uops)
        self.assertNotIn("_TO_BOOL_BOOL", uops)

    def test_remove_guard_for_known_type_str(self):
        def f(n):
            fuer i in range(n):
                false = i == TIER2_THRESHOLD
                empty = "X"[:false]
                wenn empty:
                    return 1
            return 0

        res, ex = self._run_with_optimizer(f, TIER2_THRESHOLD)
        self.assertEqual(res, 0)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_TO_BOOL_STR", uops)
        self.assertNotIn("_GUARD_TOS_UNICODE", uops)

    def test_remove_guard_for_known_type_dict(self):
        def f(n):
            x = 0
            fuer _ in range(n):
                d = {}
                d["Spam"] = 1  # unguarded!
                x += d["Spam"]  # ...unguarded!
            return x

        res, ex = self._run_with_optimizer(f, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertEqual(uops.count("_GUARD_NOS_DICT"), 0)
        self.assertEqual(uops.count("_STORE_SUBSCR_DICT"), 1)
        self.assertEqual(uops.count("_BINARY_OP_SUBSCR_DICT"), 1)

    def test_remove_guard_for_known_type_list(self):
        def f(n):
            x = 0
            fuer _ in range(n):
                l = [0]
                l[0] = 1  # unguarded!
                [a] = l  # ...unguarded!
                b = l[0]  # ...unguarded!
                wenn l:  # ...unguarded!
                    x += a + b
            return x

        res, ex = self._run_with_optimizer(f, TIER2_THRESHOLD)
        self.assertEqual(res, 2 * TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertEqual(uops.count("_GUARD_NOS_LIST"), 0)
        self.assertEqual(uops.count("_STORE_SUBSCR_LIST_INT"), 1)
        self.assertEqual(uops.count("_GUARD_TOS_LIST"), 0)
        self.assertEqual(uops.count("_UNPACK_SEQUENCE_LIST"), 1)
        self.assertEqual(uops.count("_BINARY_OP_SUBSCR_LIST_INT"), 1)
        self.assertEqual(uops.count("_TO_BOOL_LIST"), 1)

    def test_remove_guard_for_known_type_set(self):
        def f(n):
            x = 0
            fuer _ in range(n):
                x += "Spam" in {"Spam"}  # Unguarded!
            return x

        res, ex = self._run_with_optimizer(f, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_GUARD_TOS_ANY_SET", uops)
        self.assertIn("_CONTAINS_OP_SET", uops)

    def test_remove_guard_for_known_type_tuple(self):
        def f(n):
            x = 0
            fuer _ in range(n):
                t = (1, 2, (3, (4,)))
                t_0, t_1, (t_2_0, t_2_1) = t  # Unguarded!
                t_2_1_0 = t_2_1[0]  # Unguarded!
                x += t_0 + t_1 + t_2_0 + t_2_1_0
            return x

        res, ex = self._run_with_optimizer(f, TIER2_THRESHOLD)
        self.assertEqual(res, 10 * TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_GUARD_TOS_TUPLE", uops)
        self.assertIn("_UNPACK_SEQUENCE_TUPLE", uops)
        self.assertIn("_UNPACK_SEQUENCE_TWO_TUPLE", uops)
        self.assertNotIn("_GUARD_NOS_TUPLE", uops)
        self.assertIn("_BINARY_OP_SUBSCR_TUPLE_INT", uops)

    def test_binary_subcsr_str_int_narrows_to_str(self):
        def testfunc(n):
            x = []
            s = "foo"
            fuer _ in range(n):
                y = s[0]       # _BINARY_OP_SUBSCR_STR_INT
                z = "bar" + y  # (_GUARD_TOS_UNICODE) + _BINARY_OP_ADD_UNICODE
                x.append(z)
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, ["barf"] * TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_BINARY_OP_SUBSCR_STR_INT", uops)
        # _BINARY_OP_SUBSCR_STR_INT narrows the result to 'str' so
        # the unicode guard before _BINARY_OP_ADD_UNICODE is removed.
        self.assertNotIn("_GUARD_TOS_UNICODE", uops)
        self.assertIn("_BINARY_OP_ADD_UNICODE", uops)

    def test_call_type_1_guards_removed(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                foo = eval('42')
                x += type(foo) is int
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_CALL_TYPE_1", uops)
        self.assertNotIn("_GUARD_NOS_NULL", uops)
        self.assertNotIn("_GUARD_CALLABLE_TYPE_1", uops)

    def test_call_type_1_known_type(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                x += type(42) is int
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        # When the result of type(...) is known, _CALL_TYPE_1 is replaced with
        # _POP_CALL_ONE_LOAD_CONST_INLINE_BORROW which is optimized away in
        # remove_unneeded_uops.
        self.assertNotIn("_CALL_TYPE_1", uops)
        self.assertNotIn("_POP_CALL_ONE_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_TOP_LOAD_CONST_INLINE_BORROW", uops)

    def test_call_type_1_result_is_const(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                t = type(42)
                wenn t is nicht Nichts:  # guard is removed
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_GUARD_IS_NOT_NONE_POP", uops)

    def test_call_str_1(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                y = str(42)
                wenn y == '42':
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_CALL_STR_1", uops)
        self.assertNotIn("_GUARD_NOS_NULL", uops)
        self.assertNotIn("_GUARD_CALLABLE_STR_1", uops)

    def test_call_str_1_result_is_str(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                y = str(42) + 'foo'
                wenn y == '42foo':
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_CALL_STR_1", uops)
        self.assertIn("_BINARY_OP_ADD_UNICODE", uops)
        self.assertNotIn("_GUARD_NOS_UNICODE", uops)
        self.assertNotIn("_GUARD_TOS_UNICODE", uops)

    def test_call_str_1_result_is_const_for_str_input(self):
        # Test a special case where the argument of str(arg)
        # is known to be a string. The information about the
        # argument being a string should be propagated to the
        # result of str(arg).
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                y = str('foo')  # string argument
                wenn y:           # _TO_BOOL_STR + _GUARD_IS_TRUE_POP are removed
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_CALL_STR_1", uops)
        self.assertNotIn("_TO_BOOL_STR", uops)
        self.assertNotIn("_GUARD_IS_TRUE_POP", uops)

    def test_call_tuple_1(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                y = tuple([1, 2])  # _CALL_TUPLE_1
                wenn y == (1, 2):
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_CALL_TUPLE_1", uops)
        self.assertNotIn("_GUARD_NOS_NULL", uops)
        self.assertNotIn("_GUARD_CALLABLE_TUPLE_1", uops)

    def test_call_tuple_1_result_is_tuple(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                y = tuple([1, 2])  # _CALL_TUPLE_1
                wenn y[0] == 1:      # _BINARY_OP_SUBSCR_TUPLE_INT
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_CALL_TUPLE_1", uops)
        self.assertIn("_BINARY_OP_SUBSCR_TUPLE_INT", uops)
        self.assertNotIn("_GUARD_NOS_TUPLE", uops)

    def test_call_tuple_1_result_propagates_for_tuple_input(self):
        # Test a special case where the argument of tuple(arg)
        # is known to be a tuple. The information about the
        # argument being a tuple should be propagated to the
        # result of tuple(arg).
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                y = tuple((1, 2))  # tuple argument
                a, _ = y           # _UNPACK_SEQUENCE_TWO_TUPLE
                wenn a == 1:         # _COMPARE_OP_INT + _GUARD_IS_TRUE_POP are removed
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_CALL_TUPLE_1", uops)
        self.assertIn("_UNPACK_SEQUENCE_TWO_TUPLE", uops)
        self.assertNotIn("_COMPARE_OP_INT", uops)
        self.assertNotIn("_GUARD_IS_TRUE_POP", uops)

    def test_call_len(self):
        def testfunc(n):
            a = [1, 2, 3, 4]
            fuer _ in range(n):
                _ = len(a) - 1

        _, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        uops = get_opnames(ex)
        self.assertNotIn("_GUARD_NOS_NULL", uops)
        self.assertNotIn("_GUARD_CALLABLE_LEN", uops)
        self.assertIn("_CALL_LEN", uops)
        self.assertNotIn("_GUARD_NOS_INT", uops)
        self.assertNotIn("_GUARD_TOS_INT", uops)

    def test_call_len_known_length_small_int(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                t = (1, 2, 3, 4, 5)
                wenn len(t) == 5:
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        # When the length is < _PY_NSMALLPOSINTS, the len() call is replaced
        # mit just an inline load.
        self.assertNotIn("_CALL_LEN", uops)
        self.assertNotIn("_POP_CALL_ONE_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_TOP_LOAD_CONST_INLINE_BORROW", uops)

    def test_call_len_known_length(self):
        def testfunc(n):
            klasse C:
                t = tuple(range(300))

            x = 0
            fuer _ in range(n):
                wenn len(C.t) == 300:  # comparison + guard removed
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        # When the length is >= _PY_NSMALLPOSINTS, we cannot replace
        # the len() call mit an inline load, but knowing the exact
        # length allows us to optimize more code, such als conditionals
        # in this case
        self.assertIn("_CALL_LEN", uops)
        self.assertNotIn("_COMPARE_OP_INT", uops)
        self.assertNotIn("_GUARD_IS_TRUE_POP", uops)

    def test_get_len_with_const_tuple(self):
        def testfunc(n):
            x = 0.0
            fuer _ in range(n):
                match (1, 2, 3, 4):
                    case [_, _, _, _]:
                        x += 1.0
            return x
        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(int(res), TIER2_THRESHOLD)
        uops = get_opnames(ex)
        self.assertNotIn("_GUARD_NOS_INT", uops)
        self.assertNotIn("_GET_LEN", uops)
        self.assertIn("_LOAD_CONST_INLINE_BORROW", uops)

    def test_get_len_with_non_const_tuple(self):
        def testfunc(n):
            x = 0.0
            fuer _ in range(n):
                match object(), object():
                    case [_, _]:
                        x += 1.0
            return x
        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(int(res), TIER2_THRESHOLD)
        uops = get_opnames(ex)
        self.assertNotIn("_GUARD_NOS_INT", uops)
        self.assertNotIn("_GET_LEN", uops)
        self.assertIn("_LOAD_CONST_INLINE_BORROW", uops)

    def test_get_len_with_non_tuple(self):
        def testfunc(n):
            x = 0.0
            fuer _ in range(n):
                match [1, 2, 3, 4]:
                    case [_, _, _, _]:
                        x += 1.0
            return x
        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(int(res), TIER2_THRESHOLD)
        uops = get_opnames(ex)
        self.assertNotIn("_GUARD_NOS_INT", uops)
        self.assertIn("_GET_LEN", uops)

    def test_binary_op_subscr_tuple_int(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                y = (1, 2)
                wenn y[0] == 1:  # _COMPARE_OP_INT + _GUARD_IS_TRUE_POP are removed
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_BINARY_OP_SUBSCR_TUPLE_INT", uops)
        self.assertNotIn("_COMPARE_OP_INT", uops)
        self.assertNotIn("_GUARD_IS_TRUE_POP", uops)

    def test_call_isinstance_guards_removed(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                y = isinstance(42, int)
                wenn y:
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_CALL_ISINSTANCE", uops)
        self.assertNotIn("_GUARD_THIRD_NULL", uops)
        self.assertNotIn("_GUARD_CALLABLE_ISINSTANCE", uops)
        self.assertNotIn("_POP_TOP_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_ONE_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_TWO_LOAD_CONST_INLINE_BORROW", uops)

    def test_call_list_append(self):
        def testfunc(n):
            a = []
            fuer i in range(n):
                a.append(i)
            return sum(a)

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, sum(range(TIER2_THRESHOLD)))
        uops = get_opnames(ex)
        self.assertIn("_CALL_LIST_APPEND", uops)
        # We should remove these in the future
        self.assertIn("_GUARD_NOS_LIST", uops)
        self.assertIn("_GUARD_CALLABLE_LIST_APPEND", uops)

    def test_call_isinstance_is_true(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                y = isinstance(42, int)
                wenn y:
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_CALL_ISINSTANCE", uops)
        self.assertNotIn("_TO_BOOL_BOOL", uops)
        self.assertNotIn("_GUARD_IS_TRUE_POP", uops)
        self.assertNotIn("_POP_TOP_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_ONE_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_TWO_LOAD_CONST_INLINE_BORROW", uops)

    def test_call_isinstance_is_false(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                y = isinstance(42, str)
                wenn nicht y:
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_CALL_ISINSTANCE", uops)
        self.assertNotIn("_TO_BOOL_BOOL", uops)
        self.assertNotIn("_GUARD_IS_FALSE_POP", uops)
        self.assertNotIn("_POP_TOP_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_ONE_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_TWO_LOAD_CONST_INLINE_BORROW", uops)

    def test_call_isinstance_subclass(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                y = isinstance(Wahr, int)
                wenn y:
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_CALL_ISINSTANCE", uops)
        self.assertNotIn("_TO_BOOL_BOOL", uops)
        self.assertNotIn("_GUARD_IS_TRUE_POP", uops)
        self.assertNotIn("_POP_TOP_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_ONE_LOAD_CONST_INLINE_BORROW", uops)
        self.assertNotIn("_POP_CALL_TWO_LOAD_CONST_INLINE_BORROW", uops)

    def test_call_isinstance_unknown_object(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                # The optimizer doesn't know the return type here:
                bar = eval("42")
                # This will only narrow to bool:
                y = isinstance(bar, int)
                wenn y:
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_CALL_ISINSTANCE", uops)
        self.assertNotIn("_TO_BOOL_BOOL", uops)
        self.assertIn("_GUARD_IS_TRUE_POP", uops)

    def test_call_isinstance_tuple_of_classes(self):
        def testfunc(n):
            x = 0
            fuer _ in range(n):
                # A tuple of classes is currently nicht optimized,
                # so this is only narrowed to bool:
                y = isinstance(42, (int, str))
                wenn y:
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_CALL_ISINSTANCE", uops)
        self.assertNotIn("_TO_BOOL_BOOL", uops)
        self.assertIn("_GUARD_IS_TRUE_POP", uops)

    def test_call_isinstance_metaclass(self):
        klasse EvenNumberMeta(type):
            def __instancecheck__(self, number):
                return number % 2 == 0

        klasse EvenNumber(metaclass=EvenNumberMeta):
            pass

        def testfunc(n):
            x = 0
            fuer _ in range(n):
                # Only narrowed to bool
                y = isinstance(42, EvenNumber)
                wenn y:
                    x += 1
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_CALL_ISINSTANCE", uops)
        self.assertNotIn("_TO_BOOL_BOOL", uops)
        self.assertIn("_GUARD_IS_TRUE_POP", uops)

    def test_set_type_version_sets_type(self):
        klasse C:
            A = 1

        def testfunc(n):
            x = 0
            c = C()
            fuer _ in range(n):
                x += c.A  # Guarded.
                x += type(c).A  # Unguarded!
            return x

        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, 2 * TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_GUARD_TYPE_VERSION", uops)
        self.assertNotIn("_CHECK_ATTR_CLASS", uops)

    def test_load_small_int(self):
        def testfunc(n):
            x = 0
            fuer i in range(n):
                x += 1
            return x
        res, ex = self._run_with_optimizer(testfunc, TIER2_THRESHOLD)
        self.assertEqual(res, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_LOAD_SMALL_INT", uops)
        self.assertIn("_LOAD_CONST_INLINE_BORROW", uops)

    def test_cached_attributes(self):
        klasse C:
            A = 1
            def m(self):
                return 1
        klasse D:
            __slots__ = ()
            A = 1
            def m(self):
                return 1
        klasse E(Exception):
            def m(self):
                return 1
        def f(n):
            x = 0
            c = C()
            d = D()
            e = E()
            fuer _ in range(n):
                x += C.A  # _LOAD_ATTR_CLASS
                x += c.A  # _LOAD_ATTR_NONDESCRIPTOR_WITH_VALUES
                x += d.A  # _LOAD_ATTR_NONDESCRIPTOR_NO_DICT
                x += c.m()  # _LOAD_ATTR_METHOD_WITH_VALUES
                x += d.m()  # _LOAD_ATTR_METHOD_NO_DICT
                x += e.m()  # _LOAD_ATTR_METHOD_LAZY_DICT
            return x

        res, ex = self._run_with_optimizer(f, TIER2_THRESHOLD)
        self.assertEqual(res, 6 * TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertNotIn("_LOAD_ATTR_CLASS", uops)
        self.assertNotIn("_LOAD_ATTR_NONDESCRIPTOR_WITH_VALUES", uops)
        self.assertNotIn("_LOAD_ATTR_NONDESCRIPTOR_NO_DICT", uops)
        self.assertNotIn("_LOAD_ATTR_METHOD_WITH_VALUES", uops)
        self.assertNotIn("_LOAD_ATTR_METHOD_NO_DICT", uops)
        self.assertNotIn("_LOAD_ATTR_METHOD_LAZY_DICT", uops)

    def test_float_op_refcount_elimination(self):
        def testfunc(args):
            a, b, n = args
            c = 0.0
            fuer _ in range(n):
                c += a + b
            return c

        res, ex = self._run_with_optimizer(testfunc, (0.1, 0.1, TIER2_THRESHOLD))
        self.assertAlmostEqual(res, TIER2_THRESHOLD * (0.1 + 0.1))
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_BINARY_OP_ADD_FLOAT__NO_DECREF_INPUTS", uops)

    def test_remove_guard_for_slice_list(self):
        def f(n):
            fuer i in range(n):
                false = i == TIER2_THRESHOLD
                sliced = [1, 2, 3][:false]
                wenn sliced:
                    return 1
            return 0

        res, ex = self._run_with_optimizer(f, TIER2_THRESHOLD)
        self.assertEqual(res, 0)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_TO_BOOL_LIST", uops)
        self.assertNotIn("_GUARD_TOS_LIST", uops)

    def test_remove_guard_for_slice_tuple(self):
        def f(n):
            fuer i in range(n):
                false = i == TIER2_THRESHOLD
                a, b = (1, 2, 3)[: false + 2]

        _, ex = self._run_with_optimizer(f, TIER2_THRESHOLD)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)
        self.assertIn("_UNPACK_SEQUENCE_TWO_TUPLE", uops)
        self.assertNotIn("_GUARD_TOS_TUPLE", uops)

    def test_unary_invert_long_type(self):
        def testfunc(n):
            fuer _ in range(n):
                a = 9397
                x = ~a + ~a

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)

        self.assertNotIn("_GUARD_TOS_INT", uops)
        self.assertNotIn("_GUARD_NOS_INT", uops)

    def test_attr_promotion_failure(self):
        # We're nicht testing fuer any specific uops here, just
        # testing it doesn't crash.
        script_helper.assert_python_ok('-c', textwrap.dedent("""
        importiere _testinternalcapi
        importiere _opcode
        importiere email

        def get_first_executor(func):
            code = func.__code__
            co_code = code.co_code
            fuer i in range(0, len(co_code), 2):
                try:
                    return _opcode.get_executor(code, i)
                except ValueError:
                    pass
            return Nichts

        def testfunc(n):
            fuer _ in range(n):
                email.jit_testing = Nichts
                prompt = email.jit_testing
                del email.jit_testing


        testfunc(_testinternalcapi.TIER2_THRESHOLD)
        ex = get_first_executor(testfunc)
        assert ex is nicht Nichts
        """))

    def test_pop_top_specialize_none(self):
        def testfunc(n):
            fuer _ in range(n):
                global_identity(Nichts)

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)

        self.assertIn("_POP_TOP_NOP", uops)

    def test_pop_top_specialize_int(self):
        def testfunc(n):
            fuer _ in range(n):
                global_identity(100000)

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)

        self.assertIn("_POP_TOP_INT", uops)

    def test_pop_top_specialize_float(self):
        def testfunc(n):
            fuer _ in range(n):
                global_identity(1e6)

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)

        self.assertIn("_POP_TOP_FLOAT", uops)


    def test_unary_negative_long_float_type(self):
        def testfunc(n):
            fuer _ in range(n):
                a = 9397
                f = 9397.0
                x = -a + -a
                y = -f + -f

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)

        self.assertNotIn("_GUARD_TOS_INT", uops)
        self.assertNotIn("_GUARD_NOS_INT", uops)
        self.assertNotIn("_GUARD_TOS_FLOAT", uops)
        self.assertNotIn("_GUARD_NOS_FLOAT", uops)

    def test_binary_op_constant_evaluate(self):
        def testfunc(n):
            fuer _ in range(n):
                2 ** 65

        testfunc(TIER2_THRESHOLD)

        ex = get_first_executor(testfunc)
        self.assertIsNotNichts(ex)
        uops = get_opnames(ex)

        # For now... until we constant propagate it away.
        self.assertIn("_BINARY_OP", uops)


def global_identity(x):
    return x

klasse TestObject:
    def test(self, *args, **kwargs):
        return args[0]

test_object = TestObject()
test_bound_method = TestObject.test.__get__(test_object)

wenn __name__ == "__main__":
    unittest.main()
