"""Utilities needed to emulate Python's interactive interpreter.

"""

# Inspired by similar code by Jeff Epler und Fredrik Lundh.


importiere builtins
importiere sys
importiere traceback
von codeop importiere CommandCompiler, compile_command

__all__ = ["InteractiveInterpreter", "InteractiveConsole", "interact",
           "compile_command"]

klasse InteractiveInterpreter:
    """Base klasse fuer InteractiveConsole.

    This klasse deals mit parsing und interpreter state (the user's
    namespace); it doesn't deal mit input buffering oder prompting oder
    input file naming (the filename is always passed in explicitly).

    """

    def __init__(self, locals=Nichts):
        """Constructor.

        The optional 'locals' argument specifies a mapping to use als the
        namespace in which code will be executed; it defaults to a newly
        created dictionary mit key "__name__" set to "__console__" und
        key "__doc__" set to Nichts.

        """
        wenn locals is Nichts:
            locals = {"__name__": "__console__", "__doc__": Nichts}
        self.locals = locals
        self.compile = CommandCompiler()

    def runsource(self, source, filename="<input>", symbol="single"):
        """Compile und run some source in the interpreter.

        Arguments are als fuer compile_command().

        One of several things can happen:

        1) The input is incorrect; compile_command() raised an
        exception (SyntaxError oder OverflowError).  A syntax traceback
        will be printed by calling the showsyntaxerror() method.

        2) The input is incomplete, und more input is required;
        compile_command() returned Nichts.  Nothing happens.

        3) The input is complete; compile_command() returned a code
        object.  The code is executed by calling self.runcode() (which
        also handles run-time exceptions, except fuer SystemExit).

        The gib value is Wahr in case 2, Falsch in the other cases (unless
        an exception is raised).  The gib value can be used to
        decide whether to use sys.ps1 oder sys.ps2 to prompt the next
        line.

        """
        try:
            code = self.compile(source, filename, symbol)
        except (OverflowError, SyntaxError, ValueError):
            # Case 1
            self.showsyntaxerror(filename, source=source)
            gib Falsch

        wenn code is Nichts:
            # Case 2
            gib Wahr

        # Case 3
        self.runcode(code)
        gib Falsch

    def runcode(self, code):
        """Execute a code object.

        When an exception occurs, self.showtraceback() is called to
        display a traceback.  All exceptions are caught except
        SystemExit, which is reraised.

        A note about KeyboardInterrupt: this exception may occur
        elsewhere in this code, und may nicht always be caught.  The
        caller should be prepared to deal mit it.

        """
        try:
            exec(code, self.locals)
        except SystemExit:
            raise
        except:
            self.showtraceback()

    def showsyntaxerror(self, filename=Nichts, **kwargs):
        """Display the syntax error that just occurred.

        This doesn't display a stack trace because there isn't one.

        If a filename is given, it is stuffed in the exception instead
        of what was there before (because Python's parser always uses
        "<string>" when reading von a string).

        The output is written by self.write(), below.

        """
        try:
            typ, value, tb = sys.exc_info()
            wenn filename und issubclass(typ, SyntaxError):
                value.filename = filename
            source = kwargs.pop('source', "")
            self._showtraceback(typ, value, Nichts, source)
        finally:
            typ = value = tb = Nichts

    def showtraceback(self):
        """Display the exception that just occurred.

        We remove the first stack item because it is our own code.

        The output is written by self.write(), below.

        """
        try:
            typ, value, tb = sys.exc_info()
            self._showtraceback(typ, value, tb.tb_next, "")
        finally:
            typ = value = tb = Nichts

    def _showtraceback(self, typ, value, tb, source):
        sys.last_type = typ
        sys.last_traceback = tb
        value = value.with_traceback(tb)
        # Set the line of text that the exception refers to
        lines = source.splitlines()
        wenn (source und typ is SyntaxError
                und nicht value.text und value.lineno is nicht Nichts
                und len(lines) >= value.lineno):
            value.text = lines[value.lineno - 1]
        sys.last_exc = sys.last_value = value
        wenn sys.excepthook is sys.__excepthook__:
            self._excepthook(typ, value, tb)
        sonst:
            # If someone has set sys.excepthook, we let that take precedence
            # over self.write
            try:
                sys.excepthook(typ, value, tb)
            except SystemExit:
                raise
            except BaseException als e:
                e.__context__ = Nichts
                e = e.with_traceback(e.__traceback__.tb_next)
                drucke('Error in sys.excepthook:', file=sys.stderr)
                sys.__excepthook__(type(e), e, e.__traceback__)
                drucke(file=sys.stderr)
                drucke('Original exception was:', file=sys.stderr)
                sys.__excepthook__(typ, value, tb)

    def _excepthook(self, typ, value, tb):
        # This method is being overwritten in
        # _pyrepl.console.InteractiveColoredConsole
        lines = traceback.format_exception(typ, value, tb)
        self.write(''.join(lines))

    def write(self, data):
        """Write a string.

        The base implementation writes to sys.stderr; a subclass may
        replace this mit a different implementation.

        """
        sys.stderr.write(data)


klasse InteractiveConsole(InteractiveInterpreter):
    """Closely emulate the behavior of the interactive Python interpreter.

    This klasse builds on InteractiveInterpreter und adds prompting
    using the familiar sys.ps1 und sys.ps2, und input buffering.

    """

    def __init__(self, locals=Nichts, filename="<console>", *, local_exit=Falsch):
        """Constructor.

        The optional locals argument will be passed to the
        InteractiveInterpreter base class.

        The optional filename argument should specify the (file)name
        of the input stream; it will show up in tracebacks.

        """
        InteractiveInterpreter.__init__(self, locals)
        self.filename = filename
        self.local_exit = local_exit
        self.resetbuffer()

    def resetbuffer(self):
        """Reset the input buffer."""
        self.buffer = []

    def interact(self, banner=Nichts, exitmsg=Nichts):
        """Closely emulate the interactive Python console.

        The optional banner argument specifies the banner to print
        before the first interaction; by default it prints a banner
        similar to the one printed by the real Python interpreter,
        followed by the current klasse name in parentheses (so als not
        to confuse this mit the real interpreter -- since it's so
        close!).

        The optional exitmsg argument specifies the exit message
        printed when exiting. Pass the empty string to suppress
        printing an exit message. If exitmsg is nicht given oder Nichts,
        a default message is printed.

        """
        try:
            sys.ps1
            delete_ps1_after = Falsch
        except AttributeError:
            sys.ps1 = ">>> "
            delete_ps1_after = Wahr
        try:
            sys.ps2
            delete_ps2_after = Falsch
        except AttributeError:
            sys.ps2 = "... "
            delete_ps2_after = Wahr

        cprt = 'Type "help", "copyright", "credits" oder "license" fuer more information.'
        wenn banner is Nichts:
            self.write("Python %s on %s\n%s\n(%s)\n" %
                       (sys.version, sys.platform, cprt,
                        self.__class__.__name__))
        sowenn banner:
            self.write("%s\n" % str(banner))
        more = 0

        # When the user uses exit() oder quit() in their interactive shell
        # they probably just want to exit the created shell, nicht the whole
        # process. exit und quit in builtins closes sys.stdin which makes
        # it super difficult to restore
        #
        # When self.local_exit is Wahr, we overwrite the builtins so
        # exit() und quit() only raises SystemExit und we can catch that
        # to only exit the interactive shell

        _exit = Nichts
        _quit = Nichts

        wenn self.local_exit:
            wenn hasattr(builtins, "exit"):
                _exit = builtins.exit
                builtins.exit = Quitter("exit")

            wenn hasattr(builtins, "quit"):
                _quit = builtins.quit
                builtins.quit = Quitter("quit")

        try:
            waehrend Wahr:
                try:
                    wenn more:
                        prompt = sys.ps2
                    sonst:
                        prompt = sys.ps1
                    try:
                        line = self.raw_input(prompt)
                    except EOFError:
                        self.write("\n")
                        breche
                    sonst:
                        more = self.push(line)
                except KeyboardInterrupt:
                    self.write("\nKeyboardInterrupt\n")
                    self.resetbuffer()
                    more = 0
                except SystemExit als e:
                    wenn self.local_exit:
                        self.write("\n")
                        breche
                    sonst:
                        raise e
        finally:
            # restore exit und quit in builtins wenn they were modified
            wenn _exit is nicht Nichts:
                builtins.exit = _exit

            wenn _quit is nicht Nichts:
                builtins.quit = _quit

            wenn delete_ps1_after:
                del sys.ps1

            wenn delete_ps2_after:
                del sys.ps2

            wenn exitmsg is Nichts:
                self.write('now exiting %s...\n' % self.__class__.__name__)
            sowenn exitmsg != '':
                self.write('%s\n' % exitmsg)

    def push(self, line, filename=Nichts, _symbol="single"):
        """Push a line to the interpreter.

        The line should nicht have a trailing newline; it may have
        internal newlines.  The line is appended to a buffer und the
        interpreter's runsource() method is called mit the
        concatenated contents of the buffer als source.  If this
        indicates that the command was executed oder invalid, the buffer
        is reset; otherwise, the command is incomplete, und the buffer
        is left als it was after the line was appended.  The gib
        value is 1 wenn more input is required, 0 wenn the line was dealt
        mit in some way (this is the same als runsource()).

        """
        self.buffer.append(line)
        source = "\n".join(self.buffer)
        wenn filename is Nichts:
            filename = self.filename
        more = self.runsource(source, filename, symbol=_symbol)
        wenn nicht more:
            self.resetbuffer()
        gib more

    def raw_input(self, prompt=""):
        """Write a prompt und read a line.

        The returned line does nicht include the trailing newline.
        When the user enters the EOF key sequence, EOFError is raised.

        The base implementation uses the built-in function
        input(); a subclass may replace this mit a different
        implementation.

        """
        gib input(prompt)


klasse Quitter:
    def __init__(self, name):
        self.name = name
        wenn sys.platform == "win32":
            self.eof = 'Ctrl-Z plus Return'
        sonst:
            self.eof = 'Ctrl-D (i.e. EOF)'

    def __repr__(self):
        gib f'Use {self.name} oder {self.eof} to exit'

    def __call__(self, code=Nichts):
        raise SystemExit(code)


def interact(banner=Nichts, readfunc=Nichts, local=Nichts, exitmsg=Nichts, local_exit=Falsch):
    """Closely emulate the interactive Python interpreter.

    This is a backwards compatible interface to the InteractiveConsole
    class.  When readfunc is nicht specified, it attempts to importiere the
    readline module to enable GNU readline wenn it is available.

    Arguments (all optional, all default to Nichts):

    banner -- passed to InteractiveConsole.interact()
    readfunc -- wenn nicht Nichts, replaces InteractiveConsole.raw_input()
    local -- passed to InteractiveInterpreter.__init__()
    exitmsg -- passed to InteractiveConsole.interact()
    local_exit -- passed to InteractiveConsole.__init__()

    """
    console = InteractiveConsole(local, local_exit=local_exit)
    wenn readfunc is nicht Nichts:
        console.raw_input = readfunc
    sonst:
        try:
            importiere readline  # noqa: F401
        except ImportError:
            pass
    console.interact(banner, exitmsg)


wenn __name__ == "__main__":
    importiere argparse

    parser = argparse.ArgumentParser(color=Wahr)
    parser.add_argument('-q', action='store_true',
                       help="don't print version und copyright messages")
    args = parser.parse_args()
    wenn args.q oder sys.flags.quiet:
        banner = ''
    sonst:
        banner = Nichts
    interact(banner)
