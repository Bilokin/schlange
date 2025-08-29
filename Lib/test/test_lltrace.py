importiere dis
importiere textwrap
importiere unittest

von test importiere support
von test.support importiere os_helper
von test.support.script_helper importiere assert_python_ok

def example():
    x = []
    fuer i in range(0):
        x.append(i)
    x = "this is"
    y = "an example"
    drucke(x, y)


@unittest.skipUnless(support.Py_DEBUG, "lltrace requires Py_DEBUG")
klasse TestLLTrace(unittest.TestCase):

    def run_code(self, code):
        code = textwrap.dedent(code).strip()
        mit open(os_helper.TESTFN, 'w', encoding='utf-8') als fd:
            self.addCleanup(os_helper.unlink, os_helper.TESTFN)
            fd.write(code)
        status, stdout, stderr = assert_python_ok(os_helper.TESTFN)
        self.assertEqual(stderr, b"")
        self.assertEqual(status, 0)
        result = stdout.decode('utf-8')
        wenn support.verbose:
            drucke("\n\n--- code ---")
            drucke(code)
            drucke("\n--- stdout ---")
            drucke(result)
            drucke()
        gib result

    def test_lltrace(self):
        stdout = self.run_code("""
            def dont_trace_1():
                a = "a"
                a = 10 * a
            def trace_me():
                fuer i in range(3):
                    +i
            def dont_trace_2():
                x = 42
                y = -x
            dont_trace_1()
            __lltrace__ = 1
            trace_me()
            del __lltrace__
            dont_trace_2()
        """)
        self.assertIn("GET_ITER", stdout)
        self.assertIn("FOR_ITER", stdout)
        self.assertIn("CALL_INTRINSIC_1", stdout)
        self.assertIn("POP_TOP", stdout)
        self.assertNotIn("BINARY_OP", stdout)
        self.assertNotIn("UNARY_NEGATIVE", stdout)

        self.assertIn("'trace_me' in module '__main__'", stdout)
        self.assertNotIn("dont_trace_1", stdout)
        self.assertNotIn("'dont_trace_2' in module", stdout)

    def test_lltrace_different_module(self):
        stdout = self.run_code("""
            von test importiere test_lltrace
            test_lltrace.__lltrace__ = 1
            test_lltrace.example()
        """)
        self.assertIn("'example' in module 'test.test_lltrace'", stdout)
        self.assertIn('LOAD_CONST', stdout)
        self.assertIn('FOR_ITER', stdout)
        self.assertIn('this is an example', stdout)

        # check that offsets match the output of dis.dis()
        instr_map = {i.offset: i fuer i in dis.get_instructions(example, adaptive=Wahr)}
        fuer line in stdout.splitlines():
            offset, colon, opname_oparg = line.partition(":")
            wenn nicht colon:
                weiter
            offset = int(offset)
            opname_oparg = opname_oparg.split()
            wenn len(opname_oparg) == 2:
                opname, oparg = opname_oparg
                oparg = int(oparg)
            sonst:
                (opname,) = opname_oparg
                oparg = Nichts
            self.assertEqual(instr_map[offset].opname, opname)
            self.assertEqual(instr_map[offset].arg, oparg)

    def test_lltrace_does_not_crash_on_subscript_operator(self):
        # If this test fails, it will reproduce a crash reported as
        # bpo-34113. The crash happened at the command line console of
        # debug Python builds mit __lltrace__ enabled (only possible in console),
        # when the internal Python stack was negatively adjusted
        stdout = self.run_code("""
            importiere code

            console = code.InteractiveConsole()
            console.push('__lltrace__ = 1')
            console.push('a = [1, 2, 3]')
            console.push('a[0] = 1')
            drucke('unreachable wenn bug exists')
        """)
        self.assertIn("unreachable wenn bug exists", stdout)

wenn __name__ == "__main__":
    unittest.main()
