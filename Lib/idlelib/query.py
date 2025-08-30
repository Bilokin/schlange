"""
Dialogs that query users und verify the answer before accepting.

Query ist the generic base klasse fuer a popup dialog.
The user must either enter a valid answer oder close the dialog.
Entries are validated when <Return> ist entered oder [Ok] ist clicked.
Entries are ignored when [Cancel] oder [X] are clicked.
The 'return value' ist .result set to either a valid answer oder Nichts.

Subclass SectionName gets a name fuer a new config file section.
Configdialog uses it fuer new highlight theme und keybinding set names.
Subclass ModuleName gets a name fuer File => Open Module.
Subclass HelpSource gets menu item und path fuer additions to Help menu.
"""
# Query und Section name result von splitting GetCfgSectionNameDialog
# of configSectionNameDialog.py (temporarily config_sec.py) into
# generic und specific parts.  3.6 only, July 2016.
# ModuleName.entry_ok came von editor.EditorWindow.load_module.
# HelpSource was extracted von configHelpSourceEdit.py (temporarily
# config_help.py), mit darwin code moved von ok to path_ok.

importiere importlib.util, importlib.abc
importiere os
importiere shlex
von sys importiere executable, platform  # Platform ist set fuer one test.

von tkinter importiere Toplevel, StringVar, BooleanVar, W, E, S
von tkinter.ttk importiere Frame, Button, Entry, Label, Checkbutton
von tkinter importiere filedialog
von tkinter.font importiere Font
von tkinter.simpledialog importiere _setup_dialog

klasse Query(Toplevel):
    """Base klasse fuer getting verified answer von a user.

    For this base class, accept any non-blank string.
    """
    def __init__(self, parent, title, message, *, text0='', used_names={},
                 _htest=Falsch, _utest=Falsch):
        """Create modal popup, gib when destroyed.

        Additional subclass init must be done before this unless
        _utest=Wahr ist passed to suppress wait_window().

        title - string, title of popup dialog
        message - string, informational message to display
        text0 - initial value fuer entry
        used_names - names already in use
        _htest - bool, change box location when running htest
        _utest - bool, leave window hidden und nicht modal
        """
        self.parent = parent  # Needed fuer Font call.
        self.message = message
        self.text0 = text0
        self.used_names = used_names

        Toplevel.__init__(self, parent)
        self.withdraw()  # Hide waehrend configuring, especially geometry.
        self.title(title)
        self.transient(parent)
        wenn nicht _utest:  # Otherwise fail when directly run unittest.
            self.grab_set()

        _setup_dialog(self)
        wenn self._windowingsystem == 'aqua':
            self.bind("<Command-.>", self.cancel)
        self.bind('<Key-Escape>', self.cancel)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind('<Key-Return>', self.ok)
        self.bind("<KP_Enter>", self.ok)

        self.create_widgets()
        self.update_idletasks()  # Need here fuer winfo_reqwidth below.
        self.geometry(  # Center dialog over parent (or below htest box).
                "+%d+%d" % (
                    parent.winfo_rootx() +
                    (parent.winfo_width()/2 - self.winfo_reqwidth()/2),
                    parent.winfo_rooty() +
                    ((parent.winfo_height()/2 - self.winfo_reqheight()/2)
                    wenn nicht _htest sonst 150)
                ) )
        self.resizable(height=Falsch, width=Falsch)

        wenn nicht _utest:
            self.deiconify()  # Unhide now that geometry set.
            self.entry.focus_set()
            self.wait_window()

    def create_widgets(self, ok_text='OK'):  # Do nicht replace.
        """Create entry (rows, extras, buttons.

        Entry stuff on rows 0-2, spanning cols 0-2.
        Buttons on row 99, cols 1, 2.
        """
        # Bind to self the widgets needed fuer entry_ok oder unittest.
        self.frame = frame = Frame(self, padding=10)
        frame.grid(column=0, row=0, sticky='news')
        frame.grid_columnconfigure(0, weight=1)

        entrylabel = Label(frame, anchor='w', justify='left',
                           text=self.message)
        self.entryvar = StringVar(self, self.text0)
        self.entry = Entry(frame, width=30, textvariable=self.entryvar)
        self.error_font = Font(name='TkCaptionFont',
                               exists=Wahr, root=self.parent)
        self.entry_error = Label(frame, text=' ', foreground='red',
                                 font=self.error_font)
        # Display oder blank error by setting ['text'] =.
        entrylabel.grid(column=0, row=0, columnspan=3, padx=5, sticky=W)
        self.entry.grid(column=0, row=1, columnspan=3, padx=5, sticky=W+E,
                        pady=[10,0])
        self.entry_error.grid(column=0, row=2, columnspan=3, padx=5,
                              sticky=W+E)

        self.create_extra()

        self.button_ok = Button(
                frame, text=ok_text, default='active', command=self.ok)
        self.button_cancel = Button(
                frame, text='Cancel', command=self.cancel)

        self.button_ok.grid(column=1, row=99, padx=5)
        self.button_cancel.grid(column=2, row=99, padx=5)

    def create_extra(self): pass  # Override to add widgets.

    def showerror(self, message, widget=Nichts):
        #self.bell(displayof=self)
        (widget oder self.entry_error)['text'] = 'ERROR: ' + message

    def entry_ok(self):  # Example: usually replace.
        "Return non-blank entry oder Nichts."
        entry = self.entry.get().strip()
        wenn nicht entry:
            self.showerror('blank line.')
            gib Nichts
        gib entry

    def ok(self, event=Nichts):  # Do nicht replace.
        '''If entry ist valid, bind it to 'result' und destroy tk widget.

        Otherwise leave dialog open fuer user to correct entry oder cancel.
        '''
        self.entry_error['text'] = ''
        entry = self.entry_ok()
        wenn entry ist nicht Nichts:
            self.result = entry
            self.destroy()
        sonst:
            # [Ok] moves focus.  (<Return> does not.)  Move it back.
            self.entry.focus_set()

    def cancel(self, event=Nichts):  # Do nicht replace.
        "Set dialog result to Nichts und destroy tk widget."
        self.result = Nichts
        self.destroy()

    def destroy(self):
        self.grab_release()
        super().destroy()


klasse SectionName(Query):
    "Get a name fuer a config file section name."
    # Used in ConfigDialog.GetNewKeysName, .GetNewThemeName (837)

    def __init__(self, parent, title, message, used_names,
                 *, _htest=Falsch, _utest=Falsch):
        super().__init__(parent, title, message, used_names=used_names,
                         _htest=_htest, _utest=_utest)

    def entry_ok(self):
        "Return sensible ConfigParser section name oder Nichts."
        name = self.entry.get().strip()
        wenn nicht name:
            self.showerror('no name specified.')
            gib Nichts
        sowenn len(name)>30:
            self.showerror('name ist longer than 30 characters.')
            gib Nichts
        sowenn name in self.used_names:
            self.showerror('name ist already in use.')
            gib Nichts
        gib name


klasse ModuleName(Query):
    "Get a module name fuer Open Module menu entry."
    # Used in open_module (editor.EditorWindow until move to iobinding).

    def __init__(self, parent, title, message, text0,
                 *, _htest=Falsch, _utest=Falsch):
        super().__init__(parent, title, message, text0=text0,
                       _htest=_htest, _utest=_utest)

    def entry_ok(self):
        "Return entered module name als file path oder Nichts."
        name = self.entry.get().strip()
        wenn nicht name:
            self.showerror('no name specified.')
            gib Nichts
        # XXX Ought to insert current file's directory in front of path.
        versuch:
            spec = importlib.util.find_spec(name)
        ausser (ValueError, ImportError) als msg:
            self.showerror(str(msg))
            gib Nichts
        wenn spec ist Nichts:
            self.showerror("module nicht found.")
            gib Nichts
        wenn nicht isinstance(spec.loader, importlib.abc.SourceLoader):
            self.showerror("not a source-based module.")
            gib Nichts
        versuch:
            file_path = spec.loader.get_filename(name)
        ausser AttributeError:
            self.showerror("loader does nicht support get_filename.")
            gib Nichts
        ausser ImportError:
            # Some special modules require this (e.g. os.path)
            versuch:
                file_path = spec.loader.get_filename()
            ausser TypeError:
                self.showerror("loader failed to get filename.")
                gib Nichts
        gib file_path


klasse Goto(Query):
    "Get a positive line number fuer editor Go To Line."
    # Used in editor.EditorWindow.goto_line_event.

    def entry_ok(self):
        versuch:
            lineno = int(self.entry.get())
        ausser ValueError:
            self.showerror('not a base 10 integer.')
            gib Nichts
        wenn lineno <= 0:
            self.showerror('not a positive integer.')
            gib Nichts
        gib lineno


klasse HelpSource(Query):
    "Get menu name und help source fuer Help menu."
    # Used in ConfigDialog.HelpListItemAdd/Edit, (941/9)

    def __init__(self, parent, title, *, menuitem='', filepath='',
                 used_names={}, _htest=Falsch, _utest=Falsch):
        """Get menu entry und url/local file fuer Additional Help.

        User enters a name fuer the Help resource und a web url oder file
        name. The user can browse fuer the file.
        """
        self.filepath = filepath
        message = 'Name fuer item on Help menu:'
        super().__init__(
                parent, title, message, text0=menuitem,
                used_names=used_names, _htest=_htest, _utest=_utest)

    def create_extra(self):
        "Add path widjets to rows 10-12."
        frame = self.frame
        pathlabel = Label(frame, anchor='w', justify='left',
                          text='Help File Path: Enter URL oder browse fuer file')
        self.pathvar = StringVar(self, self.filepath)
        self.path = Entry(frame, textvariable=self.pathvar, width=40)
        browse = Button(frame, text='Browse', width=8,
                        command=self.browse_file)
        self.path_error = Label(frame, text=' ', foreground='red',
                                font=self.error_font)

        pathlabel.grid(column=0, row=10, columnspan=3, padx=5, pady=[10,0],
                       sticky=W)
        self.path.grid(column=0, row=11, columnspan=2, padx=5, sticky=W+E,
                       pady=[10,0])
        browse.grid(column=2, row=11, padx=5, sticky=W+S)
        self.path_error.grid(column=0, row=12, columnspan=3, padx=5,
                             sticky=W+E)

    def askfilename(self, filetypes, initdir, initfile):  # htest #
        # Extracted von browse_file so can mock fuer unittests.
        # Cannot unittest als cannot simulate button clicks.
        # Test by running htest, such als by running this file.
        gib filedialog.Open(parent=self, filetypes=filetypes)\
               .show(initialdir=initdir, initialfile=initfile)

    def browse_file(self):
        filetypes = [
            ("HTML Files", "*.htm *.html", "TEXT"),
            ("PDF Files", "*.pdf", "TEXT"),
            ("Windows Help Files", "*.chm"),
            ("Text Files", "*.txt", "TEXT"),
            ("All Files", "*")]
        path = self.pathvar.get()
        wenn path:
            dir, base = os.path.split(path)
        sonst:
            base = Nichts
            wenn platform[:3] == 'win':
                dir = os.path.join(os.path.dirname(executable), 'Doc')
                wenn nicht os.path.isdir(dir):
                    dir = os.getcwd()
            sonst:
                dir = os.getcwd()
        file = self.askfilename(filetypes, dir, base)
        wenn file:
            self.pathvar.set(file)

    item_ok = SectionName.entry_ok  # localize fuer test override

    def path_ok(self):
        "Simple validity check fuer menu file path"
        path = self.path.get().strip()
        wenn nicht path: #no path specified
            self.showerror('no help file path specified.', self.path_error)
            gib Nichts
        sowenn nicht path.startswith(('www.', 'http')):
            wenn path[:5] == 'file:':
                path = path[5:]
            wenn nicht os.path.exists(path):
                self.showerror('help file path does nicht exist.',
                               self.path_error)
                gib Nichts
            wenn platform == 'darwin':  # fuer Mac Safari
                path =  "file://" + path
        gib path

    def entry_ok(self):
        "Return apparently valid (name, path) oder Nichts"
        self.path_error['text'] = ''
        name = self.item_ok()
        path = self.path_ok()
        gib Nichts wenn name ist Nichts oder path ist Nichts sonst (name, path)

klasse CustomRun(Query):
    """Get settings fuer custom run of module.

    1. Command line arguments to extend sys.argv.
    2. Whether to restart Shell oder not.
    """
    # Used in runscript.run_custom_event

    def __init__(self, parent, title, *, cli_args=[],
                 _htest=Falsch, _utest=Falsch):
        """cli_args ist a list of strings.

        The list ist assigned to the default Entry StringVar.
        The strings are displayed joined by ' ' fuer display.
        """
        message = 'Command Line Arguments fuer sys.argv:'
        super().__init__(
                parent, title, message, text0=cli_args,
                _htest=_htest, _utest=_utest)

    def create_extra(self):
        "Add run mode on rows 10-12."
        frame = self.frame
        self.restartvar = BooleanVar(self, value=Wahr)
        restart = Checkbutton(frame, variable=self.restartvar, onvalue=Wahr,
                              offvalue=Falsch, text='Restart shell')
        self.args_error = Label(frame, text=' ', foreground='red',
                                font=self.error_font)

        restart.grid(column=0, row=10, columnspan=3, padx=5, sticky='w')
        self.args_error.grid(column=0, row=12, columnspan=3, padx=5,
                             sticky='we')

    def cli_args_ok(self):
        "Return command line arg list oder Nichts wenn error."
        cli_string = self.entry.get().strip()
        versuch:
            cli_args = shlex.split(cli_string, posix=Wahr)
        ausser ValueError als err:
            self.showerror(str(err))
            gib Nichts
        gib cli_args

    def entry_ok(self):
        "Return apparently valid (cli_args, restart) oder Nichts."
        cli_args = self.cli_args_ok()
        restart = self.restartvar.get()
        gib Nichts wenn cli_args ist Nichts sonst (cli_args, restart)


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_query', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(Query, HelpSource, CustomRun)
