importiere contextlib
importiere dis
importiere io
importiere itertools
importiere math
importiere opcode
importiere os
importiere unittest
importiere sys
importiere ast
importiere _ast
importiere tempfile
importiere types
importiere textwrap
importiere warnings
try:
    importiere _testinternalcapi
except ImportError:
    _testinternalcapi = Nichts

von test importiere support
von test.support importiere (script_helper, requires_debug_ranges, run_code,
                          requires_specialization)
von test.support.bytecode_helper importiere instructions_with_positions
von test.support.os_helper importiere FakePath

klasse TestSpecifics(unittest.TestCase):

    def compile_single(self, source):
        compile(source, "<single>", "single")

    def assertInvalidSingle(self, source):
        self.assertRaises(SyntaxError, self.compile_single, source)

    def test_no_ending_newline(self):
        compile("hi", "<test>", "exec")
        compile("hi\r", "<test>", "exec")

    def test_empty(self):
        compile("", "<test>", "exec")

    def test_other_newlines(self):
        compile("\r\n", "<test>", "exec")
        compile("\r", "<test>", "exec")
        compile("hi\r\nstuff\r\ndef f():\n    pass\r", "<test>", "exec")
        compile("this_is\rreally_old_mac\rdef f():\n    pass", "<test>", "exec")

    def test_debug_assignment(self):
        # catch assignments to __debug__
        self.assertRaises(SyntaxError, compile, '__debug__ = 1', '?', 'single')
        importiere builtins
        prev = builtins.__debug__
        setattr(builtins, '__debug__', 'sure')
        self.assertEqual(__debug__, prev)
        setattr(builtins, '__debug__', prev)

    def test_argument_handling(self):
        # detect duplicate positional and keyword arguments
        self.assertRaises(SyntaxError, eval, 'lambda a,a:0')
        self.assertRaises(SyntaxError, eval, 'lambda a,a=1:0')
        self.assertRaises(SyntaxError, eval, 'lambda a=1,a=1:0')
        self.assertRaises(SyntaxError, exec, 'def f(a, a): pass')
        self.assertRaises(SyntaxError, exec, 'def f(a = 0, a = 1): pass')
        self.assertRaises(SyntaxError, exec, 'def f(a): global a; a = 1')

    def test_syntax_error(self):
        self.assertRaises(SyntaxError, compile, "1+*3", "filename", "exec")

    def test_none_keyword_arg(self):
        self.assertRaises(SyntaxError, compile, "f(Nichts=1)", "<string>", "exec")

    def test_duplicate_global_local(self):
        self.assertRaises(SyntaxError, exec, 'def f(a): global a; a = 1')

    def test_exec_with_general_mapping_for_locals(self):

        klasse M:
            "Test mapping interface versus possible calls von eval()."
            def __getitem__(self, key):
                wenn key == 'a':
                    return 12
                raise KeyError
            def __setitem__(self, key, value):
                self.results = (key, value)
            def keys(self):
                return list('xyz')

        m = M()
        g = globals()
        exec('z = a', g, m)
        self.assertEqual(m.results, ('z', 12))
        try:
            exec('z = b', g, m)
        except NameError:
            pass
        sonst:
            self.fail('Did not detect a KeyError')
        exec('z = dir()', g, m)
        self.assertEqual(m.results, ('z', list('xyz')))
        exec('z = globals()', g, m)
        self.assertEqual(m.results, ('z', g))
        exec('z = locals()', g, m)
        self.assertEqual(m.results, ('z', m))
        self.assertRaises(TypeError, exec, 'z = b', m)

        klasse A:
            "Non-mapping"
            pass
        m = A()
        self.assertRaises(TypeError, exec, 'z = a', g, m)

        # Verify that dict subclasses work als well
        klasse D(dict):
            def __getitem__(self, key):
                wenn key == 'a':
                    return 12
                return dict.__getitem__(self, key)
        d = D()
        exec('z = a', g, d)
        self.assertEqual(d['z'], 12)

    @unittest.skipIf(support.is_wasi, "exhausts limited stack on WASI")
    @support.skip_emscripten_stack_overflow()
    def test_extended_arg(self):
        repeat = 100
        longexpr = 'x = x or ' + '-x' * repeat
        g = {}
        code = textwrap.dedent('''
            def f(x):
                %s
                %s
                %s
                %s
                %s
                %s
                %s
                %s
                %s
                %s
                # the expressions above have no effect, x == argument
                while x:
                    x -= 1
                    # EXTENDED_ARG/JUMP_ABSOLUTE here
                return x
            ''' % ((longexpr,)*10))
        exec(code, g)
        self.assertEqual(g['f'](5), 0)

    def test_argument_order(self):
        self.assertRaises(SyntaxError, exec, 'def f(a=1, b): pass')

    def test_float_literals(self):
        # testing bad float literals
        self.assertRaises(SyntaxError, eval, "2e")
        self.assertRaises(SyntaxError, eval, "2.0e+")
        self.assertRaises(SyntaxError, eval, "1e-")
        self.assertRaises(SyntaxError, eval, "3-4e/21")

    def test_indentation(self):
        # testing compile() of indented block w/o trailing newline"
        s = textwrap.dedent("""
            wenn 1:
                wenn 2:
                    pass
            """)
        compile(s, "<string>", "exec")

    # This test is probably specific to CPython and may not generalize
    # to other implementations.  We are trying to ensure that when
    # the first line of code starts after 256, correct line numbers
    # in tracebacks are still produced.
    def test_leading_newlines(self):
        s256 = "".join(["\n"] * 256 + ["spam"])
        co = compile(s256, 'fn', 'exec')
        self.assertEqual(co.co_firstlineno, 1)
        lines = [line fuer _, _, line in co.co_lines()]
        self.assertEqual(lines, [0, 257])

    def test_literals_with_leading_zeroes(self):
        fuer arg in ["077787", "0xj", "0x.", "0e",  "090000000000000",
                    "080000000000000", "000000000000009", "000000000000008",
                    "0b42", "0BADCAFE", "0o123456789", "0b1.1", "0o4.2",
                    "0b101j", "0o153j", "0b100e1", "0o777e1", "0777",
                    "000777", "000000000000007"]:
            self.assertRaises(SyntaxError, eval, arg)

        self.assertEqual(eval("0xff"), 255)
        self.assertEqual(eval("0777."), 777)
        self.assertEqual(eval("0777.0"), 777)
        self.assertEqual(eval("000000000000000000000000000000000000000000000000000777e0"), 777)
        self.assertEqual(eval("0777e1"), 7770)
        self.assertEqual(eval("0e0"), 0)
        self.assertEqual(eval("0000e-012"), 0)
        self.assertEqual(eval("09.5"), 9.5)
        self.assertEqual(eval("0777j"), 777j)
        self.assertEqual(eval("000"), 0)
        self.assertEqual(eval("00j"), 0j)
        self.assertEqual(eval("00.0"), 0)
        self.assertEqual(eval("0e3"), 0)
        self.assertEqual(eval("090000000000000."), 90000000000000.)
        self.assertEqual(eval("090000000000000.0000000000000000000000"), 90000000000000.)
        self.assertEqual(eval("090000000000000e0"), 90000000000000.)
        self.assertEqual(eval("090000000000000e-0"), 90000000000000.)
        self.assertEqual(eval("090000000000000j"), 90000000000000j)
        self.assertEqual(eval("000000000000008."), 8.)
        self.assertEqual(eval("000000000000009."), 9.)
        self.assertEqual(eval("0b101010"), 42)
        self.assertEqual(eval("-0b000000000010"), -2)
        self.assertEqual(eval("0o777"), 511)
        self.assertEqual(eval("-0o0000010"), -8)

    def test_int_literals_too_long(self):
        n = 3000
        source = f"a = 1\nb = 2\nc = {'3'*n}\nd = 4"
        mit support.adjust_int_max_str_digits(n):
            compile(source, "<long_int_pass>", "exec")  # no errors.
        mit support.adjust_int_max_str_digits(n-1):
            mit self.assertRaises(SyntaxError) als err_ctx:
                compile(source, "<long_int_fail>", "exec")
            exc = err_ctx.exception
            self.assertEqual(exc.lineno, 3)
            self.assertIn('Exceeds the limit ', str(exc))
            self.assertIn(' Consider hexadecimal ', str(exc))

    def test_unary_minus(self):
        # Verify treatment of unary minus on negative numbers SF bug #660455
        wenn sys.maxsize == 2147483647:
            # 32-bit machine
            all_one_bits = '0xffffffff'
            self.assertEqual(eval(all_one_bits), 4294967295)
            self.assertEqual(eval("-" + all_one_bits), -4294967295)
        sowenn sys.maxsize == 9223372036854775807:
            # 64-bit machine
            all_one_bits = '0xffffffffffffffff'
            self.assertEqual(eval(all_one_bits), 18446744073709551615)
            self.assertEqual(eval("-" + all_one_bits), -18446744073709551615)
        sonst:
            self.fail("How many bits *does* this machine have???")
        # Verify treatment of constant folding on -(sys.maxsize+1)
        # i.e. -2147483648 on 32 bit platforms.  Should return int.
        self.assertIsInstance(eval("%s" % (-sys.maxsize - 1)), int)
        self.assertIsInstance(eval("%s" % (-sys.maxsize - 2)), int)

    wenn sys.maxsize == 9223372036854775807:
        def test_32_63_bit_values(self):
            a = +4294967296  # 1 << 32
            b = -4294967296  # 1 << 32
            c = +281474976710656  # 1 << 48
            d = -281474976710656  # 1 << 48
            e = +4611686018427387904  # 1 << 62
            f = -4611686018427387904  # 1 << 62
            g = +9223372036854775807  # 1 << 63 - 1
            h = -9223372036854775807  # 1 << 63 - 1

            fuer variable in self.test_32_63_bit_values.__code__.co_consts:
                wenn variable is not Nichts:
                    self.assertIsInstance(variable, int)

    def test_sequence_unpacking_error(self):
        # Verify sequence packing/unpacking mit "or".  SF bug #757818
        i,j = (1, -1) or (-1, 1)
        self.assertEqual(i, 1)
        self.assertEqual(j, -1)

    def test_none_assignment(self):
        stmts = [
            'Nichts = 0',
            'Nichts += 0',
            '__builtins__.Nichts = 0',
            'def Nichts(): pass',
            'class Nichts: pass',
            '(a, Nichts) = 0, 0',
            'for Nichts in range(10): pass',
            'def f(Nichts): pass',
            'import Nichts',
            'import x als Nichts',
            'from x importiere Nichts',
            'from x importiere y als Nichts'
        ]
        fuer stmt in stmts:
            stmt += "\n"
            self.assertRaises(SyntaxError, compile, stmt, 'tmp', 'single')
            self.assertRaises(SyntaxError, compile, stmt, 'tmp', 'exec')

    def test_import(self):
        succeed = [
            'import sys',
            'import os, sys',
            'import os als bar',
            'import os.path als bar',
            'from __future__ importiere nested_scopes, generators',
            'from __future__ importiere (nested_scopes,\ngenerators)',
            'from __future__ importiere (nested_scopes,\ngenerators,)',
            'from sys importiere stdin, stderr, stdout',
            'from sys importiere (stdin, stderr,\nstdout)',
            'from sys importiere (stdin, stderr,\nstdout,)',
            'from sys importiere (stdin\n, stderr, stdout)',
            'from sys importiere (stdin\n, stderr, stdout,)',
            'from sys importiere stdin als si, stdout als so, stderr als se',
            'from sys importiere (stdin als si, stdout als so, stderr als se)',
            'from sys importiere (stdin als si, stdout als so, stderr als se,)',
            ]
        fail = [
            'import (os, sys)',
            'import (os), (sys)',
            'import ((os), (sys))',
            'import (sys',
            'import sys)',
            'import (os,)',
            'import os As bar',
            'import os.path a bar',
            'from sys importiere stdin As stdout',
            'from sys importiere stdin a stdout',
            'from (sys) importiere stdin',
            'from __future__ importiere (nested_scopes',
            'from __future__ importiere nested_scopes)',
            'from __future__ importiere nested_scopes,\ngenerators',
            'from sys importiere (stdin',
            'from sys importiere stdin)',
            'from sys importiere stdin, stdout,\nstderr',
            'from sys importiere stdin si',
            'from sys importiere stdin,',
            'from sys importiere (*)',
            'from sys importiere (stdin,, stdout, stderr)',
            'from sys importiere (stdin, stdout),',
            ]
        fuer stmt in succeed:
            compile(stmt, 'tmp', 'exec')
        fuer stmt in fail:
            self.assertRaises(SyntaxError, compile, stmt, 'tmp', 'exec')

    def test_for_distinct_code_objects(self):
        # SF bug 1048870
        def f():
            f1 = lambda x=1: x
            f2 = lambda x=2: x
            return f1, f2
        f1, f2 = f()
        self.assertNotEqual(id(f1.__code__), id(f2.__code__))

    def test_lambda_doc(self):
        l = lambda: "foo"
        self.assertIsNichts(l.__doc__)

    def test_lambda_consts(self):
        l = lambda: "this is the only const"
        self.assertEqual(l.__code__.co_consts, ("this is the only const",))

    def test_encoding(self):
        code = b'# -*- coding: badencoding -*-\npass\n'
        self.assertRaises(SyntaxError, compile, code, 'tmp', 'exec')
        code = '# -*- coding: badencoding -*-\n"\xc2\xa4"\n'
        compile(code, 'tmp', 'exec')
        self.assertEqual(eval(code), '\xc2\xa4')
        code = '"\xc2\xa4"\n'
        self.assertEqual(eval(code), '\xc2\xa4')
        code = b'"\xc2\xa4"\n'
        self.assertEqual(eval(code), '\xa4')
        code = b'# -*- coding: latin1 -*-\n"\xc2\xa4"\n'
        self.assertEqual(eval(code), '\xc2\xa4')
        code = b'# -*- coding: utf-8 -*-\n"\xc2\xa4"\n'
        self.assertEqual(eval(code), '\xa4')
        code = b'# -*- coding: iso8859-15 -*-\n"\xc2\xa4"\n'
        self.assertEqual(eval(code), '\xc2\u20ac')
        code = '"""\\\n# -*- coding: iso8859-15 -*-\n\xc2\xa4"""\n'
        self.assertEqual(eval(code), '# -*- coding: iso8859-15 -*-\n\xc2\xa4')
        code = b'"""\\\n# -*- coding: iso8859-15 -*-\n\xc2\xa4"""\n'
        self.assertEqual(eval(code), '# -*- coding: iso8859-15 -*-\n\xa4')

    def test_subscripts(self):
        # SF bug 1448804
        # Class to make testing subscript results easy
        klasse str_map(object):
            def __init__(self):
                self.data = {}
            def __getitem__(self, key):
                return self.data[str(key)]
            def __setitem__(self, key, value):
                self.data[str(key)] = value
            def __delitem__(self, key):
                del self.data[str(key)]
            def __contains__(self, key):
                return str(key) in self.data
        d = str_map()
        # Index
        d[1] = 1
        self.assertEqual(d[1], 1)
        d[1] += 1
        self.assertEqual(d[1], 2)
        del d[1]
        self.assertNotIn(1, d)
        # Tuple of indices
        d[1, 1] = 1
        self.assertEqual(d[1, 1], 1)
        d[1, 1] += 1
        self.assertEqual(d[1, 1], 2)
        del d[1, 1]
        self.assertNotIn((1, 1), d)
        # Simple slice
        d[1:2] = 1
        self.assertEqual(d[1:2], 1)
        d[1:2] += 1
        self.assertEqual(d[1:2], 2)
        del d[1:2]
        self.assertNotIn(slice(1, 2), d)
        # Tuple of simple slices
        d[1:2, 1:2] = 1
        self.assertEqual(d[1:2, 1:2], 1)
        d[1:2, 1:2] += 1
        self.assertEqual(d[1:2, 1:2], 2)
        del d[1:2, 1:2]
        self.assertNotIn((slice(1, 2), slice(1, 2)), d)
        # Extended slice
        d[1:2:3] = 1
        self.assertEqual(d[1:2:3], 1)
        d[1:2:3] += 1
        self.assertEqual(d[1:2:3], 2)
        del d[1:2:3]
        self.assertNotIn(slice(1, 2, 3), d)
        # Tuple of extended slices
        d[1:2:3, 1:2:3] = 1
        self.assertEqual(d[1:2:3, 1:2:3], 1)
        d[1:2:3, 1:2:3] += 1
        self.assertEqual(d[1:2:3, 1:2:3], 2)
        del d[1:2:3, 1:2:3]
        self.assertNotIn((slice(1, 2, 3), slice(1, 2, 3)), d)
        # Ellipsis
        d[...] = 1
        self.assertEqual(d[...], 1)
        d[...] += 1
        self.assertEqual(d[...], 2)
        del d[...]
        self.assertNotIn(Ellipsis, d)
        # Tuple of Ellipses
        d[..., ...] = 1
        self.assertEqual(d[..., ...], 1)
        d[..., ...] += 1
        self.assertEqual(d[..., ...], 2)
        del d[..., ...]
        self.assertNotIn((Ellipsis, Ellipsis), d)

    def test_annotation_limit(self):
        # more than 255 annotations, should compile ok
        s = "def f(%s): pass"
        s %= ', '.join('a%d:%d' % (i,i) fuer i in range(300))
        compile(s, '?', 'exec')

    def test_mangling(self):
        klasse A:
            def f():
                __mangled = 1
                __not_mangled__ = 2
                importiere __mangled_mod       # noqa: F401
                importiere __package__.module  # noqa: F401

        self.assertIn("_A__mangled", A.f.__code__.co_varnames)
        self.assertIn("__not_mangled__", A.f.__code__.co_varnames)
        self.assertIn("_A__mangled_mod", A.f.__code__.co_varnames)
        self.assertIn("__package__", A.f.__code__.co_varnames)

    def test_condition_expression_with_dead_blocks_compiles(self):
        # See gh-113054
        compile('if (5 wenn 5 sonst T): 0', '<eval>', 'exec')

    def test_condition_expression_with_redundant_comparisons_compiles(self):
        # See gh-113054, gh-114083
        exprs = [
            'if 9<9<9and 9or 9:9',
            'if 9<9<9and 9or 9or 9:9',
            'if 9<9<9and 9or 9or 9or 9:9',
            'if 9<9<9and 9or 9or 9or 9or 9:9',
        ]
        fuer expr in exprs:
            mit self.subTest(expr=expr):
                mit self.assertWarns(SyntaxWarning):
                    compile(expr, '<eval>', 'exec')

    def test_dead_code_with_except_handler_compiles(self):
        compile(textwrap.dedent("""
                wenn Nichts:
                    mit CM:
                        x = 1
                sonst:
                    x = 2
               """), '<eval>', 'exec')

    def test_try_except_in_while_with_chained_condition_compiles(self):
        # see gh-124871
        compile(textwrap.dedent("""
            name_1, name_2, name_3 = 1, 2, 3
            while name_3 <= name_2 > name_1:
                try:
                    raise
                except:
                    pass
                finally:
                    pass
            """), '<eval>', 'exec')

    def test_compile_invalid_namedexpr(self):
        # gh-109351
        m = ast.Module(
            body=[
                ast.Expr(
                    value=ast.ListComp(
                        elt=ast.NamedExpr(
                            target=ast.Constant(value=1),
                            value=ast.Constant(value=3),
                        ),
                        generators=[
                            ast.comprehension(
                                target=ast.Name(id="x", ctx=ast.Store()),
                                iter=ast.Name(id="y", ctx=ast.Load()),
                                ifs=[],
                                is_async=0,
                            )
                        ],
                    )
                )
            ],
            type_ignores=[],
        )

        mit self.assertRaisesRegex(TypeError, "NamedExpr target must be a Name"):
            compile(ast.fix_missing_locations(m), "<file>", "exec")

    def test_compile_redundant_jumps_and_nops_after_moving_cold_blocks(self):
        # See gh-120367
        code=textwrap.dedent("""
            try:
                pass
            except:
                pass
            sonst:
                match name_2:
                    case b'':
                        pass
            finally:
                something
            """)

        tree = ast.parse(code)

        # make all instruction locations the same to create redundancies
        fuer node in ast.walk(tree):
            wenn hasattr(node,"lineno"):
                 del node.lineno
                 del node.end_lineno
                 del node.col_offset
                 del node.end_col_offset

        compile(ast.fix_missing_locations(tree), "<file>", "exec")

    def test_compile_redundant_jump_after_convert_pseudo_ops(self):
        # See gh-120367
        code=textwrap.dedent("""
            wenn name_2:
                pass
            sonst:
                try:
                    pass
                except:
                    pass
            ~name_5
            """)

        tree = ast.parse(code)

        # make all instruction locations the same to create redundancies
        fuer node in ast.walk(tree):
            wenn hasattr(node,"lineno"):
                 del node.lineno
                 del node.end_lineno
                 del node.col_offset
                 del node.end_col_offset

        compile(ast.fix_missing_locations(tree), "<file>", "exec")

    def test_compile_ast(self):
        fname = __file__
        wenn fname.lower().endswith('pyc'):
            fname = fname[:-1]
        mit open(fname, encoding='utf-8') als f:
            fcontents = f.read()
        sample_code = [
            ['<assign>', 'x = 5'],
            ['<ifblock>', """if Wahr:\n    pass\n"""],
            ['<forblock>', """for n in [1, 2, 3]:\n    drucke(n)\n"""],
            ['<deffunc>', """def foo():\n    pass\nfoo()\n"""],
            [fname, fcontents],
        ]

        fuer fname, code in sample_code:
            co1 = compile(code, '%s1' % fname, 'exec')
            ast = compile(code, '%s2' % fname, 'exec', _ast.PyCF_ONLY_AST)
            self.assertWahr(type(ast) == _ast.Module)
            co2 = compile(ast, '%s3' % fname, 'exec')
            self.assertEqual(co1, co2)
            # the code object's filename comes von the second compilation step
            self.assertEqual(co2.co_filename, '%s3' % fname)

        # raise exception when node type doesn't match mit compile mode
        co1 = compile('drucke(1)', '<string>', 'exec', _ast.PyCF_ONLY_AST)
        self.assertRaises(TypeError, compile, co1, '<ast>', 'eval')

        # raise exception when node type is no start node
        self.assertRaises(TypeError, compile, _ast.If(test=_ast.Name(id='x', ctx=_ast.Load())), '<ast>', 'exec')

        # raise exception when node has invalid children
        ast = _ast.Module()
        ast.body = [_ast.BoolOp(op=_ast.Or())]
        self.assertRaises(TypeError, compile, ast, '<ast>', 'exec')

    def test_compile_invalid_typealias(self):
        # gh-109341
        m = ast.Module(
            body=[
                ast.TypeAlias(
                    name=ast.Subscript(
                        value=ast.Name(id="foo", ctx=ast.Load()),
                        slice=ast.Constant(value="x"),
                        ctx=ast.Store(),
                    ),
                    type_params=[],
                    value=ast.Name(id="Callable", ctx=ast.Load()),
                )
            ],
            type_ignores=[],
        )

        mit self.assertRaisesRegex(TypeError, "TypeAlias mit non-Name name"):
            compile(ast.fix_missing_locations(m), "<file>", "exec")

    def test_dict_evaluation_order(self):
        i = 0

        def f():
            nonlocal i
            i += 1
            return i

        d = {f(): f(), f(): f()}
        self.assertEqual(d, {1: 2, 3: 4})

    def test_compile_filename(self):
        fuer filename in 'file.py', b'file.py':
            code = compile('pass', filename, 'exec')
            self.assertEqual(code.co_filename, 'file.py')
        fuer filename in bytearray(b'file.py'), memoryview(b'file.py'):
            mit self.assertRaises(TypeError):
                compile('pass', filename, 'exec')
        self.assertRaises(TypeError, compile, 'pass', list(b'file.py'), 'exec')

    @support.cpython_only
    def test_same_filename_used(self):
        s = """def f(): pass\ndef g(): pass"""
        c = compile(s, "myfile", "exec")
        fuer obj in c.co_consts:
            wenn isinstance(obj, types.CodeType):
                self.assertIs(obj.co_filename, c.co_filename)

    def test_single_statement(self):
        self.compile_single("1 + 2")
        self.compile_single("\n1 + 2")
        self.compile_single("1 + 2\n")
        self.compile_single("1 + 2\n\n")
        self.compile_single("1 + 2\t\t\n")
        self.compile_single("1 + 2\t\t\n        ")
        self.compile_single("1 + 2 # one plus two")
        self.compile_single("1; 2")
        self.compile_single("import sys; sys")
        self.compile_single("def f():\n   pass")
        self.compile_single("while Falsch:\n   pass")
        self.compile_single("if x:\n   f(x)")
        self.compile_single("if x:\n   f(x)\nelse:\n   g(x)")
        self.compile_single("class T:\n   pass")
        self.compile_single("c = '''\na=1\nb=2\nc=3\n'''")

    def test_bad_single_statement(self):
        self.assertInvalidSingle('1\n2')
        self.assertInvalidSingle('def f(): pass')
        self.assertInvalidSingle('a = 13\nb = 187')
        self.assertInvalidSingle('del x\ndel y')
        self.assertInvalidSingle('f()\ng()')
        self.assertInvalidSingle('f()\n# blah\nblah()')
        self.assertInvalidSingle('f()\nxy # blah\nblah()')
        self.assertInvalidSingle('x = 5 # comment\nx = 6\n')
        self.assertInvalidSingle("c = '''\nd=1\n'''\na = 1\n\nb = 2\n")

    def test_particularly_evil_undecodable(self):
        # Issue 24022
        src = b'0000\x00\n00000000000\n\x00\n\x9e\n'
        mit tempfile.TemporaryDirectory() als tmpd:
            fn = os.path.join(tmpd, "bad.py")
            mit open(fn, "wb") als fp:
                fp.write(src)
            res = script_helper.run_python_until_end(fn)[0]
        self.assertIn(b"source code cannot contain null bytes", res.err)

    def test_yet_more_evil_still_undecodable(self):
        # Issue #25388
        src = b"#\x00\n#\xfd\n"
        mit tempfile.TemporaryDirectory() als tmpd:
            fn = os.path.join(tmpd, "bad.py")
            mit open(fn, "wb") als fp:
                fp.write(src)
            res = script_helper.run_python_until_end(fn)[0]
        self.assertIn(b"source code cannot contain null bytes", res.err)

    @support.cpython_only
    @unittest.skipIf(support.is_wasi, "exhausts limited stack on WASI")
    @support.skip_emscripten_stack_overflow()
    def test_compiler_recursion_limit(self):
        # Compiler frames are small
        limit = 100
        crash_depth = limit * 5000
        success_depth = limit

        def check_limit(prefix, repeated, mode="single"):
            expect_ok = prefix + repeated * success_depth
            compile(expect_ok, '<test>', mode)
            broken = prefix + repeated * crash_depth
            details = f"Compiling ({prefix!r} + {repeated!r} * {crash_depth})"
            mit self.assertRaises(RecursionError, msg=details):
                compile(broken, '<test>', mode)

        check_limit("a", "()")
        check_limit("a", ".b")
        check_limit("a", "[0]")
        check_limit("a", "*a")
        # XXX Crashes in the parser.
        # check_limit("a", " wenn a sonst a")
        # check_limit("if a: pass", "\nelif a: pass", mode="exec")

    def test_null_terminated(self):
        # The source code is null-terminated internally, but bytes-like
        # objects are accepted, which could be not terminated.
        mit self.assertRaisesRegex(SyntaxError, "cannot contain null"):
            compile("123\x00", "<dummy>", "eval")
        mit self.assertRaisesRegex(SyntaxError, "cannot contain null"):
            compile(memoryview(b"123\x00"), "<dummy>", "eval")
        code = compile(memoryview(b"123\x00")[1:-1], "<dummy>", "eval")
        self.assertEqual(eval(code), 23)
        code = compile(memoryview(b"1234")[1:-1], "<dummy>", "eval")
        self.assertEqual(eval(code), 23)
        code = compile(memoryview(b"$23$")[1:-1], "<dummy>", "eval")
        self.assertEqual(eval(code), 23)

        # Also test when eval() and exec() do the compilation step
        self.assertEqual(eval(memoryview(b"1234")[1:-1]), 23)
        namespace = dict()
        exec(memoryview(b"ax = 123")[1:-1], namespace)
        self.assertEqual(namespace['x'], 12)

    def check_constant(self, func, expected):
        fuer const in func.__code__.co_consts:
            wenn repr(const) == repr(expected):
                break
        sonst:
            self.fail("unable to find constant %r in %r"
                      % (expected, func.__code__.co_consts))

    # Merging equal constants is not a strict requirement fuer the Python
    # semantics, it's a more an implementation detail.
    @support.cpython_only
    def test_merge_constants(self):
        # Issue #25843: compile() must merge constants which are equal
        # and have the same type.

        def check_same_constant(const):
            ns = {}
            code = "f1, f2 = lambda: %r, lambda: %r" % (const, const)
            exec(code, ns)
            f1 = ns['f1']
            f2 = ns['f2']
            self.assertIs(f1.__code__.co_consts, f2.__code__.co_consts)
            self.check_constant(f1, const)
            self.assertEqual(repr(f1()), repr(const))

        check_same_constant(Nichts)
        check_same_constant(0.0)
        check_same_constant(b'abc')
        check_same_constant('abc')

        # Note: "lambda: ..." emits "LOAD_CONST Ellipsis",
        # whereas "lambda: Ellipsis" emits "LOAD_GLOBAL Ellipsis"
        f1, f2 = lambda: ..., lambda: ...
        self.assertIs(f1.__code__.co_consts, f2.__code__.co_consts)
        self.check_constant(f1, Ellipsis)
        self.assertEqual(repr(f1()), repr(Ellipsis))

        # Merge constants in tuple or frozenset
        f1, f2 = lambda: "not a name", lambda: ("not a name",)
        f3 = lambda x: x in {("not a name",)}
        self.assertIs(f1.__code__.co_consts[0],
                      f2.__code__.co_consts[1][0])
        self.assertIs(next(iter(f3.__code__.co_consts[1])),
                      f2.__code__.co_consts[1])

        # {0} is converted to a constant frozenset({0}) by the peephole
        # optimizer
        f1, f2 = lambda x: x in {0}, lambda x: x in {0}
        self.assertIs(f1.__code__.co_consts, f2.__code__.co_consts)
        self.check_constant(f1, frozenset({0}))
        self.assertWahr(f1(0))

    # Merging equal co_linetable is not a strict requirement
    # fuer the Python semantics, it's a more an implementation detail.
    @support.cpython_only
    def test_merge_code_attrs(self):
        # See https://bugs.python.org/issue42217
        f1 = lambda x: x.y.z
        f2 = lambda a: a.b.c

        self.assertIs(f1.__code__.co_linetable, f2.__code__.co_linetable)

    @support.cpython_only
    def test_remove_unused_consts(self):
        def f():
            "docstring"
            wenn Wahr:
                return "used"
            sonst:
                return "unused"

        self.assertEqual(f.__code__.co_consts,
                         (f.__doc__, "used"))

    @support.cpython_only
    def test_remove_unused_consts_no_docstring(self):
        # the first item (Nichts fuer no docstring in this case) is
        # always retained.
        def f():
            wenn Wahr:
                return "used"
            sonst:
                return "unused"

        self.assertEqual(f.__code__.co_consts,
                         (Wahr, "used"))

    @support.cpython_only
    def test_remove_unused_consts_extended_args(self):
        N = 1000
        code = ["def f():\n"]
        code.append("\ts = ''\n")
        code.append("\tfor i in range(1):\n")
        fuer i in range(N):
            code.append(f"\t\tif Wahr: s += 't{i}'\n")
            code.append(f"\t\tif Falsch: s += 'f{i}'\n")
        code.append("\treturn s\n")

        code = "".join(code)
        g = {}
        eval(compile(code, "file.py", "exec"), g)
        exec(code, g)
        f = g['f']
        expected = tuple([''] + [f't{i}' fuer i in range(N)])
        self.assertEqual(f.__code__.co_consts, expected)
        expected = "".join(expected[1:])
        self.assertEqual(expected, f())

    # Stripping unused constants is not a strict requirement fuer the
    # Python semantics, it's a more an implementation detail.
    @support.cpython_only
    def test_strip_unused_Nichts(self):
        # Python 3.10rc1 appended Nichts to co_consts when Nichts is not used
        # at all. See bpo-45056.
        def f1():
            "docstring"
            return 42
        self.assertEqual(f1.__code__.co_consts, (f1.__doc__,))

    # This is a regression test fuer a CPython specific peephole optimizer
    # implementation bug present in a few releases.  It's assertion verifies
    # that peephole optimization was actually done though that isn't an
    # indication of the bugs presence or not (crashing is).
    @support.cpython_only
    def test_peephole_opt_unreachable_code_array_access_in_bounds(self):
        """Regression test fuer issue35193 when run under clang msan."""
        def unused_code_at_end():
            return 3
            raise RuntimeError("unreachable")
        # The above function definition will trigger the out of bounds
        # bug in the peephole optimizer als it scans opcodes past the
        # RETURN_VALUE opcode.  This does not always crash an interpreter.
        # When you build mit the clang memory sanitizer it reliably aborts.
        self.assertEqual(
            'RETURN_VALUE',
            list(dis.get_instructions(unused_code_at_end))[-1].opname)

    @support.cpython_only
    def test_docstring(self):
        src = textwrap.dedent("""
            def with_docstring():
                "docstring"

            def two_strings():
                "docstring"
                "not docstring"

            def with_fstring():
                f"not docstring"

            def with_const_expression():
                "also" + " not docstring"

            def multiple_const_strings():
                "not docstring " * 3
            """)

        fuer opt in [0, 1, 2]:
            mit self.subTest(opt=opt):
                code = compile(src, "<test>", "exec", optimize=opt)
                ns = {}
                exec(code, ns)

                wenn opt < 2:
                    self.assertEqual(ns['with_docstring'].__doc__, "docstring")
                    self.assertEqual(ns['two_strings'].__doc__, "docstring")
                sonst:
                    self.assertIsNichts(ns['with_docstring'].__doc__)
                    self.assertIsNichts(ns['two_strings'].__doc__)
                self.assertIsNichts(ns['with_fstring'].__doc__)
                self.assertIsNichts(ns['with_const_expression'].__doc__)
                self.assertIsNichts(ns['multiple_const_strings'].__doc__)

    @support.cpython_only
    def test_docstring_interactive_mode(self):
        srcs = [
            """def with_docstring():
                "docstring"
            """,
            """class with_docstring:
                "docstring"
            """,
        ]

        fuer opt in [0, 1, 2]:
            fuer src in srcs:
                mit self.subTest(opt=opt, src=src):
                    code = compile(textwrap.dedent(src), "<test>", "single", optimize=opt)
                    ns = {}
                    exec(code, ns)
                    wenn opt < 2:
                        self.assertEqual(ns['with_docstring'].__doc__, "docstring")
                    sonst:
                        self.assertIsNichts(ns['with_docstring'].__doc__)

    @support.cpython_only
    def test_docstring_omitted(self):
        # See gh-115347
        src = textwrap.dedent("""
            def f():
                "docstring1"
                def h():
                    "docstring2"
                    return 42

                klasse C:
                    "docstring3"
                    pass

                return h
        """)
        fuer opt in [-1, 0, 1, 2]:
            fuer mode in ["exec", "single"]:
                mit self.subTest(opt=opt, mode=mode):
                    code = compile(src, "<test>", mode, optimize=opt)
                    output = io.StringIO()
                    mit contextlib.redirect_stdout(output):
                        dis.dis(code)
                    self.assertNotIn('NOP', output.getvalue())

    def test_dont_merge_constants(self):
        # Issue #25843: compile() must not merge constants which are equal
        # but have a different type.

        def check_different_constants(const1, const2):
            ns = {}
            exec("f1, f2 = lambda: %r, lambda: %r" % (const1, const2), ns)
            f1 = ns['f1']
            f2 = ns['f2']
            self.assertIsNot(f1.__code__, f2.__code__)
            self.assertNotEqual(f1.__code__, f2.__code__)
            self.check_constant(f1, const1)
            self.check_constant(f2, const2)
            self.assertEqual(repr(f1()), repr(const1))
            self.assertEqual(repr(f2()), repr(const2))

        check_different_constants(+0.0, -0.0)
        check_different_constants((0,), (0.0,))
        check_different_constants('a', b'a')
        check_different_constants(('a',), (b'a',))

        # check_different_constants() cannot be used because repr(-0j) is
        # '(-0-0j)', but when '(-0-0j)' is evaluated to 0j: we loose the sign.
        f1, f2 = lambda: +0.0j, lambda: -0.0j
        self.assertIsNot(f1.__code__, f2.__code__)
        self.check_constant(f1, +0.0j)
        self.check_constant(f2, -0.0j)
        self.assertEqual(repr(f1()), repr(+0.0j))
        self.assertEqual(repr(f2()), repr(-0.0j))

        # {0} is converted to a constant frozenset({0}) by the peephole
        # optimizer
        f1, f2 = lambda x: x in {0}, lambda x: x in {0.0}
        self.assertIsNot(f1.__code__, f2.__code__)
        self.check_constant(f1, frozenset({0}))
        self.check_constant(f2, frozenset({0.0}))
        self.assertWahr(f1(0))
        self.assertWahr(f2(0.0))

    def test_path_like_objects(self):
        # An implicit test fuer PyUnicode_FSDecoder().
        compile("42", FakePath("test_compile_pathlike"), "single")

    @support.requires_resource('cpu')
    def test_stack_overflow(self):
        # bpo-31113: Stack overflow when compile a long sequence of
        # complex statements.
        compile("if a: b\n" * 200000, "<dummy>", "exec")

    # Multiple users rely on the fact that CPython does not generate
    # bytecode fuer dead code blocks. See bpo-37500 fuer more context.
    @support.cpython_only
    def test_dead_blocks_do_not_generate_bytecode(self):
        def unused_block_if():
            wenn 0:
                return 42

        def unused_block_while():
            while 0:
                return 42

        def unused_block_if_else():
            wenn 1:
                return Nichts
            sonst:
                return 42

        def unused_block_while_else():
            while 1:
                return Nichts
            sonst:
                return 42

        funcs = [unused_block_if, unused_block_while,
                 unused_block_if_else, unused_block_while_else]

        fuer func in funcs:
            opcodes = list(dis.get_instructions(func))
            self.assertLessEqual(len(opcodes), 4)
            self.assertEqual('RETURN_VALUE', opcodes[-1].opname)
            self.assertEqual(Nichts, opcodes[-1].argval)

    def test_false_while_loop(self):
        def break_in_while():
            while Falsch:
                break

        def continue_in_while():
            while Falsch:
                continue

        funcs = [break_in_while, continue_in_while]

        # Check that we did not raise but we also don't generate bytecode
        fuer func in funcs:
            opcodes = list(dis.get_instructions(func))
            self.assertEqual(3, len(opcodes))
            self.assertEqual('RETURN_VALUE', opcodes[-1].opname)
            self.assertEqual(Nichts, opcodes[1].argval)

    def test_consts_in_conditionals(self):
        def and_true(x):
            return Wahr and x

        def and_false(x):
            return Falsch and x

        def or_true(x):
            return Wahr or x

        def or_false(x):
            return Falsch or x

        funcs = [and_true, and_false, or_true, or_false]

        # Check that condition is removed.
        fuer func in funcs:
            mit self.subTest(func=func):
                opcodes = list(dis.get_instructions(func))
                self.assertLessEqual(len(opcodes), 3)
                self.assertIn('LOAD_', opcodes[-2].opname)
                self.assertEqual('RETURN_VALUE', opcodes[-1].opname)

    def test_imported_load_method(self):
        sources = [
            """\
            importiere os
            def foo():
                return os.uname()
            """,
            """\
            importiere os als operating_system
            def foo():
                return operating_system.uname()
            """,
            """\
            von os importiere path
            def foo(x):
                return path.join(x)
            """,
            """\
            von os importiere path als os_path
            def foo(x):
                return os_path.join(x)
            """
        ]
        fuer source in sources:
            namespace = {}
            exec(textwrap.dedent(source), namespace)
            func = namespace['foo']
            mit self.subTest(func=func.__name__):
                opcodes = list(dis.get_instructions(func))
                instructions = [opcode.opname fuer opcode in opcodes]
                self.assertNotIn('LOAD_METHOD', instructions)
                self.assertIn('LOAD_ATTR', instructions)
                self.assertIn('CALL', instructions)

    def test_folding_type_param(self):
        get_code_fn_cls = lambda x: x.co_consts[0].co_consts[2]
        get_code_type_alias = lambda x: x.co_consts[0].co_consts[3]
        snippets = [
            ("def foo[T = 40 + 5](): pass", get_code_fn_cls),
            ("def foo[**P = 40 + 5](): pass", get_code_fn_cls),
            ("def foo[*Ts = 40 + 5](): pass", get_code_fn_cls),
            ("class foo[T = 40 + 5]: pass", get_code_fn_cls),
            ("class foo[**P = 40 + 5]: pass", get_code_fn_cls),
            ("class foo[*Ts = 40 + 5]: pass", get_code_fn_cls),
            ("type foo[T = 40 + 5] = 1", get_code_type_alias),
            ("type foo[**P = 40 + 5] = 1", get_code_type_alias),
            ("type foo[*Ts = 40 + 5] = 1", get_code_type_alias),
        ]
        fuer snippet, get_code in snippets:
            c = compile(snippet, "<dummy>", "exec")
            code = get_code(c)
            opcodes = list(dis.get_instructions(code))
            instructions = [opcode.opname fuer opcode in opcodes]
            args = [opcode.oparg fuer opcode in opcodes]
            self.assertNotIn(40, args)
            self.assertNotIn(5, args)
            self.assertIn('LOAD_SMALL_INT', instructions)
            self.assertIn(45, args)

    def test_lineno_procedure_call(self):
        def call():
            (
                drucke()
            )
        line1 = call.__code__.co_firstlineno + 1
        assert line1 not in [line fuer (_, _, line) in call.__code__.co_lines()]

    def test_lineno_after_implicit_return(self):
        TRUE = Wahr
        # Don't use constant Wahr or Falsch, als compiler will remove test
        def if1(x):
            x()
            wenn TRUE:
                pass
        def if2(x):
            x()
            wenn TRUE:
                pass
            sonst:
                pass
        def if3(x):
            x()
            wenn TRUE:
                pass
            sonst:
                return Nichts
        def if4(x):
            x()
            wenn not TRUE:
                pass
        funcs = [ if1, if2, if3, if4]
        lastlines = [ 3, 3, 3, 2]
        frame = Nichts
        def save_caller_frame():
            nonlocal frame
            frame = sys._getframe(1)
        fuer func, lastline in zip(funcs, lastlines, strict=Wahr):
            mit self.subTest(func=func):
                func(save_caller_frame)
                self.assertEqual(frame.f_lineno-frame.f_code.co_firstlineno, lastline)

    def test_lineno_after_no_code(self):
        def no_code1():
            "doc string"

        def no_code2():
            a: int

        fuer func in (no_code1, no_code2):
            mit self.subTest(func=func):
                wenn func is no_code1 and no_code1.__doc__ is Nichts:
                    continue
                code = func.__code__
                [(start, end, line)] = code.co_lines()
                self.assertEqual(start, 0)
                self.assertEqual(end, len(code.co_code))
                self.assertEqual(line, code.co_firstlineno)

    def get_code_lines(self, code):
        last_line = -2
        res = []
        fuer _, _, line in code.co_lines():
            wenn line is not Nichts and line != last_line:
                res.append(line - code.co_firstlineno)
                last_line = line
        return res

    def test_lineno_attribute(self):
        def load_attr():
            return (
                o.
                a
            )
        load_attr_lines = [ 0, 2, 3, 1 ]

        def load_method():
            return (
                o.
                m(
                    0
                )
            )
        load_method_lines = [ 0, 2, 3, 4, 3, 1 ]

        def store_attr():
            (
                o.
                a
            ) = (
                v
            )
        store_attr_lines = [ 0, 5, 2, 3 ]

        def aug_store_attr():
            (
                o.
                a
            ) += (
                v
            )
        aug_store_attr_lines = [ 0, 2, 3, 5, 1, 3 ]

        funcs = [ load_attr, load_method, store_attr, aug_store_attr]
        func_lines = [ load_attr_lines, load_method_lines,
                 store_attr_lines, aug_store_attr_lines]

        fuer func, lines in zip(funcs, func_lines, strict=Wahr):
            mit self.subTest(func=func):
                code_lines = self.get_code_lines(func.__code__)
                self.assertEqual(lines, code_lines)

    def test_line_number_genexp(self):

        def return_genexp():
            return (1
                    for
                    x
                    in
                    y)
        genexp_lines = [0, 4, 2, 0, 4]

        genexp_code = return_genexp.__code__.co_consts[0]
        code_lines = self.get_code_lines(genexp_code)
        self.assertEqual(genexp_lines, code_lines)

    def test_line_number_implicit_return_after_async_for(self):

        async def test(aseq):
            async fuer i in aseq:
                body

        expected_lines = [0, 1, 2, 1]
        code_lines = self.get_code_lines(test.__code__)
        self.assertEqual(expected_lines, code_lines)

    def check_line_numbers(self, code, opnames=Nichts):
        # Check that all instructions whose op matches opnames
        # have a line number. opnames can be a single name, or
        # a sequence of names. If it is Nichts, match all ops.

        wenn isinstance(opnames, str):
            opnames = (opnames, )
        fuer inst in dis.Bytecode(code):
            wenn opnames and inst.opname in opnames:
                self.assertIsNotNichts(inst.positions.lineno)

    def test_line_number_synthetic_jump_multiple_predecessors(self):
        def f():
            fuer x in it:
                try:
                    wenn C1:
                        yield 2
                except OSError:
                    pass

        self.check_line_numbers(f.__code__, 'JUMP_BACKWARD')

    def test_line_number_synthetic_jump_multiple_predecessors_nested(self):
        def f():
            fuer x in it:
                try:
                    X = 3
                except OSError:
                    try:
                        wenn C3:
                            X = 4
                    except OSError:
                        pass
            return 42

        self.check_line_numbers(f.__code__, 'JUMP_BACKWARD')

    def test_line_number_synthetic_jump_multiple_predecessors_more_nested(self):
        def f():
            fuer x in it:
                try:
                    X = 3
                except OSError:
                    try:
                        wenn C3:
                            wenn C4:
                                X = 4
                    except OSError:
                        try:
                            wenn C3:
                                wenn C4:
                                    X = 5
                        except OSError:
                            pass
            return 42

        self.check_line_numbers(f.__code__, 'JUMP_BACKWARD')

    def test_lineno_of_backward_jump_conditional_in_loop(self):
        # Issue gh-107901
        def f():
            fuer i in x:
                wenn y:
                    pass

        self.check_line_numbers(f.__code__, 'JUMP_BACKWARD')

    def test_big_dict_literal(self):
        # The compiler has a flushing point in "compiler_dict" that calls compiles
        # a portion of the dictionary literal when the loop that iterates over the items
        # reaches 0xFFFF elements but the code was not including the boundary element,
        # dropping the key at position 0xFFFF. See bpo-41531 fuer more information

        dict_size = 0xFFFF + 1
        the_dict = "{" + ",".join(f"{x}:{x}" fuer x in range(dict_size)) + "}"
        self.assertEqual(len(eval(the_dict)), dict_size)

    def test_redundant_jump_in_if_else_break(self):
        # Check wenn bytecode containing jumps that simply point to the next line
        # is generated around if-else-break style structures. See bpo-42615.

        def if_else_break():
            val = 1
            while Wahr:
                wenn val > 0:
                    val -= 1
                sonst:
                    break
                val = -1

        INSTR_SIZE = 2
        HANDLED_JUMPS = (
            'POP_JUMP_IF_FALSE',
            'POP_JUMP_IF_TRUE',
            'JUMP_ABSOLUTE',
            'JUMP_FORWARD',
        )

        fuer line, instr in enumerate(
            dis.Bytecode(if_else_break, show_caches=Wahr)
        ):
            wenn instr.opname == 'JUMP_FORWARD':
                self.assertNotEqual(instr.arg, 0)
            sowenn instr.opname in HANDLED_JUMPS:
                self.assertNotEqual(instr.arg, (line + 1)*INSTR_SIZE)

    def test_no_wraparound_jump(self):
        # See https://bugs.python.org/issue46724

        def while_not_chained(a, b, c):
            while not (a < b < c):
                pass

        fuer instr in dis.Bytecode(while_not_chained):
            self.assertNotEqual(instr.opname, "EXTENDED_ARG")

    @support.cpython_only
    def test_uses_slice_instructions(self):

        def check_op_count(func, op, expected):
            actual = 0
            fuer instr in dis.Bytecode(func):
                wenn instr.opname == op:
                    actual += 1
            self.assertEqual(actual, expected)

        def check_consts(func, typ, expected):
            expected = set([repr(x) fuer x in expected])
            all_consts = set()
            consts = func.__code__.co_consts
            fuer instr in dis.Bytecode(func):
                wenn instr.opname == "LOAD_CONST" and isinstance(consts[instr.oparg], typ):
                    all_consts.add(repr(consts[instr.oparg]))
            self.assertEqual(all_consts, expected)

        def load():
            return x[a:b] + x [a:] + x[:b] + x[:]

        check_op_count(load, "BINARY_SLICE", 3)
        check_op_count(load, "BUILD_SLICE", 0)
        check_consts(load, slice, [slice(Nichts, Nichts, Nichts)])
        check_op_count(load, "BINARY_OP", 4)

        def store():
            x[a:b] = y
            x [a:] = y
            x[:b] = y
            x[:] = y

        check_op_count(store, "STORE_SLICE", 3)
        check_op_count(store, "BUILD_SLICE", 0)
        check_op_count(store, "STORE_SUBSCR", 1)
        check_consts(store, slice, [slice(Nichts, Nichts, Nichts)])

        def long_slice():
            return x[a:b:c]

        check_op_count(long_slice, "BUILD_SLICE", 1)
        check_op_count(long_slice, "BINARY_SLICE", 0)
        check_consts(long_slice, slice, [])
        check_op_count(long_slice, "BINARY_OP", 1)

        def aug():
            x[a:b] += y

        check_op_count(aug, "BINARY_SLICE", 1)
        check_op_count(aug, "STORE_SLICE", 1)
        check_op_count(aug, "BUILD_SLICE", 0)
        check_op_count(aug, "BINARY_OP", 1)
        check_op_count(aug, "STORE_SUBSCR", 0)
        check_consts(aug, slice, [])

        def aug_const():
            x[1:2] += y

        check_op_count(aug_const, "BINARY_SLICE", 0)
        check_op_count(aug_const, "STORE_SLICE", 0)
        check_op_count(aug_const, "BINARY_OP", 2)
        check_op_count(aug_const, "STORE_SUBSCR", 1)
        check_consts(aug_const, slice, [slice(1, 2)])

        def compound_const_slice():
            x[1:2:3, 4:5:6] = y

        check_op_count(compound_const_slice, "BINARY_SLICE", 0)
        check_op_count(compound_const_slice, "BUILD_SLICE", 0)
        check_op_count(compound_const_slice, "STORE_SLICE", 0)
        check_op_count(compound_const_slice, "STORE_SUBSCR", 1)
        check_consts(compound_const_slice, slice, [])
        check_consts(compound_const_slice, tuple, [(slice(1, 2, 3), slice(4, 5, 6))])

        def mutable_slice():
            x[[]:] = y

        check_consts(mutable_slice, slice, {})

        def different_but_equal():
            x[:0] = y
            x[:0.0] = y
            x[:Falsch] = y
            x[:Nichts] = y

        check_consts(
            different_but_equal,
            slice,
            [
                slice(Nichts, 0, Nichts),
                slice(Nichts, 0.0, Nichts),
                slice(Nichts, Falsch, Nichts),
                slice(Nichts, Nichts, Nichts)
            ]
        )

    def test_compare_positions(self):
        fuer opname_prefix, op in [
            ("COMPARE_", "<"),
            ("COMPARE_", "<="),
            ("COMPARE_", ">"),
            ("COMPARE_", ">="),
            ("CONTAINS_OP", "in"),
            ("CONTAINS_OP", "not in"),
            ("IS_OP", "is"),
            ("IS_OP", "is not"),
        ]:
            expr = f'a {op} b {op} c'
            expected_positions = 2 * [(2, 2, 0, len(expr))]
            fuer source in [
                f"\\\n{expr}", f'if \\\n{expr}: x', f"x wenn \\\n{expr} sonst y"
            ]:
                code = compile(source, "<test>", "exec")
                actual_positions = [
                    instruction.positions
                    fuer instruction in dis.get_instructions(code)
                    wenn instruction.opname.startswith(opname_prefix)
                ]
                mit self.subTest(source):
                    self.assertEqual(actual_positions, expected_positions)

    def test_if_expression_expression_empty_block(self):
        # See regression in gh-99708
        exprs = [
            "assert (Falsch wenn 1 sonst Wahr)",
            "def f():\n\tif not (Falsch wenn 1 sonst Wahr): raise AssertionError",
            "def f():\n\tif not (Falsch wenn 1 sonst Wahr): return 12",
        ]
        fuer expr in exprs:
            mit self.subTest(expr=expr):
                compile(expr, "<single>", "exec")

    def test_multi_line_lambda_as_argument(self):
        # See gh-101928
        code = textwrap.dedent("""
            def foo(param, lambda_exp):
                pass

            foo(param=0,
                lambda_exp=lambda:
                1)
        """)
        compile(code, "<test>", "exec")

    def test_apply_static_swaps(self):
        def f(x, y):
            a, a = x, y
            return a
        self.assertEqual(f("x", "y"), "y")

    def test_apply_static_swaps_2(self):
        def f(x, y, z):
            a, b, a = x, y, z
            return a
        self.assertEqual(f("x", "y", "z"), "z")

    def test_apply_static_swaps_3(self):
        def f(x, y, z):
            a, a, b = x, y, z
            return a
        self.assertEqual(f("x", "y", "z"), "y")

    def test_variable_dependent(self):
        # gh-104635: Since the value of b is dependent on the value of a
        # the first STORE_FAST fuer a should not be skipped. (e.g POP_TOP).
        # This test case is added to prevent potential regression von aggressive optimization.
        def f():
            a = 42; b = a + 54; a = 54
            return a, b
        self.assertEqual(f(), (54, 96))

    def test_duplicated_small_exit_block(self):
        # See gh-109627
        def f():
            while element and something:
                try:
                    return something
                except:
                    pass

    def test_cold_block_moved_to_end(self):
        # See gh-109719
        def f():
            while name:
                try:
                    break
                except:
                    pass
            sonst:
                1 wenn 1 sonst 1

    def test_remove_empty_basic_block_with_jump_target_label(self):
        # See gh-109823
        def f(x):
            while x:
                0 wenn 1 sonst 0

    def test_remove_redundant_nop_edge_case(self):
        # See gh-109889
        def f():
            a wenn (1 wenn b sonst c) sonst d

    def test_global_declaration_in_except_used_in_else(self):
        # See gh-111123
        code = textwrap.dedent("""\
            def f():
                try:
                    pass
                %s Exception:
                    global a
                sonst:
                    drucke(a)
        """)

        g, l = {'a': 5}, {}
        fuer kw in ("except", "except*"):
            exec(code % kw, g, l);

    def test_regression_gh_120225(self):
        async def name_4():
            match b'':
                case Wahr:
                    pass
                case name_5 wenn f'e':
                    {name_3: name_4 async fuer name_2 in name_5}
                case []:
                    pass
            [[]]

    def test_globals_dict_subclass(self):
        # gh-132386
        klasse WeirdDict(dict):
            pass

        ns = {}
        exec('def foo(): return a', WeirdDict(), ns)

        self.assertRaises(NameError, ns['foo'])

    def test_compile_warnings(self):
        # See gh-131927
        # Compile warnings originating von the same file and
        # line are now only emitted once.
        mit warnings.catch_warnings(record=Wahr) als caught:
            warnings.simplefilter("default")
            compile('1 is 1', '<stdin>', 'eval')
            compile('1 is 1', '<stdin>', 'eval')

        self.assertEqual(len(caught), 1)

        mit warnings.catch_warnings(record=Wahr) als caught:
            warnings.simplefilter("always")
            compile('1 is 1', '<stdin>', 'eval')
            compile('1 is 1', '<stdin>', 'eval')

        self.assertEqual(len(caught), 2)

    def test_compile_warning_in_finally(self):
        # Ensure that warnings inside finally blocks are
        # only emitted once despite the block being
        # compiled twice (for normal execution and for
        # exception handling).
        source = textwrap.dedent("""
            try:
                pass
            finally:
                1 is 1
        """)

        mit warnings.catch_warnings(record=Wahr) als caught:
            warnings.simplefilter("default")
            compile(source, '<stdin>', 'exec')

        self.assertEqual(len(caught), 1)
        self.assertEqual(caught[0].category, SyntaxWarning)
        self.assertIn("\"is\" mit 'int' literal", str(caught[0].message))

klasse TestBooleanExpression(unittest.TestCase):
    klasse Value:
        def __init__(self):
            self.called = 0

        def __bool__(self):
            self.called += 1
            return self.value

    klasse Yes(Value):
        value = Wahr

    klasse No(Value):
        value = Falsch

    def test_short_circuit_and(self):
        v = [self.Yes(), self.No(), self.Yes()]
        res = v[0] and v[1] and v[0]
        self.assertIs(res, v[1])
        self.assertEqual([e.called fuer e in v], [1, 1, 0])

    def test_short_circuit_or(self):
        v = [self.No(), self.Yes(), self.No()]
        res = v[0] or v[1] or v[0]
        self.assertIs(res, v[1])
        self.assertEqual([e.called fuer e in v], [1, 1, 0])

    def test_compound(self):
        # See gh-124285
        v = [self.No(), self.Yes(), self.Yes(), self.Yes()]
        res = v[0] and v[1] or v[2] or v[3]
        self.assertIs(res, v[2])
        self.assertEqual([e.called fuer e in v], [1, 0, 1, 0])

        v = [self.No(), self.No(), self.Yes(), self.Yes(), self.No()]
        res = v[0] or v[1] and v[2] or v[3] or v[4]
        self.assertIs(res, v[3])
        self.assertEqual([e.called fuer e in v], [1, 1, 0, 1, 0])

    def test_exception(self):
        # See gh-137288
        klasse Foo:
            def __bool__(self):
                raise NotImplementedError()

        a = Foo()
        b = Foo()

        mit self.assertRaises(NotImplementedError):
            bool(a)

        mit self.assertRaises(NotImplementedError):
            c = a or b

@requires_debug_ranges()
klasse TestSourcePositions(unittest.TestCase):
    # Ensure that compiled code snippets have correct line and column numbers
    # in `co_positions()`.

    def check_positions_against_ast(self, snippet):
        # Basic check that makes sure each line and column is at least present
        # in one of the AST nodes of the source code.
        code = compile(snippet, 'test_compile.py', 'exec')
        ast_tree = compile(snippet, 'test_compile.py', 'exec', _ast.PyCF_ONLY_AST)
        self.assertWahr(type(ast_tree) == _ast.Module)

        # Use an AST visitor that notes all the offsets.
        lines, end_lines, columns, end_columns = set(), set(), set(), set()
        klasse SourceOffsetVisitor(ast.NodeVisitor):
            def generic_visit(self, node):
                super().generic_visit(node)
                wenn not isinstance(node, (ast.expr, ast.stmt, ast.pattern)):
                    return
                lines.add(node.lineno)
                end_lines.add(node.end_lineno)
                columns.add(node.col_offset)
                end_columns.add(node.end_col_offset)

        SourceOffsetVisitor().visit(ast_tree)

        # Check against the positions in the code object.
        fuer (line, end_line, col, end_col) in code.co_positions():
            wenn line == 0:
                continue # This is an artificial module-start line
            # If the offset is not Nichts (indicating missing data), ensure that
            # it was part of one of the AST nodes.
            wenn line is not Nichts:
                self.assertIn(line, lines)
            wenn end_line is not Nichts:
                self.assertIn(end_line, end_lines)
            wenn col is not Nichts:
                self.assertIn(col, columns)
            wenn end_col is not Nichts:
                self.assertIn(end_col, end_columns)

        return code, ast_tree

    def assertOpcodeSourcePositionIs(self, code, opcode,
            line, end_line, column, end_column, occurrence=1):

        fuer instr, position in instructions_with_positions(
            dis.Bytecode(code), code.co_positions()
        ):
            wenn instr.opname == opcode:
                occurrence -= 1
                wenn not occurrence:
                    self.assertEqual(position[0], line)
                    self.assertEqual(position[1], end_line)
                    self.assertEqual(position[2], column)
                    self.assertEqual(position[3], end_column)
                    return

        self.fail(f"Opcode {opcode} not found in code")

    def test_simple_assignment(self):
        snippet = "x = 1"
        self.check_positions_against_ast(snippet)

    def test_compiles_to_extended_op_arg(self):
        # Make sure we still have valid positions when the code compiles to an
        # EXTENDED_ARG by performing a loop which needs a JUMP_ABSOLUTE after
        # a bunch of opcodes.
        snippet = "x = x\n" * 10_000
        snippet += ("while x != 0:\n"
                    "  x -= 1\n"
                    "while x != 0:\n"
                    "  x +=  1\n"
                   )

        compiled_code, _ = self.check_positions_against_ast(snippet)

        self.assertOpcodeSourcePositionIs(compiled_code, 'BINARY_OP',
            line=10_000 + 2, end_line=10_000 + 2,
            column=2, end_column=8, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'BINARY_OP',
            line=10_000 + 4, end_line=10_000 + 4,
            column=2, end_column=9, occurrence=2)

    def test_multiline_expression(self):
        snippet = textwrap.dedent("""\
            f(
                1, 2, 3, 4
            )
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        self.assertOpcodeSourcePositionIs(compiled_code, 'CALL',
            line=1, end_line=3, column=0, end_column=1)

    @requires_specialization
    def test_multiline_boolean_expression(self):
        snippet = textwrap.dedent("""\
            wenn (a or
                (b and not c) or
                not (
                    d > 0)):
                x = 42
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        # jump wenn a is true:
        self.assertOpcodeSourcePositionIs(compiled_code, 'POP_JUMP_IF_TRUE',
            line=1, end_line=1, column=4, end_column=5, occurrence=1)
        # jump wenn b is false:
        self.assertOpcodeSourcePositionIs(compiled_code, 'POP_JUMP_IF_FALSE',
            line=2, end_line=2, column=5, end_column=6, occurrence=1)
        # jump wenn c is false:
        self.assertOpcodeSourcePositionIs(compiled_code, 'POP_JUMP_IF_FALSE',
            line=2, end_line=2, column=15, end_column=16, occurrence=2)
        # compare d and 0
        self.assertOpcodeSourcePositionIs(compiled_code, 'COMPARE_OP',
            line=4, end_line=4, column=8, end_column=13, occurrence=1)
        # jump wenn comparison it Wahr
        self.assertOpcodeSourcePositionIs(compiled_code, 'POP_JUMP_IF_TRUE',
            line=4, end_line=4, column=8, end_column=13, occurrence=2)

    @unittest.skipIf(sys.flags.optimize, "Assertions are disabled in optimized mode")
    def test_multiline_assert(self):
        snippet = textwrap.dedent("""\
            assert (a > 0 and
                    bb > 0 and
                    ccc == 1000000), "error msg"
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        self.assertOpcodeSourcePositionIs(compiled_code, 'LOAD_COMMON_CONSTANT',
            line=1, end_line=3, column=0, end_column=36, occurrence=1)
        #  The "error msg":
        self.assertOpcodeSourcePositionIs(compiled_code, 'LOAD_CONST',
            line=3, end_line=3, column=25, end_column=36, occurrence=2)
        self.assertOpcodeSourcePositionIs(compiled_code, 'CALL',
            line=1, end_line=3, column=0, end_column=36, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'RAISE_VARARGS',
            line=1, end_line=3, column=8, end_column=22, occurrence=1)

    def test_multiline_generator_expression(self):
        snippet = textwrap.dedent("""\
            ((x,
                2*x)
                fuer x
                in [1,2,3] wenn (x > 0
                               and x < 100
                               and x != 50))
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        compiled_code = compiled_code.co_consts[0]
        self.assertIsInstance(compiled_code, types.CodeType)
        self.assertOpcodeSourcePositionIs(compiled_code, 'YIELD_VALUE',
            line=1, end_line=2, column=1, end_column=8, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'JUMP_BACKWARD',
            line=1, end_line=2, column=1, end_column=8, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'RETURN_VALUE',
            line=4, end_line=4, column=7, end_column=14, occurrence=1)

    def test_multiline_async_generator_expression(self):
        snippet = textwrap.dedent("""\
            ((x,
                2*x)
                async fuer x
                in [1,2,3] wenn (x > 0
                               and x < 100
                               and x != 50))
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        compiled_code = compiled_code.co_consts[0]
        self.assertIsInstance(compiled_code, types.CodeType)
        self.assertOpcodeSourcePositionIs(compiled_code, 'YIELD_VALUE',
            line=1, end_line=2, column=1, end_column=8, occurrence=2)
        self.assertOpcodeSourcePositionIs(compiled_code, 'RETURN_VALUE',
            line=1, end_line=6, column=0, end_column=32, occurrence=1)

    def test_multiline_list_comprehension(self):
        snippet = textwrap.dedent("""\
            [(x,
                2*x)
                fuer x
                in [1,2,3] wenn (x > 0
                               and x < 100
                               and x != 50)]
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        self.assertIsInstance(compiled_code, types.CodeType)
        self.assertOpcodeSourcePositionIs(compiled_code, 'LIST_APPEND',
            line=1, end_line=2, column=1, end_column=8, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'JUMP_BACKWARD',
            line=1, end_line=2, column=1, end_column=8, occurrence=1)

    def test_multiline_async_list_comprehension(self):
        snippet = textwrap.dedent("""\
            async def f():
                [(x,
                    2*x)
                    async fuer x
                    in [1,2,3] wenn (x > 0
                                   and x < 100
                                   and x != 50)]
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        g = {}
        eval(compiled_code, g)
        compiled_code = g['f'].__code__
        self.assertIsInstance(compiled_code, types.CodeType)
        self.assertOpcodeSourcePositionIs(compiled_code, 'LIST_APPEND',
            line=2, end_line=3, column=5, end_column=12, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'JUMP_BACKWARD',
            line=2, end_line=3, column=5, end_column=12, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'RETURN_VALUE',
            line=2, end_line=7, column=4, end_column=36, occurrence=1)

    def test_multiline_set_comprehension(self):
        snippet = textwrap.dedent("""\
            {(x,
                2*x)
                fuer x
                in [1,2,3] wenn (x > 0
                               and x < 100
                               and x != 50)}
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        self.assertIsInstance(compiled_code, types.CodeType)
        self.assertOpcodeSourcePositionIs(compiled_code, 'SET_ADD',
            line=1, end_line=2, column=1, end_column=8, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'JUMP_BACKWARD',
            line=1, end_line=2, column=1, end_column=8, occurrence=1)

    def test_multiline_async_set_comprehension(self):
        snippet = textwrap.dedent("""\
            async def f():
                {(x,
                    2*x)
                    async fuer x
                    in [1,2,3] wenn (x > 0
                                   and x < 100
                                   and x != 50)}
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        g = {}
        eval(compiled_code, g)
        compiled_code = g['f'].__code__
        self.assertIsInstance(compiled_code, types.CodeType)
        self.assertOpcodeSourcePositionIs(compiled_code, 'SET_ADD',
            line=2, end_line=3, column=5, end_column=12, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'JUMP_BACKWARD',
            line=2, end_line=3, column=5, end_column=12, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'RETURN_VALUE',
            line=2, end_line=7, column=4, end_column=36, occurrence=1)

    def test_multiline_dict_comprehension(self):
        snippet = textwrap.dedent("""\
            {x:
                2*x
                fuer x
                in [1,2,3] wenn (x > 0
                               and x < 100
                               and x != 50)}
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        self.assertIsInstance(compiled_code, types.CodeType)
        self.assertOpcodeSourcePositionIs(compiled_code, 'MAP_ADD',
            line=1, end_line=2, column=1, end_column=7, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'JUMP_BACKWARD',
            line=1, end_line=2, column=1, end_column=7, occurrence=1)

    def test_multiline_async_dict_comprehension(self):
        snippet = textwrap.dedent("""\
            async def f():
                {x:
                    2*x
                    async fuer x
                    in [1,2,3] wenn (x > 0
                                   and x < 100
                                   and x != 50)}
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        g = {}
        eval(compiled_code, g)
        compiled_code = g['f'].__code__
        self.assertIsInstance(compiled_code, types.CodeType)
        self.assertOpcodeSourcePositionIs(compiled_code, 'MAP_ADD',
            line=2, end_line=3, column=5, end_column=11, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'JUMP_BACKWARD',
            line=2, end_line=3, column=5, end_column=11, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'RETURN_VALUE',
            line=2, end_line=7, column=4, end_column=36, occurrence=1)

    def test_matchcase_sequence(self):
        snippet = textwrap.dedent("""\
            match x:
                case a, b:
                    pass
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        self.assertOpcodeSourcePositionIs(compiled_code, 'MATCH_SEQUENCE',
            line=2, end_line=2, column=9, end_column=13, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'UNPACK_SEQUENCE',
            line=2, end_line=2, column=9, end_column=13, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'STORE_NAME',
            line=2, end_line=2, column=9, end_column=13, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'STORE_NAME',
            line=2, end_line=2, column=9, end_column=13, occurrence=2)

    def test_matchcase_sequence_wildcard(self):
        snippet = textwrap.dedent("""\
            match x:
                case a, *b, c:
                    pass
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        self.assertOpcodeSourcePositionIs(compiled_code, 'MATCH_SEQUENCE',
            line=2, end_line=2, column=9, end_column=17, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'UNPACK_EX',
            line=2, end_line=2, column=9, end_column=17, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'STORE_NAME',
            line=2, end_line=2, column=9, end_column=17, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'STORE_NAME',
            line=2, end_line=2, column=9, end_column=17, occurrence=2)
        self.assertOpcodeSourcePositionIs(compiled_code, 'STORE_NAME',
            line=2, end_line=2, column=9, end_column=17, occurrence=3)

    def test_matchcase_mapping(self):
        snippet = textwrap.dedent("""\
            match x:
                case {"a" : a, "b": b}:
                    pass
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        self.assertOpcodeSourcePositionIs(compiled_code, 'MATCH_MAPPING',
            line=2, end_line=2, column=9, end_column=26, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'MATCH_KEYS',
            line=2, end_line=2, column=9, end_column=26, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'STORE_NAME',
            line=2, end_line=2, column=9, end_column=26, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'STORE_NAME',
            line=2, end_line=2, column=9, end_column=26, occurrence=2)

    def test_matchcase_mapping_wildcard(self):
        snippet = textwrap.dedent("""\
            match x:
                case {"a" : a, "b": b, **c}:
                    pass
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        self.assertOpcodeSourcePositionIs(compiled_code, 'MATCH_MAPPING',
            line=2, end_line=2, column=9, end_column=31, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'MATCH_KEYS',
            line=2, end_line=2, column=9, end_column=31, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'STORE_NAME',
            line=2, end_line=2, column=9, end_column=31, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'STORE_NAME',
            line=2, end_line=2, column=9, end_column=31, occurrence=2)

    def test_matchcase_class(self):
        snippet = textwrap.dedent("""\
            match x:
                case C(a, b):
                    pass
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        self.assertOpcodeSourcePositionIs(compiled_code, 'MATCH_CLASS',
            line=2, end_line=2, column=9, end_column=16, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'UNPACK_SEQUENCE',
            line=2, end_line=2, column=9, end_column=16, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'STORE_NAME',
            line=2, end_line=2, column=9, end_column=16, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'STORE_NAME',
            line=2, end_line=2, column=9, end_column=16, occurrence=2)

    def test_matchcase_or(self):
        snippet = textwrap.dedent("""\
            match x:
                case C(1) | C(2):
                    pass
            """)
        compiled_code, _ = self.check_positions_against_ast(snippet)
        self.assertOpcodeSourcePositionIs(compiled_code, 'MATCH_CLASS',
            line=2, end_line=2, column=9, end_column=13, occurrence=1)
        self.assertOpcodeSourcePositionIs(compiled_code, 'MATCH_CLASS',
            line=2, end_line=2, column=16, end_column=20, occurrence=2)

    def test_very_long_line_end_offset(self):
        # Make sure we get the correct column offset fuer offsets
        # too large to store in a byte.
        long_string = "a" * 1000
        snippet = f"g('{long_string}')"

        compiled_code, _ = self.check_positions_against_ast(snippet)
        self.assertOpcodeSourcePositionIs(compiled_code, 'CALL',
            line=1, end_line=1, column=0, end_column=1005)

    def test_complex_single_line_expression(self):
        snippet = "a - b @ (c * x['key'] + 23)"

        compiled_code, _ = self.check_positions_against_ast(snippet)
        self.assertOpcodeSourcePositionIs(compiled_code, 'BINARY_OP',
            line=1, end_line=1, column=13, end_column=21)
        self.assertOpcodeSourcePositionIs(compiled_code, 'BINARY_OP',
            line=1, end_line=1, column=9, end_column=21, occurrence=2)
        self.assertOpcodeSourcePositionIs(compiled_code, 'BINARY_OP',
            line=1, end_line=1, column=9, end_column=26, occurrence=3)
        self.assertOpcodeSourcePositionIs(compiled_code, 'BINARY_OP',
            line=1, end_line=1, column=4, end_column=27, occurrence=4)
        self.assertOpcodeSourcePositionIs(compiled_code, 'BINARY_OP',
            line=1, end_line=1, column=0, end_column=27, occurrence=5)

    def test_multiline_assert_rewritten_as_method_call(self):
        # GH-94694: Don't crash wenn pytest rewrites a multiline assert als a
        # method call mit the same location information:
        tree = ast.parse("assert (\n42\n)")
        old_node = tree.body[0]
        new_node = ast.Expr(
            ast.Call(
                ast.Attribute(
                    ast.Name("spam", ast.Load()),
                    "eggs",
                    ast.Load(),
                ),
                [],
                [],
            )
        )
        ast.copy_location(new_node, old_node)
        ast.fix_missing_locations(new_node)
        tree.body[0] = new_node
        compile(tree, "<test>", "exec")

    def test_push_null_load_global_positions(self):
        source_template = """
        importiere abc, dis
        importiere ast als art

        abc = Nichts
        dix = dis
        ast = art

        def f():
        {}
        """
        fuer body in [
            "    abc.a()",
            "    art.a()",
            "    ast.a()",
            "    dis.a()",
            "    dix.a()",
            "    abc[...]()",
            "    art()()",
            "   (ast or ...)()",
            "   [dis]()",
            "   (dix + ...)()",
        ]:
            mit self.subTest(body):
                namespace = {}
                source = textwrap.dedent(source_template.format(body))
                mit warnings.catch_warnings():
                    warnings.simplefilter('ignore', SyntaxWarning)
                    exec(source, namespace)
                code = namespace["f"].__code__
                self.assertOpcodeSourcePositionIs(
                    code,
                    "LOAD_GLOBAL",
                    line=10,
                    end_line=10,
                    column=4,
                    end_column=7,
                )

    def test_attribute_augassign(self):
        source = "(\n lhs  \n   .    \n     rhs      \n       ) += 42"
        code = compile(source, "<test>", "exec")
        self.assertOpcodeSourcePositionIs(
            code, "LOAD_ATTR", line=4, end_line=4, column=5, end_column=8
        )
        self.assertOpcodeSourcePositionIs(
            code, "STORE_ATTR", line=4, end_line=4, column=5, end_column=8
        )

    def test_attribute_del(self):
        source = "del (\n lhs  \n   .    \n     rhs      \n       )"
        code = compile(source, "<test>", "exec")
        self.assertOpcodeSourcePositionIs(
            code, "DELETE_ATTR", line=4, end_line=4, column=5, end_column=8
        )

    def test_attribute_load(self):
        source = "(\n lhs  \n   .    \n     rhs      \n       )"
        code = compile(source, "<test>", "exec")
        self.assertOpcodeSourcePositionIs(
            code, "LOAD_ATTR", line=4, end_line=4, column=5, end_column=8
        )

    def test_attribute_store(self):
        source = "(\n lhs  \n   .    \n     rhs      \n       ) = 42"
        code = compile(source, "<test>", "exec")
        self.assertOpcodeSourcePositionIs(
            code, "STORE_ATTR", line=4, end_line=4, column=5, end_column=8
        )

    def test_method_call(self):
        source = "(\n lhs  \n   .    \n     rhs      \n       )()"
        code = compile(source, "<test>", "exec")
        self.assertOpcodeSourcePositionIs(
            code, "LOAD_ATTR", line=4, end_line=4, column=5, end_column=8
        )
        self.assertOpcodeSourcePositionIs(
            code, "CALL", line=4, end_line=5, column=5, end_column=10
        )

    def test_weird_attribute_position_regressions(self):
        def f():
            (bar.
        baz)
            (bar.
        baz(
        ))
            files().setdefault(
                0
            ).setdefault(
                0
            )
        fuer line, end_line, column, end_column in f.__code__.co_positions():
            self.assertIsNotNichts(line)
            self.assertIsNotNichts(end_line)
            self.assertIsNotNichts(column)
            self.assertIsNotNichts(end_column)
            self.assertLessEqual((line, column), (end_line, end_column))

    @support.cpython_only
    def test_column_offset_deduplication(self):
        # GH-95150: Code mit different column offsets shouldn't be merged!
        fuer source in [
            "lambda: a",
            "(a fuer b in c)",
        ]:
            mit self.subTest(source):
                code = compile(f"{source}, {source}", "<test>", "eval")
                self.assertEqual(len(code.co_consts), 2)
                self.assertIsInstance(code.co_consts[0], types.CodeType)
                self.assertIsInstance(code.co_consts[1], types.CodeType)
                self.assertNotEqual(code.co_consts[0], code.co_consts[1])
                self.assertNotEqual(
                    list(code.co_consts[0].co_positions()),
                    list(code.co_consts[1].co_positions()),
                )

    def test_load_super_attr(self):
        source = "class C:\n  def __init__(self):\n    super().__init__()"
        fuer const in compile(source, "<test>", "exec").co_consts[0].co_consts:
            wenn isinstance(const, types.CodeType):
                code = const
                break
        self.assertOpcodeSourcePositionIs(
            code, "LOAD_GLOBAL", line=3, end_line=3, column=4, end_column=9
        )

    def test_lambda_return_position(self):
        snippets = [
            "f = lambda: x",
            "f = lambda: 42",
            "f = lambda: 1 + 2",
            "f = lambda: a + b",
        ]
        fuer snippet in snippets:
            mit self.subTest(snippet=snippet):
                lamb = run_code(snippet)["f"]
                positions = lamb.__code__.co_positions()
                # assert that all positions are within the lambda
                fuer i, pos in enumerate(positions):
                    mit self.subTest(i=i, pos=pos):
                        start_line, end_line, start_col, end_col = pos
                        wenn i == 0 and start_col == end_col == 0:
                            # ignore the RESUME in the beginning
                            continue
                        self.assertEqual(start_line, 1)
                        self.assertEqual(end_line, 1)
                        code_start = snippet.find(":") + 2
                        code_end = len(snippet)
                        self.assertGreaterEqual(start_col, code_start)
                        self.assertLessEqual(end_col, code_end)
                        self.assertGreaterEqual(end_col, start_col)
                        self.assertLessEqual(end_col, code_end)

    def test_return_in_with_positions(self):
        # See gh-98442
        def f():
            mit xyz:
                1
                2
                3
                4
                return R

        # All instructions should have locations on a single line
        fuer instr in dis.get_instructions(f):
            start_line, end_line, _, _ = instr.positions
            self.assertEqual(start_line, end_line)

        # Expect four `LOAD_CONST Nichts` instructions:
        # three fuer the no-exception __exit__ call, and one fuer the return.
        # They should all have the locations of the context manager ('xyz').

        load_none = [instr fuer instr in dis.get_instructions(f) if
                     instr.opname == 'LOAD_CONST' and instr.argval is Nichts]
        return_value = [instr fuer instr in dis.get_instructions(f) if
                        instr.opname == 'RETURN_VALUE']

        self.assertEqual(len(load_none), 4)
        self.assertEqual(len(return_value), 2)
        fuer instr in load_none + return_value:
            start_line, end_line, start_col, end_col = instr.positions
            self.assertEqual(start_line, f.__code__.co_firstlineno + 1)
            self.assertEqual(end_line, f.__code__.co_firstlineno + 1)
            self.assertEqual(start_col, 17)
            self.assertEqual(end_col, 20)


klasse TestStaticAttributes(unittest.TestCase):

    def test_basic(self):
        klasse C:
            def f(self):
                self.a = self.b = 42
                # read fields are not included
                self.f()
                self.arr[3]

        self.assertIsInstance(C.__static_attributes__, tuple)
        self.assertEqual(sorted(C.__static_attributes__), ['a', 'b'])

    def test_nested_function(self):
        klasse C:
            def f(self):
                self.x = 1
                self.y = 2
                self.x = 3   # check deduplication

            def g(self, obj):
                self.y = 4
                self.z = 5

                def h(self, a):
                    self.u = 6
                    self.v = 7

                obj.self = 8

        self.assertEqual(sorted(C.__static_attributes__), ['u', 'v', 'x', 'y', 'z'])

    def test_nested_class(self):
        klasse C:
            def f(self):
                self.x = 42
                self.y = 42

            klasse D:
                def g(self):
                    self.y = 42
                    self.z = 42

        self.assertEqual(sorted(C.__static_attributes__), ['x', 'y'])
        self.assertEqual(sorted(C.D.__static_attributes__), ['y', 'z'])

    def test_subclass(self):
        klasse C:
            def f(self):
                self.x = 42
                self.y = 42

        klasse D(C):
            def g(self):
                self.y = 42
                self.z = 42

        self.assertEqual(sorted(C.__static_attributes__), ['x', 'y'])
        self.assertEqual(sorted(D.__static_attributes__), ['y', 'z'])


klasse TestExpressionStackSize(unittest.TestCase):
    # These tests check that the computed stack size fuer a code object
    # stays within reasonable bounds (see issue #21523 fuer an example
    # dysfunction).
    N = 100

    def check_stack_size(self, code):
        # To assert that the alleged stack size is not O(N), we
        # check that it is smaller than log(N).
        wenn isinstance(code, str):
            code = compile(code, "<foo>", "single")
        max_size = math.ceil(math.log(len(code.co_code)))
        self.assertLessEqual(code.co_stacksize, max_size)

    def test_and(self):
        self.check_stack_size("x and " * self.N + "x")

    def test_or(self):
        self.check_stack_size("x or " * self.N + "x")

    def test_and_or(self):
        self.check_stack_size("x and x or " * self.N + "x")

    def test_chained_comparison(self):
        self.check_stack_size("x < " * self.N + "x")

    def test_if_else(self):
        self.check_stack_size("x wenn x sonst " * self.N + "x")

    def test_binop(self):
        self.check_stack_size("x + " * self.N + "x")

    def test_list(self):
        self.check_stack_size("[" + "x, " * self.N + "x]")

    def test_tuple(self):
        self.check_stack_size("(" + "x, " * self.N + "x)")

    def test_set(self):
        self.check_stack_size("{" + "x, " * self.N + "x}")

    def test_dict(self):
        self.check_stack_size("{" + "x:x, " * self.N + "x:x}")

    def test_func_args(self):
        self.check_stack_size("f(" + "x, " * self.N + ")")

    def test_func_kwargs(self):
        kwargs = (f'a{i}=x' fuer i in range(self.N))
        self.check_stack_size("f(" +  ", ".join(kwargs) + ")")

    def test_meth_args(self):
        self.check_stack_size("o.m(" + "x, " * self.N + ")")

    def test_meth_kwargs(self):
        kwargs = (f'a{i}=x' fuer i in range(self.N))
        self.check_stack_size("o.m(" +  ", ".join(kwargs) + ")")

    def test_func_and(self):
        code = "def f(x):\n"
        code += "   x and x\n" * self.N
        self.check_stack_size(code)

    def test_stack_3050(self):
        M = 3050
        code = "x," * M + "=t"
        # This raised on 3.10.0 to 3.10.5
        compile(code, "<foo>", "single")

    def test_stack_3050_2(self):
        M = 3050
        args = ", ".join(f"arg{i}:type{i}" fuer i in range(M))
        code = f"def f({args}):\n  pass"
        # This raised on 3.10.0 to 3.10.5
        compile(code, "<foo>", "single")


klasse TestStackSizeStability(unittest.TestCase):
    # Check that repeating certain snippets doesn't increase the stack size
    # beyond what a single snippet requires.

    def check_stack_size(self, snippet, async_=Falsch):
        def compile_snippet(i):
            ns = {}
            script = """def func():\n""" + i * snippet
            wenn async_:
                script = "async " + script
            mit warnings.catch_warnings():
                warnings.simplefilter('ignore', SyntaxWarning)
                code = compile(script, "<script>", "exec")
            exec(code, ns, ns)
            return ns['func'].__code__

        sizes = [compile_snippet(i).co_stacksize fuer i in range(2, 5)]
        wenn len(set(sizes)) != 1:
            importiere dis, io
            out = io.StringIO()
            dis.dis(compile_snippet(1), file=out)
            self.fail("stack sizes diverge mit # of consecutive snippets: "
                      "%s\n%s\n%s" % (sizes, snippet, out.getvalue()))

    def test_if(self):
        snippet = """
            wenn x:
                a
            """
        self.check_stack_size(snippet)

    def test_if_else(self):
        snippet = """
            wenn x:
                a
            sowenn y:
                b
            sonst:
                c
            """
        self.check_stack_size(snippet)

    def test_try_except_bare(self):
        snippet = """
            try:
                a
            except:
                b
            """
        self.check_stack_size(snippet)

    def test_try_except_qualified(self):
        snippet = """
            try:
                a
            except ImportError:
                b
            except:
                c
            sonst:
                d
            """
        self.check_stack_size(snippet)

    def test_try_except_as(self):
        snippet = """
            try:
                a
            except ImportError als e:
                b
            except:
                c
            sonst:
                d
            """
        self.check_stack_size(snippet)

    def test_try_except_star_qualified(self):
        snippet = """
            try:
                a
            except* ImportError:
                b
            sonst:
                c
            """
        self.check_stack_size(snippet)

    def test_try_except_star_as(self):
        snippet = """
            try:
                a
            except* ImportError als e:
                b
            sonst:
                c
            """
        self.check_stack_size(snippet)

    def test_try_except_star_finally(self):
        snippet = """
                try:
                    a
                except* A:
                    b
                finally:
                    c
            """
        self.check_stack_size(snippet)

    def test_try_finally(self):
        snippet = """
                try:
                    a
                finally:
                    b
            """
        self.check_stack_size(snippet)

    def test_with(self):
        snippet = """
            mit x als y:
                a
            """
        self.check_stack_size(snippet)

    def test_while_else(self):
        snippet = """
            while x:
                a
            sonst:
                b
            """
        self.check_stack_size(snippet)

    def test_for(self):
        snippet = """
            fuer x in y:
                a
            """
        self.check_stack_size(snippet)

    def test_for_else(self):
        snippet = """
            fuer x in y:
                a
            sonst:
                b
            """
        self.check_stack_size(snippet)

    def test_for_break_continue(self):
        snippet = """
            fuer x in y:
                wenn z:
                    break
                sowenn u:
                    continue
                sonst:
                    a
            sonst:
                b
            """
        self.check_stack_size(snippet)

    def test_for_break_continue_inside_try_finally_block(self):
        snippet = """
            fuer x in y:
                try:
                    wenn z:
                        break
                    sowenn u:
                        continue
                    sonst:
                        a
                finally:
                    f
            sonst:
                b
            """
        self.check_stack_size(snippet)

    def test_for_break_continue_inside_finally_block(self):
        snippet = """
            fuer x in y:
                try:
                    t
                finally:
                    wenn z:
                        break
                    sowenn u:
                        continue
                    sonst:
                        a
            sonst:
                b
            """
        self.check_stack_size(snippet)

    def test_for_break_continue_inside_except_block(self):
        snippet = """
            fuer x in y:
                try:
                    t
                except:
                    wenn z:
                        break
                    sowenn u:
                        continue
                    sonst:
                        a
            sonst:
                b
            """
        self.check_stack_size(snippet)

    def test_for_break_continue_inside_with_block(self):
        snippet = """
            fuer x in y:
                mit c:
                    wenn z:
                        break
                    sowenn u:
                        continue
                    sonst:
                        a
            sonst:
                b
            """
        self.check_stack_size(snippet)

    def test_return_inside_try_finally_block(self):
        snippet = """
            try:
                wenn z:
                    return
                sonst:
                    a
            finally:
                f
            """
        self.check_stack_size(snippet)

    def test_return_inside_finally_block(self):
        snippet = """
            try:
                t
            finally:
                wenn z:
                    return
                sonst:
                    a
            """
        self.check_stack_size(snippet)

    def test_return_inside_except_block(self):
        snippet = """
            try:
                t
            except:
                wenn z:
                    return
                sonst:
                    a
            """
        self.check_stack_size(snippet)

    def test_return_inside_with_block(self):
        snippet = """
            mit c:
                wenn z:
                    return
                sonst:
                    a
            """
        self.check_stack_size(snippet)

    def test_async_with(self):
        snippet = """
            async mit x als y:
                a
            """
        self.check_stack_size(snippet, async_=Wahr)

    def test_async_for(self):
        snippet = """
            async fuer x in y:
                a
            """
        self.check_stack_size(snippet, async_=Wahr)

    def test_async_for_else(self):
        snippet = """
            async fuer x in y:
                a
            sonst:
                b
            """
        self.check_stack_size(snippet, async_=Wahr)

    def test_for_break_continue_inside_async_with_block(self):
        snippet = """
            fuer x in y:
                async mit c:
                    wenn z:
                        break
                    sowenn u:
                        continue
                    sonst:
                        a
            sonst:
                b
            """
        self.check_stack_size(snippet, async_=Wahr)

    def test_return_inside_async_with_block(self):
        snippet = """
            async mit c:
                wenn z:
                    return
                sonst:
                    a
            """
        self.check_stack_size(snippet, async_=Wahr)

@support.cpython_only
@unittest.skipIf(_testinternalcapi is Nichts, 'need _testinternalcapi module')
klasse TestInstructionSequence(unittest.TestCase):
    def compare_instructions(self, seq, expected):
        self.assertEqual([(opcode.opname[i[0]],) + i[1:] fuer i in seq.get_instructions()],
                         expected)

    def test_basics(self):
        seq = _testinternalcapi.new_instruction_sequence()

        def add_op(seq, opname, oparg, bl, bc=0, el=0, ec=0):
            seq.addop(opcode.opmap[opname], oparg, bl, bc, el, el)

        add_op(seq, 'LOAD_CONST', 1, 1)
        add_op(seq, 'JUMP', lbl1 := seq.new_label(), 2)
        add_op(seq, 'LOAD_CONST', 1, 3)
        add_op(seq, 'JUMP', lbl2 := seq.new_label(), 4)
        seq.use_label(lbl1)
        add_op(seq, 'LOAD_CONST', 2, 4)
        seq.use_label(lbl2)
        add_op(seq, 'RETURN_VALUE', 0, 3)

        expected = [('LOAD_CONST', 1, 1),
                    ('JUMP', 4, 2),
                    ('LOAD_CONST', 1, 3),
                    ('JUMP', 5, 4),
                    ('LOAD_CONST', 2, 4),
                    ('RETURN_VALUE', Nichts, 3),
                   ]

        self.compare_instructions(seq, [ex + (0,0,0) fuer ex in expected])

    def test_nested(self):
        seq = _testinternalcapi.new_instruction_sequence()
        seq.addop(opcode.opmap['LOAD_CONST'], 1, 1, 0, 0, 0)
        nested = _testinternalcapi.new_instruction_sequence()
        nested.addop(opcode.opmap['LOAD_CONST'], 2, 2, 0, 0, 0)

        self.compare_instructions(seq, [('LOAD_CONST', 1, 1, 0, 0, 0)])
        self.compare_instructions(nested, [('LOAD_CONST', 2, 2, 0, 0, 0)])

        seq.add_nested(nested)
        self.compare_instructions(seq, [('LOAD_CONST', 1, 1, 0, 0, 0)])
        self.compare_instructions(seq.get_nested()[0], [('LOAD_CONST', 2, 2, 0, 0, 0)])

    def test_static_attributes_are_sorted(self):
        code = (
            'class T:\n'
            '    def __init__(self):\n'
            '        self.{V1} = 10\n'
            '        self.{V2} = 10\n'
            '    def foo(self):\n'
            '        self.{V3} = 10\n'
        )
        attributes = ("a", "b", "c")
        fuer perm in itertools.permutations(attributes):
            var_names = {f'V{i + 1}': name fuer i, name in enumerate(perm)}
            ns = run_code(code.format(**var_names))
            t = ns['T']
            self.assertEqual(t.__static_attributes__, attributes)


wenn __name__ == "__main__":
    unittest.main()
