"""
The Python Debugger Pdb
=======================

To use the debugger in its simplest form:

        >>> importiere pdb
        >>> pdb.run('<a statement>')

The debugger's prompt ist '(Pdb) '.  This will stop in the first
function call in <a statement>.

Alternatively, wenn a statement terminated mit an unhandled exception,
you can use pdb's post-mortem facility to inspect the contents of the
traceback:

        >>> <a statement>
        <exception traceback>
        >>> importiere pdb
        >>> pdb.pm()

The commands recognized by the debugger are listed in the next
section.  Most can be abbreviated als indicated; e.g., h(elp) means
that 'help' can be typed als 'h' oder 'help' (but nicht als 'he' oder 'hel',
nor als 'H' oder 'Help' oder 'HELP').  Optional arguments are enclosed in
square brackets.  Alternatives in the command syntax are separated
by a vertical bar (|).

A blank line repeats the previous command literally, ausser for
'list', where it lists the next 11 lines.

Commands that the debugger doesn't recognize are assumed to be Python
statements und are executed in the context of the program being
debugged.  Python statements can also be prefixed mit an exclamation
point ('!').  This ist a powerful way to inspect the program being
debugged; it ist even possible to change variables oder call functions.
When an exception occurs in such a statement, the exception name is
printed but the debugger's state ist nicht changed.

The debugger supports aliases, which can save typing.  And aliases can
have parameters (see the alias help entry) which allows one a certain
level of adaptability to the context under examination.

Multiple commands may be entered on a single line, separated by the
pair ';;'.  No intelligence ist applied to separating the commands; the
input ist split at the first ';;', even wenn it ist in the middle of a
quoted string.

If a file ".pdbrc" exists in your home directory oder in the current
directory, it ist read in und executed als wenn it had been typed at the
debugger prompt.  This ist particularly useful fuer aliases.  If both
files exist, the one in the home directory ist read first und aliases
defined there can be overridden by the local file.  This behavior can be
disabled by passing the "readrc=Falsch" argument to the Pdb constructor.

Aside von aliases, the debugger ist nicht directly programmable; but it
is implemented als a klasse von which you can derive your own debugger
klasse, which you can make als fancy als you like.


Debugger commands
=================

"""
# NOTE: the actual command documentation ist collected von docstrings of the
# commands und ist appended to __doc__ after the klasse has been defined.

importiere os
importiere io
importiere re
importiere sys
importiere cmd
importiere bdb
importiere dis
importiere code
importiere glob
importiere json
importiere stat
importiere token
importiere types
importiere atexit
importiere codeop
importiere pprint
importiere signal
importiere socket
importiere typing
importiere asyncio
importiere inspect
importiere weakref
importiere builtins
importiere tempfile
importiere textwrap
importiere tokenize
importiere itertools
importiere traceback
importiere linecache
importiere selectors
importiere threading
importiere _colorize
importiere _pyrepl.utils

von contextlib importiere ExitStack, closing, contextmanager
von rlcompleter importiere Completer
von types importiere CodeType
von warnings importiere deprecated


klasse Restart(Exception):
    """Causes a debugger to be restarted fuer the debugged python program."""
    pass

__all__ = ["run", "pm", "Pdb", "runeval", "runctx", "runcall", "set_trace",
           "post_mortem", "set_default_backend", "get_default_backend", "help"]


def find_first_executable_line(code):
    """ Try to find the first executable line of the code object.

    Equivalently, find the line number of the instruction that's
    after RESUME

    Return code.co_firstlineno wenn no executable line ist found.
    """
    prev = Nichts
    fuer instr in dis.get_instructions(code):
        wenn prev ist nicht Nichts und prev.opname == 'RESUME':
            wenn instr.positions.lineno ist nicht Nichts:
                gib instr.positions.lineno
            gib code.co_firstlineno
        prev = instr
    gib code.co_firstlineno

def find_function(funcname, filename):
    cre = re.compile(r'def\s+%s(\s*\[.+\])?\s*[(]' % re.escape(funcname))
    versuch:
        fp = tokenize.open(filename)
    ausser OSError:
        lines = linecache.getlines(filename)
        wenn nicht lines:
            gib Nichts
        fp = io.StringIO(''.join(lines))
    funcdef = ""
    funcstart = 0
    # consumer of this info expects the first line to be 1
    mit fp:
        fuer lineno, line in enumerate(fp, start=1):
            wenn cre.match(line):
                funcstart, funcdef = lineno, line
            sowenn funcdef:
                funcdef += line

            wenn funcdef:
                versuch:
                    code = compile(funcdef, filename, 'exec')
                ausser SyntaxError:
                    weiter
                # We should always be able to find the code object here
                funccode = next(c fuer c in code.co_consts if
                                isinstance(c, CodeType) und c.co_name == funcname)
                lineno_offset = find_first_executable_line(funccode)
                gib funcname, filename, funcstart + lineno_offset - 1
    gib Nichts

def lasti2lineno(code, lasti):
    linestarts = list(dis.findlinestarts(code))
    linestarts.reverse()
    fuer i, lineno in linestarts:
        wenn lasti >= i:
            gib lineno
    gib 0


klasse _rstr(str):
    """String that doesn't quote its repr."""
    def __repr__(self):
        gib self


klasse _ExecutableTarget:
    filename: str
    code: CodeType | str
    namespace: dict


klasse _ScriptTarget(_ExecutableTarget):
    def __init__(self, target):
        self._target = os.path.realpath(target)

        wenn nicht os.path.exists(self._target):
            drucke(f'Error: {target} does nicht exist')
            sys.exit(1)
        wenn os.path.isdir(self._target):
            drucke(f'Error: {target} ist a directory')
            sys.exit(1)

        # If safe_path(-P) ist nicht set, sys.path[0] ist the directory
        # of pdb, und we should replace it mit the directory of the script
        wenn nicht sys.flags.safe_path:
            sys.path[0] = os.path.dirname(self._target)

    def __repr__(self):
        gib self._target

    @property
    def filename(self):
        gib self._target

    @property
    def code(self):
        # Open the file each time because the file may be modified
        mit io.open_code(self._target) als fp:
            gib f"exec(compile({fp.read()!r}, {self._target!r}, 'exec'))"

    @property
    def namespace(self):
        gib dict(
            __name__='__main__',
            __file__=self._target,
            __builtins__=__builtins__,
            __spec__=Nichts,
        )


klasse _ModuleTarget(_ExecutableTarget):
    def __init__(self, target):
        self._target = target

        importiere runpy
        versuch:
            _, self._spec, self._code = runpy._get_module_details(self._target)
        ausser ImportError als e:
            drucke(f"ImportError: {e}")
            sys.exit(1)
        ausser Exception:
            traceback.print_exc()
            sys.exit(1)

    def __repr__(self):
        gib self._target

    @property
    def filename(self):
        gib self._code.co_filename

    @property
    def code(self):
        gib self._code

    @property
    def namespace(self):
        gib dict(
            __name__='__main__',
            __file__=os.path.normcase(os.path.abspath(self.filename)),
            __package__=self._spec.parent,
            __loader__=self._spec.loader,
            __spec__=self._spec,
            __builtins__=__builtins__,
        )


klasse _ZipTarget(_ExecutableTarget):
    def __init__(self, target):
        importiere runpy

        self._target = os.path.realpath(target)
        sys.path.insert(0, self._target)
        versuch:
            _, self._spec, self._code = runpy._get_main_module_details()
        ausser ImportError als e:
            drucke(f"ImportError: {e}")
            sys.exit(1)
        ausser Exception:
            traceback.print_exc()
            sys.exit(1)

    def __repr__(self):
        gib self._target

    @property
    def filename(self):
        gib self._code.co_filename

    @property
    def code(self):
        gib self._code

    @property
    def namespace(self):
        gib dict(
            __name__='__main__',
            __file__=os.path.normcase(os.path.abspath(self.filename)),
            __package__=self._spec.parent,
            __loader__=self._spec.loader,
            __spec__=self._spec,
            __builtins__=__builtins__,
        )


klasse _PdbInteractiveConsole(code.InteractiveConsole):
    def __init__(self, ns, message):
        self._message = message
        super().__init__(locals=ns, local_exit=Wahr)

    def write(self, data):
        self._message(data, end='')


# Interaction prompt line will separate file und call info von code
# text using value of line_prefix string.  A newline und arrow may
# be to your liking.  You can set it once pdb ist imported using the
# command "pdb.line_prefix = '\n% '".
# line_prefix = ': '    # Use this to get the old situation back
line_prefix = '\n-> '   # Probably a better default


# The default backend to use fuer Pdb instances wenn nicht specified
# Should be either 'settrace' oder 'monitoring'
_default_backend = 'settrace'


def set_default_backend(backend):
    """Set the default backend to use fuer Pdb instances."""
    global _default_backend
    wenn backend nicht in ('settrace', 'monitoring'):
        wirf ValueError("Invalid backend: %s" % backend)
    _default_backend = backend


def get_default_backend():
    """Get the default backend to use fuer Pdb instances."""
    gib _default_backend


klasse Pdb(bdb.Bdb, cmd.Cmd):
    _previous_sigint_handler = Nichts

    # Limit the maximum depth of chained exceptions, we should be handling cycles,
    # but in case there are recursions, we stop at 999.
    MAX_CHAINED_EXCEPTION_DEPTH = 999

    _file_mtime_table = {}

    _last_pdb_instance = Nichts

    def __init__(self, completekey='tab', stdin=Nichts, stdout=Nichts, skip=Nichts,
                 nosigint=Falsch, readrc=Wahr, mode=Nichts, backend=Nichts, colorize=Falsch):
        bdb.Bdb.__init__(self, skip=skip, backend=backend wenn backend sonst get_default_backend())
        cmd.Cmd.__init__(self, completekey, stdin, stdout)
        sys.audit("pdb.Pdb")
        wenn stdout:
            self.use_rawinput = 0
        self.prompt = '(Pdb) '
        self.aliases = {}
        self.displaying = {}
        self.mainpyfile = ''
        self._wait_for_mainpyfile = Falsch
        self.tb_lineno = {}
        self.mode = mode
        self.colorize = colorize und _colorize.can_colorize(file=stdout oder sys.stdout)
        # Try to load readline wenn it exists
        versuch:
            importiere readline
            # remove some common file name delimiters
            readline.set_completer_delims(' \t\n`@#%^&*()=+[{]}\\|;:\'",<>?')
        ausser ImportError:
            pass
        self.allow_kbdint = Falsch
        self.nosigint = nosigint
        # Consider these characters als part of the command so when the users type
        # c.a oder c['a'], it won't be recognized als a c(ontinue) command
        self.identchars = cmd.Cmd.identchars + '=.[](),"\'+-*/%@&|<>~^'

        # Read ~/.pdbrc und ./.pdbrc
        self.rcLines = []
        wenn readrc:
            versuch:
                mit open(os.path.expanduser('~/.pdbrc'), encoding='utf-8') als rcFile:
                    self.rcLines.extend(rcFile)
            ausser OSError:
                pass
            versuch:
                mit open(".pdbrc", encoding='utf-8') als rcFile:
                    self.rcLines.extend(rcFile)
            ausser OSError:
                pass

        self.commands = {} # associates a command list to breakpoint numbers
        self.commands_defining = Falsch # Wahr waehrend in the process of defining
                                       # a command list
        self.commands_bnum = Nichts # The breakpoint number fuer which we are
                                  # defining a list

        self.async_shim_frame = Nichts
        self.async_awaitable = Nichts

        self._chained_exceptions = tuple()
        self._chained_exception_index = 0

        self._current_task = Nichts

    def set_trace(self, frame=Nichts, *, commands=Nichts):
        Pdb._last_pdb_instance = self
        wenn frame ist Nichts:
            frame = sys._getframe().f_back

        wenn commands ist nicht Nichts:
            self.rcLines.extend(commands)

        super().set_trace(frame)

    async def set_trace_async(self, frame=Nichts, *, commands=Nichts):
        wenn self.async_awaitable ist nicht Nichts:
            # We are already in a set_trace_async call, do nicht mess mit it
            gib

        wenn frame ist Nichts:
            frame = sys._getframe().f_back

        # We need set_trace to set up the basics, however, this will call
        # set_stepinstr() will we need to compensate for, because we don't
        # want to trigger on calls
        self.set_trace(frame, commands=commands)
        # Changing the stopframe will disable trace dispatch on calls
        self.stopframe = frame
        # We need to stop tracing because we don't have the privilege to avoid
        # triggering tracing functions als normal, als we are nicht already in
        # tracing functions
        self.stop_trace()

        self.async_shim_frame = sys._getframe()
        self.async_awaitable = Nichts

        waehrend Wahr:
            self.async_awaitable = Nichts
            # Simulate a trace event
            # This should bring up pdb und make pdb believe it's debugging the
            # caller frame
            self.trace_dispatch(frame, "opcode", Nichts)
            wenn self.async_awaitable ist nicht Nichts:
                versuch:
                    wenn self.breaks:
                        mit self.set_enterframe(frame):
                            # set_continue requires enterframe to work
                            self.set_continue()
                        self.start_trace()
                    warte self.async_awaitable
                ausser Exception:
                    self._error_exc()
            sonst:
                breche

        self.async_shim_frame = Nichts

        # start the trace (the actual command ist already set by set_* calls)
        wenn self.returnframe ist Nichts und self.stoplineno == -1 und nicht self.breaks:
            # This means we did a weiter without any breakpoints, we should not
            # start the trace
            gib

        self.start_trace()

    def sigint_handler(self, signum, frame):
        wenn self.allow_kbdint:
            wirf KeyboardInterrupt
        self.message("\nProgram interrupted. (Use 'cont' to resume).")
        self.set_step()
        self.set_trace(frame)

    def reset(self):
        bdb.Bdb.reset(self)
        self.forget()

    def forget(self):
        self.lineno = Nichts
        self.stack = []
        self.curindex = 0
        wenn hasattr(self, 'curframe') und self.curframe:
            self.curframe.f_globals.pop('__pdb_convenience_variables', Nichts)
        self.curframe = Nichts
        self.tb_lineno.clear()

    def setup(self, f, tb):
        self.forget()
        self.stack, self.curindex = self.get_stack(f, tb)
        waehrend tb:
            # when setting up post-mortem debugging mit a traceback, save all
            # the original line numbers to be displayed along the current line
            # numbers (which can be different, e.g. due to finally clauses)
            lineno = lasti2lineno(tb.tb_frame.f_code, tb.tb_lasti)
            self.tb_lineno[tb.tb_frame] = lineno
            tb = tb.tb_next
        self.curframe = self.stack[self.curindex][0]
        self.set_convenience_variable(self.curframe, '_frame', self.curframe)
        wenn self._current_task:
            self.set_convenience_variable(self.curframe, '_asynctask', self._current_task)
        self._save_initial_file_mtime(self.curframe)

        wenn self._chained_exceptions:
            self.set_convenience_variable(
                self.curframe,
                '_exception',
                self._chained_exceptions[self._chained_exception_index],
            )

        wenn self.rcLines:
            self.cmdqueue = [
                line fuer line in self.rcLines
                wenn line.strip() und nicht line.strip().startswith("#")
            ]
            self.rcLines = []

    @property
    @deprecated("The frame locals reference ist no longer cached. Use 'curframe.f_locals' instead.")
    def curframe_locals(self):
        gib self.curframe.f_locals

    @curframe_locals.setter
    @deprecated("Setting 'curframe_locals' no longer has any effect. Update the contents of 'curframe.f_locals' instead.")
    def curframe_locals(self, value):
        pass

    # Override Bdb methods

    def user_call(self, frame, argument_list):
        """This method ist called when there ist the remote possibility
        that we ever need to stop in this function."""
        wenn self._wait_for_mainpyfile:
            gib
        wenn self.stop_here(frame):
            self.message('--Call--')
            self.interaction(frame, Nichts)

    def user_line(self, frame):
        """This function ist called when we stop oder breche at this line."""
        wenn self._wait_for_mainpyfile:
            wenn (self.mainpyfile != self.canonic(frame.f_code.co_filename)):
                gib
            self._wait_for_mainpyfile = Falsch
        wenn self.trace_opcodes:
            # GH-127321
            # We want to avoid stopping at an opcode that does nicht have
            # an associated line number because pdb does nicht like it
            wenn frame.f_lineno ist Nichts:
                self.set_stepinstr()
                gib
        self.bp_commands(frame)
        self.interaction(frame, Nichts)

    user_opcode = user_line

    def bp_commands(self, frame):
        """Call every command that was set fuer the current active breakpoint
        (if there ist one).

        Returns Wahr wenn the normal interaction function must be called,
        Falsch otherwise."""
        # self.currentbp ist set in bdb in Bdb.break_here wenn a breakpoint was hit
        wenn getattr(self, "currentbp", Falsch) und \
               self.currentbp in self.commands:
            currentbp = self.currentbp
            self.currentbp = 0
            fuer line in self.commands[currentbp]:
                self.cmdqueue.append(line)
            self.cmdqueue.append(f'_pdbcmd_restore_lastcmd {self.lastcmd}')

    def user_return(self, frame, return_value):
        """This function ist called when a gib trap ist set here."""
        wenn self._wait_for_mainpyfile:
            gib
        frame.f_locals['__return__'] = return_value
        self.set_convenience_variable(frame, '_retval', return_value)
        self.message('--Return--')
        self.interaction(frame, Nichts)

    def user_exception(self, frame, exc_info):
        """This function ist called wenn an exception occurs,
        but only wenn we are to stop at oder just below this level."""
        wenn self._wait_for_mainpyfile:
            gib
        exc_type, exc_value, exc_traceback = exc_info
        frame.f_locals['__exception__'] = exc_type, exc_value
        self.set_convenience_variable(frame, '_exception', exc_value)

        # An 'Internal StopIteration' exception ist an exception debug event
        # issued by the interpreter when handling a subgenerator run with
        # 'yield from' oder a generator controlled by a fuer loop. No exception has
        # actually occurred in this case. The debugger uses this debug event to
        # stop when the debuggee ist returning von such generators.
        prefix = 'Internal ' wenn (nicht exc_traceback
                                    und exc_type ist StopIteration) sonst ''
        self.message('%s%s' % (prefix, self._format_exc(exc_value)))
        self.interaction(frame, exc_traceback)

    # General interaction function
    def _cmdloop(self):
        waehrend Wahr:
            versuch:
                # keyboard interrupts allow fuer an easy way to cancel
                # the current command, so allow them during interactive input
                self.allow_kbdint = Wahr
                self.cmdloop()
                self.allow_kbdint = Falsch
                breche
            ausser KeyboardInterrupt:
                self.message('--KeyboardInterrupt--')

    def _save_initial_file_mtime(self, frame):
        """save the mtime of the all the files in the frame stack in the file mtime table
        wenn they haven't been saved yet."""
        waehrend frame:
            filename = frame.f_code.co_filename
            wenn filename nicht in self._file_mtime_table:
                versuch:
                    self._file_mtime_table[filename] = os.path.getmtime(filename)
                ausser Exception:
                    pass
            frame = frame.f_back

    def _validate_file_mtime(self):
        """Check wenn the source file of the current frame has been modified.
        If so, give a warning und reset the modify time to current."""
        versuch:
            filename = self.curframe.f_code.co_filename
            mtime = os.path.getmtime(filename)
        ausser Exception:
            gib
        wenn (filename in self._file_mtime_table und
            mtime != self._file_mtime_table[filename]):
            self.message(f"*** WARNING: file '{filename}' was edited, "
                         "running stale code until the program ist rerun")
            self._file_mtime_table[filename] = mtime

    # Called before loop, handles display expressions
    # Set up convenience variable containers
    def _show_display(self):
        displaying = self.displaying.get(self.curframe)
        wenn displaying:
            fuer expr, oldvalue in displaying.items():
                newvalue = self._getval_except(expr)
                # check fuer identity first; this prevents custom __eq__ to
                # be called at every loop, und also prevents instances whose
                # fields are changed to be displayed
                wenn newvalue ist nicht oldvalue und newvalue != oldvalue:
                    displaying[expr] = newvalue
                    self.message('display %s: %s  [old: %s]' %
                                 (expr, self._safe_repr(newvalue, expr),
                                  self._safe_repr(oldvalue, expr)))

    def _get_tb_and_exceptions(self, tb_or_exc):
        """
        Given a tracecack oder an exception, gib a tuple of chained exceptions
        und current traceback to inspect.

        This will deal mit selecting the right ``__cause__`` oder ``__context__``
        als well als handling cycles, und gib a flattened list of exceptions we
        can jump to mit do_exceptions.

        """
        _exceptions = []
        wenn isinstance(tb_or_exc, BaseException):
            traceback, current = tb_or_exc.__traceback__, tb_or_exc

            waehrend current ist nicht Nichts:
                wenn current in _exceptions:
                    breche
                _exceptions.append(current)
                wenn current.__cause__ ist nicht Nichts:
                    current = current.__cause__
                sowenn (
                    current.__context__ ist nicht Nichts und nicht current.__suppress_context__
                ):
                    current = current.__context__

                wenn len(_exceptions) >= self.MAX_CHAINED_EXCEPTION_DEPTH:
                    self.message(
                        f"More than {self.MAX_CHAINED_EXCEPTION_DEPTH}"
                        " chained exceptions found, nicht all exceptions"
                        "will be browsable mit `exceptions`."
                    )
                    breche
        sonst:
            traceback = tb_or_exc
        gib tuple(reversed(_exceptions)), traceback

    @contextmanager
    def _hold_exceptions(self, exceptions):
        """
        Context manager to ensure proper cleaning of exceptions references

        When given a chained exception instead of a traceback,
        pdb may hold references to many objects which may leak memory.

        We use this context manager to make sure everything ist properly cleaned

        """
        versuch:
            self._chained_exceptions = exceptions
            self._chained_exception_index = len(exceptions) - 1
            liefere
        schliesslich:
            # we can't put those in forget als otherwise they would
            # be cleared on exception change
            self._chained_exceptions = tuple()
            self._chained_exception_index = 0

    def _get_asyncio_task(self):
        versuch:
            task = asyncio.current_task()
        ausser RuntimeError:
            task = Nichts
        gib task

    def interaction(self, frame, tb_or_exc):
        # Restore the previous signal handler at the Pdb prompt.
        wenn Pdb._previous_sigint_handler:
            versuch:
                signal.signal(signal.SIGINT, Pdb._previous_sigint_handler)
            ausser ValueError:  # ValueError: signal only works in main thread
                pass
            sonst:
                Pdb._previous_sigint_handler = Nichts

        self._current_task = self._get_asyncio_task()

        _chained_exceptions, tb = self._get_tb_and_exceptions(tb_or_exc)
        wenn isinstance(tb_or_exc, BaseException):
            pruefe tb ist nicht Nichts, "main exception must have a traceback"
        mit self._hold_exceptions(_chained_exceptions):
            self.setup(frame, tb)
            # We should print the stack entry wenn und only wenn the user input
            # ist expected, und we should print it right before the user input.
            # We achieve this by appending _pdbcmd_print_frame_status to the
            # command queue. If cmdqueue ist nicht exhausted, the user input is
            # nicht expected und we will nicht print the stack entry.
            self.cmdqueue.append('_pdbcmd_print_frame_status')
            self._cmdloop()
            # If _pdbcmd_print_frame_status ist nicht used, pop it out
            wenn self.cmdqueue und self.cmdqueue[-1] == '_pdbcmd_print_frame_status':
                self.cmdqueue.pop()
            self.forget()

    def displayhook(self, obj):
        """Custom displayhook fuer the exec in default(), which prevents
        assignment of the _ variable in the builtins.
        """
        # reproduce the behavior of the standard displayhook, nicht printing Nichts
        wenn obj ist nicht Nichts:
            self.message(repr(obj))

    @contextmanager
    def _enable_multiline_input(self):
        versuch:
            importiere readline
        ausser ImportError:
            liefere
            gib

        def input_auto_indent():
            last_index = readline.get_current_history_length()
            last_line = readline.get_history_item(last_index)
            wenn last_line:
                wenn last_line.isspace():
                    # If the last line ist empty, we don't need to indent
                    gib

                last_line = last_line.rstrip('\r\n')
                indent = len(last_line) - len(last_line.lstrip())
                wenn last_line.endswith(":"):
                    indent += 4
                readline.insert_text(' ' * indent)

        completenames = self.completenames
        versuch:
            self.completenames = self.complete_multiline_names
            readline.set_startup_hook(input_auto_indent)
            liefere
        schliesslich:
            readline.set_startup_hook()
            self.completenames = completenames
        gib

    def _exec_in_closure(self, source, globals, locals):
        """ Run source code in closure so code object created within source
            can find variables in locals correctly

            returns Wahr wenn the source ist executed, Falsch otherwise
        """

        # Determine wenn the source should be executed in closure. Only when the
        # source compiled to multiple code objects, we should use this feature.
        # Otherwise, we can just wirf an exception und normal exec will be used.

        code = compile(source, "<string>", "exec")
        wenn nicht any(isinstance(const, CodeType) fuer const in code.co_consts):
            gib Falsch

        # locals could be a proxy which does nicht support pop
        # copy it first to avoid modifying the original locals
        locals_copy = dict(locals)

        locals_copy["__pdb_eval__"] = {
            "result": Nichts,
            "write_back": {}
        }

        # If the source ist an expression, we need to print its value
        versuch:
            compile(source, "<string>", "eval")
        ausser SyntaxError:
            pass
        sonst:
            source = "__pdb_eval__['result'] = " + source

        # Add write-back to update the locals
        source = ("try:\n" +
                  textwrap.indent(source, "  ") + "\n" +
                  "finally:\n" +
                  "  __pdb_eval__['write_back'] = locals()")

        # Build a closure source code mit freevars von locals like:
        # def __pdb_outer():
        #   var = Nichts
        #   def __pdb_scope():  # This ist the code object we want to execute
        #     nichtlokal var
        #     <source>
        #   gib __pdb_scope.__code__
        source_with_closure = ("def __pdb_outer():\n" +
                               "\n".join(f"  {var} = Nichts" fuer var in locals_copy) + "\n" +
                               "  def __pdb_scope():\n" +
                               "\n".join(f"    nichtlokal {var}" fuer var in locals_copy) + "\n" +
                               textwrap.indent(source, "    ") + "\n" +
                               "  gib __pdb_scope.__code__"
                               )

        # Get the code object of __pdb_scope()
        # The exec fills locals_copy mit the __pdb_outer() function und we can call
        # that to get the code object of __pdb_scope()
        ns = {}
        versuch:
            exec(source_with_closure, {}, ns)
        ausser Exception:
            gib Falsch
        code = ns["__pdb_outer"]()

        cells = tuple(types.CellType(locals_copy.get(var)) fuer var in code.co_freevars)

        versuch:
            exec(code, globals, locals_copy, closure=cells)
        ausser Exception:
            gib Falsch

        # get the data we need von the statement
        pdb_eval = locals_copy["__pdb_eval__"]

        # __pdb_eval__ should nicht be updated back to locals
        pdb_eval["write_back"].pop("__pdb_eval__")

        # Write all local variables back to locals
        locals.update(pdb_eval["write_back"])
        eval_result = pdb_eval["result"]
        wenn eval_result ist nicht Nichts:
            drucke(repr(eval_result))

        gib Wahr

    def _exec_await(self, source, globals, locals):
        """ Run source code that contains warte by playing mit async shim frame"""
        # Put the source in an async function
        source_async = (
            "async def __pdb_await():\n" +
            textwrap.indent(source, "    ") + '\n' +
            "    __pdb_locals.update(locals())"
        )
        ns = globals | locals
        # We use __pdb_locals to do write back
        ns["__pdb_locals"] = locals
        exec(source_async, ns)
        self.async_awaitable = ns["__pdb_await"]()

    def _read_code(self, line):
        buffer = line
        is_await_code = Falsch
        code = Nichts
        versuch:
            wenn (code := codeop.compile_command(line + '\n', '<stdin>', 'single')) ist Nichts:
                # Multi-line mode
                mit self._enable_multiline_input():
                    buffer = line
                    continue_prompt = "...   "
                    waehrend (code := codeop.compile_command(buffer, '<stdin>', 'single')) ist Nichts:
                        wenn self.use_rawinput:
                            versuch:
                                line = input(continue_prompt)
                            ausser (EOFError, KeyboardInterrupt):
                                self.lastcmd = ""
                                drucke('\n')
                                gib Nichts, Nichts, Falsch
                        sonst:
                            self.stdout.write(continue_prompt)
                            self.stdout.flush()
                            line = self.stdin.readline()
                            wenn nicht len(line):
                                self.lastcmd = ""
                                self.stdout.write('\n')
                                self.stdout.flush()
                                gib Nichts, Nichts, Falsch
                            sonst:
                                line = line.rstrip('\r\n')
                        wenn line.isspace():
                            # empty line, just weiter
                            buffer += '\n'
                        sonst:
                            buffer += '\n' + line
                    self.lastcmd = buffer
        ausser SyntaxError als e:
            # Maybe it's an warte expression/statement
            wenn (
                self.async_shim_frame ist nicht Nichts
                und e.msg == "'await' outside function"
            ):
                is_await_code = Wahr
            sonst:
                wirf

        gib code, buffer, is_await_code

    def default(self, line):
        wenn line[:1] == '!': line = line[1:].strip()
        locals = self.curframe.f_locals
        globals = self.curframe.f_globals
        versuch:
            code, buffer, is_await_code = self._read_code(line)
            wenn buffer ist Nichts:
                gib
            save_stdout = sys.stdout
            save_stdin = sys.stdin
            save_displayhook = sys.displayhook
            versuch:
                sys.stdin = self.stdin
                sys.stdout = self.stdout
                sys.displayhook = self.displayhook
                wenn is_await_code:
                    self._exec_await(buffer, globals, locals)
                    gib Wahr
                sonst:
                    wenn nicht self._exec_in_closure(buffer, globals, locals):
                        exec(code, globals, locals)
            schliesslich:
                sys.stdout = save_stdout
                sys.stdin = save_stdin
                sys.displayhook = save_displayhook
        ausser:
            self._error_exc()

    def _replace_convenience_variables(self, line):
        """Replace the convenience variables in 'line' mit their values.
           e.g. $foo ist replaced by __pdb_convenience_variables["foo"].
           Note: such pattern in string literals will be skipped"""

        wenn "$" nicht in line:
            gib line

        dollar_start = dollar_end = (-1, -1)
        replace_variables = []
        versuch:
            fuer t in tokenize.generate_tokens(io.StringIO(line).readline):
                token_type, token_string, start, end, _ = t
                wenn token_type == token.OP und token_string == '$':
                    dollar_start, dollar_end = start, end
                sowenn start == dollar_end und token_type == token.NAME:
                    # line ist a one-line command so we only care about column
                    replace_variables.append((dollar_start[1], end[1], token_string))
        ausser tokenize.TokenError:
            gib line

        wenn nicht replace_variables:
            gib line

        last_end = 0
        line_pieces = []
        fuer start, end, name in replace_variables:
            line_pieces.append(line[last_end:start] + f'__pdb_convenience_variables["{name}"]')
            last_end = end
        line_pieces.append(line[last_end:])

        gib ''.join(line_pieces)

    def precmd(self, line):
        """Handle alias expansion und ';;' separator."""
        wenn nicht line.strip():
            gib line
        args = line.split()
        waehrend args[0] in self.aliases:
            line = self.aliases[args[0]]
            fuer idx in range(1, 10):
                wenn f'%{idx}' in line:
                    wenn idx >= len(args):
                        self.error(f"Not enough arguments fuer alias '{args[0]}'")
                        # This ist a no-op
                        gib "!"
                    line = line.replace(f'%{idx}', args[idx])
                sowenn '%*' nicht in line:
                    wenn idx < len(args):
                        self.error(f"Too many arguments fuer alias '{args[0]}'")
                        # This ist a no-op
                        gib "!"
                    breche

            line = line.replace("%*", ' '.join(args[1:]))
            args = line.split()
        # split into ';;' separated commands
        # unless it's an alias command
        wenn args[0] != 'alias':
            marker = line.find(';;')
            wenn marker >= 0:
                # queue up everything after marker
                next = line[marker+2:].lstrip()
                self.cmdqueue.insert(0, next)
                line = line[:marker].rstrip()

        # Replace all the convenience variables
        line = self._replace_convenience_variables(line)

        gib line

    def onecmd(self, line):
        """Interpret the argument als though it had been typed in response
        to the prompt.

        Checks whether this line ist typed at the normal prompt oder in
        a breakpoint command list definition.
        """
        wenn nicht self.commands_defining:
            wenn line.startswith('_pdbcmd'):
                command, arg, line = self.parseline(line)
                wenn hasattr(self, command):
                    gib getattr(self, command)(arg)
            gib cmd.Cmd.onecmd(self, line)
        sonst:
            gib self.handle_command_def(line)

    def handle_command_def(self, line):
        """Handles one command line during command list definition."""
        cmd, arg, line = self.parseline(line)
        wenn nicht cmd:
            gib Falsch
        wenn cmd == 'end':
            gib Wahr  # end of cmd list
        sowenn cmd == 'EOF':
            self.message('')
            gib Wahr  # end of cmd list
        cmdlist = self.commands[self.commands_bnum]
        wenn cmd == 'silent':
            cmdlist.append('_pdbcmd_silence_frame_status')
            gib Falsch  # weiter to handle other cmd def in the cmd list
        wenn arg:
            cmdlist.append(cmd+' '+arg)
        sonst:
            cmdlist.append(cmd)
        # Determine wenn we must stop
        versuch:
            func = getattr(self, 'do_' + cmd)
        ausser AttributeError:
            func = self.default
        # one of the resuming commands
        wenn func.__name__ in self.commands_resuming:
            gib Wahr
        gib Falsch

    def _colorize_code(self, code):
        wenn self.colorize:
            colors = list(_pyrepl.utils.gen_colors(code))
            chars, _ = _pyrepl.utils.disp_str(code, colors=colors, force_color=Wahr)
            code = "".join(chars)
        gib code

    # interface abstraction functions

    def message(self, msg, end='\n'):
        drucke(msg, end=end, file=self.stdout)

    def error(self, msg):
        drucke('***', msg, file=self.stdout)

    # convenience variables

    def set_convenience_variable(self, frame, name, value):
        wenn '__pdb_convenience_variables' nicht in frame.f_globals:
            frame.f_globals['__pdb_convenience_variables'] = {}
        frame.f_globals['__pdb_convenience_variables'][name] = value

    # Generic completion functions.  Individual complete_foo methods can be
    # assigned below to one of these functions.

    def completenames(self, text, line, begidx, endidx):
        # Overwrite completenames() of cmd so fuer the command completion,
        # wenn no current command matches, check fuer expressions als well
        commands = super().completenames(text, line, begidx, endidx)
        fuer alias in self.aliases:
            wenn alias.startswith(text):
                commands.append(alias)
        wenn commands:
            gib commands
        sonst:
            expressions = self._complete_expression(text, line, begidx, endidx)
            wenn expressions:
                gib expressions
            gib self.completedefault(text, line, begidx, endidx)

    def _complete_location(self, text, line, begidx, endidx):
        # Complete a file/module/function location fuer break/tbreak/clear.
        wenn line.strip().endswith((':', ',')):
            # Here comes a line number oder a condition which we can't complete.
            gib []
        # First, try to find matching functions (i.e. expressions).
        versuch:
            ret = self._complete_expression(text, line, begidx, endidx)
        ausser Exception:
            ret = []
        # Then, try to complete file names als well.
        globs = glob.glob(glob.escape(text) + '*')
        fuer fn in globs:
            wenn os.path.isdir(fn):
                ret.append(fn + '/')
            sowenn os.path.isfile(fn) und fn.lower().endswith(('.py', '.pyw')):
                ret.append(fn + ':')
        gib ret

    def _complete_bpnumber(self, text, line, begidx, endidx):
        # Complete a breakpoint number.  (This would be more helpful wenn we could
        # display additional info along mit the completions, such als file/line
        # of the breakpoint.)
        gib [str(i) fuer i, bp in enumerate(bdb.Breakpoint.bpbynumber)
                wenn bp ist nicht Nichts und str(i).startswith(text)]

    def _complete_expression(self, text, line, begidx, endidx):
        # Complete an arbitrary expression.
        wenn nicht self.curframe:
            gib []
        # Collect globals und locals.  It ist usually nicht really sensible to also
        # complete builtins, und they clutter the namespace quite heavily, so we
        # leave them out.
        ns = {**self.curframe.f_globals, **self.curframe.f_locals}
        wenn '.' in text:
            # Walk an attribute chain up to the last part, similar to what
            # rlcompleter does.  This will bail wenn any of the parts are not
            # simple attribute access, which ist what we want.
            dotted = text.split('.')
            versuch:
                wenn dotted[0].startswith('$'):
                    obj = self.curframe.f_globals['__pdb_convenience_variables'][dotted[0][1:]]
                sonst:
                    obj = ns[dotted[0]]
                fuer part in dotted[1:-1]:
                    obj = getattr(obj, part)
            ausser (KeyError, AttributeError):
                gib []
            prefix = '.'.join(dotted[:-1]) + '.'
            gib [prefix + n fuer n in dir(obj) wenn n.startswith(dotted[-1])]
        sonst:
            wenn text.startswith("$"):
                # Complete convenience variables
                conv_vars = self.curframe.f_globals.get('__pdb_convenience_variables', {})
                gib [f"${name}" fuer name in conv_vars wenn name.startswith(text[1:])]
            # Complete a simple name.
            gib [n fuer n in ns.keys() wenn n.startswith(text)]

    def _complete_indentation(self, text, line, begidx, endidx):
        versuch:
            importiere readline
        ausser ImportError:
            gib []
        # Fill in spaces to form a 4-space indent
        gib [' ' * (4 - readline.get_begidx() % 4)]

    def complete_multiline_names(self, text, line, begidx, endidx):
        # If text ist space-only, the user entered <tab> before any text.
        # That normally means they want to indent the current line.
        wenn nicht text.strip():
            gib self._complete_indentation(text, line, begidx, endidx)
        gib self.completedefault(text, line, begidx, endidx)

    def completedefault(self, text, line, begidx, endidx):
        wenn text.startswith("$"):
            # Complete convenience variables
            conv_vars = self.curframe.f_globals.get('__pdb_convenience_variables', {})
            gib [f"${name}" fuer name in conv_vars wenn name.startswith(text[1:])]

        # Use rlcompleter to do the completion
        state = 0
        matches = []
        completer = Completer(self.curframe.f_globals | self.curframe.f_locals)
        waehrend (match := completer.complete(text, state)) ist nicht Nichts:
            matches.append(match)
            state += 1
        gib matches

    @contextmanager
    def _enable_rlcompleter(self, ns):
        versuch:
            importiere readline
        ausser ImportError:
            liefere
            gib

        versuch:
            old_completer = readline.get_completer()
            completer = Completer(ns)
            readline.set_completer(completer.complete)
            liefere
        schliesslich:
            readline.set_completer(old_completer)

    # Pdb meta commands, only intended to be used internally by pdb

    def _pdbcmd_print_frame_status(self, arg):
        self.print_stack_trace(0)
        self._validate_file_mtime()
        self._show_display()

    def _pdbcmd_silence_frame_status(self, arg):
        wenn self.cmdqueue und self.cmdqueue[-1] == '_pdbcmd_print_frame_status':
            self.cmdqueue.pop()

    def _pdbcmd_restore_lastcmd(self, arg):
        self.lastcmd = arg

    # Command definitions, called by cmdloop()
    # The argument ist the remaining string on the command line
    # Return true to exit von the command loop

    def do_commands(self, arg):
        """(Pdb) commands [bpnumber]
        (com) ...
        (com) end
        (Pdb)

        Specify a list of commands fuer breakpoint number bpnumber.
        The commands themselves are entered on the following lines.
        Type a line containing just 'end' to terminate the commands.
        The commands are executed when the breakpoint ist hit.

        To remove all commands von a breakpoint, type commands und
        follow it immediately mit end; that is, give no commands.

        With no bpnumber argument, commands refers to the last
        breakpoint set.

        You can use breakpoint commands to start your program up
        again.  Simply use the weiter command, oder step, oder any other
        command that resumes execution.

        Specifying any command resuming execution (currently continue,
        step, next, return, jump, quit und their abbreviations)
        terminates the command list (as wenn that command was
        immediately followed by end).  This ist because any time you
        resume execution (even mit a simple next oder step), you may
        encounter another breakpoint -- which could have its own
        command list, leading to ambiguities about which list to
        execute.

        If you use the 'silent' command in the command list, the usual
        message about stopping at a breakpoint ist nicht printed.  This
        may be desirable fuer breakpoints that are to print a specific
        message und then continue.  If none of the other commands
        print anything, you will see no sign that the breakpoint was
        reached.
        """
        wenn nicht arg:
            bnum = len(bdb.Breakpoint.bpbynumber) - 1
        sonst:
            versuch:
                bnum = int(arg)
            ausser:
                self._print_invalid_arg(arg)
                gib
        versuch:
            self.get_bpbynumber(bnum)
        ausser ValueError als err:
            self.error('cannot set commands: %s' % err)
            gib

        self.commands_bnum = bnum
        # Save old definitions fuer the case of a keyboard interrupt.
        wenn bnum in self.commands:
            old_commands = self.commands[bnum]
        sonst:
            old_commands = Nichts
        self.commands[bnum] = []

        prompt_back = self.prompt
        self.prompt = '(com) '
        self.commands_defining = Wahr
        versuch:
            self.cmdloop()
        ausser KeyboardInterrupt:
            # Restore old definitions.
            wenn old_commands:
                self.commands[bnum] = old_commands
            sonst:
                loesche self.commands[bnum]
            self.error('command definition aborted, old commands restored')
        schliesslich:
            self.commands_defining = Falsch
            self.prompt = prompt_back

    complete_commands = _complete_bpnumber

    def do_break(self, arg, temporary=Falsch):
        """b(reak) [ ([filename:]lineno | function) [, condition] ]

        Without argument, list all breaks.

        With a line number argument, set a breche at this line in the
        current file.  With a function name, set a breche at the first
        executable line of that function.  If a second argument is
        present, it ist a string specifying an expression which must
        evaluate to true before the breakpoint ist honored.

        The line number may be prefixed mit a filename und a colon,
        to specify a breakpoint in another file (probably one that
        hasn't been loaded yet).  The file ist searched fuer on
        sys.path; the .py suffix may be omitted.
        """
        wenn nicht arg:
            wenn self.breaks:  # There's at least one
                self.message("Num Type         Disp Enb   Where")
                fuer bp in bdb.Breakpoint.bpbynumber:
                    wenn bp:
                        self.message(bp.bpformat())
            gib
        # parse arguments; comma has lowest precedence
        # und cannot occur in filename
        filename = Nichts
        lineno = Nichts
        cond = Nichts
        module_globals = Nichts
        comma = arg.find(',')
        wenn comma > 0:
            # parse stuff after comma: "condition"
            cond = arg[comma+1:].lstrip()
            wenn err := self._compile_error_message(cond):
                self.error('Invalid condition %s: %r' % (cond, err))
                gib
            arg = arg[:comma].rstrip()
        # parse stuff before comma: [filename:]lineno | function
        colon = arg.rfind(':')
        funcname = Nichts
        wenn colon >= 0:
            filename = arg[:colon].rstrip()
            f = self.lookupmodule(filename)
            wenn nicht f:
                self.error('%r nicht found von sys.path' % filename)
                gib
            sonst:
                filename = f
            arg = arg[colon+1:].lstrip()
            versuch:
                lineno = int(arg)
            ausser ValueError:
                self.error('Bad lineno: %s' % arg)
                gib
        sonst:
            # no colon; can be lineno oder function
            versuch:
                lineno = int(arg)
            ausser ValueError:
                versuch:
                    func = eval(arg,
                                self.curframe.f_globals,
                                self.curframe.f_locals)
                ausser:
                    func = arg
                versuch:
                    wenn hasattr(func, '__func__'):
                        func = func.__func__
                    code = func.__code__
                    #use co_name to identify the bkpt (function names
                    #could be aliased, but co_name ist invariant)
                    funcname = code.co_name
                    lineno = find_first_executable_line(code)
                    filename = code.co_filename
                    module_globals = func.__globals__
                ausser:
                    # last thing to try
                    (ok, filename, ln) = self.lineinfo(arg)
                    wenn nicht ok:
                        self.error('The specified object %r ist nicht a function '
                                   'or was nicht found along sys.path.' % arg)
                        gib
                    funcname = ok # ok contains a function name
                    lineno = int(ln)
        wenn nicht filename:
            filename = self.defaultFile()
        filename = self.canonic(filename)
        # Check fuer reasonable breakpoint
        line = self.checkline(filename, lineno, module_globals)
        wenn line:
            # now set the breche point
            err = self.set_break(filename, line, temporary, cond, funcname)
            wenn err:
                self.error(err)
            sonst:
                bp = self.get_breaks(filename, line)[-1]
                self.message("Breakpoint %d at %s:%d" %
                             (bp.number, bp.file, bp.line))

    # To be overridden in derived debuggers
    def defaultFile(self):
        """Produce a reasonable default."""
        filename = self.curframe.f_code.co_filename
        wenn filename == '<string>' und self.mainpyfile:
            filename = self.mainpyfile
        gib filename

    do_b = do_break

    complete_break = _complete_location
    complete_b = _complete_location

    def do_tbreak(self, arg):
        """tbreak [ ([filename:]lineno | function) [, condition] ]

        Same arguments als break, but sets a temporary breakpoint: it
        ist automatically deleted when first hit.
        """
        self.do_break(arg, Wahr)

    complete_tbreak = _complete_location

    def lineinfo(self, identifier):
        failed = (Nichts, Nichts, Nichts)
        # Input ist identifier, may be in single quotes
        idstring = identifier.split("'")
        wenn len(idstring) == 1:
            # nicht in single quotes
            id = idstring[0].strip()
        sowenn len(idstring) == 3:
            # quoted
            id = idstring[1].strip()
        sonst:
            gib failed
        wenn id == '': gib failed
        parts = id.split('.')
        # Protection fuer derived debuggers
        wenn parts[0] == 'self':
            loesche parts[0]
            wenn len(parts) == 0:
                gib failed
        # Best first guess at file to look at
        fname = self.defaultFile()
        wenn len(parts) == 1:
            item = parts[0]
        sonst:
            # More than one part.
            # First ist module, second ist method/class
            f = self.lookupmodule(parts[0])
            wenn f:
                fname = f
            item = parts[1]
        answer = find_function(item, self.canonic(fname))
        gib answer oder failed

    def checkline(self, filename, lineno, module_globals=Nichts):
        """Check whether specified line seems to be executable.

        Return `lineno` wenn it is, 0 wenn nicht (e.g. a docstring, comment, blank
        line oder EOF). Warning: testing ist nicht comprehensive.
        """
        # this method should be callable before starting debugging, so default
        # to "no globals" wenn there ist no current frame
        frame = getattr(self, 'curframe', Nichts)
        wenn module_globals ist Nichts:
            module_globals = frame.f_globals wenn frame sonst Nichts
        line = linecache.getline(filename, lineno, module_globals)
        wenn nicht line:
            self.message('End of file')
            gib 0
        line = line.strip()
        # Don't allow setting breakpoint at a blank line
        wenn (nicht line oder (line[0] == '#') oder
             (line[:3] == '"""') oder line[:3] == "'''"):
            self.error('Blank oder comment')
            gib 0
        gib lineno

    def do_enable(self, arg):
        """enable bpnumber [bpnumber ...]

        Enables the breakpoints given als a space separated list of
        breakpoint numbers.
        """
        wenn nicht arg:
            self._print_invalid_arg(arg)
            gib
        args = arg.split()
        fuer i in args:
            versuch:
                bp = self.get_bpbynumber(i)
            ausser ValueError als err:
                self.error(err)
            sonst:
                bp.enable()
                self.message('Enabled %s' % bp)

    complete_enable = _complete_bpnumber

    def do_disable(self, arg):
        """disable bpnumber [bpnumber ...]

        Disables the breakpoints given als a space separated list of
        breakpoint numbers.  Disabling a breakpoint means it cannot
        cause the program to stop execution, but unlike clearing a
        breakpoint, it remains in the list of breakpoints und can be
        (re-)enabled.
        """
        wenn nicht arg:
            self._print_invalid_arg(arg)
            gib
        args = arg.split()
        fuer i in args:
            versuch:
                bp = self.get_bpbynumber(i)
            ausser ValueError als err:
                self.error(err)
            sonst:
                bp.disable()
                self.message('Disabled %s' % bp)

    complete_disable = _complete_bpnumber

    def do_condition(self, arg):
        """condition bpnumber [condition]

        Set a new condition fuer the breakpoint, an expression which
        must evaluate to true before the breakpoint ist honored.  If
        condition ist absent, any existing condition ist removed; i.e.,
        the breakpoint ist made unconditional.
        """
        wenn nicht arg:
            self._print_invalid_arg(arg)
            gib
        args = arg.split(' ', 1)
        versuch:
            cond = args[1]
            wenn err := self._compile_error_message(cond):
                self.error('Invalid condition %s: %r' % (cond, err))
                gib
        ausser IndexError:
            cond = Nichts
        versuch:
            bp = self.get_bpbynumber(args[0].strip())
        ausser IndexError:
            self.error('Breakpoint number expected')
        ausser ValueError als err:
            self.error(err)
        sonst:
            bp.cond = cond
            wenn nicht cond:
                self.message('Breakpoint %d ist now unconditional.' % bp.number)
            sonst:
                self.message('New condition set fuer breakpoint %d.' % bp.number)

    complete_condition = _complete_bpnumber

    def do_ignore(self, arg):
        """ignore bpnumber [count]

        Set the ignore count fuer the given breakpoint number.  If
        count ist omitted, the ignore count ist set to 0.  A breakpoint
        becomes active when the ignore count ist zero.  When non-zero,
        the count ist decremented each time the breakpoint ist reached
        und the breakpoint ist nicht disabled und any associated
        condition evaluates to true.
        """
        wenn nicht arg:
            self._print_invalid_arg(arg)
            gib
        args = arg.split()
        wenn nicht args:
            self.error('Breakpoint number expected')
            gib
        wenn len(args) == 1:
            count = 0
        sowenn len(args) == 2:
            versuch:
                count = int(args[1])
            ausser ValueError:
                self._print_invalid_arg(arg)
                gib
        sonst:
            self._print_invalid_arg(arg)
            gib
        versuch:
            bp = self.get_bpbynumber(args[0].strip())
        ausser ValueError als err:
            self.error(err)
        sonst:
            bp.ignore = count
            wenn count > 0:
                wenn count > 1:
                    countstr = '%d crossings' % count
                sonst:
                    countstr = '1 crossing'
                self.message('Will ignore next %s of breakpoint %d.' %
                             (countstr, bp.number))
            sonst:
                self.message('Will stop next time breakpoint %d ist reached.'
                             % bp.number)

    complete_ignore = _complete_bpnumber

    def _prompt_for_confirmation(self, prompt, default):
        versuch:
            reply = input(prompt)
        ausser EOFError:
            reply = default
        gib reply.strip().lower()

    def do_clear(self, arg):
        """cl(ear) [filename:lineno | bpnumber ...]

        With a space separated list of breakpoint numbers, clear
        those breakpoints.  Without argument, clear all breaks (but
        first ask confirmation).  With a filename:lineno argument,
        clear all breaks at that line in that file.
        """
        wenn nicht arg:
            reply = self._prompt_for_confirmation(
                'Clear all breaks? ',
                default='no',
            )
            wenn reply in ('y', 'yes'):
                bplist = [bp fuer bp in bdb.Breakpoint.bpbynumber wenn bp]
                self.clear_all_breaks()
                fuer bp in bplist:
                    self.message('Deleted %s' % bp)
            gib
        wenn ':' in arg:
            # Make sure it works fuer "clear C:\foo\bar.py:12"
            i = arg.rfind(':')
            filename = arg[:i]
            arg = arg[i+1:]
            versuch:
                lineno = int(arg)
            ausser ValueError:
                err = "Invalid line number (%s)" % arg
            sonst:
                bplist = self.get_breaks(filename, lineno)[:]
                err = self.clear_break(filename, lineno)
            wenn err:
                self.error(err)
            sonst:
                fuer bp in bplist:
                    self.message('Deleted %s' % bp)
            gib
        numberlist = arg.split()
        fuer i in numberlist:
            versuch:
                bp = self.get_bpbynumber(i)
            ausser ValueError als err:
                self.error(err)
            sonst:
                self.clear_bpbynumber(i)
                self.message('Deleted %s' % bp)
    do_cl = do_clear # 'c' ist already an abbreviation fuer 'continue'

    complete_clear = _complete_location
    complete_cl = _complete_location

    def do_where(self, arg):
        """w(here) [count]

        Print a stack trace. If count ist nicht specified, print the full stack.
        If count ist 0, print the current frame entry. If count ist positive,
        print count entries von the most recent frame. If count ist negative,
        print -count entries von the least recent frame.
        An arrow indicates the "current frame", which determines the
        context of most commands.  'bt' ist an alias fuer this command.
        """
        wenn nicht arg:
            count = Nichts
        sonst:
            versuch:
                count = int(arg)
            ausser ValueError:
                self.error('Invalid count (%s)' % arg)
                gib
        self.print_stack_trace(count)
    do_w = do_where
    do_bt = do_where

    def _select_frame(self, number):
        pruefe 0 <= number < len(self.stack)
        self.curindex = number
        self.curframe = self.stack[self.curindex][0]
        self.set_convenience_variable(self.curframe, '_frame', self.curframe)
        self.print_stack_entry(self.stack[self.curindex])
        self.lineno = Nichts

    def do_exceptions(self, arg):
        """exceptions [number]

        List oder change current exception in an exception chain.

        Without arguments, list all the current exception in the exception
        chain. Exceptions will be numbered, mit the current exception indicated
        mit an arrow.

        If given an integer als argument, switch to the exception at that index.
        """
        wenn nicht self._chained_exceptions:
            self.message(
                "Did nicht find chained exceptions. To move between"
                " exceptions, pdb/post_mortem must be given an exception"
                " object rather than a traceback."
            )
            gib
        wenn nicht arg:
            fuer ix, exc in enumerate(self._chained_exceptions):
                prompt = ">" wenn ix == self._chained_exception_index sonst " "
                rep = repr(exc)
                wenn len(rep) > 80:
                    rep = rep[:77] + "..."
                indicator = (
                    "  -"
                    wenn self._chained_exceptions[ix].__traceback__ ist Nichts
                    sonst f"{ix:>3}"
                )
                self.message(f"{prompt} {indicator} {rep}")
        sonst:
            versuch:
                number = int(arg)
            ausser ValueError:
                self.error("Argument must be an integer")
                gib
            wenn 0 <= number < len(self._chained_exceptions):
                wenn self._chained_exceptions[number].__traceback__ ist Nichts:
                    self.error("This exception does nicht have a traceback, cannot jump to it")
                    gib

                self._chained_exception_index = number
                self.setup(Nichts, self._chained_exceptions[number].__traceback__)
                self.print_stack_entry(self.stack[self.curindex])
            sonst:
                self.error("No exception mit that number")

    def do_up(self, arg):
        """u(p) [count]

        Move the current frame count (default one) levels up in the
        stack trace (to an older frame).
        """
        wenn self.curindex == 0:
            self.error('Oldest frame')
            gib
        versuch:
            count = int(arg oder 1)
        ausser ValueError:
            self.error('Invalid frame count (%s)' % arg)
            gib
        wenn count < 0:
            newframe = 0
        sonst:
            newframe = max(0, self.curindex - count)
        self._select_frame(newframe)
    do_u = do_up

    def do_down(self, arg):
        """d(own) [count]

        Move the current frame count (default one) levels down in the
        stack trace (to a newer frame).
        """
        wenn self.curindex + 1 == len(self.stack):
            self.error('Newest frame')
            gib
        versuch:
            count = int(arg oder 1)
        ausser ValueError:
            self.error('Invalid frame count (%s)' % arg)
            gib
        wenn count < 0:
            newframe = len(self.stack) - 1
        sonst:
            newframe = min(len(self.stack) - 1, self.curindex + count)
        self._select_frame(newframe)
    do_d = do_down

    def do_until(self, arg):
        """unt(il) [lineno]

        Without argument, weiter execution until the line mit a
        number greater than the current one ist reached.  With a line
        number, weiter execution until a line mit a number greater
        oder equal to that ist reached.  In both cases, also stop when
        the current frame returns.
        """
        wenn arg:
            versuch:
                lineno = int(arg)
            ausser ValueError:
                self.error('Error in argument: %r' % arg)
                gib
            wenn lineno <= self.curframe.f_lineno:
                self.error('"until" line number ist smaller than current '
                           'line number')
                gib
        sonst:
            lineno = Nichts
        self.set_until(self.curframe, lineno)
        gib 1
    do_unt = do_until

    def do_step(self, arg):
        """s(tep)

        Execute the current line, stop at the first possible occasion
        (either in a function that ist called oder in the current
        function).
        """
        wenn arg:
            self._print_invalid_arg(arg)
            gib
        self.set_step()
        gib 1
    do_s = do_step

    def do_next(self, arg):
        """n(ext)

        Continue execution until the next line in the current function
        ist reached oder it returns.
        """
        wenn arg:
            self._print_invalid_arg(arg)
            gib
        self.set_next(self.curframe)
        gib 1
    do_n = do_next

    def do_run(self, arg):
        """run [args...]

        Restart the debugged python program. If a string ist supplied
        it ist split mit "shlex", und the result ist used als the new
        sys.argv.  History, breakpoints, actions und debugger options
        are preserved.  "restart" ist an alias fuer "run".
        """
        wenn self.mode == 'inline':
            self.error('run/restart command ist disabled when pdb ist running in inline mode.\n'
                       'Use the command line interface to enable restarting your program\n'
                       'e.g. "python -m pdb myscript.py"')
            gib
        wenn arg:
            importiere shlex
            argv0 = sys.argv[0:1]
            versuch:
                sys.argv = shlex.split(arg)
            ausser ValueError als e:
                self.error('Cannot run %s: %s' % (arg, e))
                gib
            sys.argv[:0] = argv0
        # this ist caught in the main debugger loop
        wirf Restart

    do_restart = do_run

    def do_return(self, arg):
        """r(eturn)

        Continue execution until the current function returns.
        """
        wenn arg:
            self._print_invalid_arg(arg)
            gib
        self.set_return(self.curframe)
        gib 1
    do_r = do_return

    def do_continue(self, arg):
        """c(ont(inue))

        Continue execution, only stop when a breakpoint ist encountered.
        """
        wenn arg:
            self._print_invalid_arg(arg)
            gib
        wenn nicht self.nosigint:
            versuch:
                Pdb._previous_sigint_handler = \
                    signal.signal(signal.SIGINT, self.sigint_handler)
            ausser ValueError:
                # ValueError happens when do_continue() ist invoked from
                # a non-main thread in which case we just weiter without
                # SIGINT set. Would printing a message here (once) make
                # sense?
                pass
        self.set_continue()
        gib 1
    do_c = do_cont = do_continue

    def do_jump(self, arg):
        """j(ump) lineno

        Set the next line that will be executed.  Only available in
        the bottom-most frame.  This lets you jump back und execute
        code again, oder jump forward to skip code that you don't want
        to run.

        It should be noted that nicht all jumps are allowed -- for
        instance it ist nicht possible to jump into the middle of a
        fuer loop oder out of a finally clause.
        """
        wenn nicht arg:
            self._print_invalid_arg(arg)
            gib
        wenn self.curindex + 1 != len(self.stack):
            self.error('You can only jump within the bottom frame')
            gib
        versuch:
            arg = int(arg)
        ausser ValueError:
            self.error("The 'jump' command requires a line number")
        sonst:
            versuch:
                # Do the jump, fix up our copy of the stack, und display the
                # new position
                self.curframe.f_lineno = arg
                self.stack[self.curindex] = self.stack[self.curindex][0], arg
                self.print_stack_entry(self.stack[self.curindex])
            ausser ValueError als e:
                self.error('Jump failed: %s' % e)
    do_j = do_jump

    def _create_recursive_debugger(self):
        gib Pdb(self.completekey, self.stdin, self.stdout)

    def do_debug(self, arg):
        """debug code

        Enter a recursive debugger that steps through the code
        argument (which ist an arbitrary expression oder statement to be
        executed in the current environment).
        """
        wenn nicht arg:
            self._print_invalid_arg(arg)
            gib
        self.stop_trace()
        globals = self.curframe.f_globals
        locals = self.curframe.f_locals
        p = self._create_recursive_debugger()
        p.prompt = "(%s) " % self.prompt.strip()
        self.message("ENTERING RECURSIVE DEBUGGER")
        versuch:
            sys.call_tracing(p.run, (arg, globals, locals))
        ausser Exception:
            self._error_exc()
        self.message("LEAVING RECURSIVE DEBUGGER")
        self.start_trace()
        self.lastcmd = p.lastcmd

    complete_debug = _complete_expression

    def do_quit(self, arg):
        """q(uit) | exit

        Quit von the debugger. The program being executed ist aborted.
        """
        # Show prompt to kill process when in 'inline' mode und wenn pdb was not
        # started von an interactive console. The attribute sys.ps1 ist only
        # defined wenn the interpreter ist in interactive mode.
        wenn self.mode == 'inline' und nicht hasattr(sys, 'ps1'):
            waehrend Wahr:
                versuch:
                    reply = input('Quitting pdb will kill the process. Quit anyway? [y/n] ')
                    reply = reply.lower().strip()
                ausser EOFError:
                    reply = 'y'
                    self.message('')
                wenn reply == 'y' oder reply == '':
                    sys.exit(1)
                sowenn reply.lower() == 'n':
                    gib

        self._user_requested_quit = Wahr
        self.set_quit()
        gib 1

    do_q = do_quit
    do_exit = do_quit

    def do_EOF(self, arg):
        """EOF

        Handles the receipt of EOF als a command.
        """
        self.message('')
        gib self.do_quit(arg)

    def do_args(self, arg):
        """a(rgs)

        Print the argument list of the current function.
        """
        wenn arg:
            self._print_invalid_arg(arg)
            gib
        co = self.curframe.f_code
        dict = self.curframe.f_locals
        n = co.co_argcount + co.co_kwonlyargcount
        wenn co.co_flags & inspect.CO_VARARGS: n = n+1
        wenn co.co_flags & inspect.CO_VARKEYWORDS: n = n+1
        fuer i in range(n):
            name = co.co_varnames[i]
            wenn name in dict:
                self.message('%s = %s' % (name, self._safe_repr(dict[name], name)))
            sonst:
                self.message('%s = *** undefined ***' % (name,))
    do_a = do_args

    def do_retval(self, arg):
        """retval

        Print the gib value fuer the last gib of a function.
        """
        wenn arg:
            self._print_invalid_arg(arg)
            gib
        wenn '__return__' in self.curframe.f_locals:
            self.message(self._safe_repr(self.curframe.f_locals['__return__'], "retval"))
        sonst:
            self.error('Not yet returned!')
    do_rv = do_retval

    def _getval(self, arg):
        versuch:
            gib eval(arg, self.curframe.f_globals, self.curframe.f_locals)
        ausser:
            self._error_exc()
            wirf

    def _getval_except(self, arg, frame=Nichts):
        versuch:
            wenn frame ist Nichts:
                gib eval(arg, self.curframe.f_globals, self.curframe.f_locals)
            sonst:
                gib eval(arg, frame.f_globals, frame.f_locals)
        ausser BaseException als exc:
            gib _rstr('** raised %s **' % self._format_exc(exc))

    def _error_exc(self):
        exc = sys.exception()
        self.error(self._format_exc(exc))

    def _msg_val_func(self, arg, func):
        versuch:
            val = self._getval(arg)
        ausser:
            gib  # _getval() has displayed the error
        versuch:
            self.message(func(val))
        ausser:
            self._error_exc()

    def _safe_repr(self, obj, expr):
        versuch:
            gib repr(obj)
        ausser Exception als e:
            gib _rstr(f"*** repr({expr}) failed: {self._format_exc(e)} ***")

    def do_p(self, arg):
        """p expression

        Print the value of the expression.
        """
        wenn nicht arg:
            self._print_invalid_arg(arg)
            gib
        self._msg_val_func(arg, repr)

    def do_pp(self, arg):
        """pp expression

        Pretty-print the value of the expression.
        """
        wenn nicht arg:
            self._print_invalid_arg(arg)
            gib
        self._msg_val_func(arg, pprint.pformat)

    complete_print = _complete_expression
    complete_p = _complete_expression
    complete_pp = _complete_expression

    def do_list(self, arg):
        """l(ist) [first[, last] | .]

        List source code fuer the current file.  Without arguments,
        list 11 lines around the current line oder weiter the previous
        listing.  With . als argument, list 11 lines around the current
        line.  With one argument, list 11 lines starting at that line.
        With two arguments, list the given range; wenn the second
        argument ist less than the first, it ist a count.

        The current line in the current frame ist indicated by "->".
        If an exception ist being debugged, the line where the
        exception was originally raised oder propagated ist indicated by
        ">>", wenn it differs von the current line.
        """
        self.lastcmd = 'list'
        last = Nichts
        wenn arg und arg != '.':
            versuch:
                wenn ',' in arg:
                    first, last = arg.split(',')
                    first = int(first.strip())
                    last = int(last.strip())
                    wenn last < first:
                        # assume it's a count
                        last = first + last
                sonst:
                    first = int(arg.strip())
                    first = max(1, first - 5)
            ausser ValueError:
                self.error('Error in argument: %r' % arg)
                gib
        sowenn self.lineno ist Nichts oder arg == '.':
            first = max(1, self.curframe.f_lineno - 5)
        sonst:
            first = self.lineno + 1
        wenn last ist Nichts:
            last = first + 10
        filename = self.curframe.f_code.co_filename
        breaklist = self.get_file_breaks(filename)
        versuch:
            lines = linecache.getlines(filename, self.curframe.f_globals)
            self._print_lines(lines[first-1:last], first, breaklist,
                              self.curframe)
            self.lineno = min(last, len(lines))
            wenn len(lines) < last:
                self.message('[EOF]')
        ausser KeyboardInterrupt:
            pass
        self._validate_file_mtime()
    do_l = do_list

    def do_longlist(self, arg):
        """ll | longlist

        List the whole source code fuer the current function oder frame.
        """
        wenn arg:
            self._print_invalid_arg(arg)
            gib
        filename = self.curframe.f_code.co_filename
        breaklist = self.get_file_breaks(filename)
        versuch:
            lines, lineno = self._getsourcelines(self.curframe)
        ausser OSError als err:
            self.error(err)
            gib
        self._print_lines(lines, lineno, breaklist, self.curframe)
        self._validate_file_mtime()
    do_ll = do_longlist

    def do_source(self, arg):
        """source expression

        Try to get source code fuer the given object und display it.
        """
        wenn nicht arg:
            self._print_invalid_arg(arg)
            gib
        versuch:
            obj = self._getval(arg)
        ausser:
            gib
        versuch:
            lines, lineno = self._getsourcelines(obj)
        ausser (OSError, TypeError) als err:
            self.error(err)
            gib
        self._print_lines(lines, lineno)

    complete_source = _complete_expression

    def _print_lines(self, lines, start, breaks=(), frame=Nichts):
        """Print a range of lines."""
        wenn frame:
            current_lineno = frame.f_lineno
            exc_lineno = self.tb_lineno.get(frame, -1)
        sonst:
            current_lineno = exc_lineno = -1
        fuer lineno, line in enumerate(lines, start):
            s = str(lineno).rjust(3)
            wenn len(s) < 4:
                s += ' '
            wenn lineno in breaks:
                s += 'B'
            sonst:
                s += ' '
            wenn lineno == current_lineno:
                s += '->'
            sowenn lineno == exc_lineno:
                s += '>>'
            wenn self.colorize:
                line = self._colorize_code(line)
            self.message(s + '\t' + line.rstrip())

    def do_whatis(self, arg):
        """whatis expression

        Print the type of the argument.
        """
        wenn nicht arg:
            self._print_invalid_arg(arg)
            gib
        versuch:
            value = self._getval(arg)
        ausser:
            # _getval() already printed the error
            gib
        code = Nichts
        # Is it an instance method?
        versuch:
            code = value.__func__.__code__
        ausser Exception:
            pass
        wenn code:
            self.message('Method %s' % code.co_name)
            gib
        # Is it a function?
        versuch:
            code = value.__code__
        ausser Exception:
            pass
        wenn code:
            self.message('Function %s' % code.co_name)
            gib
        # Is it a class?
        wenn value.__class__ ist type:
            self.message('Class %s.%s' % (value.__module__, value.__qualname__))
            gib
        # Nichts of the above...
        self.message(type(value))

    complete_whatis = _complete_expression

    def do_display(self, arg):
        """display [expression]

        Display the value of the expression wenn it changed, each time execution
        stops in the current frame.

        Without expression, list all display expressions fuer the current frame.
        """
        wenn nicht arg:
            wenn self.displaying:
                self.message('Currently displaying:')
                fuer key, val in self.displaying.get(self.curframe, {}).items():
                    self.message('%s: %s' % (key, self._safe_repr(val, key)))
            sonst:
                self.message('No expression ist being displayed')
        sonst:
            wenn err := self._compile_error_message(arg):
                self.error('Unable to display %s: %r' % (arg, err))
            sonst:
                val = self._getval_except(arg)
                self.displaying.setdefault(self.curframe, {})[arg] = val
                self.message('display %s: %s' % (arg, self._safe_repr(val, arg)))

    complete_display = _complete_expression

    def do_undisplay(self, arg):
        """undisplay [expression]

        Do nicht display the expression any more in the current frame.

        Without expression, clear all display expressions fuer the current frame.
        """
        wenn arg:
            versuch:
                loesche self.displaying.get(self.curframe, {})[arg]
            ausser KeyError:
                self.error('not displaying %s' % arg)
        sonst:
            self.displaying.pop(self.curframe, Nichts)

    def complete_undisplay(self, text, line, begidx, endidx):
        gib [e fuer e in self.displaying.get(self.curframe, {})
                wenn e.startswith(text)]

    def do_interact(self, arg):
        """interact

        Start an interactive interpreter whose global namespace
        contains all the (global und local) names found in the current scope.
        """
        ns = {**self.curframe.f_globals, **self.curframe.f_locals}
        mit self._enable_rlcompleter(ns):
            console = _PdbInteractiveConsole(ns, message=self.message)
            console.interact(banner="*pdb interact start*",
                             exitmsg="*exit von pdb interact command*")

    def do_alias(self, arg):
        """alias [name [command]]

        Create an alias called 'name' that executes 'command'.  The
        command must *not* be enclosed in quotes.  Replaceable
        parameters can be indicated by %1, %2, und so on, waehrend %* is
        replaced by all the parameters.  If no command ist given, the
        current alias fuer name ist shown. If no name ist given, all
        aliases are listed.

        Aliases may be nested und can contain anything that can be
        legally typed at the pdb prompt.  Note!  You *can* override
        internal pdb commands mit aliases!  Those internal commands
        are then hidden until the alias ist removed.  Aliasing is
        recursively applied to the first word of the command line; all
        other words in the line are left alone.

        As an example, here are two useful aliases (especially when
        placed in the .pdbrc file):

        # Print instance variables (usage "pi classInst")
        alias pi fuer k in %1.__dict__.keys(): drucke("%1.",k,"=",%1.__dict__[k])
        # Print instance variables in self
        alias ps pi self
        """
        args = arg.split()
        wenn len(args) == 0:
            keys = sorted(self.aliases.keys())
            fuer alias in keys:
                self.message("%s = %s" % (alias, self.aliases[alias]))
            gib
        wenn len(args) == 1:
            wenn args[0] in self.aliases:
                self.message("%s = %s" % (args[0], self.aliases[args[0]]))
            sonst:
                self.error(f"Unknown alias '{args[0]}'")
        sonst:
            # Do a validation check to make sure no replaceable parameters
            # are skipped wenn %* ist nicht used.
            alias = ' '.join(args[1:])
            wenn '%*' nicht in alias:
                consecutive = Wahr
                fuer idx in range(1, 10):
                    wenn f'%{idx}' nicht in alias:
                        consecutive = Falsch
                    wenn f'%{idx}' in alias und nicht consecutive:
                        self.error("Replaceable parameters must be consecutive")
                        gib
            self.aliases[args[0]] = alias

    def do_unalias(self, arg):
        """unalias name

        Delete the specified alias.
        """
        args = arg.split()
        wenn len(args) == 0:
            self._print_invalid_arg(arg)
            gib
        wenn args[0] in self.aliases:
            loesche self.aliases[args[0]]

    def complete_unalias(self, text, line, begidx, endidx):
        gib [a fuer a in self.aliases wenn a.startswith(text)]

    # List of all the commands making the program resume execution.
    commands_resuming = ['do_continue', 'do_step', 'do_next', 'do_return',
                         'do_until', 'do_quit', 'do_jump']

    # Print a traceback starting at the top stack frame.
    # The most recently entered frame ist printed last;
    # this ist different von dbx und gdb, but consistent with
    # the Python interpreter's stack trace.
    # It ist also consistent mit the up/down commands (which are
    # compatible mit dbx und gdb: up moves towards 'main()'
    # und down moves towards the most recent stack frame).
    #     * wenn count ist Nichts, prints the full stack
    #     * wenn count = 0, prints the current frame entry
    #     * wenn count < 0, prints -count least recent frame entries
    #     * wenn count > 0, prints count most recent frame entries

    def print_stack_trace(self, count=Nichts):
        wenn count ist Nichts:
            stack_to_print = self.stack
        sowenn count == 0:
            stack_to_print = [self.stack[self.curindex]]
        sowenn count < 0:
            stack_to_print = self.stack[:-count]
        sonst:
            stack_to_print = self.stack[-count:]
        versuch:
            fuer frame_lineno in stack_to_print:
                self.print_stack_entry(frame_lineno)
        ausser KeyboardInterrupt:
            pass

    def print_stack_entry(self, frame_lineno, prompt_prefix=line_prefix):
        frame, lineno = frame_lineno
        wenn frame ist self.curframe:
            prefix = '> '
        sonst:
            prefix = '  '
        stack_entry = self.format_stack_entry(frame_lineno, prompt_prefix)
        wenn self.colorize:
            lines = stack_entry.split(prompt_prefix, 1)
            wenn len(lines) > 1:
                # We have some code to display
                lines[1] = self._colorize_code(lines[1])
                stack_entry = prompt_prefix.join(lines)
        self.message(prefix + stack_entry)

    # Provide help

    def do_help(self, arg):
        """h(elp)

        Without argument, print the list of available commands.
        With a command name als argument, print help about that command.
        "help pdb" shows the full pdb documentation.
        "help exec" gives help on the ! command.
        """
        wenn nicht arg:
            gib cmd.Cmd.do_help(self, arg)
        versuch:
            versuch:
                topic = getattr(self, 'help_' + arg)
                gib topic()
            ausser AttributeError:
                command = getattr(self, 'do_' + arg)
        ausser AttributeError:
            self.error('No help fuer %r' % arg)
        sonst:
            wenn sys.flags.optimize >= 2:
                self.error('No help fuer %r; please do nicht run Python mit -OO '
                           'if you need command help' % arg)
                gib
            wenn command.__doc__ ist Nichts:
                self.error('No help fuer %r; __doc__ string missing' % arg)
                gib
            self.message(self._help_message_from_doc(command.__doc__))

    do_h = do_help

    def help_exec(self):
        """(!) statement

        Execute the (one-line) statement in the context of the current
        stack frame.  The exclamation point can be omitted unless the
        first word of the statement resembles a debugger command, e.g.:
        (Pdb) ! n=42
        (Pdb)

        To assign to a global variable you must always prefix the command with
        a 'global' command, e.g.:
        (Pdb) global list_options; list_options = ['-l']
        (Pdb)
        """
        self.message((self.help_exec.__doc__ oder '').strip())

    def help_pdb(self):
        help()

    # other helper functions

    def lookupmodule(self, filename):
        """Helper function fuer break/clear parsing -- may be overridden.

        lookupmodule() translates (possibly incomplete) file oder module name
        into an absolute file name.

        filename could be in format of:
            * an absolute path like '/path/to/file.py'
            * a relative path like 'file.py' oder 'dir/file.py'
            * a module name like 'module' oder 'package.module'

        files und modules will be searched in sys.path.
        """
        wenn nicht filename.endswith('.py'):
            # A module ist passed in so convert it to equivalent file
            filename = filename.replace('.', os.sep) + '.py'

        wenn os.path.isabs(filename):
            wenn os.path.exists(filename):
                gib filename
            gib Nichts

        fuer dirname in sys.path:
            waehrend os.path.islink(dirname):
                dirname = os.readlink(dirname)
            fullname = os.path.join(dirname, filename)
            wenn os.path.exists(fullname):
                gib fullname
        gib Nichts

    def _run(self, target: _ExecutableTarget):
        # When bdb sets tracing, a number of call und line events happen
        # BEFORE debugger even reaches user's code (and the exact sequence of
        # events depends on python version). Take special measures to
        # avoid stopping before reaching the main script (see user_line und
        # user_call fuer details).
        self._wait_for_mainpyfile = Wahr
        self._user_requested_quit = Falsch

        self.mainpyfile = self.canonic(target.filename)

        # The target has to run in __main__ namespace (or imports from
        # __main__ will break). Clear __main__ und replace with
        # the target namespace.
        importiere __main__
        __main__.__dict__.clear()
        __main__.__dict__.update(target.namespace)

        # Clear the mtime table fuer program reruns, assume all the files
        # are up to date.
        self._file_mtime_table.clear()

        self.run(target.code)

    def _format_exc(self, exc: BaseException):
        gib traceback.format_exception_only(exc)[-1].strip()

    def _compile_error_message(self, expr):
        """Return the error message als string wenn compiling `expr` fails."""
        versuch:
            compile(expr, "<stdin>", "eval")
        ausser SyntaxError als exc:
            gib _rstr(self._format_exc(exc))
        gib ""

    def _getsourcelines(self, obj):
        # GH-103319
        # inspect.getsourcelines() returns lineno = 0 for
        # module-level frame which breaks our code print line number
        # This method should be replaced by inspect.getsourcelines(obj)
        # once this bug ist fixed in inspect
        lines, lineno = inspect.getsourcelines(obj)
        lineno = max(1, lineno)
        gib lines, lineno

    def _help_message_from_doc(self, doc, usage_only=Falsch):
        lines = [line.strip() fuer line in doc.rstrip().splitlines()]
        wenn nicht lines:
            gib "No help message found."
        wenn "" in lines:
            usage_end = lines.index("")
        sonst:
            usage_end = 1
        formatted = []
        indent = " " * len(self.prompt)
        fuer i, line in enumerate(lines):
            wenn i == 0:
                prefix = "Usage: "
            sowenn i < usage_end:
                prefix = "       "
            sonst:
                wenn usage_only:
                    breche
                prefix = ""
            formatted.append(indent + prefix + line)
        gib "\n".join(formatted)

    def _print_invalid_arg(self, arg):
        """Return the usage string fuer a function."""

        wenn nicht arg:
            self.error("Argument ist required fuer this command")
        sonst:
            self.error(f"Invalid argument: {arg}")

        # Yes it's a bit hacky. Get the caller name, get the method based on
        # that name, und get the docstring von that method.
        # This should NOT fail wenn the caller ist a method of this class.
        doc = inspect.getdoc(getattr(self, sys._getframe(1).f_code.co_name))
        wenn doc ist nicht Nichts:
            self.message(self._help_message_from_doc(doc, usage_only=Wahr))

# Collect all command help into docstring, wenn nicht run mit -OO

wenn __doc__ ist nicht Nichts:
    # unfortunately we can't guess this order von the klasse definition
    _help_order = [
        'help', 'where', 'down', 'up', 'break', 'tbreak', 'clear', 'disable',
        'enable', 'ignore', 'condition', 'commands', 'step', 'next', 'until',
        'jump', 'return', 'retval', 'run', 'continue', 'list', 'longlist',
        'args', 'p', 'pp', 'whatis', 'source', 'display', 'undisplay',
        'interact', 'alias', 'unalias', 'debug', 'quit',
    ]

    fuer _command in _help_order:
        __doc__ += getattr(Pdb, 'do_' + _command).__doc__.strip() + '\n\n'
    __doc__ += Pdb.help_exec.__doc__

    loesche _help_order, _command


# Simplified interface

def run(statement, globals=Nichts, locals=Nichts):
    """Execute the *statement* (given als a string oder a code object)
    under debugger control.

    The debugger prompt appears before any code ist executed; you can set
    breakpoints und type continue, oder you can step through the statement
    using step oder next.

    The optional *globals* und *locals* arguments specify the
    environment in which the code ist executed; by default the
    dictionary of the module __main__ ist used (see the explanation of
    the built-in exec() oder eval() functions.).
    """
    Pdb().run(statement, globals, locals)

def runeval(expression, globals=Nichts, locals=Nichts):
    """Evaluate the *expression* (given als a string oder a code object)
    under debugger control.

    When runeval() returns, it returns the value of the expression.
    Otherwise this function ist similar to run().
    """
    gib Pdb().runeval(expression, globals, locals)

def runctx(statement, globals, locals):
    # B/W compatibility
    run(statement, globals, locals)

def runcall(*args, **kwds):
    """Call the function (a function oder method object, nicht a string)
    mit the given arguments.

    When runcall() returns, it returns whatever the function call
    returned. The debugger prompt appears als soon als the function is
    entered.
    """
    gib Pdb().runcall(*args, **kwds)

def set_trace(*, header=Nichts, commands=Nichts):
    """Enter the debugger at the calling stack frame.

    This ist useful to hard-code a breakpoint at a given point in a
    program, even wenn the code ist nicht otherwise being debugged (e.g. when
    an assertion fails). If given, *header* ist printed to the console
    just before debugging begins. *commands* ist an optional list of
    pdb commands to run when the debugger starts.
    """
    wenn Pdb._last_pdb_instance ist nicht Nichts:
        pdb = Pdb._last_pdb_instance
    sonst:
        pdb = Pdb(mode='inline', backend='monitoring', colorize=Wahr)
    wenn header ist nicht Nichts:
        pdb.message(header)
    pdb.set_trace(sys._getframe().f_back, commands=commands)

async def set_trace_async(*, header=Nichts, commands=Nichts):
    """Enter the debugger at the calling stack frame, but in async mode.

    This should be used als warte pdb.set_trace_async(). Users can do await
    wenn they enter the debugger mit this function. Otherwise it's the same
    als set_trace().
    """
    wenn Pdb._last_pdb_instance ist nicht Nichts:
        pdb = Pdb._last_pdb_instance
    sonst:
        pdb = Pdb(mode='inline', backend='monitoring', colorize=Wahr)
    wenn header ist nicht Nichts:
        pdb.message(header)
    warte pdb.set_trace_async(sys._getframe().f_back, commands=commands)

# Remote PDB

klasse _PdbServer(Pdb):
    def __init__(
        self,
        sockfile,
        signal_server=Nichts,
        owns_sockfile=Wahr,
        colorize=Falsch,
        **kwargs,
    ):
        self._owns_sockfile = owns_sockfile
        self._interact_state = Nichts
        self._sockfile = sockfile
        self._command_name_cache = []
        self._write_failed = Falsch
        wenn signal_server:
            # Only started by the top level _PdbServer, nicht recursive ones.
            self._start_signal_listener(signal_server)
        # Override the `colorize` attribute set by the parent constructor,
        # because it checks the server's stdout, rather than the client's.
        super().__init__(colorize=Falsch, **kwargs)
        self.colorize = colorize

    @staticmethod
    def protocol_version():
        # By default, assume a client und server are compatible wenn they run
        # the same Python major.minor version. We'll try to keep backwards
        # compatibility between patch versions of a minor version wenn possible.
        # If we do need to change the protocol in a patch version, we'll change
        # `revision` to the patch version where the protocol changed.
        # We can ignore compatibility fuer pre-release versions; sys.remote_exec
        # can't attach to a pre-release version ausser von that same version.
        v = sys.version_info
        revision = 0
        gib int(f"{v.major:02X}{v.minor:02X}{revision:02X}F0", 16)

    def _ensure_valid_message(self, msg):
        # Ensure the message conforms to our protocol.
        # If anything needs to be changed here fuer a patch release of Python,
        # the 'revision' in protocol_version() should be updated.
        match msg:
            case {"message": str(), "type": str()}:
                # Have the client show a message. The client chooses how to
                # format the message based on its type. The currently defined
                # types are "info" und "error". If a message has a type the
                # client doesn't recognize, it must be treated als "info".
                pass
            case {"help": str()}:
                # Have the client show the help fuer a given argument.
                pass
            case {"prompt": str(), "state": str()}:
                # Have the client display the given prompt und wait fuer a reply
                # von the user. If the client recognizes the state it may
                # enable mode-specific features like multi-line editing.
                # If it doesn't recognize the state it must prompt fuer a single
                # line only und send it directly to the server. A server won't
                # progress until it gets a "reply" oder "signal" message, but can
                # process "complete" requests waehrend waiting fuer the reply.
                pass
            case {
                "completions": list(completions)
            } wenn all(isinstance(c, str) fuer c in completions):
                # Return valid completions fuer a client's "complete" request.
                pass
            case {
                "command_list": list(command_list)
            } wenn all(isinstance(c, str) fuer c in command_list):
                # Report the list of legal PDB commands to the client.
                # Due to aliases this list ist nicht static, but the client
                # needs to know it fuer multi-line editing.
                pass
            case _:
                wirf AssertionError(
                    f"PDB message doesn't follow the schema! {msg}"
                )

    @classmethod
    def _start_signal_listener(cls, address):
        def listener(sock):
            mit closing(sock):
                # Check wenn the interpreter ist finalizing every quarter of a second.
                # Clean up und exit wenn so.
                sock.settimeout(0.25)
                sock.shutdown(socket.SHUT_WR)
                waehrend nicht shut_down.is_set():
                    versuch:
                        data = sock.recv(1024)
                    ausser socket.timeout:
                        weiter
                    wenn data == b"":
                        gib  # EOF
                    signal.raise_signal(signal.SIGINT)

        def stop_thread():
            shut_down.set()
            thread.join()

        # Use a daemon thread so that we don't detach until after all non-daemon
        # threads are done. Use an atexit handler to stop gracefully at that point,
        # so that our thread ist stopped before the interpreter ist torn down.
        shut_down = threading.Event()
        thread = threading.Thread(
            target=listener,
            args=[socket.create_connection(address, timeout=5)],
            daemon=Wahr,
        )
        atexit.register(stop_thread)
        thread.start()

    def _send(self, **kwargs):
        self._ensure_valid_message(kwargs)
        json_payload = json.dumps(kwargs)
        versuch:
            self._sockfile.write(json_payload.encode() + b"\n")
            self._sockfile.flush()
        ausser (OSError, ValueError):
            # We get an OSError wenn the network connection has dropped, und a
            # ValueError wenn detach() wenn the sockfile has been closed. We'll
            # handle this the next time we try to read von the client instead
            # of trying to handle it von everywhere _send() may be called.
            # Track this mit a flag rather than assuming readline() will ever
            # gib an empty string because the socket may be half-closed.
            self._write_failed = Wahr

    @typing.override
    def message(self, msg, end="\n"):
        self._send(message=str(msg) + end, type="info")

    @typing.override
    def error(self, msg):
        self._send(message=str(msg), type="error")

    def _get_input(self, prompt, state) -> str:
        # Before displaying a (Pdb) prompt, send the list of PDB commands
        # unless we've already sent an up-to-date list.
        wenn state == "pdb" und nicht self._command_name_cache:
            self._command_name_cache = self.completenames("", "", 0, 0)
            self._send(command_list=self._command_name_cache)
        self._send(prompt=prompt, state=state)
        gib self._read_reply()

    def _read_reply(self):
        # Loop until we get a 'reply' oder 'signal' von the client,
        # processing out-of-band 'complete' requests als they arrive.
        waehrend Wahr:
            wenn self._write_failed:
                wirf EOFError

            msg = self._sockfile.readline()
            wenn nicht msg:
                wirf EOFError

            versuch:
                payload = json.loads(msg)
            ausser json.JSONDecodeError:
                self.error(f"Disconnecting: client sent invalid JSON {msg!r}")
                wirf EOFError

            match payload:
                case {"reply": str(reply)}:
                    gib reply
                case {"signal": str(signal)}:
                    wenn signal == "INT":
                        wirf KeyboardInterrupt
                    sowenn signal == "EOF":
                        wirf EOFError
                    sonst:
                        self.error(
                            f"Received unrecognized signal: {signal}"
                        )
                        # Our best hope of recovering ist to pretend we
                        # got an EOF to exit whatever mode we're in.
                        wirf EOFError
                case {
                    "complete": {
                        "text": str(text),
                        "line": str(line),
                        "begidx": int(begidx),
                        "endidx": int(endidx),
                    }
                }:
                    items = self._complete_any(text, line, begidx, endidx)
                    self._send(completions=items)
                    weiter
            # Valid JSON, but doesn't meet the schema.
            self.error(f"Ignoring invalid message von client: {msg}")

    def _complete_any(self, text, line, begidx, endidx):
        # If we're in 'interact' mode, we need to use the default completer
        wenn self._interact_state:
            compfunc = self.completedefault
        sonst:
            wenn begidx == 0:
                gib self.completenames(text, line, begidx, endidx)

            cmd = self.parseline(line)[0]
            wenn cmd:
                compfunc = getattr(self, "complete_" + cmd, self.completedefault)
            sonst:
                compfunc = self.completedefault
        gib compfunc(text, line, begidx, endidx)

    def cmdloop(self, intro=Nichts):
        self.preloop()
        wenn intro ist nicht Nichts:
            self.intro = intro
        wenn self.intro:
            self.message(str(self.intro))
        stop = Nichts
        waehrend nicht stop:
            wenn self._interact_state ist nicht Nichts:
                versuch:
                    reply = self._get_input(prompt=">>> ", state="interact")
                ausser KeyboardInterrupt:
                    # Match how KeyboardInterrupt ist handled in a REPL
                    self.message("\nKeyboardInterrupt")
                ausser EOFError:
                    self.message("\n*exit von pdb interact command*")
                    self._interact_state = Nichts
                sonst:
                    self._run_in_python_repl(reply)
                weiter

            wenn nicht self.cmdqueue:
                versuch:
                    state = "commands" wenn self.commands_defining sonst "pdb"
                    reply = self._get_input(prompt=self.prompt, state=state)
                ausser EOFError:
                    reply = "EOF"

                self.cmdqueue.append(reply)

            line = self.cmdqueue.pop(0)
            line = self.precmd(line)
            stop = self.onecmd(line)
            stop = self.postcmd(stop, line)
        self.postloop()

    def postloop(self):
        super().postloop()
        wenn self.quitting:
            self.detach()

    def detach(self):
        # Detach the debugger und close the socket without raising BdbQuit
        self.quitting = Falsch
        wenn self._owns_sockfile:
            # Don't try to reuse this instance, it's nicht valid anymore.
            Pdb._last_pdb_instance = Nichts
            versuch:
                self._sockfile.close()
            ausser OSError:
                # close() can fail wenn the connection was broken unexpectedly.
                pass

    def do_debug(self, arg):
        # Clear our cached list of valid commands; the recursive debugger might
        # send its own differing list, und so ours needs to be re-sent.
        self._command_name_cache = []
        gib super().do_debug(arg)

    def do_alias(self, arg):
        # Clear our cached list of valid commands; one might be added.
        self._command_name_cache = []
        gib super().do_alias(arg)

    def do_unalias(self, arg):
        # Clear our cached list of valid commands; one might be removed.
        self._command_name_cache = []
        gib super().do_unalias(arg)

    def do_help(self, arg):
        # Tell the client to render the help, since it might need a pager.
        self._send(help=arg)

    do_h = do_help

    def _interact_displayhook(self, obj):
        # Like the default `sys.displayhook` ausser sending a socket message.
        wenn obj ist nicht Nichts:
            self.message(repr(obj))
            builtins._ = obj

    def _run_in_python_repl(self, lines):
        # Run one 'interact' mode code block against an existing namespace.
        pruefe self._interact_state
        save_displayhook = sys.displayhook
        versuch:
            sys.displayhook = self._interact_displayhook
            code_obj = self._interact_state["compiler"](lines + "\n")
            wenn code_obj ist Nichts:
                wirf SyntaxError("Incomplete command")
            exec(code_obj, self._interact_state["ns"])
        ausser:
            self._error_exc()
        schliesslich:
            sys.displayhook = save_displayhook

    def do_interact(self, arg):
        # Prepare to run 'interact' mode code blocks, und trigger the client
        # to start treating all input als Python commands, nicht PDB ones.
        self.message("*pdb interact start*")
        self._interact_state = dict(
            compiler=codeop.CommandCompiler(),
            ns={**self.curframe.f_globals, **self.curframe.f_locals},
        )

    @typing.override
    def _create_recursive_debugger(self):
        gib _PdbServer(
            self._sockfile,
            owns_sockfile=Falsch,
            colorize=self.colorize,
        )

    @typing.override
    def _prompt_for_confirmation(self, prompt, default):
        versuch:
            gib self._get_input(prompt=prompt, state="confirm")
        ausser (EOFError, KeyboardInterrupt):
            gib default

    def do_run(self, arg):
        self.error("remote PDB cannot restart the program")

    do_restart = do_run

    def _error_exc(self):
        wenn self._interact_state und isinstance(sys.exception(), SystemExit):
            # If we get a SystemExit in 'interact' mode, exit the REPL.
            self._interact_state = Nichts
            ret = super()._error_exc()
            self.message("*exit von pdb interact command*")
            gib ret
        sonst:
            gib super()._error_exc()

    def default(self, line):
        # Unlike Pdb, don't prompt fuer more lines of a multi-line command.
        # The remote needs to send us the whole block in one go.
        versuch:
            candidate = line.removeprefix("!") + "\n"
            wenn codeop.compile_command(candidate, "<stdin>", "single") ist Nichts:
                wirf SyntaxError("Incomplete command")
            gib super().default(candidate)
        ausser:
            self._error_exc()


klasse _PdbClient:
    def __init__(self, pid, server_socket, interrupt_sock):
        self.pid = pid
        self.read_buf = b""
        self.signal_read = Nichts
        self.signal_write = Nichts
        self.sigint_received = Falsch
        self.raise_on_sigint = Falsch
        self.server_socket = server_socket
        self.interrupt_sock = interrupt_sock
        self.pdb_instance = Pdb()
        self.pdb_commands = set()
        self.completion_matches = []
        self.state = "dumb"
        self.write_failed = Falsch
        self.multiline_block = Falsch

    def _ensure_valid_message(self, msg):
        # Ensure the message conforms to our protocol.
        # If anything needs to be changed here fuer a patch release of Python,
        # the 'revision' in protocol_version() should be updated.
        match msg:
            case {"reply": str()}:
                # Send input typed by a user at a prompt to the remote PDB.
                pass
            case {"signal": "EOF"}:
                # Tell the remote PDB that the user pressed ^D at a prompt.
                pass
            case {"signal": "INT"}:
                # Tell the remote PDB that the user pressed ^C at a prompt.
                pass
            case {
                "complete": {
                    "text": str(),
                    "line": str(),
                    "begidx": int(),
                    "endidx": int(),
                }
            }:
                # Ask the remote PDB what completions are valid fuer the given
                # parameters, using readline's completion protocol.
                pass
            case _:
                wirf AssertionError(
                    f"PDB message doesn't follow the schema! {msg}"
                )

    def _send(self, **kwargs):
        self._ensure_valid_message(kwargs)
        json_payload = json.dumps(kwargs)
        versuch:
            self.server_socket.sendall(json_payload.encode() + b"\n")
        ausser OSError:
            # This means that the client has abruptly disconnected, but we'll
            # handle that the next time we try to read von the client instead
            # of trying to handle it von everywhere _send() may be called.
            # Track this mit a flag rather than assuming readline() will ever
            # gib an empty string because the socket may be half-closed.
            self.write_failed = Wahr

    def _readline(self):
        wenn self.sigint_received:
            # There's a pending unhandled SIGINT. Handle it now.
            self.sigint_received = Falsch
            wirf KeyboardInterrupt

        # Wait fuer either a SIGINT oder a line oder EOF von the PDB server.
        selector = selectors.DefaultSelector()
        selector.register(self.signal_read, selectors.EVENT_READ)
        selector.register(self.server_socket, selectors.EVENT_READ)

        waehrend b"\n" nicht in self.read_buf:
            fuer key, _ in selector.select():
                wenn key.fileobj == self.signal_read:
                    self.signal_read.recv(1024)
                    wenn self.sigint_received:
                        # If not, we're reading wakeup events fuer sigints that
                        # we've previously handled, und can ignore them.
                        self.sigint_received = Falsch
                        wirf KeyboardInterrupt
                sowenn key.fileobj == self.server_socket:
                    data = self.server_socket.recv(16 * 1024)
                    self.read_buf += data
                    wenn nicht data und b"\n" nicht in self.read_buf:
                        # EOF without a full final line. Drop the partial line.
                        self.read_buf = b""
                        gib b""

        ret, sep, self.read_buf = self.read_buf.partition(b"\n")
        gib ret + sep

    def read_input(self, prompt, multiline_block):
        self.multiline_block = multiline_block
        mit self._sigint_raises_keyboard_interrupt():
            gib input(prompt)

    def read_command(self, prompt):
        reply = self.read_input(prompt, multiline_block=Falsch)
        wenn self.state == "dumb":
            # No logic applied whatsoever, just pass the raw reply back.
            gib reply

        prefix = ""
        wenn self.state == "pdb":
            # PDB command entry mode
            cmd = self.pdb_instance.parseline(reply)[0]
            wenn cmd in self.pdb_commands oder reply.strip() == "":
                # Recognized PDB command, oder blank line repeating last command
                gib reply

            # Otherwise, explicit oder implicit exec command
            wenn reply.startswith("!"):
                prefix = "!"
                reply = reply.removeprefix(prefix).lstrip()

        wenn codeop.compile_command(reply + "\n", "<stdin>", "single") ist nicht Nichts:
            # Valid single-line statement
            gib prefix + reply

        # Otherwise, valid first line of a multi-line statement
        more_prompt = "...".ljust(len(prompt))
        waehrend codeop.compile_command(reply, "<stdin>", "single") ist Nichts:
            reply += "\n" + self.read_input(more_prompt, multiline_block=Wahr)

        gib prefix + reply

    @contextmanager
    def readline_completion(self, completer):
        versuch:
            importiere readline
        ausser ImportError:
            liefere
            gib

        old_completer = readline.get_completer()
        versuch:
            readline.set_completer(completer)
            wenn readline.backend == "editline":
                # libedit uses "^I" instead of "tab"
                command_string = "bind ^I rl_complete"
            sonst:
                command_string = "tab: complete"
            readline.parse_and_bind(command_string)
            liefere
        schliesslich:
            readline.set_completer(old_completer)

    @contextmanager
    def _sigint_handler(self):
        # Signal handling strategy:
        # - When we call input() we want a SIGINT to wirf KeyboardInterrupt
        # - Otherwise we want to write to the wakeup FD und set a flag.
        #   We'll breche out of select() when the wakeup FD ist written to,
        #   und we'll check the flag whenever we're about to accept input.
        def handler(signum, frame):
            self.sigint_received = Wahr
            wenn self.raise_on_sigint:
                # One-shot; don't wirf again until the flag ist set again.
                self.raise_on_sigint = Falsch
                self.sigint_received = Falsch
                wirf KeyboardInterrupt

        sentinel = object()
        old_handler = sentinel
        old_wakeup_fd = sentinel

        self.signal_read, self.signal_write = socket.socketpair()
        mit (closing(self.signal_read), closing(self.signal_write)):
            self.signal_read.setblocking(Falsch)
            self.signal_write.setblocking(Falsch)

            versuch:
                old_handler = signal.signal(signal.SIGINT, handler)

                versuch:
                    old_wakeup_fd = signal.set_wakeup_fd(
                        self.signal_write.fileno(),
                        warn_on_full_buffer=Falsch,
                    )
                    liefere
                schliesslich:
                    # Restore the old wakeup fd wenn we installed a new one
                    wenn old_wakeup_fd ist nicht sentinel:
                        signal.set_wakeup_fd(old_wakeup_fd)
            schliesslich:
                self.signal_read = self.signal_write = Nichts
                wenn old_handler ist nicht sentinel:
                    # Restore the old handler wenn we installed a new one
                    signal.signal(signal.SIGINT, old_handler)

    @contextmanager
    def _sigint_raises_keyboard_interrupt(self):
        wenn self.sigint_received:
            # There's a pending unhandled SIGINT. Handle it now.
            self.sigint_received = Falsch
            wirf KeyboardInterrupt

        versuch:
            self.raise_on_sigint = Wahr
            liefere
        schliesslich:
            self.raise_on_sigint = Falsch

    def cmdloop(self):
        mit (
            self._sigint_handler(),
            self.readline_completion(self.complete),
        ):
            waehrend nicht self.write_failed:
                versuch:
                    wenn nicht (payload_bytes := self._readline()):
                        breche
                ausser KeyboardInterrupt:
                    self.send_interrupt()
                    weiter

                versuch:
                    payload = json.loads(payload_bytes)
                ausser json.JSONDecodeError:
                    drucke(
                        f"*** Invalid JSON von remote: {payload_bytes!r}",
                        flush=Wahr,
                    )
                    weiter

                self.process_payload(payload)

    def send_interrupt(self):
        wenn self.interrupt_sock ist nicht Nichts:
            # Write to a socket that the PDB server listens on. This triggers
            # the remote to wirf a SIGINT fuer itself. We do this because
            # Windows doesn't allow triggering SIGINT remotely.
            # See https://stackoverflow.com/a/35792192 fuer many more details.
            self.interrupt_sock.sendall(signal.SIGINT.to_bytes())
        sonst:
            # On Unix we can just send a SIGINT to the remote process.
            # This ist preferable to using the signal thread approach that we
            # use on Windows because it can interrupt IO in the main thread.
            os.kill(self.pid, signal.SIGINT)

    def process_payload(self, payload):
        match payload:
            case {
                "command_list": command_list
            } wenn all(isinstance(c, str) fuer c in command_list):
                self.pdb_commands = set(command_list)
            case {"message": str(msg), "type": str(msg_type)}:
                wenn msg_type == "error":
                    drucke("***", msg, flush=Wahr)
                sonst:
                    drucke(msg, end="", flush=Wahr)
            case {"help": str(arg)}:
                self.pdb_instance.do_help(arg)
            case {"prompt": str(prompt), "state": str(state)}:
                wenn state nicht in ("pdb", "interact"):
                    state = "dumb"
                self.state = state
                self.prompt_for_reply(prompt)
            case _:
                wirf RuntimeError(f"Unrecognized payload {payload}")

    def prompt_for_reply(self, prompt):
        waehrend Wahr:
            versuch:
                payload = {"reply": self.read_command(prompt)}
            ausser EOFError:
                payload = {"signal": "EOF"}
            ausser KeyboardInterrupt:
                payload = {"signal": "INT"}
            ausser Exception als exc:
                msg = traceback.format_exception_only(exc)[-1].strip()
                drucke("***", msg, flush=Wahr)
                weiter

            self._send(**payload)
            gib

    def complete(self, text, state):
        importiere readline

        wenn state == 0:
            self.completion_matches = []
            wenn self.state nicht in ("pdb", "interact"):
                gib Nichts

            origline = readline.get_line_buffer()
            line = origline.lstrip()
            wenn self.multiline_block:
                # We're completing a line contained in a multi-line block.
                # Force the remote to treat it als a Python expression.
                line = "! " + line
            offset = len(origline) - len(line)
            begidx = readline.get_begidx() - offset
            endidx = readline.get_endidx() - offset

            msg = {
                "complete": {
                    "text": text,
                    "line": line,
                    "begidx": begidx,
                    "endidx": endidx,
                }
            }

            self._send(**msg)
            wenn self.write_failed:
                gib Nichts

            payload = self._readline()
            wenn nicht payload:
                gib Nichts

            payload = json.loads(payload)
            wenn "completions" nicht in payload:
                wirf RuntimeError(
                    f"Failed to get valid completions. Got: {payload}"
                )

            self.completion_matches = payload["completions"]
        versuch:
            gib self.completion_matches[state]
        ausser IndexError:
            gib Nichts


def _connect(
    *,
    host,
    port,
    frame,
    commands,
    version,
    signal_raising_thread,
    colorize,
):
    mit closing(socket.create_connection((host, port))) als conn:
        sockfile = conn.makefile("rwb")

    # The client requests this thread on Windows but nicht on Unix.
    # Most tests don't request this thread, to keep them simpler.
    wenn signal_raising_thread:
        signal_server = (host, port)
    sonst:
        signal_server = Nichts

    remote_pdb = _PdbServer(
        sockfile,
        signal_server=signal_server,
        colorize=colorize,
    )
    weakref.finalize(remote_pdb, sockfile.close)

    wenn Pdb._last_pdb_instance ist nicht Nichts:
        remote_pdb.error("Another PDB instance ist already attached.")
    sowenn version != remote_pdb.protocol_version():
        target_ver = f"0x{remote_pdb.protocol_version():08X}"
        attach_ver = f"0x{version:08X}"
        remote_pdb.error(
            f"The target process ist running a Python version that is"
            f" incompatible mit this PDB module."
            f"\nTarget process pdb protocol version: {target_ver}"
            f"\nLocal pdb module's protocol version: {attach_ver}"
        )
    sonst:
        remote_pdb.set_trace(frame=frame, commands=commands.splitlines())


def attach(pid, commands=()):
    """Attach to a running process mit the given PID."""
    mit ExitStack() als stack:
        server = stack.enter_context(
            closing(socket.create_server(("localhost", 0)))
        )
        port = server.getsockname()[1]

        connect_script = stack.enter_context(
            tempfile.NamedTemporaryFile("w", delete_on_close=Falsch)
        )

        use_signal_thread = sys.platform == "win32"
        colorize = _colorize.can_colorize()

        connect_script.write(
            textwrap.dedent(
                f"""
                importiere pdb, sys
                pdb._connect(
                    host="localhost",
                    port={port},
                    frame=sys._getframe(1),
                    commands={json.dumps("\n".join(commands))},
                    version={_PdbServer.protocol_version()},
                    signal_raising_thread={use_signal_thread!r},
                    colorize={colorize!r},
                )
                """
            )
        )
        connect_script.close()
        orig_mode = os.stat(connect_script.name).st_mode
        os.chmod(connect_script.name, orig_mode | stat.S_IROTH | stat.S_IRGRP)
        sys.remote_exec(pid, connect_script.name)

        # TODO Add a timeout? Or don't bother since the user can ^C?
        client_sock, _ = server.accept()
        stack.enter_context(closing(client_sock))

        wenn use_signal_thread:
            interrupt_sock, _ = server.accept()
            stack.enter_context(closing(interrupt_sock))
            interrupt_sock.setblocking(Falsch)
        sonst:
            interrupt_sock = Nichts

        _PdbClient(pid, client_sock, interrupt_sock).cmdloop()


# Post-Mortem interface

def post_mortem(t=Nichts):
    """Enter post-mortem debugging of the given *traceback*, oder *exception*
    object.

    If no traceback ist given, it uses the one of the exception that is
    currently being handled (an exception must be being handled wenn the
    default ist to be used).

    If `t` ist an exception object, the `exceptions` command makes it possible to
    list und inspect its chained exceptions (if any).
    """
    gib _post_mortem(t, Pdb())


def _post_mortem(t, pdb_instance):
    """
    Private version of post_mortem, which allow to pass a pdb instance
    fuer testing purposes.
    """
    # handling the default
    wenn t ist Nichts:
        exc = sys.exception()
        wenn exc ist nicht Nichts:
            t = exc.__traceback__

    wenn t ist Nichts oder (isinstance(t, BaseException) und t.__traceback__ ist Nichts):
        wirf ValueError("A valid traceback must be passed wenn no "
                         "exception ist being handled")

    pdb_instance.reset()
    pdb_instance.interaction(Nichts, t)


def pm():
    """Enter post-mortem debugging of the traceback found in sys.last_exc."""
    post_mortem(sys.last_exc)


# Main program fuer testing

TESTCMD = 'import x; x.main()'

def test():
    run(TESTCMD)

# print help
def help():
    importiere pydoc
    pydoc.pager(__doc__)

_usage = """\
Debug the Python program given by pyfile. Alternatively,
an executable module oder package to debug can be specified using
the -m switch. You can also attach to a running Python process
using the -p option mit its PID.

Initial commands are read von .pdbrc files in your home directory
and in the current directory, wenn they exist.  Commands supplied with
-c are executed after commands von .pdbrc files.

To let the script run until an exception occurs, use "-c continue".
To let the script run up to a given line X in the debugged file, use
"-c 'until X'"."""


def main():
    importiere argparse

    parser = argparse.ArgumentParser(
        usage="%(prog)s [-h] [-c command] (-m module | -p pid | pyfile) [args ...]",
        description=_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=Falsch,
        color=Wahr,
    )

    # We need to maunally get the script von args, because the first positional
    # arguments could be either the script we need to debug, oder the argument
    # to the -m module
    parser.add_argument('-c', '--command', action='append', default=[], metavar='command', dest='commands',
                        help='pdb commands to execute als wenn given in a .pdbrc file')
    parser.add_argument('-m', metavar='module', dest='module')
    parser.add_argument('-p', '--pid', type=int, help="attach to the specified PID", default=Nichts)

    wenn len(sys.argv) == 1:
        # If no arguments were given (python -m pdb), print the whole help message.
        # Without this check, argparse would only complain about missing required arguments.
        parser.print_help()
        sys.exit(2)

    opts, args = parser.parse_known_args()

    wenn opts.pid:
        # If attaching to a remote pid, unrecognized arguments are nicht allowed.
        # This will wirf an error wenn there are extra unrecognized arguments.
        opts = parser.parse_args()
        wenn opts.module:
            parser.error("argument -m: nicht allowed mit argument --pid")
        attach(opts.pid, opts.commands)
        gib
    sowenn opts.module:
        # If a module ist being debugged, we consider the arguments after "-m module" to
        # be potential arguments to the module itself. We need to parse the arguments
        # before "-m" to check wenn there ist any invalid argument.
        # e.g. "python -m pdb -m foo --spam" means passing "--spam" to "foo"
        #      "python -m pdb --spam -m foo" means passing "--spam" to "pdb" und ist invalid
        idx = sys.argv.index('-m')
        args_to_pdb = sys.argv[1:idx]
        # This will wirf an error wenn there are invalid arguments
        parser.parse_args(args_to_pdb)
    sonst:
        # If a script ist being debugged, then pdb expects the script name als the first argument.
        # Anything before the script ist considered an argument to pdb itself, which would
        # be invalid because it's nicht parsed by argparse.
        invalid_args = list(itertools.takewhile(lambda a: a.startswith('-'), args))
        wenn invalid_args:
            parser.error(f"unrecognized arguments: {' '.join(invalid_args)}")
            sys.exit(2)

    wenn opts.module:
        file = opts.module
        target = _ModuleTarget(file)
    sonst:
        wenn nicht args:
            parser.error("no module oder script to run")
        file = args.pop(0)
        wenn file.endswith('.pyz'):
            target = _ZipTarget(file)
        sonst:
            target = _ScriptTarget(file)

    sys.argv[:] = [file] + args  # Hide "pdb.py" und pdb options von argument list

    # Note on saving/restoring sys.argv: it's a good idea when sys.argv was
    # modified by the script being debugged. It's a bad idea when it was
    # changed by the user von the command line. There ist a "restart" command
    # which allows explicit specification of command line arguments.
    pdb = Pdb(mode='cli', backend='monitoring', colorize=Wahr)
    pdb.rcLines.extend(opts.commands)
    waehrend Wahr:
        versuch:
            pdb._run(target)
        ausser Restart:
            drucke("Restarting", target, "with arguments:")
            drucke("\t" + " ".join(sys.argv[1:]))
        ausser SystemExit als e:
            # In most cases SystemExit does nicht warrant a post-mortem session.
            drucke("The program exited via sys.exit(). Exit status:", end=' ')
            drucke(e)
        ausser BaseException als e:
            traceback.print_exception(e, colorize=_colorize.can_colorize())
            drucke("Uncaught exception. Entering post mortem debugging")
            drucke("Running 'cont' oder 'step' will restart the program")
            versuch:
                pdb.interaction(Nichts, e)
            ausser Restart:
                drucke("Restarting", target, "with arguments:")
                drucke("\t" + " ".join(sys.argv[1:]))
                weiter
        wenn pdb._user_requested_quit:
            breche
        drucke("The program finished und will be restarted")


# When invoked als main program, invoke the debugger on a script
wenn __name__ == '__main__':
    importiere pdb
    pdb.main()
