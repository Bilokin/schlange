"""
The Python Debugger Pdb
=======================

To use the debugger in its simplest form:

        >>> importiere pdb
        >>> pdb.run('<a statement>')

The debugger's prompt is '(Pdb) '.  This will stop in the first
function call in <a statement>.

Alternatively, wenn a statement terminated with an unhandled exception,
you can use pdb's post-mortem facility to inspect the contents of the
traceback:

        >>> <a statement>
        <exception traceback>
        >>> importiere pdb
        >>> pdb.pm()

The commands recognized by the debugger are listed in the next
section.  Most can be abbreviated as indicated; e.g., h(elp) means
that 'help' can be typed as 'h' or 'help' (but not as 'he' or 'hel',
nor as 'H' or 'Help' or 'HELP').  Optional arguments are enclosed in
square brackets.  Alternatives in the command syntax are separated
by a vertical bar (|).

A blank line repeats the previous command literally, except for
'list', where it lists the next 11 lines.

Commands that the debugger doesn't recognize are assumed to be Python
statements and are executed in the context of the program being
debugged.  Python statements can also be prefixed with an exclamation
point ('!').  This is a powerful way to inspect the program being
debugged; it is even possible to change variables or call functions.
When an exception occurs in such a statement, the exception name is
printed but the debugger's state is not changed.

The debugger supports aliases, which can save typing.  And aliases can
have parameters (see the alias help entry) which allows one a certain
level of adaptability to the context under examination.

Multiple commands may be entered on a single line, separated by the
pair ';;'.  No intelligence is applied to separating the commands; the
input is split at the first ';;', even wenn it is in the middle of a
quoted string.

If a file ".pdbrc" exists in your home directory or in the current
directory, it is read in and executed as wenn it had been typed at the
debugger prompt.  This is particularly useful fuer aliases.  If both
files exist, the one in the home directory is read first and aliases
defined there can be overridden by the local file.  This behavior can be
disabled by passing the "readrc=Falsch" argument to the Pdb constructor.

Aside von aliases, the debugger is not directly programmable; but it
is implemented as a klasse von which you can derive your own debugger
klasse, which you can make as fancy as you like.


Debugger commands
=================

"""
# NOTE: the actual command documentation is collected von docstrings of the
# commands and is appended to __doc__ after the klasse has been defined.

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

    Return code.co_firstlineno wenn no executable line is found.
    """
    prev = Nichts
    fuer instr in dis.get_instructions(code):
        wenn prev is not Nichts and prev.opname == 'RESUME':
            wenn instr.positions.lineno is not Nichts:
                return instr.positions.lineno
            return code.co_firstlineno
        prev = instr
    return code.co_firstlineno

def find_function(funcname, filename):
    cre = re.compile(r'def\s+%s(\s*\[.+\])?\s*[(]' % re.escape(funcname))
    try:
        fp = tokenize.open(filename)
    except OSError:
        lines = linecache.getlines(filename)
        wenn not lines:
            return Nichts
        fp = io.StringIO(''.join(lines))
    funcdef = ""
    funcstart = 0
    # consumer of this info expects the first line to be 1
    with fp:
        fuer lineno, line in enumerate(fp, start=1):
            wenn cre.match(line):
                funcstart, funcdef = lineno, line
            sowenn funcdef:
                funcdef += line

            wenn funcdef:
                try:
                    code = compile(funcdef, filename, 'exec')
                except SyntaxError:
                    continue
                # We should always be able to find the code object here
                funccode = next(c fuer c in code.co_consts if
                                isinstance(c, CodeType) and c.co_name == funcname)
                lineno_offset = find_first_executable_line(funccode)
                return funcname, filename, funcstart + lineno_offset - 1
    return Nichts

def lasti2lineno(code, lasti):
    linestarts = list(dis.findlinestarts(code))
    linestarts.reverse()
    fuer i, lineno in linestarts:
        wenn lasti >= i:
            return lineno
    return 0


klasse _rstr(str):
    """String that doesn't quote its repr."""
    def __repr__(self):
        return self


klasse _ExecutableTarget:
    filename: str
    code: CodeType | str
    namespace: dict


klasse _ScriptTarget(_ExecutableTarget):
    def __init__(self, target):
        self._target = os.path.realpath(target)

        wenn not os.path.exists(self._target):
            drucke(f'Error: {target} does not exist')
            sys.exit(1)
        wenn os.path.isdir(self._target):
            drucke(f'Error: {target} is a directory')
            sys.exit(1)

        # If safe_path(-P) is not set, sys.path[0] is the directory
        # of pdb, and we should replace it with the directory of the script
        wenn not sys.flags.safe_path:
            sys.path[0] = os.path.dirname(self._target)

    def __repr__(self):
        return self._target

    @property
    def filename(self):
        return self._target

    @property
    def code(self):
        # Open the file each time because the file may be modified
        with io.open_code(self._target) as fp:
            return f"exec(compile({fp.read()!r}, {self._target!r}, 'exec'))"

    @property
    def namespace(self):
        return dict(
            __name__='__main__',
            __file__=self._target,
            __builtins__=__builtins__,
            __spec__=Nichts,
        )


klasse _ModuleTarget(_ExecutableTarget):
    def __init__(self, target):
        self._target = target

        importiere runpy
        try:
            _, self._spec, self._code = runpy._get_module_details(self._target)
        except ImportError as e:
            drucke(f"ImportError: {e}")
            sys.exit(1)
        except Exception:
            traceback.print_exc()
            sys.exit(1)

    def __repr__(self):
        return self._target

    @property
    def filename(self):
        return self._code.co_filename

    @property
    def code(self):
        return self._code

    @property
    def namespace(self):
        return dict(
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
        try:
            _, self._spec, self._code = runpy._get_main_module_details()
        except ImportError as e:
            drucke(f"ImportError: {e}")
            sys.exit(1)
        except Exception:
            traceback.print_exc()
            sys.exit(1)

    def __repr__(self):
        return self._target

    @property
    def filename(self):
        return self._code.co_filename

    @property
    def code(self):
        return self._code

    @property
    def namespace(self):
        return dict(
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


# Interaction prompt line will separate file and call info von code
# text using value of line_prefix string.  A newline and arrow may
# be to your liking.  You can set it once pdb is imported using the
# command "pdb.line_prefix = '\n% '".
# line_prefix = ': '    # Use this to get the old situation back
line_prefix = '\n-> '   # Probably a better default


# The default backend to use fuer Pdb instances wenn not specified
# Should be either 'settrace' or 'monitoring'
_default_backend = 'settrace'


def set_default_backend(backend):
    """Set the default backend to use fuer Pdb instances."""
    global _default_backend
    wenn backend not in ('settrace', 'monitoring'):
        raise ValueError("Invalid backend: %s" % backend)
    _default_backend = backend


def get_default_backend():
    """Get the default backend to use fuer Pdb instances."""
    return _default_backend


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
        self.colorize = colorize and _colorize.can_colorize(file=stdout or sys.stdout)
        # Try to load readline wenn it exists
        try:
            importiere readline
            # remove some common file name delimiters
            readline.set_completer_delims(' \t\n`@#%^&*()=+[{]}\\|;:\'",<>?')
        except ImportError:
            pass
        self.allow_kbdint = Falsch
        self.nosigint = nosigint
        # Consider these characters as part of the command so when the users type
        # c.a or c['a'], it won't be recognized as a c(ontinue) command
        self.identchars = cmd.Cmd.identchars + '=.[](),"\'+-*/%@&|<>~^'

        # Read ~/.pdbrc and ./.pdbrc
        self.rcLines = []
        wenn readrc:
            try:
                with open(os.path.expanduser('~/.pdbrc'), encoding='utf-8') as rcFile:
                    self.rcLines.extend(rcFile)
            except OSError:
                pass
            try:
                with open(".pdbrc", encoding='utf-8') as rcFile:
                    self.rcLines.extend(rcFile)
            except OSError:
                pass

        self.commands = {} # associates a command list to breakpoint numbers
        self.commands_defining = Falsch # Wahr while in the process of defining
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
        wenn frame is Nichts:
            frame = sys._getframe().f_back

        wenn commands is not Nichts:
            self.rcLines.extend(commands)

        super().set_trace(frame)

    async def set_trace_async(self, frame=Nichts, *, commands=Nichts):
        wenn self.async_awaitable is not Nichts:
            # We are already in a set_trace_async call, do not mess with it
            return

        wenn frame is Nichts:
            frame = sys._getframe().f_back

        # We need set_trace to set up the basics, however, this will call
        # set_stepinstr() will we need to compensate for, because we don't
        # want to trigger on calls
        self.set_trace(frame, commands=commands)
        # Changing the stopframe will disable trace dispatch on calls
        self.stopframe = frame
        # We need to stop tracing because we don't have the privilege to avoid
        # triggering tracing functions as normal, as we are not already in
        # tracing functions
        self.stop_trace()

        self.async_shim_frame = sys._getframe()
        self.async_awaitable = Nichts

        while Wahr:
            self.async_awaitable = Nichts
            # Simulate a trace event
            # This should bring up pdb and make pdb believe it's debugging the
            # caller frame
            self.trace_dispatch(frame, "opcode", Nichts)
            wenn self.async_awaitable is not Nichts:
                try:
                    wenn self.breaks:
                        with self.set_enterframe(frame):
                            # set_continue requires enterframe to work
                            self.set_continue()
                        self.start_trace()
                    await self.async_awaitable
                except Exception:
                    self._error_exc()
            sonst:
                break

        self.async_shim_frame = Nichts

        # start the trace (the actual command is already set by set_* calls)
        wenn self.returnframe is Nichts and self.stoplineno == -1 and not self.breaks:
            # This means we did a continue without any breakpoints, we should not
            # start the trace
            return

        self.start_trace()

    def sigint_handler(self, signum, frame):
        wenn self.allow_kbdint:
            raise KeyboardInterrupt
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
        wenn hasattr(self, 'curframe') and self.curframe:
            self.curframe.f_globals.pop('__pdb_convenience_variables', Nichts)
        self.curframe = Nichts
        self.tb_lineno.clear()

    def setup(self, f, tb):
        self.forget()
        self.stack, self.curindex = self.get_stack(f, tb)
        while tb:
            # when setting up post-mortem debugging with a traceback, save all
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
                wenn line.strip() and not line.strip().startswith("#")
            ]
            self.rcLines = []

    @property
    @deprecated("The frame locals reference is no longer cached. Use 'curframe.f_locals' instead.")
    def curframe_locals(self):
        return self.curframe.f_locals

    @curframe_locals.setter
    @deprecated("Setting 'curframe_locals' no longer has any effect. Update the contents of 'curframe.f_locals' instead.")
    def curframe_locals(self, value):
        pass

    # Override Bdb methods

    def user_call(self, frame, argument_list):
        """This method is called when there is the remote possibility
        that we ever need to stop in this function."""
        wenn self._wait_for_mainpyfile:
            return
        wenn self.stop_here(frame):
            self.message('--Call--')
            self.interaction(frame, Nichts)

    def user_line(self, frame):
        """This function is called when we stop or break at this line."""
        wenn self._wait_for_mainpyfile:
            wenn (self.mainpyfile != self.canonic(frame.f_code.co_filename)):
                return
            self._wait_for_mainpyfile = Falsch
        wenn self.trace_opcodes:
            # GH-127321
            # We want to avoid stopping at an opcode that does not have
            # an associated line number because pdb does not like it
            wenn frame.f_lineno is Nichts:
                self.set_stepinstr()
                return
        self.bp_commands(frame)
        self.interaction(frame, Nichts)

    user_opcode = user_line

    def bp_commands(self, frame):
        """Call every command that was set fuer the current active breakpoint
        (if there is one).

        Returns Wahr wenn the normal interaction function must be called,
        Falsch otherwise."""
        # self.currentbp is set in bdb in Bdb.break_here wenn a breakpoint was hit
        wenn getattr(self, "currentbp", Falsch) and \
               self.currentbp in self.commands:
            currentbp = self.currentbp
            self.currentbp = 0
            fuer line in self.commands[currentbp]:
                self.cmdqueue.append(line)
            self.cmdqueue.append(f'_pdbcmd_restore_lastcmd {self.lastcmd}')

    def user_return(self, frame, return_value):
        """This function is called when a return trap is set here."""
        wenn self._wait_for_mainpyfile:
            return
        frame.f_locals['__return__'] = return_value
        self.set_convenience_variable(frame, '_retval', return_value)
        self.message('--Return--')
        self.interaction(frame, Nichts)

    def user_exception(self, frame, exc_info):
        """This function is called wenn an exception occurs,
        but only wenn we are to stop at or just below this level."""
        wenn self._wait_for_mainpyfile:
            return
        exc_type, exc_value, exc_traceback = exc_info
        frame.f_locals['__exception__'] = exc_type, exc_value
        self.set_convenience_variable(frame, '_exception', exc_value)

        # An 'Internal StopIteration' exception is an exception debug event
        # issued by the interpreter when handling a subgenerator run with
        # 'yield from' or a generator controlled by a fuer loop. No exception has
        # actually occurred in this case. The debugger uses this debug event to
        # stop when the debuggee is returning von such generators.
        prefix = 'Internal ' wenn (not exc_traceback
                                    and exc_type is StopIteration) sonst ''
        self.message('%s%s' % (prefix, self._format_exc(exc_value)))
        self.interaction(frame, exc_traceback)

    # General interaction function
    def _cmdloop(self):
        while Wahr:
            try:
                # keyboard interrupts allow fuer an easy way to cancel
                # the current command, so allow them during interactive input
                self.allow_kbdint = Wahr
                self.cmdloop()
                self.allow_kbdint = Falsch
                break
            except KeyboardInterrupt:
                self.message('--KeyboardInterrupt--')

    def _save_initial_file_mtime(self, frame):
        """save the mtime of the all the files in the frame stack in the file mtime table
        wenn they haven't been saved yet."""
        while frame:
            filename = frame.f_code.co_filename
            wenn filename not in self._file_mtime_table:
                try:
                    self._file_mtime_table[filename] = os.path.getmtime(filename)
                except Exception:
                    pass
            frame = frame.f_back

    def _validate_file_mtime(self):
        """Check wenn the source file of the current frame has been modified.
        If so, give a warning and reset the modify time to current."""
        try:
            filename = self.curframe.f_code.co_filename
            mtime = os.path.getmtime(filename)
        except Exception:
            return
        wenn (filename in self._file_mtime_table and
            mtime != self._file_mtime_table[filename]):
            self.message(f"*** WARNING: file '{filename}' was edited, "
                         "running stale code until the program is rerun")
            self._file_mtime_table[filename] = mtime

    # Called before loop, handles display expressions
    # Set up convenience variable containers
    def _show_display(self):
        displaying = self.displaying.get(self.curframe)
        wenn displaying:
            fuer expr, oldvalue in displaying.items():
                newvalue = self._getval_except(expr)
                # check fuer identity first; this prevents custom __eq__ to
                # be called at every loop, and also prevents instances whose
                # fields are changed to be displayed
                wenn newvalue is not oldvalue and newvalue != oldvalue:
                    displaying[expr] = newvalue
                    self.message('display %s: %s  [old: %s]' %
                                 (expr, self._safe_repr(newvalue, expr),
                                  self._safe_repr(oldvalue, expr)))

    def _get_tb_and_exceptions(self, tb_or_exc):
        """
        Given a tracecack or an exception, return a tuple of chained exceptions
        and current traceback to inspect.

        This will deal with selecting the right ``__cause__`` or ``__context__``
        as well as handling cycles, and return a flattened list of exceptions we
        can jump to with do_exceptions.

        """
        _exceptions = []
        wenn isinstance(tb_or_exc, BaseException):
            traceback, current = tb_or_exc.__traceback__, tb_or_exc

            while current is not Nichts:
                wenn current in _exceptions:
                    break
                _exceptions.append(current)
                wenn current.__cause__ is not Nichts:
                    current = current.__cause__
                sowenn (
                    current.__context__ is not Nichts and not current.__suppress_context__
                ):
                    current = current.__context__

                wenn len(_exceptions) >= self.MAX_CHAINED_EXCEPTION_DEPTH:
                    self.message(
                        f"More than {self.MAX_CHAINED_EXCEPTION_DEPTH}"
                        " chained exceptions found, not all exceptions"
                        "will be browsable with `exceptions`."
                    )
                    break
        sonst:
            traceback = tb_or_exc
        return tuple(reversed(_exceptions)), traceback

    @contextmanager
    def _hold_exceptions(self, exceptions):
        """
        Context manager to ensure proper cleaning of exceptions references

        When given a chained exception instead of a traceback,
        pdb may hold references to many objects which may leak memory.

        We use this context manager to make sure everything is properly cleaned

        """
        try:
            self._chained_exceptions = exceptions
            self._chained_exception_index = len(exceptions) - 1
            yield
        finally:
            # we can't put those in forget as otherwise they would
            # be cleared on exception change
            self._chained_exceptions = tuple()
            self._chained_exception_index = 0

    def _get_asyncio_task(self):
        try:
            task = asyncio.current_task()
        except RuntimeError:
            task = Nichts
        return task

    def interaction(self, frame, tb_or_exc):
        # Restore the previous signal handler at the Pdb prompt.
        wenn Pdb._previous_sigint_handler:
            try:
                signal.signal(signal.SIGINT, Pdb._previous_sigint_handler)
            except ValueError:  # ValueError: signal only works in main thread
                pass
            sonst:
                Pdb._previous_sigint_handler = Nichts

        self._current_task = self._get_asyncio_task()

        _chained_exceptions, tb = self._get_tb_and_exceptions(tb_or_exc)
        wenn isinstance(tb_or_exc, BaseException):
            assert tb is not Nichts, "main exception must have a traceback"
        with self._hold_exceptions(_chained_exceptions):
            self.setup(frame, tb)
            # We should print the stack entry wenn and only wenn the user input
            # is expected, and we should print it right before the user input.
            # We achieve this by appending _pdbcmd_print_frame_status to the
            # command queue. If cmdqueue is not exhausted, the user input is
            # not expected and we will not print the stack entry.
            self.cmdqueue.append('_pdbcmd_print_frame_status')
            self._cmdloop()
            # If _pdbcmd_print_frame_status is not used, pop it out
            wenn self.cmdqueue and self.cmdqueue[-1] == '_pdbcmd_print_frame_status':
                self.cmdqueue.pop()
            self.forget()

    def displayhook(self, obj):
        """Custom displayhook fuer the exec in default(), which prevents
        assignment of the _ variable in the builtins.
        """
        # reproduce the behavior of the standard displayhook, not printing Nichts
        wenn obj is not Nichts:
            self.message(repr(obj))

    @contextmanager
    def _enable_multiline_input(self):
        try:
            importiere readline
        except ImportError:
            yield
            return

        def input_auto_indent():
            last_index = readline.get_current_history_length()
            last_line = readline.get_history_item(last_index)
            wenn last_line:
                wenn last_line.isspace():
                    # If the last line is empty, we don't need to indent
                    return

                last_line = last_line.rstrip('\r\n')
                indent = len(last_line) - len(last_line.lstrip())
                wenn last_line.endswith(":"):
                    indent += 4
                readline.insert_text(' ' * indent)

        completenames = self.completenames
        try:
            self.completenames = self.complete_multiline_names
            readline.set_startup_hook(input_auto_indent)
            yield
        finally:
            readline.set_startup_hook()
            self.completenames = completenames
        return

    def _exec_in_closure(self, source, globals, locals):
        """ Run source code in closure so code object created within source
            can find variables in locals correctly

            returns Wahr wenn the source is executed, Falsch otherwise
        """

        # Determine wenn the source should be executed in closure. Only when the
        # source compiled to multiple code objects, we should use this feature.
        # Otherwise, we can just raise an exception and normal exec will be used.

        code = compile(source, "<string>", "exec")
        wenn not any(isinstance(const, CodeType) fuer const in code.co_consts):
            return Falsch

        # locals could be a proxy which does not support pop
        # copy it first to avoid modifying the original locals
        locals_copy = dict(locals)

        locals_copy["__pdb_eval__"] = {
            "result": Nichts,
            "write_back": {}
        }

        # If the source is an expression, we need to print its value
        try:
            compile(source, "<string>", "eval")
        except SyntaxError:
            pass
        sonst:
            source = "__pdb_eval__['result'] = " + source

        # Add write-back to update the locals
        source = ("try:\n" +
                  textwrap.indent(source, "  ") + "\n" +
                  "finally:\n" +
                  "  __pdb_eval__['write_back'] = locals()")

        # Build a closure source code with freevars von locals like:
        # def __pdb_outer():
        #   var = Nichts
        #   def __pdb_scope():  # This is the code object we want to execute
        #     nonlocal var
        #     <source>
        #   return __pdb_scope.__code__
        source_with_closure = ("def __pdb_outer():\n" +
                               "\n".join(f"  {var} = Nichts" fuer var in locals_copy) + "\n" +
                               "  def __pdb_scope():\n" +
                               "\n".join(f"    nonlocal {var}" fuer var in locals_copy) + "\n" +
                               textwrap.indent(source, "    ") + "\n" +
                               "  return __pdb_scope.__code__"
                               )

        # Get the code object of __pdb_scope()
        # The exec fills locals_copy with the __pdb_outer() function and we can call
        # that to get the code object of __pdb_scope()
        ns = {}
        try:
            exec(source_with_closure, {}, ns)
        except Exception:
            return Falsch
        code = ns["__pdb_outer"]()

        cells = tuple(types.CellType(locals_copy.get(var)) fuer var in code.co_freevars)

        try:
            exec(code, globals, locals_copy, closure=cells)
        except Exception:
            return Falsch

        # get the data we need von the statement
        pdb_eval = locals_copy["__pdb_eval__"]

        # __pdb_eval__ should not be updated back to locals
        pdb_eval["write_back"].pop("__pdb_eval__")

        # Write all local variables back to locals
        locals.update(pdb_eval["write_back"])
        eval_result = pdb_eval["result"]
        wenn eval_result is not Nichts:
            drucke(repr(eval_result))

        return Wahr

    def _exec_await(self, source, globals, locals):
        """ Run source code that contains await by playing with async shim frame"""
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
        try:
            wenn (code := codeop.compile_command(line + '\n', '<stdin>', 'single')) is Nichts:
                # Multi-line mode
                with self._enable_multiline_input():
                    buffer = line
                    continue_prompt = "...   "
                    while (code := codeop.compile_command(buffer, '<stdin>', 'single')) is Nichts:
                        wenn self.use_rawinput:
                            try:
                                line = input(continue_prompt)
                            except (EOFError, KeyboardInterrupt):
                                self.lastcmd = ""
                                drucke('\n')
                                return Nichts, Nichts, Falsch
                        sonst:
                            self.stdout.write(continue_prompt)
                            self.stdout.flush()
                            line = self.stdin.readline()
                            wenn not len(line):
                                self.lastcmd = ""
                                self.stdout.write('\n')
                                self.stdout.flush()
                                return Nichts, Nichts, Falsch
                            sonst:
                                line = line.rstrip('\r\n')
                        wenn line.isspace():
                            # empty line, just continue
                            buffer += '\n'
                        sonst:
                            buffer += '\n' + line
                    self.lastcmd = buffer
        except SyntaxError as e:
            # Maybe it's an await expression/statement
            wenn (
                self.async_shim_frame is not Nichts
                and e.msg == "'await' outside function"
            ):
                is_await_code = Wahr
            sonst:
                raise

        return code, buffer, is_await_code

    def default(self, line):
        wenn line[:1] == '!': line = line[1:].strip()
        locals = self.curframe.f_locals
        globals = self.curframe.f_globals
        try:
            code, buffer, is_await_code = self._read_code(line)
            wenn buffer is Nichts:
                return
            save_stdout = sys.stdout
            save_stdin = sys.stdin
            save_displayhook = sys.displayhook
            try:
                sys.stdin = self.stdin
                sys.stdout = self.stdout
                sys.displayhook = self.displayhook
                wenn is_await_code:
                    self._exec_await(buffer, globals, locals)
                    return Wahr
                sonst:
                    wenn not self._exec_in_closure(buffer, globals, locals):
                        exec(code, globals, locals)
            finally:
                sys.stdout = save_stdout
                sys.stdin = save_stdin
                sys.displayhook = save_displayhook
        except:
            self._error_exc()

    def _replace_convenience_variables(self, line):
        """Replace the convenience variables in 'line' with their values.
           e.g. $foo is replaced by __pdb_convenience_variables["foo"].
           Note: such pattern in string literals will be skipped"""

        wenn "$" not in line:
            return line

        dollar_start = dollar_end = (-1, -1)
        replace_variables = []
        try:
            fuer t in tokenize.generate_tokens(io.StringIO(line).readline):
                token_type, token_string, start, end, _ = t
                wenn token_type == token.OP and token_string == '$':
                    dollar_start, dollar_end = start, end
                sowenn start == dollar_end and token_type == token.NAME:
                    # line is a one-line command so we only care about column
                    replace_variables.append((dollar_start[1], end[1], token_string))
        except tokenize.TokenError:
            return line

        wenn not replace_variables:
            return line

        last_end = 0
        line_pieces = []
        fuer start, end, name in replace_variables:
            line_pieces.append(line[last_end:start] + f'__pdb_convenience_variables["{name}"]')
            last_end = end
        line_pieces.append(line[last_end:])

        return ''.join(line_pieces)

    def precmd(self, line):
        """Handle alias expansion and ';;' separator."""
        wenn not line.strip():
            return line
        args = line.split()
        while args[0] in self.aliases:
            line = self.aliases[args[0]]
            fuer idx in range(1, 10):
                wenn f'%{idx}' in line:
                    wenn idx >= len(args):
                        self.error(f"Not enough arguments fuer alias '{args[0]}'")
                        # This is a no-op
                        return "!"
                    line = line.replace(f'%{idx}', args[idx])
                sowenn '%*' not in line:
                    wenn idx < len(args):
                        self.error(f"Too many arguments fuer alias '{args[0]}'")
                        # This is a no-op
                        return "!"
                    break

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

        return line

    def onecmd(self, line):
        """Interpret the argument as though it had been typed in response
        to the prompt.

        Checks whether this line is typed at the normal prompt or in
        a breakpoint command list definition.
        """
        wenn not self.commands_defining:
            wenn line.startswith('_pdbcmd'):
                command, arg, line = self.parseline(line)
                wenn hasattr(self, command):
                    return getattr(self, command)(arg)
            return cmd.Cmd.onecmd(self, line)
        sonst:
            return self.handle_command_def(line)

    def handle_command_def(self, line):
        """Handles one command line during command list definition."""
        cmd, arg, line = self.parseline(line)
        wenn not cmd:
            return Falsch
        wenn cmd == 'end':
            return Wahr  # end of cmd list
        sowenn cmd == 'EOF':
            self.message('')
            return Wahr  # end of cmd list
        cmdlist = self.commands[self.commands_bnum]
        wenn cmd == 'silent':
            cmdlist.append('_pdbcmd_silence_frame_status')
            return Falsch  # continue to handle other cmd def in the cmd list
        wenn arg:
            cmdlist.append(cmd+' '+arg)
        sonst:
            cmdlist.append(cmd)
        # Determine wenn we must stop
        try:
            func = getattr(self, 'do_' + cmd)
        except AttributeError:
            func = self.default
        # one of the resuming commands
        wenn func.__name__ in self.commands_resuming:
            return Wahr
        return Falsch

    def _colorize_code(self, code):
        wenn self.colorize:
            colors = list(_pyrepl.utils.gen_colors(code))
            chars, _ = _pyrepl.utils.disp_str(code, colors=colors, force_color=Wahr)
            code = "".join(chars)
        return code

    # interface abstraction functions

    def message(self, msg, end='\n'):
        drucke(msg, end=end, file=self.stdout)

    def error(self, msg):
        drucke('***', msg, file=self.stdout)

    # convenience variables

    def set_convenience_variable(self, frame, name, value):
        wenn '__pdb_convenience_variables' not in frame.f_globals:
            frame.f_globals['__pdb_convenience_variables'] = {}
        frame.f_globals['__pdb_convenience_variables'][name] = value

    # Generic completion functions.  Individual complete_foo methods can be
    # assigned below to one of these functions.

    def completenames(self, text, line, begidx, endidx):
        # Overwrite completenames() of cmd so fuer the command completion,
        # wenn no current command matches, check fuer expressions as well
        commands = super().completenames(text, line, begidx, endidx)
        fuer alias in self.aliases:
            wenn alias.startswith(text):
                commands.append(alias)
        wenn commands:
            return commands
        sonst:
            expressions = self._complete_expression(text, line, begidx, endidx)
            wenn expressions:
                return expressions
            return self.completedefault(text, line, begidx, endidx)

    def _complete_location(self, text, line, begidx, endidx):
        # Complete a file/module/function location fuer break/tbreak/clear.
        wenn line.strip().endswith((':', ',')):
            # Here comes a line number or a condition which we can't complete.
            return []
        # First, try to find matching functions (i.e. expressions).
        try:
            ret = self._complete_expression(text, line, begidx, endidx)
        except Exception:
            ret = []
        # Then, try to complete file names as well.
        globs = glob.glob(glob.escape(text) + '*')
        fuer fn in globs:
            wenn os.path.isdir(fn):
                ret.append(fn + '/')
            sowenn os.path.isfile(fn) and fn.lower().endswith(('.py', '.pyw')):
                ret.append(fn + ':')
        return ret

    def _complete_bpnumber(self, text, line, begidx, endidx):
        # Complete a breakpoint number.  (This would be more helpful wenn we could
        # display additional info along with the completions, such as file/line
        # of the breakpoint.)
        return [str(i) fuer i, bp in enumerate(bdb.Breakpoint.bpbynumber)
                wenn bp is not Nichts and str(i).startswith(text)]

    def _complete_expression(self, text, line, begidx, endidx):
        # Complete an arbitrary expression.
        wenn not self.curframe:
            return []
        # Collect globals and locals.  It is usually not really sensible to also
        # complete builtins, and they clutter the namespace quite heavily, so we
        # leave them out.
        ns = {**self.curframe.f_globals, **self.curframe.f_locals}
        wenn '.' in text:
            # Walk an attribute chain up to the last part, similar to what
            # rlcompleter does.  This will bail wenn any of the parts are not
            # simple attribute access, which is what we want.
            dotted = text.split('.')
            try:
                wenn dotted[0].startswith('$'):
                    obj = self.curframe.f_globals['__pdb_convenience_variables'][dotted[0][1:]]
                sonst:
                    obj = ns[dotted[0]]
                fuer part in dotted[1:-1]:
                    obj = getattr(obj, part)
            except (KeyError, AttributeError):
                return []
            prefix = '.'.join(dotted[:-1]) + '.'
            return [prefix + n fuer n in dir(obj) wenn n.startswith(dotted[-1])]
        sonst:
            wenn text.startswith("$"):
                # Complete convenience variables
                conv_vars = self.curframe.f_globals.get('__pdb_convenience_variables', {})
                return [f"${name}" fuer name in conv_vars wenn name.startswith(text[1:])]
            # Complete a simple name.
            return [n fuer n in ns.keys() wenn n.startswith(text)]

    def _complete_indentation(self, text, line, begidx, endidx):
        try:
            importiere readline
        except ImportError:
            return []
        # Fill in spaces to form a 4-space indent
        return [' ' * (4 - readline.get_begidx() % 4)]

    def complete_multiline_names(self, text, line, begidx, endidx):
        # If text is space-only, the user entered <tab> before any text.
        # That normally means they want to indent the current line.
        wenn not text.strip():
            return self._complete_indentation(text, line, begidx, endidx)
        return self.completedefault(text, line, begidx, endidx)

    def completedefault(self, text, line, begidx, endidx):
        wenn text.startswith("$"):
            # Complete convenience variables
            conv_vars = self.curframe.f_globals.get('__pdb_convenience_variables', {})
            return [f"${name}" fuer name in conv_vars wenn name.startswith(text[1:])]

        # Use rlcompleter to do the completion
        state = 0
        matches = []
        completer = Completer(self.curframe.f_globals | self.curframe.f_locals)
        while (match := completer.complete(text, state)) is not Nichts:
            matches.append(match)
            state += 1
        return matches

    @contextmanager
    def _enable_rlcompleter(self, ns):
        try:
            importiere readline
        except ImportError:
            yield
            return

        try:
            old_completer = readline.get_completer()
            completer = Completer(ns)
            readline.set_completer(completer.complete)
            yield
        finally:
            readline.set_completer(old_completer)

    # Pdb meta commands, only intended to be used internally by pdb

    def _pdbcmd_print_frame_status(self, arg):
        self.print_stack_trace(0)
        self._validate_file_mtime()
        self._show_display()

    def _pdbcmd_silence_frame_status(self, arg):
        wenn self.cmdqueue and self.cmdqueue[-1] == '_pdbcmd_print_frame_status':
            self.cmdqueue.pop()

    def _pdbcmd_restore_lastcmd(self, arg):
        self.lastcmd = arg

    # Command definitions, called by cmdloop()
    # The argument is the remaining string on the command line
    # Return true to exit von the command loop

    def do_commands(self, arg):
        """(Pdb) commands [bpnumber]
        (com) ...
        (com) end
        (Pdb)

        Specify a list of commands fuer breakpoint number bpnumber.
        The commands themselves are entered on the following lines.
        Type a line containing just 'end' to terminate the commands.
        The commands are executed when the breakpoint is hit.

        To remove all commands von a breakpoint, type commands and
        follow it immediately with end; that is, give no commands.

        With no bpnumber argument, commands refers to the last
        breakpoint set.

        You can use breakpoint commands to start your program up
        again.  Simply use the continue command, or step, or any other
        command that resumes execution.

        Specifying any command resuming execution (currently continue,
        step, next, return, jump, quit and their abbreviations)
        terminates the command list (as wenn that command was
        immediately followed by end).  This is because any time you
        resume execution (even with a simple next or step), you may
        encounter another breakpoint -- which could have its own
        command list, leading to ambiguities about which list to
        execute.

        If you use the 'silent' command in the command list, the usual
        message about stopping at a breakpoint is not printed.  This
        may be desirable fuer breakpoints that are to print a specific
        message and then continue.  If none of the other commands
        print anything, you will see no sign that the breakpoint was
        reached.
        """
        wenn not arg:
            bnum = len(bdb.Breakpoint.bpbynumber) - 1
        sonst:
            try:
                bnum = int(arg)
            except:
                self._print_invalid_arg(arg)
                return
        try:
            self.get_bpbynumber(bnum)
        except ValueError as err:
            self.error('cannot set commands: %s' % err)
            return

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
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            # Restore old definitions.
            wenn old_commands:
                self.commands[bnum] = old_commands
            sonst:
                del self.commands[bnum]
            self.error('command definition aborted, old commands restored')
        finally:
            self.commands_defining = Falsch
            self.prompt = prompt_back

    complete_commands = _complete_bpnumber

    def do_break(self, arg, temporary=Falsch):
        """b(reak) [ ([filename:]lineno | function) [, condition] ]

        Without argument, list all breaks.

        With a line number argument, set a break at this line in the
        current file.  With a function name, set a break at the first
        executable line of that function.  If a second argument is
        present, it is a string specifying an expression which must
        evaluate to true before the breakpoint is honored.

        The line number may be prefixed with a filename and a colon,
        to specify a breakpoint in another file (probably one that
        hasn't been loaded yet).  The file is searched fuer on
        sys.path; the .py suffix may be omitted.
        """
        wenn not arg:
            wenn self.breaks:  # There's at least one
                self.message("Num Type         Disp Enb   Where")
                fuer bp in bdb.Breakpoint.bpbynumber:
                    wenn bp:
                        self.message(bp.bpformat())
            return
        # parse arguments; comma has lowest precedence
        # and cannot occur in filename
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
                return
            arg = arg[:comma].rstrip()
        # parse stuff before comma: [filename:]lineno | function
        colon = arg.rfind(':')
        funcname = Nichts
        wenn colon >= 0:
            filename = arg[:colon].rstrip()
            f = self.lookupmodule(filename)
            wenn not f:
                self.error('%r not found von sys.path' % filename)
                return
            sonst:
                filename = f
            arg = arg[colon+1:].lstrip()
            try:
                lineno = int(arg)
            except ValueError:
                self.error('Bad lineno: %s' % arg)
                return
        sonst:
            # no colon; can be lineno or function
            try:
                lineno = int(arg)
            except ValueError:
                try:
                    func = eval(arg,
                                self.curframe.f_globals,
                                self.curframe.f_locals)
                except:
                    func = arg
                try:
                    wenn hasattr(func, '__func__'):
                        func = func.__func__
                    code = func.__code__
                    #use co_name to identify the bkpt (function names
                    #could be aliased, but co_name is invariant)
                    funcname = code.co_name
                    lineno = find_first_executable_line(code)
                    filename = code.co_filename
                    module_globals = func.__globals__
                except:
                    # last thing to try
                    (ok, filename, ln) = self.lineinfo(arg)
                    wenn not ok:
                        self.error('The specified object %r is not a function '
                                   'or was not found along sys.path.' % arg)
                        return
                    funcname = ok # ok contains a function name
                    lineno = int(ln)
        wenn not filename:
            filename = self.defaultFile()
        filename = self.canonic(filename)
        # Check fuer reasonable breakpoint
        line = self.checkline(filename, lineno, module_globals)
        wenn line:
            # now set the break point
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
        wenn filename == '<string>' and self.mainpyfile:
            filename = self.mainpyfile
        return filename

    do_b = do_break

    complete_break = _complete_location
    complete_b = _complete_location

    def do_tbreak(self, arg):
        """tbreak [ ([filename:]lineno | function) [, condition] ]

        Same arguments as break, but sets a temporary breakpoint: it
        is automatically deleted when first hit.
        """
        self.do_break(arg, Wahr)

    complete_tbreak = _complete_location

    def lineinfo(self, identifier):
        failed = (Nichts, Nichts, Nichts)
        # Input is identifier, may be in single quotes
        idstring = identifier.split("'")
        wenn len(idstring) == 1:
            # not in single quotes
            id = idstring[0].strip()
        sowenn len(idstring) == 3:
            # quoted
            id = idstring[1].strip()
        sonst:
            return failed
        wenn id == '': return failed
        parts = id.split('.')
        # Protection fuer derived debuggers
        wenn parts[0] == 'self':
            del parts[0]
            wenn len(parts) == 0:
                return failed
        # Best first guess at file to look at
        fname = self.defaultFile()
        wenn len(parts) == 1:
            item = parts[0]
        sonst:
            # More than one part.
            # First is module, second is method/class
            f = self.lookupmodule(parts[0])
            wenn f:
                fname = f
            item = parts[1]
        answer = find_function(item, self.canonic(fname))
        return answer or failed

    def checkline(self, filename, lineno, module_globals=Nichts):
        """Check whether specified line seems to be executable.

        Return `lineno` wenn it is, 0 wenn not (e.g. a docstring, comment, blank
        line or EOF). Warning: testing is not comprehensive.
        """
        # this method should be callable before starting debugging, so default
        # to "no globals" wenn there is no current frame
        frame = getattr(self, 'curframe', Nichts)
        wenn module_globals is Nichts:
            module_globals = frame.f_globals wenn frame sonst Nichts
        line = linecache.getline(filename, lineno, module_globals)
        wenn not line:
            self.message('End of file')
            return 0
        line = line.strip()
        # Don't allow setting breakpoint at a blank line
        wenn (not line or (line[0] == '#') or
             (line[:3] == '"""') or line[:3] == "'''"):
            self.error('Blank or comment')
            return 0
        return lineno

    def do_enable(self, arg):
        """enable bpnumber [bpnumber ...]

        Enables the breakpoints given as a space separated list of
        breakpoint numbers.
        """
        wenn not arg:
            self._print_invalid_arg(arg)
            return
        args = arg.split()
        fuer i in args:
            try:
                bp = self.get_bpbynumber(i)
            except ValueError as err:
                self.error(err)
            sonst:
                bp.enable()
                self.message('Enabled %s' % bp)

    complete_enable = _complete_bpnumber

    def do_disable(self, arg):
        """disable bpnumber [bpnumber ...]

        Disables the breakpoints given as a space separated list of
        breakpoint numbers.  Disabling a breakpoint means it cannot
        cause the program to stop execution, but unlike clearing a
        breakpoint, it remains in the list of breakpoints and can be
        (re-)enabled.
        """
        wenn not arg:
            self._print_invalid_arg(arg)
            return
        args = arg.split()
        fuer i in args:
            try:
                bp = self.get_bpbynumber(i)
            except ValueError as err:
                self.error(err)
            sonst:
                bp.disable()
                self.message('Disabled %s' % bp)

    complete_disable = _complete_bpnumber

    def do_condition(self, arg):
        """condition bpnumber [condition]

        Set a new condition fuer the breakpoint, an expression which
        must evaluate to true before the breakpoint is honored.  If
        condition is absent, any existing condition is removed; i.e.,
        the breakpoint is made unconditional.
        """
        wenn not arg:
            self._print_invalid_arg(arg)
            return
        args = arg.split(' ', 1)
        try:
            cond = args[1]
            wenn err := self._compile_error_message(cond):
                self.error('Invalid condition %s: %r' % (cond, err))
                return
        except IndexError:
            cond = Nichts
        try:
            bp = self.get_bpbynumber(args[0].strip())
        except IndexError:
            self.error('Breakpoint number expected')
        except ValueError as err:
            self.error(err)
        sonst:
            bp.cond = cond
            wenn not cond:
                self.message('Breakpoint %d is now unconditional.' % bp.number)
            sonst:
                self.message('New condition set fuer breakpoint %d.' % bp.number)

    complete_condition = _complete_bpnumber

    def do_ignore(self, arg):
        """ignore bpnumber [count]

        Set the ignore count fuer the given breakpoint number.  If
        count is omitted, the ignore count is set to 0.  A breakpoint
        becomes active when the ignore count is zero.  When non-zero,
        the count is decremented each time the breakpoint is reached
        and the breakpoint is not disabled and any associated
        condition evaluates to true.
        """
        wenn not arg:
            self._print_invalid_arg(arg)
            return
        args = arg.split()
        wenn not args:
            self.error('Breakpoint number expected')
            return
        wenn len(args) == 1:
            count = 0
        sowenn len(args) == 2:
            try:
                count = int(args[1])
            except ValueError:
                self._print_invalid_arg(arg)
                return
        sonst:
            self._print_invalid_arg(arg)
            return
        try:
            bp = self.get_bpbynumber(args[0].strip())
        except ValueError as err:
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
                self.message('Will stop next time breakpoint %d is reached.'
                             % bp.number)

    complete_ignore = _complete_bpnumber

    def _prompt_for_confirmation(self, prompt, default):
        try:
            reply = input(prompt)
        except EOFError:
            reply = default
        return reply.strip().lower()

    def do_clear(self, arg):
        """cl(ear) [filename:lineno | bpnumber ...]

        With a space separated list of breakpoint numbers, clear
        those breakpoints.  Without argument, clear all breaks (but
        first ask confirmation).  With a filename:lineno argument,
        clear all breaks at that line in that file.
        """
        wenn not arg:
            reply = self._prompt_for_confirmation(
                'Clear all breaks? ',
                default='no',
            )
            wenn reply in ('y', 'yes'):
                bplist = [bp fuer bp in bdb.Breakpoint.bpbynumber wenn bp]
                self.clear_all_breaks()
                fuer bp in bplist:
                    self.message('Deleted %s' % bp)
            return
        wenn ':' in arg:
            # Make sure it works fuer "clear C:\foo\bar.py:12"
            i = arg.rfind(':')
            filename = arg[:i]
            arg = arg[i+1:]
            try:
                lineno = int(arg)
            except ValueError:
                err = "Invalid line number (%s)" % arg
            sonst:
                bplist = self.get_breaks(filename, lineno)[:]
                err = self.clear_break(filename, lineno)
            wenn err:
                self.error(err)
            sonst:
                fuer bp in bplist:
                    self.message('Deleted %s' % bp)
            return
        numberlist = arg.split()
        fuer i in numberlist:
            try:
                bp = self.get_bpbynumber(i)
            except ValueError as err:
                self.error(err)
            sonst:
                self.clear_bpbynumber(i)
                self.message('Deleted %s' % bp)
    do_cl = do_clear # 'c' is already an abbreviation fuer 'continue'

    complete_clear = _complete_location
    complete_cl = _complete_location

    def do_where(self, arg):
        """w(here) [count]

        Print a stack trace. If count is not specified, print the full stack.
        If count is 0, print the current frame entry. If count is positive,
        print count entries von the most recent frame. If count is negative,
        print -count entries von the least recent frame.
        An arrow indicates the "current frame", which determines the
        context of most commands.  'bt' is an alias fuer this command.
        """
        wenn not arg:
            count = Nichts
        sonst:
            try:
                count = int(arg)
            except ValueError:
                self.error('Invalid count (%s)' % arg)
                return
        self.print_stack_trace(count)
    do_w = do_where
    do_bt = do_where

    def _select_frame(self, number):
        assert 0 <= number < len(self.stack)
        self.curindex = number
        self.curframe = self.stack[self.curindex][0]
        self.set_convenience_variable(self.curframe, '_frame', self.curframe)
        self.print_stack_entry(self.stack[self.curindex])
        self.lineno = Nichts

    def do_exceptions(self, arg):
        """exceptions [number]

        List or change current exception in an exception chain.

        Without arguments, list all the current exception in the exception
        chain. Exceptions will be numbered, with the current exception indicated
        with an arrow.

        If given an integer as argument, switch to the exception at that index.
        """
        wenn not self._chained_exceptions:
            self.message(
                "Did not find chained exceptions. To move between"
                " exceptions, pdb/post_mortem must be given an exception"
                " object rather than a traceback."
            )
            return
        wenn not arg:
            fuer ix, exc in enumerate(self._chained_exceptions):
                prompt = ">" wenn ix == self._chained_exception_index sonst " "
                rep = repr(exc)
                wenn len(rep) > 80:
                    rep = rep[:77] + "..."
                indicator = (
                    "  -"
                    wenn self._chained_exceptions[ix].__traceback__ is Nichts
                    sonst f"{ix:>3}"
                )
                self.message(f"{prompt} {indicator} {rep}")
        sonst:
            try:
                number = int(arg)
            except ValueError:
                self.error("Argument must be an integer")
                return
            wenn 0 <= number < len(self._chained_exceptions):
                wenn self._chained_exceptions[number].__traceback__ is Nichts:
                    self.error("This exception does not have a traceback, cannot jump to it")
                    return

                self._chained_exception_index = number
                self.setup(Nichts, self._chained_exceptions[number].__traceback__)
                self.print_stack_entry(self.stack[self.curindex])
            sonst:
                self.error("No exception with that number")

    def do_up(self, arg):
        """u(p) [count]

        Move the current frame count (default one) levels up in the
        stack trace (to an older frame).
        """
        wenn self.curindex == 0:
            self.error('Oldest frame')
            return
        try:
            count = int(arg or 1)
        except ValueError:
            self.error('Invalid frame count (%s)' % arg)
            return
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
            return
        try:
            count = int(arg or 1)
        except ValueError:
            self.error('Invalid frame count (%s)' % arg)
            return
        wenn count < 0:
            newframe = len(self.stack) - 1
        sonst:
            newframe = min(len(self.stack) - 1, self.curindex + count)
        self._select_frame(newframe)
    do_d = do_down

    def do_until(self, arg):
        """unt(il) [lineno]

        Without argument, continue execution until the line with a
        number greater than the current one is reached.  With a line
        number, continue execution until a line with a number greater
        or equal to that is reached.  In both cases, also stop when
        the current frame returns.
        """
        wenn arg:
            try:
                lineno = int(arg)
            except ValueError:
                self.error('Error in argument: %r' % arg)
                return
            wenn lineno <= self.curframe.f_lineno:
                self.error('"until" line number is smaller than current '
                           'line number')
                return
        sonst:
            lineno = Nichts
        self.set_until(self.curframe, lineno)
        return 1
    do_unt = do_until

    def do_step(self, arg):
        """s(tep)

        Execute the current line, stop at the first possible occasion
        (either in a function that is called or in the current
        function).
        """
        wenn arg:
            self._print_invalid_arg(arg)
            return
        self.set_step()
        return 1
    do_s = do_step

    def do_next(self, arg):
        """n(ext)

        Continue execution until the next line in the current function
        is reached or it returns.
        """
        wenn arg:
            self._print_invalid_arg(arg)
            return
        self.set_next(self.curframe)
        return 1
    do_n = do_next

    def do_run(self, arg):
        """run [args...]

        Restart the debugged python program. If a string is supplied
        it is split with "shlex", and the result is used as the new
        sys.argv.  History, breakpoints, actions and debugger options
        are preserved.  "restart" is an alias fuer "run".
        """
        wenn self.mode == 'inline':
            self.error('run/restart command is disabled when pdb is running in inline mode.\n'
                       'Use the command line interface to enable restarting your program\n'
                       'e.g. "python -m pdb myscript.py"')
            return
        wenn arg:
            importiere shlex
            argv0 = sys.argv[0:1]
            try:
                sys.argv = shlex.split(arg)
            except ValueError as e:
                self.error('Cannot run %s: %s' % (arg, e))
                return
            sys.argv[:0] = argv0
        # this is caught in the main debugger loop
        raise Restart

    do_restart = do_run

    def do_return(self, arg):
        """r(eturn)

        Continue execution until the current function returns.
        """
        wenn arg:
            self._print_invalid_arg(arg)
            return
        self.set_return(self.curframe)
        return 1
    do_r = do_return

    def do_continue(self, arg):
        """c(ont(inue))

        Continue execution, only stop when a breakpoint is encountered.
        """
        wenn arg:
            self._print_invalid_arg(arg)
            return
        wenn not self.nosigint:
            try:
                Pdb._previous_sigint_handler = \
                    signal.signal(signal.SIGINT, self.sigint_handler)
            except ValueError:
                # ValueError happens when do_continue() is invoked from
                # a non-main thread in which case we just continue without
                # SIGINT set. Would printing a message here (once) make
                # sense?
                pass
        self.set_continue()
        return 1
    do_c = do_cont = do_continue

    def do_jump(self, arg):
        """j(ump) lineno

        Set the next line that will be executed.  Only available in
        the bottom-most frame.  This lets you jump back and execute
        code again, or jump forward to skip code that you don't want
        to run.

        It should be noted that not all jumps are allowed -- for
        instance it is not possible to jump into the middle of a
        fuer loop or out of a finally clause.
        """
        wenn not arg:
            self._print_invalid_arg(arg)
            return
        wenn self.curindex + 1 != len(self.stack):
            self.error('You can only jump within the bottom frame')
            return
        try:
            arg = int(arg)
        except ValueError:
            self.error("The 'jump' command requires a line number")
        sonst:
            try:
                # Do the jump, fix up our copy of the stack, and display the
                # new position
                self.curframe.f_lineno = arg
                self.stack[self.curindex] = self.stack[self.curindex][0], arg
                self.print_stack_entry(self.stack[self.curindex])
            except ValueError as e:
                self.error('Jump failed: %s' % e)
    do_j = do_jump

    def _create_recursive_debugger(self):
        return Pdb(self.completekey, self.stdin, self.stdout)

    def do_debug(self, arg):
        """debug code

        Enter a recursive debugger that steps through the code
        argument (which is an arbitrary expression or statement to be
        executed in the current environment).
        """
        wenn not arg:
            self._print_invalid_arg(arg)
            return
        self.stop_trace()
        globals = self.curframe.f_globals
        locals = self.curframe.f_locals
        p = self._create_recursive_debugger()
        p.prompt = "(%s) " % self.prompt.strip()
        self.message("ENTERING RECURSIVE DEBUGGER")
        try:
            sys.call_tracing(p.run, (arg, globals, locals))
        except Exception:
            self._error_exc()
        self.message("LEAVING RECURSIVE DEBUGGER")
        self.start_trace()
        self.lastcmd = p.lastcmd

    complete_debug = _complete_expression

    def do_quit(self, arg):
        """q(uit) | exit

        Quit von the debugger. The program being executed is aborted.
        """
        # Show prompt to kill process when in 'inline' mode and wenn pdb was not
        # started von an interactive console. The attribute sys.ps1 is only
        # defined wenn the interpreter is in interactive mode.
        wenn self.mode == 'inline' and not hasattr(sys, 'ps1'):
            while Wahr:
                try:
                    reply = input('Quitting pdb will kill the process. Quit anyway? [y/n] ')
                    reply = reply.lower().strip()
                except EOFError:
                    reply = 'y'
                    self.message('')
                wenn reply == 'y' or reply == '':
                    sys.exit(1)
                sowenn reply.lower() == 'n':
                    return

        self._user_requested_quit = Wahr
        self.set_quit()
        return 1

    do_q = do_quit
    do_exit = do_quit

    def do_EOF(self, arg):
        """EOF

        Handles the receipt of EOF as a command.
        """
        self.message('')
        return self.do_quit(arg)

    def do_args(self, arg):
        """a(rgs)

        Print the argument list of the current function.
        """
        wenn arg:
            self._print_invalid_arg(arg)
            return
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

        Print the return value fuer the last return of a function.
        """
        wenn arg:
            self._print_invalid_arg(arg)
            return
        wenn '__return__' in self.curframe.f_locals:
            self.message(self._safe_repr(self.curframe.f_locals['__return__'], "retval"))
        sonst:
            self.error('Not yet returned!')
    do_rv = do_retval

    def _getval(self, arg):
        try:
            return eval(arg, self.curframe.f_globals, self.curframe.f_locals)
        except:
            self._error_exc()
            raise

    def _getval_except(self, arg, frame=Nichts):
        try:
            wenn frame is Nichts:
                return eval(arg, self.curframe.f_globals, self.curframe.f_locals)
            sonst:
                return eval(arg, frame.f_globals, frame.f_locals)
        except BaseException as exc:
            return _rstr('** raised %s **' % self._format_exc(exc))

    def _error_exc(self):
        exc = sys.exception()
        self.error(self._format_exc(exc))

    def _msg_val_func(self, arg, func):
        try:
            val = self._getval(arg)
        except:
            return  # _getval() has displayed the error
        try:
            self.message(func(val))
        except:
            self._error_exc()

    def _safe_repr(self, obj, expr):
        try:
            return repr(obj)
        except Exception as e:
            return _rstr(f"*** repr({expr}) failed: {self._format_exc(e)} ***")

    def do_p(self, arg):
        """p expression

        Print the value of the expression.
        """
        wenn not arg:
            self._print_invalid_arg(arg)
            return
        self._msg_val_func(arg, repr)

    def do_pp(self, arg):
        """pp expression

        Pretty-print the value of the expression.
        """
        wenn not arg:
            self._print_invalid_arg(arg)
            return
        self._msg_val_func(arg, pprint.pformat)

    complete_print = _complete_expression
    complete_p = _complete_expression
    complete_pp = _complete_expression

    def do_list(self, arg):
        """l(ist) [first[, last] | .]

        List source code fuer the current file.  Without arguments,
        list 11 lines around the current line or continue the previous
        listing.  With . as argument, list 11 lines around the current
        line.  With one argument, list 11 lines starting at that line.
        With two arguments, list the given range; wenn the second
        argument is less than the first, it is a count.

        The current line in the current frame is indicated by "->".
        If an exception is being debugged, the line where the
        exception was originally raised or propagated is indicated by
        ">>", wenn it differs von the current line.
        """
        self.lastcmd = 'list'
        last = Nichts
        wenn arg and arg != '.':
            try:
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
            except ValueError:
                self.error('Error in argument: %r' % arg)
                return
        sowenn self.lineno is Nichts or arg == '.':
            first = max(1, self.curframe.f_lineno - 5)
        sonst:
            first = self.lineno + 1
        wenn last is Nichts:
            last = first + 10
        filename = self.curframe.f_code.co_filename
        breaklist = self.get_file_breaks(filename)
        try:
            lines = linecache.getlines(filename, self.curframe.f_globals)
            self._print_lines(lines[first-1:last], first, breaklist,
                              self.curframe)
            self.lineno = min(last, len(lines))
            wenn len(lines) < last:
                self.message('[EOF]')
        except KeyboardInterrupt:
            pass
        self._validate_file_mtime()
    do_l = do_list

    def do_longlist(self, arg):
        """ll | longlist

        List the whole source code fuer the current function or frame.
        """
        wenn arg:
            self._print_invalid_arg(arg)
            return
        filename = self.curframe.f_code.co_filename
        breaklist = self.get_file_breaks(filename)
        try:
            lines, lineno = self._getsourcelines(self.curframe)
        except OSError as err:
            self.error(err)
            return
        self._print_lines(lines, lineno, breaklist, self.curframe)
        self._validate_file_mtime()
    do_ll = do_longlist

    def do_source(self, arg):
        """source expression

        Try to get source code fuer the given object and display it.
        """
        wenn not arg:
            self._print_invalid_arg(arg)
            return
        try:
            obj = self._getval(arg)
        except:
            return
        try:
            lines, lineno = self._getsourcelines(obj)
        except (OSError, TypeError) as err:
            self.error(err)
            return
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
        wenn not arg:
            self._print_invalid_arg(arg)
            return
        try:
            value = self._getval(arg)
        except:
            # _getval() already printed the error
            return
        code = Nichts
        # Is it an instance method?
        try:
            code = value.__func__.__code__
        except Exception:
            pass
        wenn code:
            self.message('Method %s' % code.co_name)
            return
        # Is it a function?
        try:
            code = value.__code__
        except Exception:
            pass
        wenn code:
            self.message('Function %s' % code.co_name)
            return
        # Is it a class?
        wenn value.__class__ is type:
            self.message('Class %s.%s' % (value.__module__, value.__qualname__))
            return
        # Nichts of the above...
        self.message(type(value))

    complete_whatis = _complete_expression

    def do_display(self, arg):
        """display [expression]

        Display the value of the expression wenn it changed, each time execution
        stops in the current frame.

        Without expression, list all display expressions fuer the current frame.
        """
        wenn not arg:
            wenn self.displaying:
                self.message('Currently displaying:')
                fuer key, val in self.displaying.get(self.curframe, {}).items():
                    self.message('%s: %s' % (key, self._safe_repr(val, key)))
            sonst:
                self.message('No expression is being displayed')
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

        Do not display the expression any more in the current frame.

        Without expression, clear all display expressions fuer the current frame.
        """
        wenn arg:
            try:
                del self.displaying.get(self.curframe, {})[arg]
            except KeyError:
                self.error('not displaying %s' % arg)
        sonst:
            self.displaying.pop(self.curframe, Nichts)

    def complete_undisplay(self, text, line, begidx, endidx):
        return [e fuer e in self.displaying.get(self.curframe, {})
                wenn e.startswith(text)]

    def do_interact(self, arg):
        """interact

        Start an interactive interpreter whose global namespace
        contains all the (global and local) names found in the current scope.
        """
        ns = {**self.curframe.f_globals, **self.curframe.f_locals}
        with self._enable_rlcompleter(ns):
            console = _PdbInteractiveConsole(ns, message=self.message)
            console.interact(banner="*pdb interact start*",
                             exitmsg="*exit von pdb interact command*")

    def do_alias(self, arg):
        """alias [name [command]]

        Create an alias called 'name' that executes 'command'.  The
        command must *not* be enclosed in quotes.  Replaceable
        parameters can be indicated by %1, %2, and so on, while %* is
        replaced by all the parameters.  If no command is given, the
        current alias fuer name is shown. If no name is given, all
        aliases are listed.

        Aliases may be nested and can contain anything that can be
        legally typed at the pdb prompt.  Note!  You *can* override
        internal pdb commands with aliases!  Those internal commands
        are then hidden until the alias is removed.  Aliasing is
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
            return
        wenn len(args) == 1:
            wenn args[0] in self.aliases:
                self.message("%s = %s" % (args[0], self.aliases[args[0]]))
            sonst:
                self.error(f"Unknown alias '{args[0]}'")
        sonst:
            # Do a validation check to make sure no replaceable parameters
            # are skipped wenn %* is not used.
            alias = ' '.join(args[1:])
            wenn '%*' not in alias:
                consecutive = Wahr
                fuer idx in range(1, 10):
                    wenn f'%{idx}' not in alias:
                        consecutive = Falsch
                    wenn f'%{idx}' in alias and not consecutive:
                        self.error("Replaceable parameters must be consecutive")
                        return
            self.aliases[args[0]] = alias

    def do_unalias(self, arg):
        """unalias name

        Delete the specified alias.
        """
        args = arg.split()
        wenn len(args) == 0:
            self._print_invalid_arg(arg)
            return
        wenn args[0] in self.aliases:
            del self.aliases[args[0]]

    def complete_unalias(self, text, line, begidx, endidx):
        return [a fuer a in self.aliases wenn a.startswith(text)]

    # List of all the commands making the program resume execution.
    commands_resuming = ['do_continue', 'do_step', 'do_next', 'do_return',
                         'do_until', 'do_quit', 'do_jump']

    # Print a traceback starting at the top stack frame.
    # The most recently entered frame is printed last;
    # this is different von dbx and gdb, but consistent with
    # the Python interpreter's stack trace.
    # It is also consistent with the up/down commands (which are
    # compatible with dbx and gdb: up moves towards 'main()'
    # and down moves towards the most recent stack frame).
    #     * wenn count is Nichts, prints the full stack
    #     * wenn count = 0, prints the current frame entry
    #     * wenn count < 0, prints -count least recent frame entries
    #     * wenn count > 0, prints count most recent frame entries

    def print_stack_trace(self, count=Nichts):
        wenn count is Nichts:
            stack_to_print = self.stack
        sowenn count == 0:
            stack_to_print = [self.stack[self.curindex]]
        sowenn count < 0:
            stack_to_print = self.stack[:-count]
        sonst:
            stack_to_print = self.stack[-count:]
        try:
            fuer frame_lineno in stack_to_print:
                self.print_stack_entry(frame_lineno)
        except KeyboardInterrupt:
            pass

    def print_stack_entry(self, frame_lineno, prompt_prefix=line_prefix):
        frame, lineno = frame_lineno
        wenn frame is self.curframe:
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
        With a command name as argument, print help about that command.
        "help pdb" shows the full pdb documentation.
        "help exec" gives help on the ! command.
        """
        wenn not arg:
            return cmd.Cmd.do_help(self, arg)
        try:
            try:
                topic = getattr(self, 'help_' + arg)
                return topic()
            except AttributeError:
                command = getattr(self, 'do_' + arg)
        except AttributeError:
            self.error('No help fuer %r' % arg)
        sonst:
            wenn sys.flags.optimize >= 2:
                self.error('No help fuer %r; please do not run Python with -OO '
                           'if you need command help' % arg)
                return
            wenn command.__doc__ is Nichts:
                self.error('No help fuer %r; __doc__ string missing' % arg)
                return
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
        self.message((self.help_exec.__doc__ or '').strip())

    def help_pdb(self):
        help()

    # other helper functions

    def lookupmodule(self, filename):
        """Helper function fuer break/clear parsing -- may be overridden.

        lookupmodule() translates (possibly incomplete) file or module name
        into an absolute file name.

        filename could be in format of:
            * an absolute path like '/path/to/file.py'
            * a relative path like 'file.py' or 'dir/file.py'
            * a module name like 'module' or 'package.module'

        files and modules will be searched in sys.path.
        """
        wenn not filename.endswith('.py'):
            # A module is passed in so convert it to equivalent file
            filename = filename.replace('.', os.sep) + '.py'

        wenn os.path.isabs(filename):
            wenn os.path.exists(filename):
                return filename
            return Nichts

        fuer dirname in sys.path:
            while os.path.islink(dirname):
                dirname = os.readlink(dirname)
            fullname = os.path.join(dirname, filename)
            wenn os.path.exists(fullname):
                return fullname
        return Nichts

    def _run(self, target: _ExecutableTarget):
        # When bdb sets tracing, a number of call and line events happen
        # BEFORE debugger even reaches user's code (and the exact sequence of
        # events depends on python version). Take special measures to
        # avoid stopping before reaching the main script (see user_line and
        # user_call fuer details).
        self._wait_for_mainpyfile = Wahr
        self._user_requested_quit = Falsch

        self.mainpyfile = self.canonic(target.filename)

        # The target has to run in __main__ namespace (or imports from
        # __main__ will break). Clear __main__ and replace with
        # the target namespace.
        importiere __main__
        __main__.__dict__.clear()
        __main__.__dict__.update(target.namespace)

        # Clear the mtime table fuer program reruns, assume all the files
        # are up to date.
        self._file_mtime_table.clear()

        self.run(target.code)

    def _format_exc(self, exc: BaseException):
        return traceback.format_exception_only(exc)[-1].strip()

    def _compile_error_message(self, expr):
        """Return the error message as string wenn compiling `expr` fails."""
        try:
            compile(expr, "<stdin>", "eval")
        except SyntaxError as exc:
            return _rstr(self._format_exc(exc))
        return ""

    def _getsourcelines(self, obj):
        # GH-103319
        # inspect.getsourcelines() returns lineno = 0 for
        # module-level frame which breaks our code print line number
        # This method should be replaced by inspect.getsourcelines(obj)
        # once this bug is fixed in inspect
        lines, lineno = inspect.getsourcelines(obj)
        lineno = max(1, lineno)
        return lines, lineno

    def _help_message_from_doc(self, doc, usage_only=Falsch):
        lines = [line.strip() fuer line in doc.rstrip().splitlines()]
        wenn not lines:
            return "No help message found."
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
                    break
                prefix = ""
            formatted.append(indent + prefix + line)
        return "\n".join(formatted)

    def _print_invalid_arg(self, arg):
        """Return the usage string fuer a function."""

        wenn not arg:
            self.error("Argument is required fuer this command")
        sonst:
            self.error(f"Invalid argument: {arg}")

        # Yes it's a bit hacky. Get the caller name, get the method based on
        # that name, and get the docstring von that method.
        # This should NOT fail wenn the caller is a method of this class.
        doc = inspect.getdoc(getattr(self, sys._getframe(1).f_code.co_name))
        wenn doc is not Nichts:
            self.message(self._help_message_from_doc(doc, usage_only=Wahr))

# Collect all command help into docstring, wenn not run with -OO

wenn __doc__ is not Nichts:
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

    del _help_order, _command


# Simplified interface

def run(statement, globals=Nichts, locals=Nichts):
    """Execute the *statement* (given as a string or a code object)
    under debugger control.

    The debugger prompt appears before any code is executed; you can set
    breakpoints and type continue, or you can step through the statement
    using step or next.

    The optional *globals* and *locals* arguments specify the
    environment in which the code is executed; by default the
    dictionary of the module __main__ is used (see the explanation of
    the built-in exec() or eval() functions.).
    """
    Pdb().run(statement, globals, locals)

def runeval(expression, globals=Nichts, locals=Nichts):
    """Evaluate the *expression* (given as a string or a code object)
    under debugger control.

    When runeval() returns, it returns the value of the expression.
    Otherwise this function is similar to run().
    """
    return Pdb().runeval(expression, globals, locals)

def runctx(statement, globals, locals):
    # B/W compatibility
    run(statement, globals, locals)

def runcall(*args, **kwds):
    """Call the function (a function or method object, not a string)
    with the given arguments.

    When runcall() returns, it returns whatever the function call
    returned. The debugger prompt appears as soon as the function is
    entered.
    """
    return Pdb().runcall(*args, **kwds)

def set_trace(*, header=Nichts, commands=Nichts):
    """Enter the debugger at the calling stack frame.

    This is useful to hard-code a breakpoint at a given point in a
    program, even wenn the code is not otherwise being debugged (e.g. when
    an assertion fails). If given, *header* is printed to the console
    just before debugging begins. *commands* is an optional list of
    pdb commands to run when the debugger starts.
    """
    wenn Pdb._last_pdb_instance is not Nichts:
        pdb = Pdb._last_pdb_instance
    sonst:
        pdb = Pdb(mode='inline', backend='monitoring', colorize=Wahr)
    wenn header is not Nichts:
        pdb.message(header)
    pdb.set_trace(sys._getframe().f_back, commands=commands)

async def set_trace_async(*, header=Nichts, commands=Nichts):
    """Enter the debugger at the calling stack frame, but in async mode.

    This should be used as await pdb.set_trace_async(). Users can do await
    wenn they enter the debugger with this function. Otherwise it's the same
    as set_trace().
    """
    wenn Pdb._last_pdb_instance is not Nichts:
        pdb = Pdb._last_pdb_instance
    sonst:
        pdb = Pdb(mode='inline', backend='monitoring', colorize=Wahr)
    wenn header is not Nichts:
        pdb.message(header)
    await pdb.set_trace_async(sys._getframe().f_back, commands=commands)

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
            # Only started by the top level _PdbServer, not recursive ones.
            self._start_signal_listener(signal_server)
        # Override the `colorize` attribute set by the parent constructor,
        # because it checks the server's stdout, rather than the client's.
        super().__init__(colorize=Falsch, **kwargs)
        self.colorize = colorize

    @staticmethod
    def protocol_version():
        # By default, assume a client and server are compatible wenn they run
        # the same Python major.minor version. We'll try to keep backwards
        # compatibility between patch versions of a minor version wenn possible.
        # If we do need to change the protocol in a patch version, we'll change
        # `revision` to the patch version where the protocol changed.
        # We can ignore compatibility fuer pre-release versions; sys.remote_exec
        # can't attach to a pre-release version except von that same version.
        v = sys.version_info
        revision = 0
        return int(f"{v.major:02X}{v.minor:02X}{revision:02X}F0", 16)

    def _ensure_valid_message(self, msg):
        # Ensure the message conforms to our protocol.
        # If anything needs to be changed here fuer a patch release of Python,
        # the 'revision' in protocol_version() should be updated.
        match msg:
            case {"message": str(), "type": str()}:
                # Have the client show a message. The client chooses how to
                # format the message based on its type. The currently defined
                # types are "info" and "error". If a message has a type the
                # client doesn't recognize, it must be treated as "info".
                pass
            case {"help": str()}:
                # Have the client show the help fuer a given argument.
                pass
            case {"prompt": str(), "state": str()}:
                # Have the client display the given prompt and wait fuer a reply
                # von the user. If the client recognizes the state it may
                # enable mode-specific features like multi-line editing.
                # If it doesn't recognize the state it must prompt fuer a single
                # line only and send it directly to the server. A server won't
                # progress until it gets a "reply" or "signal" message, but can
                # process "complete" requests while waiting fuer the reply.
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
                # Due to aliases this list is not static, but the client
                # needs to know it fuer multi-line editing.
                pass
            case _:
                raise AssertionError(
                    f"PDB message doesn't follow the schema! {msg}"
                )

    @classmethod
    def _start_signal_listener(cls, address):
        def listener(sock):
            with closing(sock):
                # Check wenn the interpreter is finalizing every quarter of a second.
                # Clean up and exit wenn so.
                sock.settimeout(0.25)
                sock.shutdown(socket.SHUT_WR)
                while not shut_down.is_set():
                    try:
                        data = sock.recv(1024)
                    except socket.timeout:
                        continue
                    wenn data == b"":
                        return  # EOF
                    signal.raise_signal(signal.SIGINT)

        def stop_thread():
            shut_down.set()
            thread.join()

        # Use a daemon thread so that we don't detach until after all non-daemon
        # threads are done. Use an atexit handler to stop gracefully at that point,
        # so that our thread is stopped before the interpreter is torn down.
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
        try:
            self._sockfile.write(json_payload.encode() + b"\n")
            self._sockfile.flush()
        except (OSError, ValueError):
            # We get an OSError wenn the network connection has dropped, and a
            # ValueError wenn detach() wenn the sockfile has been closed. We'll
            # handle this the next time we try to read von the client instead
            # of trying to handle it von everywhere _send() may be called.
            # Track this with a flag rather than assuming readline() will ever
            # return an empty string because the socket may be half-closed.
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
        wenn state == "pdb" and not self._command_name_cache:
            self._command_name_cache = self.completenames("", "", 0, 0)
            self._send(command_list=self._command_name_cache)
        self._send(prompt=prompt, state=state)
        return self._read_reply()

    def _read_reply(self):
        # Loop until we get a 'reply' or 'signal' von the client,
        # processing out-of-band 'complete' requests as they arrive.
        while Wahr:
            wenn self._write_failed:
                raise EOFError

            msg = self._sockfile.readline()
            wenn not msg:
                raise EOFError

            try:
                payload = json.loads(msg)
            except json.JSONDecodeError:
                self.error(f"Disconnecting: client sent invalid JSON {msg!r}")
                raise EOFError

            match payload:
                case {"reply": str(reply)}:
                    return reply
                case {"signal": str(signal)}:
                    wenn signal == "INT":
                        raise KeyboardInterrupt
                    sowenn signal == "EOF":
                        raise EOFError
                    sonst:
                        self.error(
                            f"Received unrecognized signal: {signal}"
                        )
                        # Our best hope of recovering is to pretend we
                        # got an EOF to exit whatever mode we're in.
                        raise EOFError
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
                    continue
            # Valid JSON, but doesn't meet the schema.
            self.error(f"Ignoring invalid message von client: {msg}")

    def _complete_any(self, text, line, begidx, endidx):
        # If we're in 'interact' mode, we need to use the default completer
        wenn self._interact_state:
            compfunc = self.completedefault
        sonst:
            wenn begidx == 0:
                return self.completenames(text, line, begidx, endidx)

            cmd = self.parseline(line)[0]
            wenn cmd:
                compfunc = getattr(self, "complete_" + cmd, self.completedefault)
            sonst:
                compfunc = self.completedefault
        return compfunc(text, line, begidx, endidx)

    def cmdloop(self, intro=Nichts):
        self.preloop()
        wenn intro is not Nichts:
            self.intro = intro
        wenn self.intro:
            self.message(str(self.intro))
        stop = Nichts
        while not stop:
            wenn self._interact_state is not Nichts:
                try:
                    reply = self._get_input(prompt=">>> ", state="interact")
                except KeyboardInterrupt:
                    # Match how KeyboardInterrupt is handled in a REPL
                    self.message("\nKeyboardInterrupt")
                except EOFError:
                    self.message("\n*exit von pdb interact command*")
                    self._interact_state = Nichts
                sonst:
                    self._run_in_python_repl(reply)
                continue

            wenn not self.cmdqueue:
                try:
                    state = "commands" wenn self.commands_defining sonst "pdb"
                    reply = self._get_input(prompt=self.prompt, state=state)
                except EOFError:
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
        # Detach the debugger and close the socket without raising BdbQuit
        self.quitting = Falsch
        wenn self._owns_sockfile:
            # Don't try to reuse this instance, it's not valid anymore.
            Pdb._last_pdb_instance = Nichts
            try:
                self._sockfile.close()
            except OSError:
                # close() can fail wenn the connection was broken unexpectedly.
                pass

    def do_debug(self, arg):
        # Clear our cached list of valid commands; the recursive debugger might
        # send its own differing list, and so ours needs to be re-sent.
        self._command_name_cache = []
        return super().do_debug(arg)

    def do_alias(self, arg):
        # Clear our cached list of valid commands; one might be added.
        self._command_name_cache = []
        return super().do_alias(arg)

    def do_unalias(self, arg):
        # Clear our cached list of valid commands; one might be removed.
        self._command_name_cache = []
        return super().do_unalias(arg)

    def do_help(self, arg):
        # Tell the client to render the help, since it might need a pager.
        self._send(help=arg)

    do_h = do_help

    def _interact_displayhook(self, obj):
        # Like the default `sys.displayhook` except sending a socket message.
        wenn obj is not Nichts:
            self.message(repr(obj))
            builtins._ = obj

    def _run_in_python_repl(self, lines):
        # Run one 'interact' mode code block against an existing namespace.
        assert self._interact_state
        save_displayhook = sys.displayhook
        try:
            sys.displayhook = self._interact_displayhook
            code_obj = self._interact_state["compiler"](lines + "\n")
            wenn code_obj is Nichts:
                raise SyntaxError("Incomplete command")
            exec(code_obj, self._interact_state["ns"])
        except:
            self._error_exc()
        finally:
            sys.displayhook = save_displayhook

    def do_interact(self, arg):
        # Prepare to run 'interact' mode code blocks, and trigger the client
        # to start treating all input as Python commands, not PDB ones.
        self.message("*pdb interact start*")
        self._interact_state = dict(
            compiler=codeop.CommandCompiler(),
            ns={**self.curframe.f_globals, **self.curframe.f_locals},
        )

    @typing.override
    def _create_recursive_debugger(self):
        return _PdbServer(
            self._sockfile,
            owns_sockfile=Falsch,
            colorize=self.colorize,
        )

    @typing.override
    def _prompt_for_confirmation(self, prompt, default):
        try:
            return self._get_input(prompt=prompt, state="confirm")
        except (EOFError, KeyboardInterrupt):
            return default

    def do_run(self, arg):
        self.error("remote PDB cannot restart the program")

    do_restart = do_run

    def _error_exc(self):
        wenn self._interact_state and isinstance(sys.exception(), SystemExit):
            # If we get a SystemExit in 'interact' mode, exit the REPL.
            self._interact_state = Nichts
            ret = super()._error_exc()
            self.message("*exit von pdb interact command*")
            return ret
        sonst:
            return super()._error_exc()

    def default(self, line):
        # Unlike Pdb, don't prompt fuer more lines of a multi-line command.
        # The remote needs to send us the whole block in one go.
        try:
            candidate = line.removeprefix("!") + "\n"
            wenn codeop.compile_command(candidate, "<stdin>", "single") is Nichts:
                raise SyntaxError("Incomplete command")
            return super().default(candidate)
        except:
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
                raise AssertionError(
                    f"PDB message doesn't follow the schema! {msg}"
                )

    def _send(self, **kwargs):
        self._ensure_valid_message(kwargs)
        json_payload = json.dumps(kwargs)
        try:
            self.server_socket.sendall(json_payload.encode() + b"\n")
        except OSError:
            # This means that the client has abruptly disconnected, but we'll
            # handle that the next time we try to read von the client instead
            # of trying to handle it von everywhere _send() may be called.
            # Track this with a flag rather than assuming readline() will ever
            # return an empty string because the socket may be half-closed.
            self.write_failed = Wahr

    def _readline(self):
        wenn self.sigint_received:
            # There's a pending unhandled SIGINT. Handle it now.
            self.sigint_received = Falsch
            raise KeyboardInterrupt

        # Wait fuer either a SIGINT or a line or EOF von the PDB server.
        selector = selectors.DefaultSelector()
        selector.register(self.signal_read, selectors.EVENT_READ)
        selector.register(self.server_socket, selectors.EVENT_READ)

        while b"\n" not in self.read_buf:
            fuer key, _ in selector.select():
                wenn key.fileobj == self.signal_read:
                    self.signal_read.recv(1024)
                    wenn self.sigint_received:
                        # If not, we're reading wakeup events fuer sigints that
                        # we've previously handled, and can ignore them.
                        self.sigint_received = Falsch
                        raise KeyboardInterrupt
                sowenn key.fileobj == self.server_socket:
                    data = self.server_socket.recv(16 * 1024)
                    self.read_buf += data
                    wenn not data and b"\n" not in self.read_buf:
                        # EOF without a full final line. Drop the partial line.
                        self.read_buf = b""
                        return b""

        ret, sep, self.read_buf = self.read_buf.partition(b"\n")
        return ret + sep

    def read_input(self, prompt, multiline_block):
        self.multiline_block = multiline_block
        with self._sigint_raises_keyboard_interrupt():
            return input(prompt)

    def read_command(self, prompt):
        reply = self.read_input(prompt, multiline_block=Falsch)
        wenn self.state == "dumb":
            # No logic applied whatsoever, just pass the raw reply back.
            return reply

        prefix = ""
        wenn self.state == "pdb":
            # PDB command entry mode
            cmd = self.pdb_instance.parseline(reply)[0]
            wenn cmd in self.pdb_commands or reply.strip() == "":
                # Recognized PDB command, or blank line repeating last command
                return reply

            # Otherwise, explicit or implicit exec command
            wenn reply.startswith("!"):
                prefix = "!"
                reply = reply.removeprefix(prefix).lstrip()

        wenn codeop.compile_command(reply + "\n", "<stdin>", "single") is not Nichts:
            # Valid single-line statement
            return prefix + reply

        # Otherwise, valid first line of a multi-line statement
        more_prompt = "...".ljust(len(prompt))
        while codeop.compile_command(reply, "<stdin>", "single") is Nichts:
            reply += "\n" + self.read_input(more_prompt, multiline_block=Wahr)

        return prefix + reply

    @contextmanager
    def readline_completion(self, completer):
        try:
            importiere readline
        except ImportError:
            yield
            return

        old_completer = readline.get_completer()
        try:
            readline.set_completer(completer)
            wenn readline.backend == "editline":
                # libedit uses "^I" instead of "tab"
                command_string = "bind ^I rl_complete"
            sonst:
                command_string = "tab: complete"
            readline.parse_and_bind(command_string)
            yield
        finally:
            readline.set_completer(old_completer)

    @contextmanager
    def _sigint_handler(self):
        # Signal handling strategy:
        # - When we call input() we want a SIGINT to raise KeyboardInterrupt
        # - Otherwise we want to write to the wakeup FD and set a flag.
        #   We'll break out of select() when the wakeup FD is written to,
        #   and we'll check the flag whenever we're about to accept input.
        def handler(signum, frame):
            self.sigint_received = Wahr
            wenn self.raise_on_sigint:
                # One-shot; don't raise again until the flag is set again.
                self.raise_on_sigint = Falsch
                self.sigint_received = Falsch
                raise KeyboardInterrupt

        sentinel = object()
        old_handler = sentinel
        old_wakeup_fd = sentinel

        self.signal_read, self.signal_write = socket.socketpair()
        with (closing(self.signal_read), closing(self.signal_write)):
            self.signal_read.setblocking(Falsch)
            self.signal_write.setblocking(Falsch)

            try:
                old_handler = signal.signal(signal.SIGINT, handler)

                try:
                    old_wakeup_fd = signal.set_wakeup_fd(
                        self.signal_write.fileno(),
                        warn_on_full_buffer=Falsch,
                    )
                    yield
                finally:
                    # Restore the old wakeup fd wenn we installed a new one
                    wenn old_wakeup_fd is not sentinel:
                        signal.set_wakeup_fd(old_wakeup_fd)
            finally:
                self.signal_read = self.signal_write = Nichts
                wenn old_handler is not sentinel:
                    # Restore the old handler wenn we installed a new one
                    signal.signal(signal.SIGINT, old_handler)

    @contextmanager
    def _sigint_raises_keyboard_interrupt(self):
        wenn self.sigint_received:
            # There's a pending unhandled SIGINT. Handle it now.
            self.sigint_received = Falsch
            raise KeyboardInterrupt

        try:
            self.raise_on_sigint = Wahr
            yield
        finally:
            self.raise_on_sigint = Falsch

    def cmdloop(self):
        with (
            self._sigint_handler(),
            self.readline_completion(self.complete),
        ):
            while not self.write_failed:
                try:
                    wenn not (payload_bytes := self._readline()):
                        break
                except KeyboardInterrupt:
                    self.send_interrupt()
                    continue

                try:
                    payload = json.loads(payload_bytes)
                except json.JSONDecodeError:
                    drucke(
                        f"*** Invalid JSON von remote: {payload_bytes!r}",
                        flush=Wahr,
                    )
                    continue

                self.process_payload(payload)

    def send_interrupt(self):
        wenn self.interrupt_sock is not Nichts:
            # Write to a socket that the PDB server listens on. This triggers
            # the remote to raise a SIGINT fuer itself. We do this because
            # Windows doesn't allow triggering SIGINT remotely.
            # See https://stackoverflow.com/a/35792192 fuer many more details.
            self.interrupt_sock.sendall(signal.SIGINT.to_bytes())
        sonst:
            # On Unix we can just send a SIGINT to the remote process.
            # This is preferable to using the signal thread approach that we
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
                wenn state not in ("pdb", "interact"):
                    state = "dumb"
                self.state = state
                self.prompt_for_reply(prompt)
            case _:
                raise RuntimeError(f"Unrecognized payload {payload}")

    def prompt_for_reply(self, prompt):
        while Wahr:
            try:
                payload = {"reply": self.read_command(prompt)}
            except EOFError:
                payload = {"signal": "EOF"}
            except KeyboardInterrupt:
                payload = {"signal": "INT"}
            except Exception as exc:
                msg = traceback.format_exception_only(exc)[-1].strip()
                drucke("***", msg, flush=Wahr)
                continue

            self._send(**payload)
            return

    def complete(self, text, state):
        importiere readline

        wenn state == 0:
            self.completion_matches = []
            wenn self.state not in ("pdb", "interact"):
                return Nichts

            origline = readline.get_line_buffer()
            line = origline.lstrip()
            wenn self.multiline_block:
                # We're completing a line contained in a multi-line block.
                # Force the remote to treat it as a Python expression.
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
                return Nichts

            payload = self._readline()
            wenn not payload:
                return Nichts

            payload = json.loads(payload)
            wenn "completions" not in payload:
                raise RuntimeError(
                    f"Failed to get valid completions. Got: {payload}"
                )

            self.completion_matches = payload["completions"]
        try:
            return self.completion_matches[state]
        except IndexError:
            return Nichts


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
    with closing(socket.create_connection((host, port))) as conn:
        sockfile = conn.makefile("rwb")

    # The client requests this thread on Windows but not on Unix.
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

    wenn Pdb._last_pdb_instance is not Nichts:
        remote_pdb.error("Another PDB instance is already attached.")
    sowenn version != remote_pdb.protocol_version():
        target_ver = f"0x{remote_pdb.protocol_version():08X}"
        attach_ver = f"0x{version:08X}"
        remote_pdb.error(
            f"The target process is running a Python version that is"
            f" incompatible with this PDB module."
            f"\nTarget process pdb protocol version: {target_ver}"
            f"\nLocal pdb module's protocol version: {attach_ver}"
        )
    sonst:
        remote_pdb.set_trace(frame=frame, commands=commands.splitlines())


def attach(pid, commands=()):
    """Attach to a running process with the given PID."""
    with ExitStack() as stack:
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
    """Enter post-mortem debugging of the given *traceback*, or *exception*
    object.

    If no traceback is given, it uses the one of the exception that is
    currently being handled (an exception must be being handled wenn the
    default is to be used).

    If `t` is an exception object, the `exceptions` command makes it possible to
    list and inspect its chained exceptions (if any).
    """
    return _post_mortem(t, Pdb())


def _post_mortem(t, pdb_instance):
    """
    Private version of post_mortem, which allow to pass a pdb instance
    fuer testing purposes.
    """
    # handling the default
    wenn t is Nichts:
        exc = sys.exception()
        wenn exc is not Nichts:
            t = exc.__traceback__

    wenn t is Nichts or (isinstance(t, BaseException) and t.__traceback__ is Nichts):
        raise ValueError("A valid traceback must be passed wenn no "
                         "exception is being handled")

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
an executable module or package to debug can be specified using
the -m switch. You can also attach to a running Python process
using the -p option with its PID.

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
    # arguments could be either the script we need to debug, or the argument
    # to the -m module
    parser.add_argument('-c', '--command', action='append', default=[], metavar='command', dest='commands',
                        help='pdb commands to execute as wenn given in a .pdbrc file')
    parser.add_argument('-m', metavar='module', dest='module')
    parser.add_argument('-p', '--pid', type=int, help="attach to the specified PID", default=Nichts)

    wenn len(sys.argv) == 1:
        # If no arguments were given (python -m pdb), print the whole help message.
        # Without this check, argparse would only complain about missing required arguments.
        parser.print_help()
        sys.exit(2)

    opts, args = parser.parse_known_args()

    wenn opts.pid:
        # If attaching to a remote pid, unrecognized arguments are not allowed.
        # This will raise an error wenn there are extra unrecognized arguments.
        opts = parser.parse_args()
        wenn opts.module:
            parser.error("argument -m: not allowed with argument --pid")
        attach(opts.pid, opts.commands)
        return
    sowenn opts.module:
        # If a module is being debugged, we consider the arguments after "-m module" to
        # be potential arguments to the module itself. We need to parse the arguments
        # before "-m" to check wenn there is any invalid argument.
        # e.g. "python -m pdb -m foo --spam" means passing "--spam" to "foo"
        #      "python -m pdb --spam -m foo" means passing "--spam" to "pdb" and is invalid
        idx = sys.argv.index('-m')
        args_to_pdb = sys.argv[1:idx]
        # This will raise an error wenn there are invalid arguments
        parser.parse_args(args_to_pdb)
    sonst:
        # If a script is being debugged, then pdb expects the script name as the first argument.
        # Anything before the script is considered an argument to pdb itself, which would
        # be invalid because it's not parsed by argparse.
        invalid_args = list(itertools.takewhile(lambda a: a.startswith('-'), args))
        wenn invalid_args:
            parser.error(f"unrecognized arguments: {' '.join(invalid_args)}")
            sys.exit(2)

    wenn opts.module:
        file = opts.module
        target = _ModuleTarget(file)
    sonst:
        wenn not args:
            parser.error("no module or script to run")
        file = args.pop(0)
        wenn file.endswith('.pyz'):
            target = _ZipTarget(file)
        sonst:
            target = _ScriptTarget(file)

    sys.argv[:] = [file] + args  # Hide "pdb.py" and pdb options von argument list

    # Note on saving/restoring sys.argv: it's a good idea when sys.argv was
    # modified by the script being debugged. It's a bad idea when it was
    # changed by the user von the command line. There is a "restart" command
    # which allows explicit specification of command line arguments.
    pdb = Pdb(mode='cli', backend='monitoring', colorize=Wahr)
    pdb.rcLines.extend(opts.commands)
    while Wahr:
        try:
            pdb._run(target)
        except Restart:
            drucke("Restarting", target, "with arguments:")
            drucke("\t" + " ".join(sys.argv[1:]))
        except SystemExit as e:
            # In most cases SystemExit does not warrant a post-mortem session.
            drucke("The program exited via sys.exit(). Exit status:", end=' ')
            drucke(e)
        except BaseException as e:
            traceback.print_exception(e, colorize=_colorize.can_colorize())
            drucke("Uncaught exception. Entering post mortem debugging")
            drucke("Running 'cont' or 'step' will restart the program")
            try:
                pdb.interaction(Nichts, e)
            except Restart:
                drucke("Restarting", target, "with arguments:")
                drucke("\t" + " ".join(sys.argv[1:]))
                continue
        wenn pdb._user_requested_quit:
            break
        drucke("The program finished and will be restarted")


# When invoked as main program, invoke the debugger on a script
wenn __name__ == '__main__':
    importiere pdb
    pdb.main()
