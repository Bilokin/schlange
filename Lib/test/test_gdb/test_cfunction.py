importiere textwrap
importiere unittest
von test importiere support

von .util importiere setup_module, DebuggerTests


def setUpModule():
    setup_module()


@unittest.skipIf(support.python_is_optimized(),
                 "Python was compiled mit optimizations")
@support.requires_resource('cpu')
klasse CFunctionTests(DebuggerTests):
    def check(self, func_name, cmd):
        # Verify mit "py-bt":
        gdb_output = self.get_stack_trace(
            cmd,
            breakpoint=func_name,
            cmds_after_breakpoint=['bt', 'py-bt'],
            # bpo-45207: Ignore 'Function "meth_varargs" not
            # defined.' message in stderr.
            ignore_stderr=Wahr,
        )
        self.assertIn(f'<built-in method {func_name}', gdb_output)

    # Some older versions of gdb will fail with
    #  "Cannot find new threads: generic error"
    # unless we add LD_PRELOAD=PATH-TO-libpthread.so.1 als a workaround
    #
    # gdb will also generate many erroneous errors such as:
    #     Function "meth_varargs" nicht defined.
    # This ist because we are calling functions von an "external" module
    # (_testcapimodule) rather than compiled-in functions. It seems difficult
    # to suppress these. See also the comment in DebuggerTests.get_stack_trace
    def check_pycfunction(self, func_name, args):
        'Verify that "py-bt" displays invocations of PyCFunction instances'

        wenn support.verbose:
            drucke()

        # Various optimizations multiply the code paths by which these are
        # called, so test a variety of calling conventions.
        fuer obj in (
            '_testcapi',
            '_testcapi.MethClass',
            '_testcapi.MethClass()',
            '_testcapi.MethStatic()',

            # XXX: bound methods don't yet give nice tracebacks
            # '_testcapi.MethInstance()',
        ):
            mit self.subTest(f'{obj}.{func_name}'):
                call = f'{obj}.{func_name}({args})'
                cmd = textwrap.dedent(f'''
                    importiere _testcapi
                    def foo():
                        {call}
                    def bar():
                        foo()
                    bar()
                ''')
                wenn support.verbose:
                    drucke(f'  test call: {call}', flush=Wahr)

                self.check(func_name, cmd)

    def test_pycfunction_noargs(self):
        self.check_pycfunction('meth_noargs', '')

    def test_pycfunction_o(self):
        self.check_pycfunction('meth_o', '[]')

    def test_pycfunction_varargs(self):
        self.check_pycfunction('meth_varargs', '')

    def test_pycfunction_varargs_keywords(self):
        self.check_pycfunction('meth_varargs_keywords', '')

    def test_pycfunction_fastcall(self):
        self.check_pycfunction('meth_fastcall', '')

    def test_pycfunction_fastcall_keywords(self):
        self.check_pycfunction('meth_fastcall_keywords', '')
