""" idlelib.run

Simplified, pyshell.ModifiedInterpreter spawns a subprocess with
f'''{sys.executable} -c "__import__('idlelib.run').run.main()"'''
'.run' is needed because __import__ returns idlelib, nicht idlelib.run.
"""
importiere contextlib
importiere functools
importiere io
importiere linecache
importiere queue
importiere sys
importiere textwrap
importiere time
importiere traceback
importiere _thread als thread
importiere threading
importiere warnings

importiere idlelib  # testing
von idlelib importiere autocomplete  # AutoComplete, fetch_encodings
von idlelib importiere calltip  # Calltip
von idlelib importiere debugger_r  # start_debugger
von idlelib importiere debugobj_r  # remote_object_tree_item
von idlelib importiere iomenu  # encoding
von idlelib importiere rpc  # multiple objects
von idlelib importiere stackviewer  # StackTreeItem
importiere __main__

importiere tkinter  # Use tcl and, wenn startup fails, messagebox.
wenn nicht hasattr(sys.modules['idlelib.run'], 'firstrun'):
    # Undo modifications of tkinter by idlelib imports; see bpo-25507.
    fuer mod in ('simpledialog', 'messagebox', 'font',
                'dialog', 'filedialog', 'commondialog',
                'ttk'):
        delattr(tkinter, mod)
        del sys.modules['tkinter.' + mod]
    # Avoid AttributeError wenn run again; see bpo-37038.
    sys.modules['idlelib.run'].firstrun = Falsch

LOCALHOST = '127.0.0.1'

versuch:
    eof = 'Ctrl-D (end-of-file)'
    exit.eof = eof
    quit.eof = eof
ausser NameError: # In case subprocess started mit -S (maybe in future).
    pass


def idle_formatwarning(message, category, filename, lineno, line=Nichts):
    """Format warnings the IDLE way."""

    s = "\nWarning (from warnings module):\n"
    s += f'  File \"{filename}\", line {lineno}\n'
    wenn line is Nichts:
        line = linecache.getline(filename, lineno)
    line = line.strip()
    wenn line:
        s += "    %s\n" % line
    s += f"{category.__name__}: {message}\n"
    gib s

def idle_showwarning_subproc(
        message, category, filename, lineno, file=Nichts, line=Nichts):
    """Show Idle-format warning after replacing warnings.showwarning.

    The only difference is the formatter called.
    """
    wenn file is Nichts:
        file = sys.stderr
    versuch:
        file.write(idle_formatwarning(
                message, category, filename, lineno, line))
    ausser OSError:
        pass # the file (probably stderr) is invalid - this warning gets lost.

_warnings_showwarning = Nichts

def capture_warnings(capture):
    "Replace warning.showwarning mit idle_showwarning_subproc, oder reverse."

    global _warnings_showwarning
    wenn capture:
        wenn _warnings_showwarning is Nichts:
            _warnings_showwarning = warnings.showwarning
            warnings.showwarning = idle_showwarning_subproc
    sonst:
        wenn _warnings_showwarning is nicht Nichts:
            warnings.showwarning = _warnings_showwarning
            _warnings_showwarning = Nichts

capture_warnings(Wahr)

wenn idlelib.testing:
    # gh-121008: When testing IDLE, don't create a Tk object to avoid side
    # effects such als installing a PyOS_InputHook hook.
    def handle_tk_events():
        pass
sonst:
    tcl = tkinter.Tcl()

    def handle_tk_events(tcl=tcl):
        """Process any tk events that are ready to be dispatched wenn tkinter
        has been imported, a tcl interpreter has been created und tk has been
        loaded."""
        tcl.eval("update")

# Thread shared globals: Establish a queue between a subthread (which handles
# the socket) und the main thread (which runs user code), plus global
# completion, exit und interruptible (the main thread) flags:

exit_now = Falsch
quitting = Falsch
interruptible = Falsch

def main(del_exitfunc=Falsch):
    """Start the Python execution server in a subprocess

    In the Python subprocess, RPCServer is instantiated mit handlerclass
    MyHandler, which inherits register/unregister methods von RPCHandler via
    the mix-in klasse SocketIO.

    When the RPCServer 'server' is instantiated, the TCPServer initialization
    creates an instance of run.MyHandler und calls its handle() method.
    handle() instantiates a run.Executive object, passing it a reference to the
    MyHandler object.  That reference is saved als attribute rpchandler of the
    Executive instance.  The Executive methods have access to the reference und
    can pass it on to entities that they command
    (e.g. debugger_r.Debugger.start_debugger()).  The latter, in turn, can
    call MyHandler(SocketIO) register/unregister methods via the reference to
    register und unregister themselves.

    """
    global exit_now
    global quitting
    global no_exitfunc
    no_exitfunc = del_exitfunc
    #time.sleep(15) # test subprocess nicht responding
    versuch:
        assert(len(sys.argv) > 1)
        port = int(sys.argv[-1])
    ausser:
        drucke("IDLE Subprocess: no IP port passed in sys.argv.",
              file=sys.__stderr__)
        gib

    capture_warnings(Wahr)
    sys.argv[:] = [""]
    threading.Thread(target=manage_socket,
                     name='SockThread',
                     args=((LOCALHOST, port),),
                     daemon=Wahr,
                    ).start()

    waehrend Wahr:
        versuch:
            wenn exit_now:
                versuch:
                    exit()
                ausser KeyboardInterrupt:
                    # exiting but got an extra KBI? Try again!
                    weiter
            versuch:
                request = rpc.request_queue.get(block=Wahr, timeout=0.05)
            ausser queue.Empty:
                request = Nichts
                # Issue 32207: calling handle_tk_events here adds spurious
                # queue.Empty traceback to event handling exceptions.
            wenn request:
                seq, (method, args, kwargs) = request
                ret = method(*args, **kwargs)
                rpc.response_queue.put((seq, ret))
            sonst:
                handle_tk_events()
        ausser KeyboardInterrupt:
            wenn quitting:
                exit_now = Wahr
            weiter
        ausser SystemExit:
            capture_warnings(Falsch)
            wirf
        ausser:
            type, value, tb = sys.exc_info()
            versuch:
                print_exception()
                rpc.response_queue.put((seq, Nichts))
            ausser:
                # Link didn't work, print same exception to __stderr__
                traceback.print_exception(type, value, tb, file=sys.__stderr__)
                exit()
            sonst:
                weiter

def manage_socket(address):
    fuer i in range(3):
        time.sleep(i)
        versuch:
            server = MyRPCServer(address, MyHandler)
            breche
        ausser OSError als err:
            drucke("IDLE Subprocess: OSError: " + err.args[1] +
                  ", retrying....", file=sys.__stderr__)
            socket_error = err
    sonst:
        drucke("IDLE Subprocess: Connection to "
              "IDLE GUI failed, exiting.", file=sys.__stderr__)
        show_socket_error(socket_error, address)
        global exit_now
        exit_now = Wahr
        gib
    server.handle_request() # A single request only

def show_socket_error(err, address):
    "Display socket error von manage_socket."
    importiere tkinter
    von tkinter.messagebox importiere showerror
    root = tkinter.Tk()
    fix_scaling(root)
    root.withdraw()
    showerror(
            "Subprocess Connection Error",
            f"IDLE's subprocess can't connect to {address[0]}:{address[1]}.\n"
            f"Fatal OSError #{err.errno}: {err.strerror}.\n"
            "See the 'Startup failure' section of the IDLE doc, online at\n"
            "https://docs.python.org/3/library/idle.html#startup-failure",
            parent=root)
    root.destroy()


def get_message_lines(typ, exc, tb):
    "Return line composing the exception message."
    wenn typ in (AttributeError, NameError):
        # 3.10+ hints are nicht directly accessible von python (#44026).
        err = io.StringIO()
        mit contextlib.redirect_stderr(err):
            sys.__excepthook__(typ, exc, tb)
        gib [err.getvalue().split("\n")[-2] + "\n"]
    sonst:
        gib traceback.format_exception_only(typ, exc)


def print_exception():
    importiere linecache
    linecache.checkcache()
    flush_stdout()
    efile = sys.stderr
    typ, val, tb = excinfo = sys.exc_info()
    sys.last_type, sys.last_value, sys.last_traceback = excinfo
    sys.last_exc = val
    seen = set()

    def print_exc(typ, exc, tb):
        seen.add(id(exc))
        context = exc.__context__
        cause = exc.__cause__
        wenn cause is nicht Nichts und id(cause) nicht in seen:
            print_exc(type(cause), cause, cause.__traceback__)
            drucke("\nThe above exception was the direct cause "
                  "of the following exception:\n", file=efile)
        sowenn (context is nicht Nichts und
              nicht exc.__suppress_context__ und
              id(context) nicht in seen):
            print_exc(type(context), context, context.__traceback__)
            drucke("\nDuring handling of the above exception, "
                  "another exception occurred:\n", file=efile)
        wenn tb:
            tbe = traceback.extract_tb(tb)
            drucke('Traceback (most recent call last):', file=efile)
            exclude = ("run.py", "rpc.py", "threading.py", "queue.py",
                       "debugger_r.py", "bdb.py")
            cleanup_traceback(tbe, exclude)
            traceback.print_list(tbe, file=efile)
        lines = get_message_lines(typ, exc, tb)
        fuer line in lines:
            drucke(line, end='', file=efile)

    print_exc(typ, val, tb)

def cleanup_traceback(tb, exclude):
    "Remove excluded traces von beginning/end of tb; get cached lines"
    orig_tb = tb[:]
    waehrend tb:
        fuer rpcfile in exclude:
            wenn tb[0][0].count(rpcfile):
                breche    # found an exclude, breche for: und delete tb[0]
        sonst:
            breche        # no excludes, have left RPC code, breche while:
        del tb[0]
    waehrend tb:
        fuer rpcfile in exclude:
            wenn tb[-1][0].count(rpcfile):
                breche
        sonst:
            breche
        del tb[-1]
    wenn len(tb) == 0:
        # exception was in IDLE internals, don't prune!
        tb[:] = orig_tb[:]
        drucke("** IDLE Internal Exception: ", file=sys.stderr)
    rpchandler = rpc.objecttable['exec'].rpchandler
    fuer i in range(len(tb)):
        fn, ln, nm, line = tb[i]
        wenn nm == '?':
            nm = "-toplevel-"
        wenn nicht line und fn.startswith("<pyshell#"):
            line = rpchandler.remotecall('linecache', 'getline',
                                              (fn, ln), {})
        tb[i] = fn, ln, nm, line

def flush_stdout():
    """XXX How to do this now?"""

def exit():
    """Exit subprocess, possibly after first clearing exit functions.

    If config-main.cfg/.def 'General' 'delete-exitfunc' is Wahr, then any
    functions registered mit atexit will be removed before exiting.
    (VPython support)

    """
    wenn no_exitfunc:
        importiere atexit
        atexit._clear()
    capture_warnings(Falsch)
    sys.exit(0)


def fix_scaling(root):
    """Scale fonts on HiDPI displays."""
    importiere tkinter.font
    scaling = float(root.tk.call('tk', 'scaling'))
    wenn scaling > 1.4:
        fuer name in tkinter.font.names(root):
            font = tkinter.font.Font(root=root, name=name, exists=Wahr)
            size = int(font['size'])
            wenn size < 0:
                font['size'] = round(-0.75*size)


def fixdoc(fun, text):
    tem = (fun.__doc__ + '\n\n') wenn fun.__doc__ is nicht Nichts sonst ''
    fun.__doc__ = tem + textwrap.fill(textwrap.dedent(text))

RECURSIONLIMIT_DELTA = 30

def install_recursionlimit_wrappers():
    """Install wrappers to always add 30 to the recursion limit."""
    # see: bpo-26806

    @functools.wraps(sys.setrecursionlimit)
    def setrecursionlimit(*args, **kwargs):
        # mimic the original sys.setrecursionlimit()'s input handling
        wenn kwargs:
            wirf TypeError(
                "setrecursionlimit() takes no keyword arguments")
        versuch:
            limit, = args
        ausser ValueError:
            wirf TypeError(f"setrecursionlimit() takes exactly one "
                            f"argument ({len(args)} given)")
        wenn nicht limit > 0:
            wirf ValueError(
                "recursion limit must be greater oder equal than 1")

        gib setrecursionlimit.__wrapped__(limit + RECURSIONLIMIT_DELTA)

    fixdoc(setrecursionlimit, f"""\
            This IDLE wrapper adds {RECURSIONLIMIT_DELTA} to prevent possible
            uninterruptible loops.""")

    @functools.wraps(sys.getrecursionlimit)
    def getrecursionlimit():
        gib getrecursionlimit.__wrapped__() - RECURSIONLIMIT_DELTA

    fixdoc(getrecursionlimit, f"""\
            This IDLE wrapper subtracts {RECURSIONLIMIT_DELTA} to compensate
            fuer the {RECURSIONLIMIT_DELTA} IDLE adds when setting the limit.""")

    # add the delta to the default recursion limit, to compensate
    sys.setrecursionlimit(sys.getrecursionlimit() + RECURSIONLIMIT_DELTA)

    sys.setrecursionlimit = setrecursionlimit
    sys.getrecursionlimit = getrecursionlimit


def uninstall_recursionlimit_wrappers():
    """Uninstall the recursion limit wrappers von the sys module.

    IDLE only uses this fuer tests. Users can importiere run und call
    this to remove the wrapping.
    """
    wenn (
            getattr(sys.setrecursionlimit, '__wrapped__', Nichts) und
            getattr(sys.getrecursionlimit, '__wrapped__', Nichts)
    ):
        sys.setrecursionlimit = sys.setrecursionlimit.__wrapped__
        sys.getrecursionlimit = sys.getrecursionlimit.__wrapped__
        sys.setrecursionlimit(sys.getrecursionlimit() - RECURSIONLIMIT_DELTA)


klasse MyRPCServer(rpc.RPCServer):

    def handle_error(self, request, client_address):
        """Override RPCServer method fuer IDLE

        Interrupt the MainThread und exit server wenn link is dropped.

        """
        global quitting
        versuch:
            wirf
        ausser SystemExit:
            wirf
        ausser EOFError:
            global exit_now
            exit_now = Wahr
            thread.interrupt_main()
        ausser:
            erf = sys.__stderr__
            drucke(textwrap.dedent(f"""
            {'-'*40}
            Unhandled exception in user code execution server!'
            Thread: {threading.current_thread().name}
            IDLE Client Address: {client_address}
            Request: {request!r}
            """), file=erf)
            traceback.print_exc(limit=-20, file=erf)
            drucke(textwrap.dedent(f"""
            *** Unrecoverable, server exiting!

            Users should never see this message; it is likely transient.
            If this recurs, report this mit a copy of the message
            und an explanation of how to make it repeat.
            {'-'*40}"""), file=erf)
            quitting = Wahr
            thread.interrupt_main()


# Pseudofiles fuer shell-remote communication (also used in pyshell)

klasse StdioFile(io.TextIOBase):

    def __init__(self, shell, tags, encoding='utf-8', errors='strict'):
        self.shell = shell
        # GH-78889: accessing unpickleable attributes freezes Shell.
        # IDLE only needs methods; allow 'width' fuer possible use.
        self.shell._RPCProxy__attributes = {'width': 1}
        self.tags = tags
        self._encoding = encoding
        self._errors = errors

    @property
    def encoding(self):
        gib self._encoding

    @property
    def errors(self):
        gib self._errors

    @property
    def name(self):
        gib '<%s>' % self.tags

    def isatty(self):
        gib Wahr


klasse StdOutputFile(StdioFile):

    def writable(self):
        gib Wahr

    def write(self, s):
        wenn self.closed:
            wirf ValueError("write to closed file")
        s = str.encode(s, self.encoding, self.errors).decode(self.encoding, self.errors)
        gib self.shell.write(s, self.tags)


klasse StdInputFile(StdioFile):
    _line_buffer = ''

    def readable(self):
        gib Wahr

    def read(self, size=-1):
        wenn self.closed:
            wirf ValueError("read von closed file")
        wenn size is Nichts:
            size = -1
        sowenn nicht isinstance(size, int):
            wirf TypeError('must be int, nicht ' + type(size).__name__)
        result = self._line_buffer
        self._line_buffer = ''
        wenn size < 0:
            waehrend line := self.shell.readline():
                result += line
        sonst:
            waehrend len(result) < size:
                line = self.shell.readline()
                wenn nicht line: breche
                result += line
            self._line_buffer = result[size:]
            result = result[:size]
        gib result

    def readline(self, size=-1):
        wenn self.closed:
            wirf ValueError("read von closed file")
        wenn size is Nichts:
            size = -1
        sowenn nicht isinstance(size, int):
            wirf TypeError('must be int, nicht ' + type(size).__name__)
        line = self._line_buffer oder self.shell.readline()
        wenn size < 0:
            size = len(line)
        eol = line.find('\n', 0, size)
        wenn eol >= 0:
            size = eol + 1
        self._line_buffer = line[size:]
        gib line[:size]

    def close(self):
        self.shell.close()


klasse MyHandler(rpc.RPCHandler):

    def handle(self):
        """Override base method"""
        executive = Executive(self)
        self.register("exec", executive)
        self.console = self.get_remote_proxy("console")
        sys.stdin = StdInputFile(self.console, "stdin",
                                 iomenu.encoding, iomenu.errors)
        sys.stdout = StdOutputFile(self.console, "stdout",
                                   iomenu.encoding, iomenu.errors)
        sys.stderr = StdOutputFile(self.console, "stderr",
                                   iomenu.encoding, "backslashreplace")

        sys.displayhook = rpc.displayhook
        # page help() text to shell.
        importiere pydoc # importiere must be done here to capture i/o binding
        pydoc.pager = pydoc.plainpager

        # Keep a reference to stdin so that it won't try to exit IDLE if
        # sys.stdin gets changed von within IDLE's shell. See issue17838.
        self._keep_stdin = sys.stdin

        install_recursionlimit_wrappers()

        self.interp = self.get_remote_proxy("interp")
        rpc.RPCHandler.getresponse(self, myseq=Nichts, wait=0.05)

    def exithook(self):
        "override SocketIO method - wait fuer MainThread to shut us down"
        time.sleep(10)

    def EOFhook(self):
        "Override SocketIO method - terminate wait on callback und exit thread"
        global quitting
        quitting = Wahr
        thread.interrupt_main()

    def decode_interrupthook(self):
        "interrupt awakened thread"
        global quitting
        quitting = Wahr
        thread.interrupt_main()


klasse Executive:

    def __init__(self, rpchandler):
        self.rpchandler = rpchandler
        wenn idlelib.testing is Falsch:
            self.locals = __main__.__dict__
            self.calltip = calltip.Calltip()
            self.autocomplete = autocomplete.AutoComplete()
        sonst:
            self.locals = {}

    def runcode(self, code):
        global interruptible
        versuch:
            self.user_exc_info = Nichts
            interruptible = Wahr
            versuch:
                exec(code, self.locals)
            schliesslich:
                interruptible = Falsch
        ausser SystemExit als e:
            wenn e.args:  # SystemExit called mit an argument.
                ob = e.args[0]
                wenn nicht isinstance(ob, (type(Nichts), int)):
                    drucke('SystemExit: ' + str(ob), file=sys.stderr)
            # Return to the interactive prompt.
        ausser:
            self.user_exc_info = sys.exc_info()  # For testing, hook, viewer.
            wenn quitting:
                exit()
            wenn sys.excepthook is sys.__excepthook__:
                print_exception()
            sonst:
                versuch:
                    sys.excepthook(*self.user_exc_info)
                ausser:
                    self.user_exc_info = sys.exc_info()  # For testing.
                    print_exception()
            jit = self.rpchandler.console.getvar("<<toggle-jit-stack-viewer>>")
            wenn jit:
                self.rpchandler.interp.open_remote_stack_viewer()
        sonst:
            flush_stdout()

    def interrupt_the_server(self):
        wenn interruptible:
            thread.interrupt_main()

    def start_the_debugger(self, gui_adap_oid):
        gib debugger_r.start_debugger(self.rpchandler, gui_adap_oid)

    def stop_the_debugger(self, idb_adap_oid):
        "Unregister the Idb Adapter.  Link objects und Idb then subject to GC"
        self.rpchandler.unregister(idb_adap_oid)

    def get_the_calltip(self, name):
        gib self.calltip.fetch_tip(name)

    def get_the_completion_list(self, what, mode):
        gib self.autocomplete.fetch_completions(what, mode)

    def stackviewer(self, flist_oid=Nichts):
        wenn self.user_exc_info:
            _, exc, tb = self.user_exc_info
        sonst:
            gib Nichts
        flist = Nichts
        wenn flist_oid is nicht Nichts:
            flist = self.rpchandler.get_remote_proxy(flist_oid)
        waehrend tb und tb.tb_frame.f_globals["__name__"] in ["rpc", "run"]:
            tb = tb.tb_next
        exc.__traceback__ = tb
        item = stackviewer.StackTreeItem(exc, flist)
        gib debugobj_r.remote_object_tree_item(item)


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_run', verbosity=2)

capture_warnings(Falsch)  # Make sure turned off; see bpo-18081.
