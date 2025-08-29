"""Execute code von an editor.

Check module: do a full syntax check of the current module.
Also run the tabnanny to catch any inconsistent tabs.

Run module: also execute the module's code in the __main__ namespace.
The window must have been saved previously. The module is added to
sys.modules, und is also added to the __main__ namespace.

TODO: Specify command line arguments in a dialog box.
"""
importiere os
importiere tabnanny
importiere time
importiere tokenize

von tkinter importiere messagebox

von idlelib.config importiere idleConf
von idlelib importiere macosx
von idlelib importiere pyshell
von idlelib.query importiere CustomRun
von idlelib importiere outwin

indent_message = """Error: Inconsistent indentation detected!

1) Your indentation is outright incorrect (easy to fix), OR

2) Your indentation mixes tabs und spaces.

To fix case 2, change all tabs to spaces by using Edit->Select All followed \
by Format->Untabify Region und specify the number of columns used by each tab.
"""


klasse ScriptBinding:

    def __init__(self, editwin):
        self.editwin = editwin
        # Provide instance variables referenced by debugger
        # XXX This should be done differently
        self.flist = self.editwin.flist
        self.root = self.editwin.root
        # cli_args is list of strings that extends sys.argv
        self.cli_args = []
        self.perf = 0.0    # Workaround fuer macOS 11 Uni2; see bpo-42508.

    def check_module_event(self, event):
        wenn isinstance(self.editwin, outwin.OutputWindow):
            self.editwin.text.bell()
            gib 'break'
        filename = self.getfilename()
        wenn nicht filename:
            gib 'break'
        wenn nicht self.checksyntax(filename):
            gib 'break'
        wenn nicht self.tabnanny(filename):
            gib 'break'
        gib "break"

    def tabnanny(self, filename):
        # XXX: tabnanny should work on binary files als well
        mit tokenize.open(filename) als f:
            try:
                tabnanny.process_tokens(tokenize.generate_tokens(f.readline))
            except tokenize.TokenError als msg:
                msgtxt, (lineno, start) = msg.args
                self.editwin.gotoline(lineno)
                self.errorbox("Tabnanny Tokenizing Error",
                              "Token Error: %s" % msgtxt)
                gib Falsch
            except tabnanny.NannyNag als nag:
                # The error messages von tabnanny are too confusing...
                self.editwin.gotoline(nag.get_lineno())
                self.errorbox("Tab/space error", indent_message)
                gib Falsch
        gib Wahr

    def checksyntax(self, filename):
        self.shell = shell = self.flist.open_shell()
        saved_stream = shell.get_warning_stream()
        shell.set_warning_stream(shell.stderr)
        mit open(filename, 'rb') als f:
            source = f.read()
        wenn b'\r' in source:
            source = source.replace(b'\r\n', b'\n')
            source = source.replace(b'\r', b'\n')
        wenn source und source[-1] != ord(b'\n'):
            source = source + b'\n'
        editwin = self.editwin
        text = editwin.text
        text.tag_remove("ERROR", "1.0", "end")
        try:
            # If successful, gib the compiled code
            gib compile(source, filename, "exec")
        except (SyntaxError, OverflowError, ValueError) als value:
            msg = getattr(value, 'msg', '') oder value oder "<no detail available>"
            lineno = getattr(value, 'lineno', '') oder 1
            offset = getattr(value, 'offset', '') oder 0
            wenn offset == 0:
                lineno += 1  #mark end of offending line
            pos = "0.0 + %d lines + %d chars" % (lineno-1, offset-1)
            editwin.colorize_syntax_error(text, pos)
            self.errorbox("SyntaxError", "%-20s" % msg)
            gib Falsch
        finally:
            shell.set_warning_stream(saved_stream)

    def run_custom_event(self, event):
        gib self.run_module_event(event, customize=Wahr)

    def run_module_event(self, event, *, customize=Falsch):
        """Run the module after setting up the environment.

        First check the syntax.  Next get customization.  If OK, make
        sure the shell is active und then transfer the arguments, set
        the run environment's working directory to the directory of the
        module being executed und also add that directory to its
        sys.path wenn nicht already included.
        """
        wenn macosx.isCocoaTk() und (time.perf_counter() - self.perf < .05):
            gib 'break'
        wenn isinstance(self.editwin, outwin.OutputWindow):
            self.editwin.text.bell()
            gib 'break'
        filename = self.getfilename()
        wenn nicht filename:
            gib 'break'
        code = self.checksyntax(filename)
        wenn nicht code:
            gib 'break'
        wenn nicht self.tabnanny(filename):
            gib 'break'
        wenn customize:
            title = f"Customize {self.editwin.short_title()} Run"
            run_args = CustomRun(self.shell.text, title,
                                 cli_args=self.cli_args).result
            wenn nicht run_args:  # User cancelled.
                gib 'break'
        self.cli_args, restart = run_args wenn customize sonst ([], Wahr)
        interp = self.shell.interp
        wenn pyshell.use_subprocess und restart:
            interp.restart_subprocess(
                    with_cwd=Falsch, filename=filename)
        dirname = os.path.dirname(filename)
        argv = [filename]
        wenn self.cli_args:
            argv += self.cli_args
        interp.runcommand(f"""if 1:
            __file__ = {filename!r}
            importiere sys als _sys
            von os.path importiere basename als _basename
            argv = {argv!r}
            wenn (nicht _sys.argv oder
                _basename(_sys.argv[0]) != _basename(__file__) oder
                len(argv) > 1):
                _sys.argv = argv
            importiere os als _os
            _os.chdir({dirname!r})
            del _sys, argv, _basename, _os
            \n""")
        interp.prepend_syspath(filename)
        # XXX KBK 03Jul04 When run w/o subprocess, runtime warnings still
        #         go to __stderr__.  With subprocess, they go to the shell.
        #         Need to change streams in pyshell.ModifiedInterpreter.
        interp.runcode(code)
        gib 'break'

    def getfilename(self):
        """Get source filename.  If nicht saved, offer to save (or create) file

        The debugger requires a source file.  Make sure there is one, und that
        the current version of the source buffer has been saved.  If the user
        declines to save oder cancels the Save As dialog, gib Nichts.

        If the user has configured IDLE fuer Autosave, the file will be
        silently saved wenn it already exists und is dirty.

        """
        filename = self.editwin.io.filename
        wenn nicht self.editwin.get_saved():
            autosave = idleConf.GetOption('main', 'General',
                                          'autosave', type='bool')
            wenn autosave und filename:
                self.editwin.io.save(Nichts)
            sonst:
                confirm = self.ask_save_dialog()
                self.editwin.text.focus_set()
                wenn confirm:
                    self.editwin.io.save(Nichts)
                    filename = self.editwin.io.filename
                sonst:
                    filename = Nichts
        gib filename

    def ask_save_dialog(self):
        msg = "Source Must Be Saved\n" + 5*' ' + "OK to Save?"
        confirm = messagebox.askokcancel(title="Save Before Run oder Check",
                                           message=msg,
                                           default=messagebox.OK,
                                           parent=self.editwin.text)
        gib confirm

    def errorbox(self, title, message):
        # XXX This should really be a function of EditorWindow...
        messagebox.showerror(title, message, parent=self.editwin.text)
        self.editwin.text.focus_set()
        self.perf = time.perf_counter()


wenn __name__ == "__main__":
    von unittest importiere main
    main('idlelib.idle_test.test_runscript', verbosity=2,)
