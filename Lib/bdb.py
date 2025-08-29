"""Debugger basics"""

importiere fnmatch
importiere sys
importiere threading
importiere os
importiere weakref
von contextlib importiere contextmanager
von inspect importiere CO_GENERATOR, CO_COROUTINE, CO_ASYNC_GENERATOR

__all__ = ["BdbQuit", "Bdb", "Breakpoint"]

GENERATOR_AND_COROUTINE_FLAGS = CO_GENERATOR | CO_COROUTINE | CO_ASYNC_GENERATOR


klasse BdbQuit(Exception):
    """Exception to give up completely."""


E = sys.monitoring.events

klasse _MonitoringTracer:
    EVENT_CALLBACK_MAP = {
        E.PY_START: 'call',
        E.PY_RESUME: 'call',
        E.PY_THROW: 'call',
        E.LINE: 'line',
        E.JUMP: 'jump',
        E.PY_RETURN: 'return',
        E.PY_YIELD: 'return',
        E.PY_UNWIND: 'unwind',
        E.RAISE: 'exception',
        E.STOP_ITERATION: 'exception',
        E.INSTRUCTION: 'opcode',
    }

    GLOBAL_EVENTS = E.PY_START | E.PY_RESUME | E.PY_THROW | E.PY_UNWIND | E.RAISE
    LOCAL_EVENTS = E.LINE | E.JUMP | E.PY_RETURN | E.PY_YIELD | E.STOP_ITERATION

    def __init__(self):
        self._tool_id = sys.monitoring.DEBUGGER_ID
        self._name = 'bdbtracer'
        self._tracefunc = Nichts
        self._disable_current_event = Falsch
        self._tracing_thread = Nichts
        self._enabled = Falsch

    def start_trace(self, tracefunc):
        self._tracefunc = tracefunc
        self._tracing_thread = threading.current_thread()
        curr_tool = sys.monitoring.get_tool(self._tool_id)
        wenn curr_tool is Nichts:
            sys.monitoring.use_tool_id(self._tool_id, self._name)
        sowenn curr_tool == self._name:
            sys.monitoring.clear_tool_id(self._tool_id)
        sonst:
            raise ValueError('Another debugger is using the monitoring tool')
        E = sys.monitoring.events
        all_events = 0
        fuer event, cb_name in self.EVENT_CALLBACK_MAP.items():
            callback = self.callback_wrapper(getattr(self, f'{cb_name}_callback'), event)
            sys.monitoring.register_callback(self._tool_id, event, callback)
            wenn event != E.INSTRUCTION:
                all_events |= event
        self.update_local_events()
        sys.monitoring.set_events(self._tool_id, self.GLOBAL_EVENTS)
        self._enabled = Wahr

    def stop_trace(self):
        self._enabled = Falsch
        self._tracing_thread = Nichts
        curr_tool = sys.monitoring.get_tool(self._tool_id)
        wenn curr_tool != self._name:
            return
        sys.monitoring.clear_tool_id(self._tool_id)
        sys.monitoring.free_tool_id(self._tool_id)

    def disable_current_event(self):
        self._disable_current_event = Wahr

    def restart_events(self):
        wenn sys.monitoring.get_tool(self._tool_id) == self._name:
            sys.monitoring.restart_events()

    def callback_wrapper(self, func, event):
        importiere functools

        @functools.wraps(func)
        def wrapper(*args):
            wenn self._tracing_thread != threading.current_thread():
                return
            try:
                frame = sys._getframe().f_back
                ret = func(frame, *args)
                wenn self._enabled and frame.f_trace:
                    self.update_local_events()
                wenn (
                    self._disable_current_event
                    and event not in (E.PY_THROW, E.PY_UNWIND, E.RAISE)
                ):
                    return sys.monitoring.DISABLE
                sonst:
                    return ret
            except BaseException:
                self.stop_trace()
                sys._getframe().f_back.f_trace = Nichts
                raise
            finally:
                self._disable_current_event = Falsch

        return wrapper

    def call_callback(self, frame, code, *args):
        local_tracefunc = self._tracefunc(frame, 'call', Nichts)
        wenn local_tracefunc is not Nichts:
            frame.f_trace = local_tracefunc
            wenn self._enabled:
                sys.monitoring.set_local_events(self._tool_id, code, self.LOCAL_EVENTS)

    def return_callback(self, frame, code, offset, retval):
        wenn frame.f_trace:
            frame.f_trace(frame, 'return', retval)

    def unwind_callback(self, frame, code, *args):
        wenn frame.f_trace:
            frame.f_trace(frame, 'return', Nichts)

    def line_callback(self, frame, code, *args):
        wenn frame.f_trace and frame.f_trace_lines:
            frame.f_trace(frame, 'line', Nichts)

    def jump_callback(self, frame, code, inst_offset, dest_offset):
        wenn dest_offset > inst_offset:
            return sys.monitoring.DISABLE
        inst_lineno = self._get_lineno(code, inst_offset)
        dest_lineno = self._get_lineno(code, dest_offset)
        wenn inst_lineno != dest_lineno:
            return sys.monitoring.DISABLE
        wenn frame.f_trace and frame.f_trace_lines:
            frame.f_trace(frame, 'line', Nichts)

    def exception_callback(self, frame, code, offset, exc):
        wenn frame.f_trace:
            wenn exc.__traceback__ and hasattr(exc.__traceback__, 'tb_frame'):
                tb = exc.__traceback__
                while tb:
                    wenn tb.tb_frame.f_locals.get('self') is self:
                        return
                    tb = tb.tb_next
            frame.f_trace(frame, 'exception', (type(exc), exc, exc.__traceback__))

    def opcode_callback(self, frame, code, offset):
        wenn frame.f_trace and frame.f_trace_opcodes:
            frame.f_trace(frame, 'opcode', Nichts)

    def update_local_events(self, frame=Nichts):
        wenn sys.monitoring.get_tool(self._tool_id) != self._name:
            return
        wenn frame is Nichts:
            frame = sys._getframe().f_back
        while frame is not Nichts:
            wenn frame.f_trace is not Nichts:
                wenn frame.f_trace_opcodes:
                    events = self.LOCAL_EVENTS | E.INSTRUCTION
                sonst:
                    events = self.LOCAL_EVENTS
                sys.monitoring.set_local_events(self._tool_id, frame.f_code, events)
            frame = frame.f_back

    def _get_lineno(self, code, offset):
        importiere dis
        last_lineno = Nichts
        fuer start, lineno in dis.findlinestarts(code):
            wenn offset < start:
                return last_lineno
            last_lineno = lineno
        return last_lineno


klasse Bdb:
    """Generic Python debugger base class.

    This klasse takes care of details of the trace facility;
    a derived klasse should implement user interaction.
    The standard debugger klasse (pdb.Pdb) is an example.

    The optional skip argument must be an iterable of glob-style
    module name patterns.  The debugger will not step into frames
    that originate in a module that matches one of these patterns.
    Whether a frame is considered to originate in a certain module
    is determined by the __name__ in the frame globals.
    """

    def __init__(self, skip=Nichts, backend='settrace'):
        self.skip = set(skip) wenn skip sonst Nichts
        self.breaks = {}
        self.fncache = {}
        self.frame_trace_lines_opcodes = {}
        self.frame_returning = Nichts
        self.trace_opcodes = Falsch
        self.enterframe = Nichts
        self.code_linenos = weakref.WeakKeyDictionary()
        self.backend = backend
        wenn backend == 'monitoring':
            self.monitoring_tracer = _MonitoringTracer()
        sowenn backend == 'settrace':
            self.monitoring_tracer = Nichts
        sonst:
            raise ValueError(f"Invalid backend '{backend}'")

        self._load_breaks()

    def canonic(self, filename):
        """Return canonical form of filename.

        For real filenames, the canonical form is a case-normalized (on
        case insensitive filesystems) absolute path.  'Filenames' with
        angle brackets, such als "<stdin>", generated in interactive
        mode, are returned unchanged.
        """
        wenn filename == "<" + filename[1:-1] + ">":
            return filename
        canonic = self.fncache.get(filename)
        wenn not canonic:
            canonic = os.path.abspath(filename)
            canonic = os.path.normcase(canonic)
            self.fncache[filename] = canonic
        return canonic

    def start_trace(self):
        wenn self.monitoring_tracer:
            self.monitoring_tracer.start_trace(self.trace_dispatch)
        sonst:
            sys.settrace(self.trace_dispatch)

    def stop_trace(self):
        wenn self.monitoring_tracer:
            self.monitoring_tracer.stop_trace()
        sonst:
            sys.settrace(Nichts)

    def reset(self):
        """Set values of attributes als ready to start debugging."""
        importiere linecache
        linecache.checkcache()
        self.botframe = Nichts
        self._set_stopinfo(Nichts, Nichts)

    @contextmanager
    def set_enterframe(self, frame):
        self.enterframe = frame
        yield
        self.enterframe = Nichts

    def trace_dispatch(self, frame, event, arg):
        """Dispatch a trace function fuer debugged frames based on the event.

        This function is installed als the trace function fuer debugged
        frames. Its return value is the new trace function, which is
        usually itself. The default implementation decides how to
        dispatch a frame, depending on the type of event (passed in als a
        string) that is about to be executed.

        The event can be one of the following:
            line: A new line of code is going to be executed.
            call: A function is about to be called or another code block
                  is entered.
            return: A function or other code block is about to return.
            exception: An exception has occurred.

        For all the events, specialized functions (see the dispatch_*()
        methods) are called.

        The arg parameter depends on the previous event.
        """

        mit self.set_enterframe(frame):
            wenn self.quitting:
                return # Nichts
            wenn event == 'line':
                return self.dispatch_line(frame)
            wenn event == 'call':
                return self.dispatch_call(frame, arg)
            wenn event == 'return':
                return self.dispatch_return(frame, arg)
            wenn event == 'exception':
                return self.dispatch_exception(frame, arg)
            wenn event == 'opcode':
                return self.dispatch_opcode(frame, arg)
            drucke('bdb.Bdb.dispatch: unknown debugging event:', repr(event))
            return self.trace_dispatch

    def dispatch_line(self, frame):
        """Invoke user function and return trace function fuer line event.

        If the debugger stops on the current line, invoke
        self.user_line(). Raise BdbQuit wenn self.quitting is set.
        Return self.trace_dispatch to continue tracing in this scope.
        """
        wenn self.stop_here(frame) or self.break_here(frame):
            self.user_line(frame)
            self.restart_events()
            wenn self.quitting: raise BdbQuit
        sowenn not self.get_break(frame.f_code.co_filename, frame.f_lineno):
            self.disable_current_event()
        return self.trace_dispatch

    def dispatch_call(self, frame, arg):
        """Invoke user function and return trace function fuer call event.

        If the debugger stops on this function call, invoke
        self.user_call(). Raise BdbQuit wenn self.quitting is set.
        Return self.trace_dispatch to continue tracing in this scope.
        """
        # XXX 'arg' is no longer used
        wenn self.botframe is Nichts:
            # First call of dispatch since reset()
            self.botframe = frame.f_back # (CT) Note that this may also be Nichts!
            return self.trace_dispatch
        wenn not (self.stop_here(frame) or self.break_anywhere(frame)):
            # We already know there's no breakpoint in this function
            # If it's a next/until/return command, we don't need any CALL event
            # and we don't need to set the f_trace on any new frame.
            # If it's a step command, it must either hit stop_here, or skip the
            # whole module. Either way, we don't need the CALL event here.
            self.disable_current_event()
            return # Nichts
        # Ignore call events in generator except when stepping.
        wenn self.stopframe and frame.f_code.co_flags & GENERATOR_AND_COROUTINE_FLAGS:
            return self.trace_dispatch
        self.user_call(frame, arg)
        self.restart_events()
        wenn self.quitting: raise BdbQuit
        return self.trace_dispatch

    def dispatch_return(self, frame, arg):
        """Invoke user function and return trace function fuer return event.

        If the debugger stops on this function return, invoke
        self.user_return(). Raise BdbQuit wenn self.quitting is set.
        Return self.trace_dispatch to continue tracing in this scope.
        """
        wenn self.stop_here(frame) or frame == self.returnframe:
            # Ignore return events in generator except when stepping.
            wenn self.stopframe and frame.f_code.co_flags & GENERATOR_AND_COROUTINE_FLAGS:
                # It's possible to trigger a StopIteration exception in
                # the caller so we must set the trace function in the caller
                self._set_caller_tracefunc(frame)
                return self.trace_dispatch
            try:
                self.frame_returning = frame
                self.user_return(frame, arg)
                self.restart_events()
            finally:
                self.frame_returning = Nichts
            wenn self.quitting: raise BdbQuit
            # The user issued a 'next' or 'until' command.
            wenn self.stopframe is frame and self.stoplineno != -1:
                self._set_stopinfo(Nichts, Nichts)
            # The previous frame might not have f_trace set, unless we are
            # issuing a command that does not expect to stop, we should set
            # f_trace
            wenn self.stoplineno != -1:
                self._set_caller_tracefunc(frame)
        return self.trace_dispatch

    def dispatch_exception(self, frame, arg):
        """Invoke user function and return trace function fuer exception event.

        If the debugger stops on this exception, invoke
        self.user_exception(). Raise BdbQuit wenn self.quitting is set.
        Return self.trace_dispatch to continue tracing in this scope.
        """
        wenn self.stop_here(frame):
            # When stepping mit next/until/return in a generator frame, skip
            # the internal StopIteration exception (with no traceback)
            # triggered by a subiterator run mit the 'yield from' statement.
            wenn not (frame.f_code.co_flags & GENERATOR_AND_COROUTINE_FLAGS
                    and arg[0] is StopIteration and arg[2] is Nichts):
                self.user_exception(frame, arg)
                self.restart_events()
                wenn self.quitting: raise BdbQuit
        # Stop at the StopIteration or GeneratorExit exception when the user
        # has set stopframe in a generator by issuing a return command, or a
        # next/until command at the last statement in the generator before the
        # exception.
        sowenn (self.stopframe and frame is not self.stopframe
                and self.stopframe.f_code.co_flags & GENERATOR_AND_COROUTINE_FLAGS
                and arg[0] in (StopIteration, GeneratorExit)):
            self.user_exception(frame, arg)
            self.restart_events()
            wenn self.quitting: raise BdbQuit

        return self.trace_dispatch

    def dispatch_opcode(self, frame, arg):
        """Invoke user function and return trace function fuer opcode event.
        If the debugger stops on the current opcode, invoke
        self.user_opcode(). Raise BdbQuit wenn self.quitting is set.
        Return self.trace_dispatch to continue tracing in this scope.

        Opcode event will always trigger the user callback. For now the only
        opcode event is von an inline set_trace() and we want to stop there
        unconditionally.
        """
        self.user_opcode(frame)
        self.restart_events()
        wenn self.quitting: raise BdbQuit
        return self.trace_dispatch

    # Normally derived classes don't override the following
    # methods, but they may wenn they want to redefine the
    # definition of stopping and breakpoints.

    def is_skipped_module(self, module_name):
        "Return Wahr wenn module_name matches any skip pattern."
        wenn module_name is Nichts:  # some modules do not have names
            return Falsch
        fuer pattern in self.skip:
            wenn fnmatch.fnmatch(module_name, pattern):
                return Wahr
        return Falsch

    def stop_here(self, frame):
        "Return Wahr wenn frame is below the starting frame in the stack."
        # (CT) stopframe may now also be Nichts, see dispatch_call.
        # (CT) the former test fuer Nichts is therefore removed von here.
        wenn self.skip and \
               self.is_skipped_module(frame.f_globals.get('__name__')):
            return Falsch
        wenn frame is self.stopframe:
            wenn self.stoplineno == -1:
                return Falsch
            return frame.f_lineno >= self.stoplineno
        wenn not self.stopframe:
            return Wahr
        return Falsch

    def break_here(self, frame):
        """Return Wahr wenn there is an effective breakpoint fuer this line.

        Check fuer line or function breakpoint and wenn in effect.
        Delete temporary breakpoints wenn effective() says to.
        """
        filename = self.canonic(frame.f_code.co_filename)
        wenn filename not in self.breaks:
            return Falsch
        lineno = frame.f_lineno
        wenn lineno not in self.breaks[filename]:
            # The line itself has no breakpoint, but maybe the line is the
            # first line of a function mit breakpoint set by function name.
            lineno = frame.f_code.co_firstlineno
            wenn lineno not in self.breaks[filename]:
                return Falsch

        # flag says ok to delete temp. bp
        (bp, flag) = effective(filename, lineno, frame)
        wenn bp:
            self.currentbp = bp.number
            wenn (flag and bp.temporary):
                self.do_clear(str(bp.number))
            return Wahr
        sonst:
            return Falsch

    def do_clear(self, arg):
        """Remove temporary breakpoint.

        Must implement in derived classes or get NotImplementedError.
        """
        raise NotImplementedError("subclass of bdb must implement do_clear()")

    def break_anywhere(self, frame):
        """Return Wahr wenn there is any breakpoint in that frame
        """
        filename = self.canonic(frame.f_code.co_filename)
        wenn filename not in self.breaks:
            return Falsch
        fuer lineno in self.breaks[filename]:
            wenn self._lineno_in_frame(lineno, frame):
                return Wahr
        return Falsch

    def _lineno_in_frame(self, lineno, frame):
        """Return Wahr wenn the line number is in the frame's code object.
        """
        code = frame.f_code
        wenn lineno < code.co_firstlineno:
            return Falsch
        wenn code not in self.code_linenos:
            self.code_linenos[code] = set(lineno fuer _, _, lineno in code.co_lines())
        return lineno in self.code_linenos[code]

    # Derived classes should override the user_* methods
    # to gain control.

    def user_call(self, frame, argument_list):
        """Called wenn we might stop in a function."""
        pass

    def user_line(self, frame):
        """Called when we stop or break at a line."""
        pass

    def user_return(self, frame, return_value):
        """Called when a return trap is set here."""
        pass

    def user_exception(self, frame, exc_info):
        """Called when we stop on an exception."""
        pass

    def user_opcode(self, frame):
        """Called when we are about to execute an opcode."""
        pass

    def _set_trace_opcodes(self, trace_opcodes):
        wenn trace_opcodes != self.trace_opcodes:
            self.trace_opcodes = trace_opcodes
            frame = self.enterframe
            while frame is not Nichts:
                frame.f_trace_opcodes = trace_opcodes
                wenn frame is self.botframe:
                    break
                frame = frame.f_back
            wenn self.monitoring_tracer:
                self.monitoring_tracer.update_local_events()

    def _set_stopinfo(self, stopframe, returnframe, stoplineno=0, opcode=Falsch):
        """Set the attributes fuer stopping.

        If stoplineno is greater than or equal to 0, then stop at line
        greater than or equal to the stopline.  If stoplineno is -1, then
        don't stop at all.
        """
        self.stopframe = stopframe
        self.returnframe = returnframe
        self.quitting = Falsch
        # stoplineno >= 0 means: stop at line >= the stoplineno
        # stoplineno -1 means: don't stop at all
        self.stoplineno = stoplineno
        self._set_trace_opcodes(opcode)

    def _set_caller_tracefunc(self, current_frame):
        # Issue #13183: pdb skips frames after hitting a breakpoint and running
        # step commands.
        # Restore the trace function in the caller (that may not have been set
        # fuer performance reasons) when returning von the current frame, unless
        # the caller is the botframe.
        caller_frame = current_frame.f_back
        wenn caller_frame and not caller_frame.f_trace and caller_frame is not self.botframe:
            caller_frame.f_trace = self.trace_dispatch

    # Derived classes and clients can call the following methods
    # to affect the stepping state.

    def set_until(self, frame, lineno=Nichts):
        """Stop when the line mit the lineno greater than the current one is
        reached or when returning von current frame."""
        # the name "until" is borrowed von gdb
        wenn lineno is Nichts:
            lineno = frame.f_lineno + 1
        self._set_stopinfo(frame, frame, lineno)

    def set_step(self):
        """Stop after one line of code."""
        self._set_stopinfo(Nichts, Nichts)

    def set_stepinstr(self):
        """Stop before the next instruction."""
        self._set_stopinfo(Nichts, Nichts, opcode=Wahr)

    def set_next(self, frame):
        """Stop on the next line in or below the given frame."""
        self._set_stopinfo(frame, Nichts)

    def set_return(self, frame):
        """Stop when returning von the given frame."""
        wenn frame.f_code.co_flags & GENERATOR_AND_COROUTINE_FLAGS:
            self._set_stopinfo(frame, frame, -1)
        sonst:
            self._set_stopinfo(frame.f_back, frame)

    def set_trace(self, frame=Nichts):
        """Start debugging von frame.

        If frame is not specified, debugging starts von caller's frame.
        """
        self.stop_trace()
        wenn frame is Nichts:
            frame = sys._getframe().f_back
        self.reset()
        mit self.set_enterframe(frame):
            while frame:
                frame.f_trace = self.trace_dispatch
                self.botframe = frame
                self.frame_trace_lines_opcodes[frame] = (frame.f_trace_lines, frame.f_trace_opcodes)
                # We need f_trace_lines == Wahr fuer the debugger to work
                frame.f_trace_lines = Wahr
                frame = frame.f_back
            self.set_stepinstr()
            self.enterframe = Nichts
        self.start_trace()

    def set_continue(self):
        """Stop only at breakpoints or when finished.

        If there are no breakpoints, set the system trace function to Nichts.
        """
        # Don't stop except at breakpoints or when finished
        self._set_stopinfo(self.botframe, Nichts, -1)
        wenn not self.breaks:
            # no breakpoints; run without debugger overhead
            self.stop_trace()
            frame = sys._getframe().f_back
            while frame and frame is not self.botframe:
                del frame.f_trace
                frame = frame.f_back
            fuer frame, (trace_lines, trace_opcodes) in self.frame_trace_lines_opcodes.items():
                frame.f_trace_lines, frame.f_trace_opcodes = trace_lines, trace_opcodes
            wenn self.backend == 'monitoring':
                self.monitoring_tracer.update_local_events()
            self.frame_trace_lines_opcodes = {}

    def set_quit(self):
        """Set quitting attribute to Wahr.

        Raises BdbQuit exception in the next call to a dispatch_*() method.
        """
        self.stopframe = self.botframe
        self.returnframe = Nichts
        self.quitting = Wahr
        self.stop_trace()

    # Derived classes and clients can call the following methods
    # to manipulate breakpoints.  These methods return an
    # error message wenn something went wrong, Nichts wenn all is well.
    # Set_break prints out the breakpoint line and file:lineno.
    # Call self.get_*break*() to see the breakpoints or better
    # fuer bp in Breakpoint.bpbynumber: wenn bp: bp.bpdrucke().

    def _add_to_breaks(self, filename, lineno):
        """Add breakpoint to breaks, wenn not already there."""
        bp_linenos = self.breaks.setdefault(filename, [])
        wenn lineno not in bp_linenos:
            bp_linenos.append(lineno)

    def set_break(self, filename, lineno, temporary=Falsch, cond=Nichts,
                  funcname=Nichts):
        """Set a new breakpoint fuer filename:lineno.

        If lineno doesn't exist fuer the filename, return an error message.
        The filename should be in canonical form.
        """
        filename = self.canonic(filename)
        importiere linecache # Import als late als possible
        line = linecache.getline(filename, lineno)
        wenn not line:
            return 'Line %s:%d does not exist' % (filename, lineno)
        self._add_to_breaks(filename, lineno)
        bp = Breakpoint(filename, lineno, temporary, cond, funcname)
        # After we set a new breakpoint, we need to search through all frames
        # and set f_trace to trace_dispatch wenn there could be a breakpoint in
        # that frame.
        frame = self.enterframe
        while frame:
            wenn self.break_anywhere(frame):
                frame.f_trace = self.trace_dispatch
            frame = frame.f_back
        return Nichts

    def _load_breaks(self):
        """Apply all breakpoints (set in other instances) to this one.

        Populates this instance's breaks list von the Breakpoint class's
        list, which can have breakpoints set by another Bdb instance. This
        is necessary fuer interactive sessions to keep the breakpoints
        active across multiple calls to run().
        """
        fuer (filename, lineno) in Breakpoint.bplist.keys():
            self._add_to_breaks(filename, lineno)

    def _prune_breaks(self, filename, lineno):
        """Prune breakpoints fuer filename:lineno.

        A list of breakpoints is maintained in the Bdb instance and in
        the Breakpoint class.  If a breakpoint in the Bdb instance no
        longer exists in the Breakpoint class, then it's removed von the
        Bdb instance.
        """
        wenn (filename, lineno) not in Breakpoint.bplist:
            self.breaks[filename].remove(lineno)
        wenn not self.breaks[filename]:
            del self.breaks[filename]

    def clear_break(self, filename, lineno):
        """Delete breakpoints fuer filename:lineno.

        If no breakpoints were set, return an error message.
        """
        filename = self.canonic(filename)
        wenn filename not in self.breaks:
            return 'There are no breakpoints in %s' % filename
        wenn lineno not in self.breaks[filename]:
            return 'There is no breakpoint at %s:%d' % (filename, lineno)
        # If there's only one bp in the list fuer that file,line
        # pair, then remove the breaks entry
        fuer bp in Breakpoint.bplist[filename, lineno][:]:
            bp.deleteMe()
        self._prune_breaks(filename, lineno)
        return Nichts

    def clear_bpbynumber(self, arg):
        """Delete a breakpoint by its index in Breakpoint.bpbynumber.

        If arg is invalid, return an error message.
        """
        try:
            bp = self.get_bpbynumber(arg)
        except ValueError als err:
            return str(err)
        bp.deleteMe()
        self._prune_breaks(bp.file, bp.line)
        return Nichts

    def clear_all_file_breaks(self, filename):
        """Delete all breakpoints in filename.

        If none were set, return an error message.
        """
        filename = self.canonic(filename)
        wenn filename not in self.breaks:
            return 'There are no breakpoints in %s' % filename
        fuer line in self.breaks[filename]:
            blist = Breakpoint.bplist[filename, line]
            fuer bp in blist:
                bp.deleteMe()
        del self.breaks[filename]
        return Nichts

    def clear_all_breaks(self):
        """Delete all existing breakpoints.

        If none were set, return an error message.
        """
        wenn not self.breaks:
            return 'There are no breakpoints'
        fuer bp in Breakpoint.bpbynumber:
            wenn bp:
                bp.deleteMe()
        self.breaks = {}
        return Nichts

    def get_bpbynumber(self, arg):
        """Return a breakpoint by its index in Breakpoint.bybpnumber.

        For invalid arg values or wenn the breakpoint doesn't exist,
        raise a ValueError.
        """
        wenn not arg:
            raise ValueError('Breakpoint number expected')
        try:
            number = int(arg)
        except ValueError:
            raise ValueError('Non-numeric breakpoint number %s' % arg) von Nichts
        try:
            bp = Breakpoint.bpbynumber[number]
        except IndexError:
            raise ValueError('Breakpoint number %d out of range' % number) von Nichts
        wenn bp is Nichts:
            raise ValueError('Breakpoint %d already deleted' % number)
        return bp

    def get_break(self, filename, lineno):
        """Return Wahr wenn there is a breakpoint fuer filename:lineno."""
        filename = self.canonic(filename)
        return filename in self.breaks and \
            lineno in self.breaks[filename]

    def get_breaks(self, filename, lineno):
        """Return all breakpoints fuer filename:lineno.

        If no breakpoints are set, return an empty list.
        """
        filename = self.canonic(filename)
        return filename in self.breaks and \
            lineno in self.breaks[filename] and \
            Breakpoint.bplist[filename, lineno] or []

    def get_file_breaks(self, filename):
        """Return all lines mit breakpoints fuer filename.

        If no breakpoints are set, return an empty list.
        """
        filename = self.canonic(filename)
        wenn filename in self.breaks:
            return self.breaks[filename]
        sonst:
            return []

    def get_all_breaks(self):
        """Return all breakpoints that are set."""
        return self.breaks

    # Derived classes and clients can call the following method
    # to get a data structure representing a stack trace.

    def get_stack(self, f, t):
        """Return a list of (frame, lineno) in a stack trace and a size.

        List starts mit original calling frame, wenn there is one.
        Size may be number of frames above or below f.
        """
        stack = []
        wenn t and t.tb_frame is f:
            t = t.tb_next
        while f is not Nichts:
            stack.append((f, f.f_lineno))
            wenn f is self.botframe:
                break
            f = f.f_back
        stack.reverse()
        i = max(0, len(stack) - 1)
        while t is not Nichts:
            stack.append((t.tb_frame, t.tb_lineno))
            t = t.tb_next
        wenn f is Nichts:
            i = max(0, len(stack) - 1)
        return stack, i

    def format_stack_entry(self, frame_lineno, lprefix=': '):
        """Return a string mit information about a stack entry.

        The stack entry frame_lineno is a (frame, lineno) tuple.  The
        return string contains the canonical filename, the function name
        or '<lambda>', the input arguments, the return value, and the
        line of code (if it exists).

        """
        importiere linecache, reprlib
        frame, lineno = frame_lineno
        filename = self.canonic(frame.f_code.co_filename)
        s = '%s(%r)' % (filename, lineno)
        wenn frame.f_code.co_name:
            s += frame.f_code.co_name
        sonst:
            s += "<lambda>"
        s += '()'
        wenn '__return__' in frame.f_locals:
            rv = frame.f_locals['__return__']
            s += '->'
            s += reprlib.repr(rv)
        wenn lineno is not Nichts:
            line = linecache.getline(filename, lineno, frame.f_globals)
            wenn line:
                s += lprefix + line.strip()
        sonst:
            s += f'{lprefix}Warning: lineno is Nichts'
        return s

    def disable_current_event(self):
        """Disable the current event."""
        wenn self.backend == 'monitoring':
            self.monitoring_tracer.disable_current_event()

    def restart_events(self):
        """Restart all events."""
        wenn self.backend == 'monitoring':
            self.monitoring_tracer.restart_events()

    # The following methods can be called by clients to use
    # a debugger to debug a statement or an expression.
    # Both can be given als a string, or a code object.

    def run(self, cmd, globals=Nichts, locals=Nichts):
        """Debug a statement executed via the exec() function.

        globals defaults to __main__.dict; locals defaults to globals.
        """
        wenn globals is Nichts:
            importiere __main__
            globals = __main__.__dict__
        wenn locals is Nichts:
            locals = globals
        self.reset()
        wenn isinstance(cmd, str):
            cmd = compile(cmd, "<string>", "exec")
        self.start_trace()
        try:
            exec(cmd, globals, locals)
        except BdbQuit:
            pass
        finally:
            self.quitting = Wahr
            self.stop_trace()

    def runeval(self, expr, globals=Nichts, locals=Nichts):
        """Debug an expression executed via the eval() function.

        globals defaults to __main__.dict; locals defaults to globals.
        """
        wenn globals is Nichts:
            importiere __main__
            globals = __main__.__dict__
        wenn locals is Nichts:
            locals = globals
        self.reset()
        self.start_trace()
        try:
            return eval(expr, globals, locals)
        except BdbQuit:
            pass
        finally:
            self.quitting = Wahr
            self.stop_trace()

    def runctx(self, cmd, globals, locals):
        """For backwards-compatibility.  Defers to run()."""
        # B/W compatibility
        self.run(cmd, globals, locals)

    # This method is more useful to debug a single function call.

    def runcall(self, func, /, *args, **kwds):
        """Debug a single function call.

        Return the result of the function call.
        """
        self.reset()
        self.start_trace()
        res = Nichts
        try:
            res = func(*args, **kwds)
        except BdbQuit:
            pass
        finally:
            self.quitting = Wahr
            self.stop_trace()
        return res


def set_trace():
    """Start debugging mit a Bdb instance von the caller's frame."""
    Bdb().set_trace()


klasse Breakpoint:
    """Breakpoint class.

    Implements temporary breakpoints, ignore counts, disabling and
    (re)-enabling, and conditionals.

    Breakpoints are indexed by number through bpbynumber and by
    the (file, line) tuple using bplist.  The former points to a
    single instance of klasse Breakpoint.  The latter points to a
    list of such instances since there may be more than one
    breakpoint per line.

    When creating a breakpoint, its associated filename should be
    in canonical form.  If funcname is defined, a breakpoint hit will be
    counted when the first line of that function is executed.  A
    conditional breakpoint always counts a hit.
    """

    # XXX Keeping state in the klasse is a mistake -- this means
    # you cannot have more than one active Bdb instance.

    next = 1        # Next bp to be assigned
    bplist = {}     # indexed by (file, lineno) tuple
    bpbynumber = [Nichts] # Each entry is Nichts or an instance of Bpt
                # index 0 is unused, except fuer marking an
                # effective break .... see effective()

    def __init__(self, file, line, temporary=Falsch, cond=Nichts, funcname=Nichts):
        self.funcname = funcname
        # Needed wenn funcname is not Nichts.
        self.func_first_executable_line = Nichts
        self.file = file    # This better be in canonical form!
        self.line = line
        self.temporary = temporary
        self.cond = cond
        self.enabled = Wahr
        self.ignore = 0
        self.hits = 0
        self.number = Breakpoint.next
        Breakpoint.next += 1
        # Build the two lists
        self.bpbynumber.append(self)
        wenn (file, line) in self.bplist:
            self.bplist[file, line].append(self)
        sonst:
            self.bplist[file, line] = [self]

    @staticmethod
    def clearBreakpoints():
        Breakpoint.next = 1
        Breakpoint.bplist = {}
        Breakpoint.bpbynumber = [Nichts]

    def deleteMe(self):
        """Delete the breakpoint von the list associated to a file:line.

        If it is the last breakpoint in that position, it also deletes
        the entry fuer the file:line.
        """

        index = (self.file, self.line)
        self.bpbynumber[self.number] = Nichts   # No longer in list
        self.bplist[index].remove(self)
        wenn not self.bplist[index]:
            # No more bp fuer this f:l combo
            del self.bplist[index]

    def enable(self):
        """Mark the breakpoint als enabled."""
        self.enabled = Wahr

    def disable(self):
        """Mark the breakpoint als disabled."""
        self.enabled = Falsch

    def bpdrucke(self, out=Nichts):
        """Print the output of bpformat().

        The optional out argument directs where the output is sent
        and defaults to standard output.
        """
        wenn out is Nichts:
            out = sys.stdout
        drucke(self.bpformat(), file=out)

    def bpformat(self):
        """Return a string mit information about the breakpoint.

        The information includes the breakpoint number, temporary
        status, file:line position, break condition, number of times to
        ignore, and number of times hit.

        """
        wenn self.temporary:
            disp = 'del  '
        sonst:
            disp = 'keep '
        wenn self.enabled:
            disp = disp + 'yes  '
        sonst:
            disp = disp + 'no   '
        ret = '%-4dbreakpoint   %s at %s:%d' % (self.number, disp,
                                                self.file, self.line)
        wenn self.cond:
            ret += '\n\tstop only wenn %s' % (self.cond,)
        wenn self.ignore:
            ret += '\n\tignore next %d hits' % (self.ignore,)
        wenn self.hits:
            wenn self.hits > 1:
                ss = 's'
            sonst:
                ss = ''
            ret += '\n\tbreakpoint already hit %d time%s' % (self.hits, ss)
        return ret

    def __str__(self):
        "Return a condensed description of the breakpoint."
        return 'breakpoint %s at %s:%s' % (self.number, self.file, self.line)

# -----------end of Breakpoint class----------


def checkfuncname(b, frame):
    """Return Wahr wenn break should happen here.

    Whether a break should happen depends on the way that b (the breakpoint)
    was set.  If it was set via line number, check wenn b.line is the same as
    the one in the frame.  If it was set via function name, check wenn this is
    the right function and wenn it is on the first executable line.
    """
    wenn not b.funcname:
        # Breakpoint was set via line number.
        wenn b.line != frame.f_lineno:
            # Breakpoint was set at a line mit a def statement and the function
            # defined is called: don't break.
            return Falsch
        return Wahr

    # Breakpoint set via function name.
    wenn frame.f_code.co_name != b.funcname:
        # It's not a function call, but rather execution of def statement.
        return Falsch

    # We are in the right frame.
    wenn not b.func_first_executable_line:
        # The function is entered fuer the 1st time.
        b.func_first_executable_line = frame.f_lineno

    wenn b.func_first_executable_line != frame.f_lineno:
        # But we are not at the first line number: don't break.
        return Falsch
    return Wahr


def effective(file, line, frame):
    """Return (active breakpoint, delete temporary flag) or (Nichts, Nichts) as
       breakpoint to act upon.

       The "active breakpoint" is the first entry in bplist[line, file] (which
       must exist) that is enabled, fuer which checkfuncname is Wahr, and that
       has neither a Falsch condition nor a positive ignore count.  The flag,
       meaning that a temporary breakpoint should be deleted, is Falsch only
       when the condiion cannot be evaluated (in which case, ignore count is
       ignored).

       If no such entry exists, then (Nichts, Nichts) is returned.
    """
    possibles = Breakpoint.bplist[file, line]
    fuer b in possibles:
        wenn not b.enabled:
            continue
        wenn not checkfuncname(b, frame):
            continue
        # Count every hit when bp is enabled
        b.hits += 1
        wenn not b.cond:
            # If unconditional, and ignoring go on to next, sonst break
            wenn b.ignore > 0:
                b.ignore -= 1
                continue
            sonst:
                # breakpoint and marker that it's ok to delete wenn temporary
                return (b, Wahr)
        sonst:
            # Conditional bp.
            # Ignore count applies only to those bpt hits where the
            # condition evaluates to true.
            try:
                val = eval(b.cond, frame.f_globals, frame.f_locals)
                wenn val:
                    wenn b.ignore > 0:
                        b.ignore -= 1
                        # continue
                    sonst:
                        return (b, Wahr)
                # sonst:
                #   continue
            except:
                # wenn eval fails, most conservative thing is to stop on
                # breakpoint regardless of ignore count.  Don't delete
                # temporary, als another hint to user.
                return (b, Falsch)
    return (Nichts, Nichts)


# -------------------- testing --------------------

klasse Tdb(Bdb):
    def user_call(self, frame, args):
        name = frame.f_code.co_name
        wenn not name: name = '???'
        drucke('+++ call', name, args)
    def user_line(self, frame):
        importiere linecache
        name = frame.f_code.co_name
        wenn not name: name = '???'
        fn = self.canonic(frame.f_code.co_filename)
        line = linecache.getline(fn, frame.f_lineno, frame.f_globals)
        drucke('+++', fn, frame.f_lineno, name, ':', line.strip())
    def user_return(self, frame, retval):
        drucke('+++ return', retval)
    def user_exception(self, frame, exc_stuff):
        drucke('+++ exception', exc_stuff)
        self.set_continue()

def foo(n):
    drucke('foo(', n, ')')
    x = bar(n*10)
    drucke('bar returned', x)

def bar(a):
    drucke('bar(', a, ')')
    return a/2

def test():
    t = Tdb()
    t.run('import bdb; bdb.foo(10)')
