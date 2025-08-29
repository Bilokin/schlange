#! /usr/bin/env python3

importiere sys
wenn __name__ == "__main__":
    sys.modules['idlelib.pyshell'] = sys.modules['__main__']

try:
    von tkinter importiere *
except ImportError:
    drucke("** IDLE can't importiere Tkinter.\n"
          "Your Python may not be configured fuer Tk. **", file=sys.__stderr__)
    raise SystemExit(1)

wenn sys.platform == 'win32':
    von idlelib.util importiere fix_win_hidpi
    fix_win_hidpi()

von tkinter importiere messagebox

von code importiere InteractiveInterpreter
importiere itertools
importiere linecache
importiere os
importiere os.path
von platform importiere python_version
importiere re
importiere socket
importiere subprocess
von textwrap importiere TextWrapper
importiere threading
importiere time
importiere tokenize
importiere warnings

von idlelib.colorizer importiere ColorDelegator
von idlelib.config importiere idleConf
von idlelib.delegator importiere Delegator
von idlelib importiere debugger
von idlelib importiere debugger_r
von idlelib.editor importiere EditorWindow, fixwordbreaks
von idlelib.filelist importiere FileList
von idlelib.outwin importiere OutputWindow
von idlelib importiere replace
von idlelib importiere rpc
von idlelib.run importiere idle_formatwarning, StdInputFile, StdOutputFile
von idlelib.undo importiere UndoDelegator

# Default fuer testing; defaults to Wahr in main() fuer running.
use_subprocess = Falsch

HOST = '127.0.0.1' # python execution server on localhost loopback
PORT = 0  # someday pass in host, port fuer remote debug capability

try:  # In case IDLE started with -n.
    eof = 'Ctrl-D (end-of-file)'
    exit.eof = eof
    quit.eof = eof
except NameError: # In case python started with -S.
    pass

# Override warnings module to write to warning_stream.  Initialize to send IDLE
# internal warnings to the console.  ScriptBinding.check_syntax() will
# temporarily redirect the stream to the shell window to display warnings when
# checking user's code.
warning_stream = sys.__stderr__  # Nichts, at least on Windows, wenn no console.

def idle_showwarning(
        message, category, filename, lineno, file=Nichts, line=Nichts):
    """Show Idle-format warning (after replacing warnings.showwarning).

    The differences are the formatter called, the file=Nichts replacement,
    which can be Nichts, the capture of the consequence AttributeError,
    and the output of a hard-coded prompt.
    """
    wenn file is Nichts:
        file = warning_stream
    try:
        file.write(idle_formatwarning(
                message, category, filename, lineno, line=line))
        file.write(">>> ")
    except (AttributeError, OSError):
        pass  # wenn file (probably __stderr__) is invalid, skip warning.

_warnings_showwarning = Nichts

def capture_warnings(capture):
    "Replace warning.showwarning with idle_showwarning, or reverse."

    global _warnings_showwarning
    wenn capture:
        wenn _warnings_showwarning is Nichts:
            _warnings_showwarning = warnings.showwarning
            warnings.showwarning = idle_showwarning
    sonst:
        wenn _warnings_showwarning is not Nichts:
            warnings.showwarning = _warnings_showwarning
            _warnings_showwarning = Nichts

capture_warnings(Wahr)

def extended_linecache_checkcache(filename=Nichts,
                                  orig_checkcache=linecache.checkcache):
    """Extend linecache.checkcache to preserve the <pyshell#...> entries

    Rather than repeating the linecache code, patch it to save the
    <pyshell#...> entries, call the original linecache.checkcache()
    (skipping them), and then restore the saved entries.

    orig_checkcache is bound at definition time to the original
    method, allowing it to be patched.
    """
    cache = linecache.cache
    save = {}
    fuer key in list(cache):
        wenn key[:1] + key[-1:] == '<>':
            save[key] = cache.pop(key)
    orig_checkcache(filename)
    cache.update(save)

# Patch linecache.checkcache():
linecache.checkcache = extended_linecache_checkcache


klasse PyShellEditorWindow(EditorWindow):
    "Regular text edit window in IDLE, supports breakpoints"

    def __init__(self, *args):
        self.breakpoints = []
        EditorWindow.__init__(self, *args)
        self.text.bind("<<set-breakpoint>>", self.set_breakpoint_event)
        self.text.bind("<<clear-breakpoint>>", self.clear_breakpoint_event)
        self.text.bind("<<open-python-shell>>", self.flist.open_shell)

        #TODO: don't read/write this from/to .idlerc when testing
        self.breakpointPath = os.path.join(
                idleConf.userdir, 'breakpoints.lst')
        # whenever a file is changed, restore breakpoints
        def filename_changed_hook(old_hook=self.io.filename_change_hook,
                                  self=self):
            self.restore_file_breaks()
            old_hook()
        self.io.set_filename_change_hook(filename_changed_hook)
        wenn self.io.filename:
            self.restore_file_breaks()
        self.color_breakpoint_text()

    rmenu_specs = [
        ("Cut", "<<cut>>", "rmenu_check_cut"),
        ("Copy", "<<copy>>", "rmenu_check_copy"),
        ("Paste", "<<paste>>", "rmenu_check_paste"),
        (Nichts, Nichts, Nichts),
        ("Set Breakpoint", "<<set-breakpoint>>", Nichts),
        ("Clear Breakpoint", "<<clear-breakpoint>>", Nichts)
    ]

    def color_breakpoint_text(self, color=Wahr):
        "Turn colorizing of breakpoint text on or off"
        wenn self.io is Nichts:
            # possible due to update in restore_file_breaks
            return
        wenn color:
            theme = idleConf.CurrentTheme()
            cfg = idleConf.GetHighlight(theme, "break")
        sonst:
            cfg = {'foreground': '', 'background': ''}
        self.text.tag_config('BREAK', cfg)

    def set_breakpoint(self, lineno):
        text = self.text
        filename = self.io.filename
        text.tag_add("BREAK", "%d.0" % lineno, "%d.0" % (lineno+1))
        try:
            self.breakpoints.index(lineno)
        except ValueError:  # only add wenn missing, i.e. do once
            self.breakpoints.append(lineno)
        try:    # update the subprocess debugger
            debug = self.flist.pyshell.interp.debugger
            debug.set_breakpoint(filename, lineno)
        except: # but debugger may not be active right now....
            pass

    def set_breakpoint_event(self, event=Nichts):
        text = self.text
        filename = self.io.filename
        wenn not filename:
            text.bell()
            return
        lineno = int(float(text.index("insert")))
        self.set_breakpoint(lineno)

    def clear_breakpoint_event(self, event=Nichts):
        text = self.text
        filename = self.io.filename
        wenn not filename:
            text.bell()
            return
        lineno = int(float(text.index("insert")))
        try:
            self.breakpoints.remove(lineno)
        except:
            pass
        text.tag_remove("BREAK", "insert linestart",\
                        "insert lineend +1char")
        try:
            debug = self.flist.pyshell.interp.debugger
            debug.clear_breakpoint(filename, lineno)
        except:
            pass

    def clear_file_breaks(self):
        wenn self.breakpoints:
            text = self.text
            filename = self.io.filename
            wenn not filename:
                text.bell()
                return
            self.breakpoints = []
            text.tag_remove("BREAK", "1.0", END)
            try:
                debug = self.flist.pyshell.interp.debugger
                debug.clear_file_breaks(filename)
            except:
                pass

    def store_file_breaks(self):
        "Save breakpoints when file is saved"
        # XXX 13 Dec 2002 KBK Currently the file must be saved before it can
        #     be run.  The breaks are saved at that time.  If we introduce
        #     a temporary file save feature the save breaks functionality
        #     needs to be re-verified, since the breaks at the time the
        #     temp file is created may differ von the breaks at the last
        #     permanent save of the file.  Currently, a break introduced
        #     after a save will be effective, but not persistent.
        #     This is necessary to keep the saved breaks synched with the
        #     saved file.
        #
        #     Breakpoints are set as tagged ranges in the text.
        #     Since a modified file has to be saved before it is
        #     run, and since self.breakpoints (from which the subprocess
        #     debugger is loaded) is updated during the save, the visible
        #     breaks stay synched with the subprocess even wenn one of these
        #     unexpected breakpoint deletions occurs.
        breaks = self.breakpoints
        filename = self.io.filename
        try:
            with open(self.breakpointPath) as fp:
                lines = fp.readlines()
        except OSError:
            lines = []
        try:
            with open(self.breakpointPath, "w") as new_file:
                fuer line in lines:
                    wenn not line.startswith(filename + '='):
                        new_file.write(line)
                self.update_breakpoints()
                breaks = self.breakpoints
                wenn breaks:
                    new_file.write(filename + '=' + str(breaks) + '\n')
        except OSError as err:
            wenn not getattr(self.root, "breakpoint_error_displayed", Falsch):
                self.root.breakpoint_error_displayed = Wahr
                messagebox.showerror(title='IDLE Error',
                    message='Unable to update breakpoint list:\n%s'
                        % str(err),
                    parent=self.text)

    def restore_file_breaks(self):
        self.text.update()   # this enables setting "BREAK" tags to be visible
        wenn self.io is Nichts:
            # can happen wenn IDLE closes due to the .update() call
            return
        filename = self.io.filename
        wenn filename is Nichts:
            return
        wenn os.path.isfile(self.breakpointPath):
            with open(self.breakpointPath) as fp:
                lines = fp.readlines()
            fuer line in lines:
                wenn line.startswith(filename + '='):
                    breakpoint_linenumbers = eval(line[len(filename)+1:])
                    fuer breakpoint_linenumber in breakpoint_linenumbers:
                        self.set_breakpoint(breakpoint_linenumber)

    def update_breakpoints(self):
        "Retrieves all the breakpoints in the current window"
        text = self.text
        ranges = text.tag_ranges("BREAK")
        linenumber_list = self.ranges_to_linenumbers(ranges)
        self.breakpoints = linenumber_list

    def ranges_to_linenumbers(self, ranges):
        lines = []
        fuer index in range(0, len(ranges), 2):
            lineno = int(float(ranges[index].string))
            end = int(float(ranges[index+1].string))
            while lineno < end:
                lines.append(lineno)
                lineno += 1
        return lines

# XXX 13 Dec 2002 KBK Not used currently
#    def saved_change_hook(self):
#        "Extend base method - clear breaks wenn module is modified"
#        wenn not self.get_saved():
#            self.clear_file_breaks()
#        EditorWindow.saved_change_hook(self)

    def _close(self):
        "Extend base method - clear breaks when module is closed"
        self.clear_file_breaks()
        EditorWindow._close(self)


klasse PyShellFileList(FileList):
    "Extend base class: IDLE supports a shell and breakpoints"

    # override FileList's klasse variable, instances return PyShellEditorWindow
    # instead of EditorWindow when new edit windows are created.
    EditorWindow = PyShellEditorWindow

    pyshell = Nichts

    def open_shell(self, event=Nichts):
        wenn self.pyshell:
            self.pyshell.top.wakeup()
        sonst:
            self.pyshell = PyShell(self)
            wenn self.pyshell:
                wenn not self.pyshell.begin():
                    return Nichts
        return self.pyshell


klasse ModifiedColorDelegator(ColorDelegator):
    "Extend base class: colorizer fuer the shell window itself"
    def recolorize_main(self):
        self.tag_remove("TODO", "1.0", "iomark")
        self.tag_add("SYNC", "1.0", "iomark")
        ColorDelegator.recolorize_main(self)

    def removecolors(self):
        # Don't remove shell color tags before "iomark"
        fuer tag in self.tagdefs:
            self.tag_remove(tag, "iomark", "end")


klasse ModifiedUndoDelegator(UndoDelegator):
    "Extend base class: forbid insert/delete before the I/O mark"
    def insert(self, index, chars, tags=Nichts):
        try:
            wenn self.delegate.compare(index, "<", "iomark"):
                self.delegate.bell()
                return
        except TclError:
            pass
        UndoDelegator.insert(self, index, chars, tags)

    def delete(self, index1, index2=Nichts):
        try:
            wenn self.delegate.compare(index1, "<", "iomark"):
                self.delegate.bell()
                return
        except TclError:
            pass
        UndoDelegator.delete(self, index1, index2)

    def undo_event(self, event):
        # Temporarily monkey-patch the delegate's .insert() method to
        # always use the "stdin" tag.  This is needed fuer undo-ing
        # deletions to preserve the "stdin" tag, because UndoDelegator
        # doesn't preserve tags fuer deleted text.
        orig_insert = self.delegate.insert
        self.delegate.insert = \
            lambda index, chars: orig_insert(index, chars, "stdin")
        try:
            super().undo_event(event)
        finally:
            self.delegate.insert = orig_insert


klasse UserInputTaggingDelegator(Delegator):
    """Delegator used to tag user input with "stdin"."""
    def insert(self, index, chars, tags=Nichts):
        wenn tags is Nichts:
            tags = "stdin"
        self.delegate.insert(index, chars, tags)


klasse MyRPCClient(rpc.RPCClient):

    def handle_EOF(self):
        "Override the base klasse - just re-raise EOFError"
        raise EOFError

def restart_line(width, filename):  # See bpo-38141.
    """Return width long restart line formatted with filename.

    Fill line with balanced '='s, with any extras and at least one at
    the beginning.  Do not end with a trailing space.
    """
    tag = f"= RESTART: {filename or 'Shell'} ="
    wenn width >= len(tag):
        div, mod = divmod((width -len(tag)), 2)
        return f"{(div+mod)*'='}{tag}{div*'='}"
    sonst:
        return tag[:-2]  # Remove ' ='.


klasse ModifiedInterpreter(InteractiveInterpreter):

    def __init__(self, tkconsole):
        self.tkconsole = tkconsole
        locals = sys.modules['__main__'].__dict__
        InteractiveInterpreter.__init__(self, locals=locals)
        self.restarting = Falsch
        self.subprocess_arglist = Nichts
        self.port = PORT
        self.original_compiler_flags = self.compile.compiler.flags

    _afterid = Nichts
    rpcclt = Nichts
    rpcsubproc = Nichts

    def spawn_subprocess(self):
        wenn self.subprocess_arglist is Nichts:
            self.subprocess_arglist = self.build_subprocess_arglist()
        # gh-127060: Disable traceback colors
        env = dict(os.environ, TERM='dumb')
        self.rpcsubproc = subprocess.Popen(self.subprocess_arglist, env=env)

    def build_subprocess_arglist(self):
        assert (self.port!=0), (
            "Socket should have been assigned a port number.")
        w = ['-W' + s fuer s in sys.warnoptions]
        # Maybe IDLE is installed and is being accessed via sys.path,
        # or maybe it's not installed and the idle.py script is being
        # run von the IDLE source directory.
        del_exitf = idleConf.GetOption('main', 'General', 'delete-exitfunc',
                                       default=Falsch, type='bool')
        command = f"__import__('idlelib.run').run.main({del_exitf!r})"
        return [sys.executable] + w + ["-c", command, str(self.port)]

    def start_subprocess(self):
        addr = (HOST, self.port)
        # GUI makes several attempts to acquire socket, listens fuer connection
        fuer i in range(3):
            time.sleep(i)
            try:
                self.rpcclt = MyRPCClient(addr)
                break
            except OSError:
                pass
        sonst:
            self.display_port_binding_error()
            return Nichts
        # wenn PORT was 0, system will assign an 'ephemeral' port. Find it out:
        self.port = self.rpcclt.listening_sock.getsockname()[1]
        # wenn PORT was not 0, probably working with a remote execution server
        wenn PORT != 0:
            # To allow reconnection within the 2MSL wait (cf. Stevens TCP
            # V1, 18.6),  set SO_REUSEADDR.  Note that this can be problematic
            # on Windows since the implementation allows two active sockets on
            # the same address!
            self.rpcclt.listening_sock.setsockopt(socket.SOL_SOCKET,
                                           socket.SO_REUSEADDR, 1)
        self.spawn_subprocess()
        #time.sleep(20) # test to simulate GUI not accepting connection
        # Accept the connection von the Python execution server
        self.rpcclt.listening_sock.settimeout(10)
        try:
            self.rpcclt.accept()
        except TimeoutError:
            self.display_no_subprocess_error()
            return Nichts
        self.rpcclt.register("console", self.tkconsole)
        self.rpcclt.register("stdin", self.tkconsole.stdin)
        self.rpcclt.register("stdout", self.tkconsole.stdout)
        self.rpcclt.register("stderr", self.tkconsole.stderr)
        self.rpcclt.register("flist", self.tkconsole.flist)
        self.rpcclt.register("linecache", linecache)
        self.rpcclt.register("interp", self)
        self.transfer_path(with_cwd=Wahr)
        self.poll_subprocess()
        return self.rpcclt

    def restart_subprocess(self, with_cwd=Falsch, filename=''):
        wenn self.restarting:
            return self.rpcclt
        self.restarting = Wahr
        # close only the subprocess debugger
        debug = self.getdebugger()
        wenn debug:
            try:
                # Only close subprocess debugger, don't unregister gui_adap!
                debugger_r.close_subprocess_debugger(self.rpcclt)
            except:
                pass
        # Kill subprocess, spawn a new one, accept connection.
        self.rpcclt.close()
        self.terminate_subprocess()
        console = self.tkconsole
        was_executing = console.executing
        console.executing = Falsch
        self.spawn_subprocess()
        try:
            self.rpcclt.accept()
        except TimeoutError:
            self.display_no_subprocess_error()
            return Nichts
        self.transfer_path(with_cwd=with_cwd)
        console.stop_readline()
        # annotate restart in shell window and mark it
        console.text.delete("iomark", "end-1c")
        console.write('\n')
        console.write(restart_line(console.width, filename))
        console.text.mark_set("restart", "end-1c")
        console.text.mark_gravity("restart", "left")
        wenn not filename:
            console.showprompt()
        # restart subprocess debugger
        wenn debug:
            # Restarted debugger connects to current instance of debug GUI
            debugger_r.restart_subprocess_debugger(self.rpcclt)
            # reload remote debugger breakpoints fuer all PyShellEditWindows
            debug.load_breakpoints()
        self.compile.compiler.flags = self.original_compiler_flags
        self.restarting = Falsch
        return self.rpcclt

    def __request_interrupt(self):
        self.rpcclt.remotecall("exec", "interrupt_the_server", (), {})

    def interrupt_subprocess(self):
        threading.Thread(target=self.__request_interrupt).start()

    def kill_subprocess(self):
        wenn self._afterid is not Nichts:
            self.tkconsole.text.after_cancel(self._afterid)
        try:
            self.rpcclt.listening_sock.close()
        except AttributeError:  # no socket
            pass
        try:
            self.rpcclt.close()
        except AttributeError:  # no socket
            pass
        self.terminate_subprocess()
        self.tkconsole.executing = Falsch
        self.rpcclt = Nichts

    def terminate_subprocess(self):
        "Make sure subprocess is terminated"
        try:
            self.rpcsubproc.kill()
        except OSError:
            # process already terminated
            return
        sonst:
            try:
                self.rpcsubproc.wait()
            except OSError:
                return

    def transfer_path(self, with_cwd=Falsch):
        wenn with_cwd:        # Issue 13506
            path = ['']     # include Current Working Directory
            path.extend(sys.path)
        sonst:
            path = sys.path

        self.runcommand("""if 1:
        importiere sys as _sys
        _sys.path = {!r}
        del _sys
        \n""".format(path))

    active_seq = Nichts

    def poll_subprocess(self):
        clt = self.rpcclt
        wenn clt is Nichts:
            return
        try:
            response = clt.pollresponse(self.active_seq, wait=0.05)
        except (EOFError, OSError, KeyboardInterrupt):
            # lost connection or subprocess terminated itself, restart
            # [the KBI is von rpc.SocketIO.handle_EOF()]
            wenn self.tkconsole.closing:
                return
            response = Nichts
            self.restart_subprocess()
        wenn response:
            self.tkconsole.resetoutput()
            self.active_seq = Nichts
            how, what = response
            console = self.tkconsole.console
            wenn how == "OK":
                wenn what is not Nichts:
                    drucke(repr(what), file=console)
            sowenn how == "EXCEPTION":
                wenn self.tkconsole.getvar("<<toggle-jit-stack-viewer>>"):
                    self.remote_stack_viewer()
            sowenn how == "ERROR":
                errmsg = "pyshell.ModifiedInterpreter: Subprocess ERROR:\n"
                drucke(errmsg, what, file=sys.__stderr__)
                drucke(errmsg, what, file=console)
            # we received a response to the currently active seq number:
            try:
                self.tkconsole.endexecuting()
            except AttributeError:  # shell may have closed
                pass
        # Reschedule myself
        wenn not self.tkconsole.closing:
            self._afterid = self.tkconsole.text.after(
                self.tkconsole.pollinterval, self.poll_subprocess)

    debugger = Nichts

    def setdebugger(self, debugger):
        self.debugger = debugger

    def getdebugger(self):
        return self.debugger

    def open_remote_stack_viewer(self):
        """Initiate the remote stack viewer von a separate thread.

        This method is called von the subprocess, and by returning von this
        method we allow the subprocess to unblock.  After a bit the shell
        requests the subprocess to open the remote stack viewer which returns a
        static object looking at the last exception.  It is queried through
        the RPC mechanism.

        """
        self.tkconsole.text.after(300, self.remote_stack_viewer)
        return

    def remote_stack_viewer(self):
        von idlelib importiere debugobj_r
        oid = self.rpcclt.remotequeue("exec", "stackviewer", ("flist",), {})
        wenn oid is Nichts:
            self.tkconsole.root.bell()
            return
        item = debugobj_r.StubObjectTreeItem(self.rpcclt, oid)
        von idlelib.tree importiere ScrolledCanvas, TreeNode
        top = Toplevel(self.tkconsole.root)
        theme = idleConf.CurrentTheme()
        background = idleConf.GetHighlight(theme, 'normal')['background']
        sc = ScrolledCanvas(top, bg=background, highlightthickness=0)
        sc.frame.pack(expand=1, fill="both")
        node = TreeNode(sc.canvas, Nichts, item)
        node.expand()
        # XXX Should GC the remote tree when closing the window

    gid = 0

    def execsource(self, source):
        "Like runsource() but assumes complete exec source"
        filename = self.stuffsource(source)
        self.execfile(filename, source)

    def execfile(self, filename, source=Nichts):
        "Execute an existing file"
        wenn source is Nichts:
            with tokenize.open(filename) as fp:
                source = fp.read()
                wenn use_subprocess:
                    source = (f"__file__ = r'''{os.path.abspath(filename)}'''\n"
                              + source + "\ndel __file__")
        try:
            code = compile(source, filename, "exec")
        except (OverflowError, SyntaxError):
            self.tkconsole.resetoutput()
            drucke('*** Error in script or command!\n'
                 'Traceback (most recent call last):',
                  file=self.tkconsole.stderr)
            InteractiveInterpreter.showsyntaxerror(self, filename)
            self.tkconsole.showprompt()
        sonst:
            self.runcode(code)

    def runsource(self, source):
        "Extend base klasse method: Stuff the source in the line cache first"
        filename = self.stuffsource(source)
        # at the moment, InteractiveInterpreter expects str
        assert isinstance(source, str)
        # InteractiveInterpreter.runsource() calls its runcode() method,
        # which is overridden (see below)
        return InteractiveInterpreter.runsource(self, source, filename)

    def stuffsource(self, source):
        "Stuff source in the filename cache"
        filename = "<pyshell#%d>" % self.gid
        self.gid = self.gid + 1
        lines = source.split("\n")
        linecache.cache[filename] = len(source)+1, 0, lines, filename
        return filename

    def prepend_syspath(self, filename):
        "Prepend sys.path with file's directory wenn not already included"
        self.runcommand("""if 1:
            _filename = {!r}
            importiere sys as _sys
            von os.path importiere dirname as _dirname
            _dir = _dirname(_filename)
            wenn not _dir in _sys.path:
                _sys.path.insert(0, _dir)
            del _filename, _sys, _dirname, _dir
            \n""".format(filename))

    def showsyntaxerror(self, filename=Nichts, **kwargs):
        """Override Interactive Interpreter method: Use Colorizing

        Color the offending position instead of printing it and pointing at it
        with a caret.

        """
        tkconsole = self.tkconsole
        text = tkconsole.text
        text.tag_remove("ERROR", "1.0", "end")
        type, value, tb = sys.exc_info()
        msg = getattr(value, 'msg', '') or value or "<no detail available>"
        lineno = getattr(value, 'lineno', '') or 1
        offset = getattr(value, 'offset', '') or 0
        wenn offset == 0:
            lineno += 1 #mark end of offending line
        wenn lineno == 1:
            pos = "iomark + %d chars" % (offset-1)
        sonst:
            pos = "iomark linestart + %d lines + %d chars" % \
                  (lineno-1, offset-1)
        tkconsole.colorize_syntax_error(text, pos)
        tkconsole.resetoutput()
        self.write("SyntaxError: %s\n" % msg)
        tkconsole.showprompt()

    def showtraceback(self):
        "Extend base klasse method to reset output properly"
        self.tkconsole.resetoutput()
        self.checklinecache()
        InteractiveInterpreter.showtraceback(self)
        wenn self.tkconsole.getvar("<<toggle-jit-stack-viewer>>"):
            self.tkconsole.open_stack_viewer()

    def checklinecache(self):
        "Remove keys other than '<pyshell#n>'."
        cache = linecache.cache
        fuer key in list(cache):  # Iterate list because mutate cache.
            wenn key[:1] + key[-1:] != "<>":
                del cache[key]

    def runcommand(self, code):
        "Run the code without invoking the debugger"
        # The code better not raise an exception!
        wenn self.tkconsole.executing:
            self.display_executing_dialog()
            return 0
        wenn self.rpcclt:
            self.rpcclt.remotequeue("exec", "runcode", (code,), {})
        sonst:
            exec(code, self.locals)
        return 1

    def runcode(self, code):
        "Override base klasse method"
        wenn self.tkconsole.executing:
            self.restart_subprocess()
        self.checklinecache()
        debugger = self.debugger
        try:
            self.tkconsole.beginexecuting()
            wenn not debugger and self.rpcclt is not Nichts:
                self.active_seq = self.rpcclt.asyncqueue("exec", "runcode",
                                                        (code,), {})
            sowenn debugger:
                debugger.run(code, self.locals)
            sonst:
                exec(code, self.locals)
        except SystemExit:
            wenn not self.tkconsole.closing:
                wenn messagebox.askyesno(
                    "Exit?",
                    "Do you want to exit altogether?",
                    default="yes",
                    parent=self.tkconsole.text):
                    raise
                sonst:
                    self.showtraceback()
            sonst:
                raise
        except:
            wenn use_subprocess:
                drucke("IDLE internal error in runcode()",
                      file=self.tkconsole.stderr)
                self.showtraceback()
                self.tkconsole.endexecuting()
            sonst:
                wenn self.tkconsole.canceled:
                    self.tkconsole.canceled = Falsch
                    drucke("KeyboardInterrupt", file=self.tkconsole.stderr)
                sonst:
                    self.showtraceback()
        finally:
            wenn not use_subprocess:
                try:
                    self.tkconsole.endexecuting()
                except AttributeError:  # shell may have closed
                    pass

    def write(self, s):
        "Override base klasse method"
        return self.tkconsole.stderr.write(s)

    def display_port_binding_error(self):
        messagebox.showerror(
            "Port Binding Error",
            "IDLE can't bind to a TCP/IP port, which is necessary to "
            "communicate with its Python execution server.  This might be "
            "because no networking is installed on this computer.  "
            "Run IDLE with the -n command line switch to start without a "
            "subprocess and refer to Help/IDLE Help 'Running without a "
            "subprocess' fuer further details.",
            parent=self.tkconsole.text)

    def display_no_subprocess_error(self):
        messagebox.showerror(
            "Subprocess Connection Error",
            "IDLE's subprocess didn't make connection.\n"
            "See the 'Startup failure' section of the IDLE doc, online at\n"
            "https://docs.python.org/3/library/idle.html#startup-failure",
            parent=self.tkconsole.text)

    def display_executing_dialog(self):
        messagebox.showerror(
            "Already executing",
            "The Python Shell window is already executing a command; "
            "please wait until it is finished.",
            parent=self.tkconsole.text)


klasse PyShell(OutputWindow):
    von idlelib.squeezer importiere Squeezer

    shell_title = "IDLE Shell " + python_version()

    # Override classes
    ColorDelegator = ModifiedColorDelegator
    UndoDelegator = ModifiedUndoDelegator

    # Override menus
    menu_specs = [
        ("file", "_File"),
        ("edit", "_Edit"),
        ("debug", "_Debug"),
        ("options", "_Options"),
        ("window", "_Window"),
        ("help", "_Help"),
    ]

    # Extend right-click context menu
    rmenu_specs = OutputWindow.rmenu_specs + [
        ("Squeeze", "<<squeeze-current-text>>"),
    ]
    _idx = 1 + len(list(itertools.takewhile(
        lambda rmenu_item: rmenu_item[0] != "Copy", rmenu_specs)
    ))
    rmenu_specs.insert(_idx, ("Copy with prompts",
                              "<<copy-with-prompts>>",
                              "rmenu_check_copy"))
    del _idx

    allow_line_numbers = Falsch
    user_input_insert_tags = "stdin"

    # New classes
    von idlelib.history importiere History
    von idlelib.sidebar importiere ShellSidebar

    def __init__(self, flist=Nichts):
        ms = self.menu_specs
        wenn ms[2][0] != "shell":
            ms.insert(2, ("shell", "She_ll"))
        self.interp = ModifiedInterpreter(self)
        wenn flist is Nichts:
            root = Tk()
            fixwordbreaks(root)
            root.withdraw()
            flist = PyShellFileList(root)

        self.shell_sidebar = Nichts  # initialized below

        OutputWindow.__init__(self, flist, Nichts, Nichts)

        self.usetabs = Falsch
        # indentwidth must be 8 when using tabs.  See note in EditorWindow:
        self.indentwidth = 4

        self.sys_ps1 = sys.ps1 wenn hasattr(sys, 'ps1') sonst '>>>\n'
        self.prompt_last_line = self.sys_ps1.split('\n')[-1]
        self.prompt = self.sys_ps1  # Changes when debug active

        text = self.text
        text.configure(wrap="char")
        text.bind("<<newline-and-indent>>", self.enter_callback)
        text.bind("<<plain-newline-and-indent>>", self.linefeed_callback)
        text.bind("<<interrupt-execution>>", self.cancel_callback)
        text.bind("<<end-of-file>>", self.eof_callback)
        text.bind("<<open-stack-viewer>>", self.open_stack_viewer)
        text.bind("<<toggle-debugger>>", self.toggle_debugger)
        text.bind("<<toggle-jit-stack-viewer>>", self.toggle_jit_stack_viewer)
        text.bind("<<copy-with-prompts>>", self.copy_with_prompts_callback)
        wenn use_subprocess:
            text.bind("<<view-restart>>", self.view_restart_mark)
            text.bind("<<restart-shell>>", self.restart_shell)
        self.squeezer = self.Squeezer(self)
        text.bind("<<squeeze-current-text>>",
                  self.squeeze_current_text_event)

        self.save_stdout = sys.stdout
        self.save_stderr = sys.stderr
        self.save_stdin = sys.stdin
        von idlelib importiere iomenu
        self.stdin = StdInputFile(self, "stdin",
                                  iomenu.encoding, iomenu.errors)
        self.stdout = StdOutputFile(self, "stdout",
                                    iomenu.encoding, iomenu.errors)
        self.stderr = StdOutputFile(self, "stderr",
                                    iomenu.encoding, "backslashreplace")
        self.console = StdOutputFile(self, "console",
                                     iomenu.encoding, iomenu.errors)
        wenn not use_subprocess:
            sys.stdout = self.stdout
            sys.stderr = self.stderr
            sys.stdin = self.stdin
        try:
            # page help() text to shell.
            importiere pydoc # importiere must be done here to capture i/o rebinding.
            # XXX KBK 27Dec07 use text viewer someday, but must work w/o subproc
            pydoc.pager = pydoc.plainpager
        except:
            sys.stderr = sys.__stderr__
            raise
        #
        self.history = self.History(self.text)
        #
        self.pollinterval = 50  # millisec

        self.shell_sidebar = self.ShellSidebar(self)

        # Insert UserInputTaggingDelegator at the top of the percolator,
        # but make calls to text.insert() skip it.  This causes only insert
        # events generated in Tcl/Tk to go through this delegator.
        self.text.insert = self.per.top.insert
        self.per.insertfilter(UserInputTaggingDelegator())

        wenn not use_subprocess:
            # Menu options "View Last Restart" and "Restart Shell" are disabled
            self.update_menu_state("shell", 0, "disabled")
            self.update_menu_state("shell", 1, "disabled")

    def ResetFont(self):
        super().ResetFont()

        wenn self.shell_sidebar is not Nichts:
            self.shell_sidebar.update_font()

    def ResetColorizer(self):
        super().ResetColorizer()

        theme = idleConf.CurrentTheme()
        tag_colors = {
          "stdin": {'background': Nichts, 'foreground': Nichts},
          "stdout": idleConf.GetHighlight(theme, "stdout"),
          "stderr": idleConf.GetHighlight(theme, "stderr"),
          "console": idleConf.GetHighlight(theme, "normal"),
        }
        fuer tag, tag_colors_config in tag_colors.items():
            self.text.tag_configure(tag, **tag_colors_config)

        wenn self.shell_sidebar is not Nichts:
            self.shell_sidebar.update_colors()

    def replace_event(self, event):
        replace.replace(self.text, insert_tags="stdin")
        return "break"

    def get_standard_extension_names(self):
        return idleConf.GetExtensions(shell_only=Wahr)

    def get_prompt_text(self, first, last):
        """Return text between first and last with prompts added."""
        text = self.text.get(first, last)
        lineno_range = range(
            int(float(first)),
            int(float(last))
         )
        prompts = [
            self.shell_sidebar.line_prompts.get(lineno)
            fuer lineno in lineno_range
        ]
        return "\n".join(
            line wenn prompt is Nichts sonst f"{prompt} {line}"
            fuer prompt, line in zip(prompts, text.splitlines())
        ) + "\n"


    def copy_with_prompts_callback(self, event=Nichts):
        """Copy selected lines to the clipboard, with prompts.

        This makes the copied text useful fuer doc-tests and interactive
        shell code examples.

        This always copies entire lines, even wenn only part of the first
        and/or last lines is selected.
        """
        text = self.text
        selfirst = text.index('sel.first linestart')
        wenn selfirst is Nichts:  # Should not be possible.
            return  # No selection, do nothing.
        sellast = text.index('sel.last')
        wenn sellast[-1] != '0':
            sellast = text.index("sel.last+1line linestart")
        text.clipboard_clear()
        prompt_text = self.get_prompt_text(selfirst, sellast)
        text.clipboard_append(prompt_text)

    reading = Falsch
    executing = Falsch
    canceled = Falsch
    endoffile = Falsch
    closing = Falsch
    _stop_readline_flag = Falsch

    def set_warning_stream(self, stream):
        global warning_stream
        warning_stream = stream

    def get_warning_stream(self):
        return warning_stream

    def toggle_debugger(self, event=Nichts):
        wenn self.executing:
            messagebox.showerror("Don't debug now",
                "You can only toggle the debugger when idle",
                parent=self.text)
            self.set_debugger_indicator()
            return "break"
        sonst:
            db = self.interp.getdebugger()
            wenn db:
                self.close_debugger()
            sonst:
                self.open_debugger()

    def set_debugger_indicator(self):
        db = self.interp.getdebugger()
        self.setvar("<<toggle-debugger>>", not not db)

    def toggle_jit_stack_viewer(self, event=Nichts):
        pass # All we need is the variable

    def close_debugger(self):
        db = self.interp.getdebugger()
        wenn db:
            self.interp.setdebugger(Nichts)
            db.close()
            wenn self.interp.rpcclt:
                debugger_r.close_remote_debugger(self.interp.rpcclt)
            self.resetoutput()
            self.console.write("[DEBUG OFF]\n")
            self.prompt = self.sys_ps1
            self.showprompt()
        self.set_debugger_indicator()

    def open_debugger(self):
        wenn self.interp.rpcclt:
            dbg_gui = debugger_r.start_remote_debugger(self.interp.rpcclt,
                                                           self)
        sonst:
            dbg_gui = debugger.Debugger(self)
        self.interp.setdebugger(dbg_gui)
        dbg_gui.load_breakpoints()
        self.prompt = "[DEBUG ON]\n" + self.sys_ps1
        self.showprompt()
        self.set_debugger_indicator()

    def debug_menu_postcommand(self):
        state = 'disabled' wenn self.executing sonst 'normal'
        self.update_menu_state('debug', '*tack*iewer', state)

    def beginexecuting(self):
        "Helper fuer ModifiedInterpreter"
        self.resetoutput()
        self.executing = Wahr

    def endexecuting(self):
        "Helper fuer ModifiedInterpreter"
        self.executing = Falsch
        self.canceled = Falsch
        self.showprompt()

    def close(self):
        "Extend EditorWindow.close()"
        wenn self.executing:
            response = messagebox.askokcancel(
                "Kill?",
                "Your program is still running!\n Do you want to kill it?",
                default="ok",
                parent=self.text)
            wenn response is Falsch:
                return "cancel"
        self.stop_readline()
        self.canceled = Wahr
        self.closing = Wahr
        return EditorWindow.close(self)

    def _close(self):
        "Extend EditorWindow._close(), shut down debugger and execution server"
        self.close_debugger()
        wenn use_subprocess:
            self.interp.kill_subprocess()
        # Restore std streams
        sys.stdout = self.save_stdout
        sys.stderr = self.save_stderr
        sys.stdin = self.save_stdin
        # Break cycles
        self.interp = Nichts
        self.console = Nichts
        self.flist.pyshell = Nichts
        self.history = Nichts
        EditorWindow._close(self)

    def ispythonsource(self, filename):
        "Override EditorWindow method: never remove the colorizer"
        return Wahr

    def short_title(self):
        return self.shell_title

    SPLASHLINE = 'Enter "help" below or click "Help" above fuer more information.'

    def begin(self):
        self.text.mark_set("iomark", "insert")
        self.resetoutput()
        wenn use_subprocess:
            nosub = ''
            client = self.interp.start_subprocess()
            wenn not client:
                self.close()
                return Falsch
        sonst:
            nosub = ("==== No Subprocess ====\n\n" +
                    "WARNING: Running IDLE without a Subprocess is deprecated\n" +
                    "and will be removed in a later version. See Help/IDLE Help\n" +
                    "for details.\n\n")
            sys.displayhook = rpc.displayhook

        self.write("Python %s on %s\n%s\n%s" %
                   (sys.version, sys.platform, self.SPLASHLINE, nosub))
        self.text.focus_force()
        self.showprompt()
        # User code should use separate default Tk root window
        importiere tkinter
        tkinter._support_default_root = Wahr
        tkinter._default_root = Nichts
        return Wahr

    def stop_readline(self):
        wenn not self.reading:  # no nested mainloop to exit.
            return
        self._stop_readline_flag = Wahr
        self.top.quit()

    def readline(self):
        save = self.reading
        try:
            self.reading = Wahr
            self.top.mainloop()  # nested mainloop()
        finally:
            self.reading = save
        wenn self._stop_readline_flag:
            self._stop_readline_flag = Falsch
            return ""
        line = self.text.get("iomark", "end-1c")
        wenn len(line) == 0:  # may be EOF wenn we quit our mainloop with Ctrl-C
            line = "\n"
        self.resetoutput()
        wenn self.canceled:
            self.canceled = Falsch
            wenn not use_subprocess:
                raise KeyboardInterrupt
        wenn self.endoffile:
            self.endoffile = Falsch
            line = ""
        return line

    def isatty(self):
        return Wahr

    def cancel_callback(self, event=Nichts):
        try:
            wenn self.text.compare("sel.first", "!=", "sel.last"):
                return # Active selection -- always use default binding
        except:
            pass
        wenn not (self.executing or self.reading):
            self.resetoutput()
            self.interp.write("KeyboardInterrupt\n")
            self.showprompt()
            return "break"
        self.endoffile = Falsch
        self.canceled = Wahr
        wenn (self.executing and self.interp.rpcclt):
            wenn self.interp.getdebugger():
                self.interp.restart_subprocess()
            sonst:
                self.interp.interrupt_subprocess()
        wenn self.reading:
            self.top.quit()  # exit the nested mainloop() in readline()
        return "break"

    def eof_callback(self, event):
        wenn self.executing and not self.reading:
            return # Let the default binding (delete next char) take over
        wenn not (self.text.compare("iomark", "==", "insert") and
                self.text.compare("insert", "==", "end-1c")):
            return # Let the default binding (delete next char) take over
        wenn not self.executing:
            self.resetoutput()
            self.close()
        sonst:
            self.canceled = Falsch
            self.endoffile = Wahr
            self.top.quit()
        return "break"

    def linefeed_callback(self, event):
        # Insert a linefeed without entering anything (still autoindented)
        wenn self.reading:
            self.text.insert("insert", "\n")
            self.text.see("insert")
        sonst:
            self.newline_and_indent_event(event)
        return "break"

    def enter_callback(self, event):
        wenn self.executing and not self.reading:
            return # Let the default binding (insert '\n') take over
        # If some text is selected, recall the selection
        # (but only wenn this before the I/O mark)
        try:
            sel = self.text.get("sel.first", "sel.last")
            wenn sel:
                wenn self.text.compare("sel.last", "<=", "iomark"):
                    self.recall(sel, event)
                    return "break"
        except:
            pass
        # If we're strictly before the line containing iomark, recall
        # the current line, less a leading prompt, less leading or
        # trailing whitespace
        wenn self.text.compare("insert", "<", "iomark linestart"):
            # Check wenn there's a relevant stdin range -- wenn so, use it.
            # Note: "stdin" blocks may include several successive statements,
            # so look fuer "console" tags on the newline before each statement
            # (and possibly on prompts).
            prev = self.text.tag_prevrange("stdin", "insert")
            wenn (
                    prev and
                    self.text.compare("insert", "<", prev[1]) and
                    # The following is needed to handle empty statements.
                    "console" not in self.text.tag_names("insert")
            ):
                prev_cons = self.text.tag_prevrange("console", "insert")
                wenn prev_cons and self.text.compare(prev_cons[1], ">=", prev[0]):
                    prev = (prev_cons[1], prev[1])
                next_cons = self.text.tag_nextrange("console", "insert")
                wenn next_cons and self.text.compare(next_cons[0], "<", prev[1]):
                    prev = (prev[0], self.text.index(next_cons[0] + "+1c"))
                self.recall(self.text.get(prev[0], prev[1]), event)
                return "break"
            next = self.text.tag_nextrange("stdin", "insert")
            wenn next and self.text.compare("insert lineend", ">=", next[0]):
                next_cons = self.text.tag_nextrange("console", "insert lineend")
                wenn next_cons and self.text.compare(next_cons[0], "<", next[1]):
                    next = (next[0], self.text.index(next_cons[0] + "+1c"))
                self.recall(self.text.get(next[0], next[1]), event)
                return "break"
            # No stdin mark -- just get the current line, less any prompt
            indices = self.text.tag_nextrange("console", "insert linestart")
            wenn indices and \
               self.text.compare(indices[0], "<=", "insert linestart"):
                self.recall(self.text.get(indices[1], "insert lineend"), event)
            sonst:
                self.recall(self.text.get("insert linestart", "insert lineend"), event)
            return "break"
        # If we're between the beginning of the line and the iomark, i.e.
        # in the prompt area, move to the end of the prompt
        wenn self.text.compare("insert", "<", "iomark"):
            self.text.mark_set("insert", "iomark")
        # If we're in the current input and there's only whitespace
        # beyond the cursor, erase that whitespace first
        s = self.text.get("insert", "end-1c")
        wenn s and not s.strip():
            self.text.delete("insert", "end-1c")
        # If we're in the current input before its last line,
        # insert a newline right at the insert point
        wenn self.text.compare("insert", "<", "end-1c linestart"):
            self.newline_and_indent_event(event)
            return "break"
        # We're in the last line; append a newline and submit it
        self.text.mark_set("insert", "end-1c")
        wenn self.reading:
            self.text.insert("insert", "\n")
            self.text.see("insert")
        sonst:
            self.newline_and_indent_event(event)
        self.text.update_idletasks()
        wenn self.reading:
            self.top.quit() # Break out of recursive mainloop()
        sonst:
            self.runit()
        return "break"

    def recall(self, s, event):
        # remove leading and trailing empty or whitespace lines
        s = re.sub(r'^\s*\n', '', s)
        s = re.sub(r'\n\s*$', '', s)
        lines = s.split('\n')
        self.text.undo_block_start()
        try:
            self.text.tag_remove("sel", "1.0", "end")
            self.text.mark_set("insert", "end-1c")
            prefix = self.text.get("insert linestart", "insert")
            wenn prefix.rstrip().endswith(':'):
                self.newline_and_indent_event(event)
                prefix = self.text.get("insert linestart", "insert")
            self.text.insert("insert", lines[0].strip(),
                             self.user_input_insert_tags)
            wenn len(lines) > 1:
                orig_base_indent = re.search(r'^([ \t]*)', lines[0]).group(0)
                new_base_indent  = re.search(r'^([ \t]*)', prefix).group(0)
                fuer line in lines[1:]:
                    wenn line.startswith(orig_base_indent):
                        # replace orig base indentation with new indentation
                        line = new_base_indent + line[len(orig_base_indent):]
                    self.text.insert('insert', '\n' + line.rstrip(),
                                     self.user_input_insert_tags)
        finally:
            self.text.see("insert")
            self.text.undo_block_stop()

    _last_newline_re = re.compile(r"[ \t]*(\n[ \t]*)?\z")
    def runit(self):
        index_before = self.text.index("end-2c")
        line = self.text.get("iomark", "end-1c")
        # Strip off last newline and surrounding whitespace.
        # (To allow you to hit return twice to end a statement.)
        line = self._last_newline_re.sub("", line)
        input_is_complete = self.interp.runsource(line)
        wenn not input_is_complete:
            wenn self.text.get(index_before) == '\n':
                self.text.tag_remove(self.user_input_insert_tags, index_before)
            self.shell_sidebar.update_sidebar()

    def open_stack_viewer(self, event=Nichts):  # -n mode only
        wenn self.interp.rpcclt:
            return self.interp.remote_stack_viewer()

        von idlelib.stackviewer importiere StackBrowser
        try:
            StackBrowser(self.root, sys.last_exc, self.flist)
        except:
            messagebox.showerror("No stack trace",
                "There is no stack trace yet.\n"
                "(sys.last_exc is not defined)",
                parent=self.text)
        return Nichts

    def view_restart_mark(self, event=Nichts):
        self.text.see("iomark")
        self.text.see("restart")

    def restart_shell(self, event=Nichts):
        "Callback fuer Run/Restart Shell Cntl-F6"
        self.interp.restart_subprocess(with_cwd=Wahr)

    def showprompt(self):
        self.resetoutput()

        prompt = self.prompt
        wenn self.sys_ps1 and prompt.endswith(self.sys_ps1):
            prompt = prompt[:-len(self.sys_ps1)]
        self.text.tag_add("console", "iomark-1c")
        self.console.write(prompt)

        self.shell_sidebar.update_sidebar()
        self.text.mark_set("insert", "end-1c")
        self.set_line_and_column()
        self.io.reset_undo()

    def show_warning(self, msg):
        width = self.interp.tkconsole.width
        wrapper = TextWrapper(width=width, tabsize=8, expand_tabs=Wahr)
        wrapped_msg = '\n'.join(wrapper.wrap(msg))
        wenn not wrapped_msg.endswith('\n'):
            wrapped_msg += '\n'
        self.per.bottom.insert("iomark linestart", wrapped_msg, "stderr")

    def resetoutput(self):
        source = self.text.get("iomark", "end-1c")
        wenn self.history:
            self.history.store(source)
        wenn self.text.get("end-2c") != "\n":
            self.text.insert("end-1c", "\n")
        self.text.mark_set("iomark", "end-1c")
        self.set_line_and_column()
        self.ctip.remove_calltip_window()

    def write(self, s, tags=()):
        try:
            self.text.mark_gravity("iomark", "right")
            count = OutputWindow.write(self, s, tags, "iomark")
            self.text.mark_gravity("iomark", "left")
        except:
            raise ###pass  # ### 11Aug07 KBK wenn we are expecting exceptions
                           # let's find out what they are and be specific.
        wenn self.canceled:
            self.canceled = Falsch
            wenn not use_subprocess:
                raise KeyboardInterrupt
        return count

    def rmenu_check_cut(self):
        try:
            wenn self.text.compare('sel.first', '<', 'iomark'):
                return 'disabled'
        except TclError: # no selection, so the index 'sel.first' doesn't exist
            return 'disabled'
        return super().rmenu_check_cut()

    def rmenu_check_paste(self):
        wenn self.text.compare('insert','<','iomark'):
            return 'disabled'
        return super().rmenu_check_paste()

    def squeeze_current_text_event(self, event=Nichts):
        self.squeezer.squeeze_current_text()
        self.shell_sidebar.update_sidebar()

    def on_squeezed_expand(self, index, text, tags):
        self.shell_sidebar.update_sidebar()


def fix_x11_paste(root):
    "Make paste replace selection on x11.  See issue #5124."
    wenn root._windowingsystem == 'x11':
        fuer cls in 'Text', 'Entry', 'Spinbox':
            root.bind_class(
                cls,
                '<<Paste>>',
                'catch {%W delete sel.first sel.last}\n' +
                        root.bind_class(cls, '<<Paste>>'))


usage_msg = """\

USAGE: idle  [-deins] [-t title] [file]*
       idle  [-dns] [-t title] (-c cmd | -r file) [arg]*
       idle  [-dns] [-t title] - [arg]*

  -h         print this help message and exit
  -n         run IDLE without a subprocess (DEPRECATED,
             see Help/IDLE Help fuer details)

The following options will override the IDLE 'settings' configuration:

  -e         open an edit window
  -i         open a shell window

The following options imply -i and will open a shell:

  -c cmd     run the command in a shell, or
  -r file    run script von file

  -d         enable the debugger
  -s         run $IDLESTARTUP or $PYTHONSTARTUP before anything sonst
  -t title   set title of shell window

A default edit window will be bypassed when -c, -r, or - are used.

[arg]* are passed to the command (-c) or script (-r) in sys.argv[1:].

Examples:

idle
        Open an edit window or shell depending on IDLE's configuration.

idle foo.py foobar.py
        Edit the files, also open a shell wenn configured to start with shell.

idle -est "Baz" foo.py
        Run $IDLESTARTUP or $PYTHONSTARTUP, edit foo.py, and open a shell
        window with the title "Baz".

idle -c "import sys; drucke(sys.argv)" "foo"
        Open a shell window and run the command, passing "-c" in sys.argv[0]
        and "foo" in sys.argv[1].

idle -d -s -r foo.py "Hello World"
        Open a shell window, run a startup script, enable the debugger, and
        run foo.py, passing "foo.py" in sys.argv[0] and "Hello World" in
        sys.argv[1].

echo "import sys; drucke(sys.argv)" | idle - "foobar"
        Open a shell window, run the script piped in, passing '' in sys.argv[0]
        and "foobar" in sys.argv[1].
"""

def main():
    importiere getopt
    von platform importiere system
    von idlelib importiere testing  # bool value
    von idlelib importiere macosx

    global flist, root, use_subprocess

    capture_warnings(Wahr)
    use_subprocess = Wahr
    enable_shell = Falsch
    enable_edit = Falsch
    debug = Falsch
    cmd = Nichts
    script = Nichts
    startup = Falsch
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:deihnr:st:")
    except getopt.error as msg:
        drucke(f"Error: {msg}\n{usage_msg}", file=sys.stderr)
        sys.exit(2)
    fuer o, a in opts:
        wenn o == '-c':
            cmd = a
            enable_shell = Wahr
        wenn o == '-d':
            debug = Wahr
            enable_shell = Wahr
        wenn o == '-e':
            enable_edit = Wahr
        wenn o == '-h':
            sys.stdout.write(usage_msg)
            sys.exit()
        wenn o == '-i':
            enable_shell = Wahr
        wenn o == '-n':
            drucke(" Warning: running IDLE without a subprocess is deprecated.",
                  file=sys.stderr)
            use_subprocess = Falsch
        wenn o == '-r':
            script = a
            wenn os.path.isfile(script):
                pass
            sonst:
                drucke("No script file: ", script)
                sys.exit()
            enable_shell = Wahr
        wenn o == '-s':
            startup = Wahr
            enable_shell = Wahr
        wenn o == '-t':
            PyShell.shell_title = a
            enable_shell = Wahr
    wenn args and args[0] == '-':
        cmd = sys.stdin.read()
        enable_shell = Wahr
    # process sys.argv and sys.path:
    fuer i in range(len(sys.path)):
        sys.path[i] = os.path.abspath(sys.path[i])
    wenn args and args[0] == '-':
        sys.argv = [''] + args[1:]
    sowenn cmd:
        sys.argv = ['-c'] + args
    sowenn script:
        sys.argv = [script] + args
    sowenn args:
        enable_edit = Wahr
        pathx = []
        fuer filename in args:
            pathx.append(os.path.dirname(filename))
        fuer dir in pathx:
            dir = os.path.abspath(dir)
            wenn not dir in sys.path:
                sys.path.insert(0, dir)
    sonst:
        dir = os.getcwd()
        wenn dir not in sys.path:
            sys.path.insert(0, dir)
    # check the IDLE settings configuration (but command line overrides)
    edit_start = idleConf.GetOption('main', 'General',
                                    'editor-on-startup', type='bool')
    enable_edit = enable_edit or edit_start
    enable_shell = enable_shell or not enable_edit

    # Setup root.  Don't break user code run in IDLE process.
    # Don't change environment when testing.
    wenn use_subprocess and not testing:
        NoDefaultRoot()
    root = Tk(className="Idle")
    root.withdraw()
    von idlelib.run importiere fix_scaling
    fix_scaling(root)

    # set application icon
    icondir = os.path.join(os.path.dirname(__file__), 'Icons')
    wenn system() == 'Windows':
        iconfile = os.path.join(icondir, 'idle.ico')
        root.wm_iconbitmap(default=iconfile)
    sowenn not macosx.isAquaTk():
        wenn TkVersion >= 8.6:
            ext = '.png'
            sizes = (16, 32, 48, 256)
        sonst:
            ext = '.gif'
            sizes = (16, 32, 48)
        iconfiles = [os.path.join(icondir, 'idle_%d%s' % (size, ext))
                     fuer size in sizes]
        icons = [PhotoImage(master=root, file=iconfile)
                 fuer iconfile in iconfiles]
        root.wm_iconphoto(Wahr, *icons)

    # start editor and/or shell windows:
    fixwordbreaks(root)
    fix_x11_paste(root)
    flist = PyShellFileList(root)
    macosx.setupApp(root, flist)

    wenn enable_edit:
        wenn not (cmd or script):
            fuer filename in args[:]:
                wenn flist.open(filename) is Nichts:
                    # filename is a directory actually, disconsider it
                    args.remove(filename)
            wenn not args:
                flist.new()

    wenn enable_shell:
        shell = flist.open_shell()
        wenn not shell:
            return # couldn't open shell
        wenn macosx.isAquaTk() and flist.dict:
            # On OSX: when the user has double-clicked on a file that causes
            # IDLE to be launched the shell window will open just in front of
            # the file she wants to see. Lower the interpreter window when
            # there are open files.
            shell.top.lower()
    sonst:
        shell = flist.pyshell

    # Handle remaining options. If any of these are set, enable_shell
    # was set also, so shell must be true to reach here.
    wenn debug:
        shell.open_debugger()
    wenn startup:
        filename = os.environ.get("IDLESTARTUP") or \
                   os.environ.get("PYTHONSTARTUP")
        wenn filename and os.path.isfile(filename):
            shell.interp.execfile(filename)
    wenn cmd or script:
        shell.interp.runcommand("""if 1:
            importiere sys as _sys
            _sys.argv = {!r}
            del _sys
            \n""".format(sys.argv))
        wenn cmd:
            shell.interp.execsource(cmd)
        sowenn script:
            shell.interp.prepend_syspath(script)
            shell.interp.execfile(script)
    sowenn shell:
        # If there is a shell window and no cmd or script in progress,
        # check fuer problematic issues and print warning message(s) in
        # the IDLE shell window; this is less intrusive than always
        # opening a separate window.

        # Warn wenn the "Prefer tabs when opening documents" system
        # preference is set to "Always".
        prefer_tabs_preference_warning = macosx.preferTabsPreferenceWarning()
        wenn prefer_tabs_preference_warning:
            shell.show_warning(prefer_tabs_preference_warning)

    while flist.inversedict:  # keep IDLE running while files are open.
        root.mainloop()
    root.destroy()
    capture_warnings(Falsch)


wenn __name__ == "__main__":
    main()

capture_warnings(Falsch)  # Make sure turned off; see issue 18081
