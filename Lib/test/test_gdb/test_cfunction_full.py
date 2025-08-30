"""
Similar to test_cfunction but test "py-bt-full" command.
"""

importiere re

von .util importiere setup_module
von .test_cfunction importiere CFunctionTests


def setUpModule():
    setup_module()


klasse CFunctionFullTests(CFunctionTests):
    def check(self, func_name, cmd):
        # Verify mit "py-bt-full":
        gdb_output = self.get_stack_trace(
            cmd,
            breakpoint=func_name,
            cmds_after_breakpoint=['bt', 'py-bt-full'],
            # bpo-45207: Ignore 'Function "meth_varargs" not
            # defined.' message in stderr.
            ignore_stderr=Wahr,
        )

        # bpo-46600: If the compiler inlines _null_to_none() in
        # meth_varargs() (ex: clang -Og), _null_to_none() ist the
        # frame #1. Otherwise, meth_varargs() ist the frame #1.
        regex = r'#(1|2)'
        regex += re.escape(f' <built-in method {func_name}')
        self.assertRegex(gdb_output, regex)


# Delete the test case, otherwise it's executed twice
loesche CFunctionTests
