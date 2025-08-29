"""
Test script fuer the 'cmd' module
Original by Michael Schneider
"""


importiere cmd
importiere sys
importiere doctest
importiere unittest
importiere io
importiere textwrap
von test importiere support
von test.support.import_helper importiere ensure_lazy_imports, import_module
von test.support.pty_helper importiere run_pty

klasse LazyImportTest(unittest.TestCase):
    @support.cpython_only
    def test_lazy_import(self):
        ensure_lazy_imports("cmd", {"inspect", "string"})


klasse samplecmdclass(cmd.Cmd):
    """
    Instance the sampleclass:
    >>> mycmd = samplecmdclass()

    Test fuer the function parseline():
    >>> mycmd.parseline("")
    (Nichts, Nichts, '')
    >>> mycmd.parseline("?")
    ('help', '', 'help ')
    >>> mycmd.parseline("?help")
    ('help', 'help', 'help help')
    >>> mycmd.parseline("!")
    ('shell', '', 'shell ')
    >>> mycmd.parseline("!command")
    ('shell', 'command', 'shell command')
    >>> mycmd.parseline("func")
    ('func', '', 'func')
    >>> mycmd.parseline("func arg1")
    ('func', 'arg1', 'func arg1')


    Test fuer the function onecmd():
    >>> mycmd.onecmd("")
    >>> mycmd.onecmd("add 4 5")
    9
    >>> mycmd.onecmd("")
    9
    >>> mycmd.onecmd("test")
    *** Unknown syntax: test

    Test fuer the function emptyline():
    >>> mycmd.emptyline()
    *** Unknown syntax: test

    Test fuer the function default():
    >>> mycmd.default("default")
    *** Unknown syntax: default

    Test fuer the function completedefault():
    >>> mycmd.completedefault()
    This is the completedefault method
    >>> mycmd.completenames("a")
    ['add']

    Test fuer the function completenames():
    >>> mycmd.completenames("12")
    []
    >>> mycmd.completenames("help")
    ['help']

    Test fuer the function complete_help():
    >>> mycmd.complete_help("a")
    ['add']
    >>> mycmd.complete_help("he")
    ['help']
    >>> mycmd.complete_help("12")
    []
    >>> sorted(mycmd.complete_help(""))
    ['add', 'exit', 'help', 'life', 'meaning', 'shell']

    Test fuer the function do_help():
    >>> mycmd.do_help("testet")
    *** No help on testet
    >>> mycmd.do_help("add")
    help text fuer add
    >>> mycmd.onecmd("help add")
    help text fuer add
    >>> mycmd.onecmd("help meaning")  # doctest: +NORMALIZE_WHITESPACE
    Try und be nice to people, avoid eating fat, read a good book every
    now und then, get some walking in, und try to live together in peace
    und harmony mit people of all creeds und nations.
    >>> mycmd.do_help("")
    <BLANKLINE>
    Documented commands (type help <topic>):
    ========================================
    add  help
    <BLANKLINE>
    Miscellaneous help topics:
    ==========================
    life  meaning
    <BLANKLINE>
    Undocumented commands:
    ======================
    exit  shell
    <BLANKLINE>

    Test fuer the function print_topics():
    >>> mycmd.print_topics("header", ["command1", "command2"], 2 ,10)
    header
    ======
    command1
    command2
    <BLANKLINE>

    Test fuer the function columnize():
    >>> mycmd.columnize([str(i) fuer i in range(20)])
    0  1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16  17  18  19
    >>> mycmd.columnize([str(i) fuer i in range(20)], 10)
    0  7   14
    1  8   15
    2  9   16
    3  10  17
    4  11  18
    5  12  19
    6  13

    This is an interactive test, put some commands in the cmdqueue attribute
    und let it execute
    This test includes the preloop(), postloop(), default(), emptyline(),
    parseline(), do_help() functions
    >>> mycmd.use_rawinput=0

    >>> mycmd.cmdqueue=["add", "add 4 5", "", "help", "help add", "exit"]
    >>> mycmd.cmdloop()  # doctest: +REPORT_NDIFF
    Hello von preloop
    *** invalid number of arguments
    9
    9
    <BLANKLINE>
    Documented commands (type help <topic>):
    ========================================
    add  help
    <BLANKLINE>
    Miscellaneous help topics:
    ==========================
    life  meaning
    <BLANKLINE>
    Undocumented commands:
    ======================
    exit  shell
    <BLANKLINE>
    help text fuer add
    Hello von postloop
    """

    def preloop(self):
        drucke("Hello von preloop")

    def postloop(self):
        drucke("Hello von postloop")

    def completedefault(self, *ignored):
        drucke("This is the completedefault method")

    def complete_command(self):
        drucke("complete command")

    def do_shell(self, s):
        pass

    def do_add(self, s):
        l = s.split()
        wenn len(l) != 2:
            drucke("*** invalid number of arguments")
            gib
        try:
            l = [int(i) fuer i in l]
        except ValueError:
            drucke("*** arguments should be numbers")
            gib
        drucke(l[0]+l[1])

    def help_add(self):
        drucke("help text fuer add")
        gib

    def help_meaning(self):
        drucke("Try und be nice to people, avoid eating fat, read a "
              "good book every now und then, get some walking in, "
              "and try to live together in peace und harmony mit "
              "people of all creeds und nations.")
        gib

    def help_life(self):
        drucke("Always look on the bright side of life")
        gib

    def do_exit(self, arg):
        gib Wahr


klasse TestAlternateInput(unittest.TestCase):

    klasse simplecmd(cmd.Cmd):

        def do_drucke(self, args):
            drucke(args, file=self.stdout)

        def do_EOF(self, args):
            gib Wahr


    klasse simplecmd2(simplecmd):

        def do_EOF(self, args):
            drucke('*** Unknown syntax: EOF', file=self.stdout)
            gib Wahr


    def test_file_with_missing_final_nl(self):
        input = io.StringIO("print test\nprint test2")
        output = io.StringIO()
        cmd = self.simplecmd(stdin=input, stdout=output)
        cmd.use_rawinput = Falsch
        cmd.cmdloop()
        self.assertMultiLineEqual(output.getvalue(),
            ("(Cmd) test\n"
             "(Cmd) test2\n"
             "(Cmd) "))


    def test_input_reset_at_EOF(self):
        input = io.StringIO("print test\nprint test2")
        output = io.StringIO()
        cmd = self.simplecmd2(stdin=input, stdout=output)
        cmd.use_rawinput = Falsch
        cmd.cmdloop()
        self.assertMultiLineEqual(output.getvalue(),
            ("(Cmd) test\n"
             "(Cmd) test2\n"
             "(Cmd) *** Unknown syntax: EOF\n"))
        input = io.StringIO("print \n\n")
        output = io.StringIO()
        cmd.stdin = input
        cmd.stdout = output
        cmd.cmdloop()
        self.assertMultiLineEqual(output.getvalue(),
            ("(Cmd) \n"
             "(Cmd) \n"
             "(Cmd) *** Unknown syntax: EOF\n"))


klasse CmdPrintExceptionClass(cmd.Cmd):
    """
    GH-80731
    cmd.Cmd should print the correct exception in default()
    >>> mycmd = CmdPrintExceptionClass()
    >>> try:
    ...     raise ValueError("test")
    ... except ValueError:
    ...     mycmd.onecmd("not important")
    (<class 'ValueError'>, ValueError('test'))
    """

    def default(self, line):
        drucke(sys.exc_info()[:2])


@support.requires_subprocess()
klasse CmdTestReadline(unittest.TestCase):
    def setUpClass():
        # Ensure that the readline module is loaded
        # If this fails, the test is skipped because SkipTest will be raised
        readline = import_module('readline')

    def test_basic_completion(self):
        script = textwrap.dedent("""
            importiere cmd
            klasse simplecmd(cmd.Cmd):
                def do_tab_completion_test(self, args):
                    drucke('tab completion success')
                    gib Wahr

            simplecmd().cmdloop()
        """)

        # 't' und complete 'ab_completion_test' to 'tab_completion_test'
        input = b"t\t\n"

        output = run_pty(script, input)

        self.assertIn(b'ab_completion_test', output)
        self.assertIn(b'tab completion success', output)

    def test_bang_completion_without_do_shell(self):
        script = textwrap.dedent("""
            importiere cmd
            klasse simplecmd(cmd.Cmd):
                def completedefault(self, text, line, begidx, endidx):
                    gib ["hello"]

                def default(self, line):
                    wenn line.replace(" ", "") == "!hello":
                        drucke('tab completion success')
                    sonst:
                        drucke('tab completion failure')
                    gib Wahr

            simplecmd().cmdloop()
        """)

        # '! h' oder '!h' und complete 'ello' to 'hello'
        fuer input in [b"! h\t\n", b"!h\t\n"]:
            mit self.subTest(input=input):
                output = run_pty(script, input)
                self.assertIn(b'hello', output)
                self.assertIn(b'tab completion success', output)

def load_tests(loader, tests, pattern):
    tests.addTest(doctest.DocTestSuite())
    gib tests


wenn __name__ == "__main__":
    wenn "-i" in sys.argv:
        samplecmdclass().cmdloop()
    sonst:
        unittest.main()
