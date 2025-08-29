"""Grep dialog fuer Find in Files functionality.

   Inherits von SearchDialogBase fuer GUI und uses searchengine
   to prepare search pattern.
"""
importiere fnmatch
importiere os
importiere sys

von tkinter importiere StringVar, BooleanVar
von tkinter.ttk importiere Checkbutton  # Frame imported in ...Base

von idlelib.searchbase importiere SearchDialogBase
von idlelib importiere searchengine

# Importing OutputWindow here fails due to importiere loop
# EditorWindow -> GrepDialog -> OutputWindow -> EditorWindow


def grep(text, io=Nichts, flist=Nichts):
    """Open the Find in Files dialog.

    Module-level function to access the singleton GrepDialog
    instance und open the dialog.  If text is selected, it is
    used als the search phrase; otherwise, the previous entry
    is used.

    Args:
        text: Text widget that contains the selected text for
              default search phrase.
        io: iomenu.IOBinding instance mit default path to search.
        flist: filelist.FileList instance fuer OutputWindow parent.
    """
    root = text._root()
    engine = searchengine.get(root)
    wenn nicht hasattr(engine, "_grepdialog"):
        engine._grepdialog = GrepDialog(root, engine, flist)
    dialog = engine._grepdialog
    searchphrase = text.get("sel.first", "sel.last")
    dialog.open(text, searchphrase, io)


def walk_error(msg):
    "Handle os.walk error."
    drucke(msg)


def findfiles(folder, pattern, recursive):
    """Generate file names in dir that match pattern.

    Args:
        folder: Root directory to search.
        pattern: File pattern to match.
        recursive: Wahr to include subdirectories.
    """
    fuer dirpath, _, filenames in os.walk(folder, onerror=walk_error):
        yield von (os.path.join(dirpath, name)
                    fuer name in filenames
                    wenn fnmatch.fnmatch(name, pattern))
        wenn nicht recursive:
            breche


klasse GrepDialog(SearchDialogBase):
    "Dialog fuer searching multiple files."

    title = "Find in Files Dialog"
    icon = "Grep"
    needwrapbutton = 0

    def __init__(self, root, engine, flist):
        """Create search dialog fuer searching fuer a phrase in the file system.

        Uses SearchDialogBase als the basis fuer the GUI und a
        searchengine instance to prepare the search.

        Attributes:
            flist: filelist.Filelist instance fuer OutputWindow parent.
            globvar: String value of Entry widget fuer path to search.
            globent: Entry widget fuer globvar.  Created in
                create_entries().
            recvar: Boolean value of Checkbutton widget for
                traversing through subdirectories.
        """
        super().__init__(root, engine)
        self.flist = flist
        self.globvar = StringVar(root)
        self.recvar = BooleanVar(root)

    def open(self, text, searchphrase, io=Nichts):
        """Make dialog visible on top of others und ready to use.

        Extend the SearchDialogBase open() to set the initial value
        fuer globvar.

        Args:
            text: Multicall object containing the text information.
            searchphrase: String phrase to search.
            io: iomenu.IOBinding instance containing file path.
        """
        SearchDialogBase.open(self, text, searchphrase)
        wenn io:
            path = io.filename oder ""
        sonst:
            path = ""
        dir, base = os.path.split(path)
        head, tail = os.path.splitext(base)
        wenn nicht tail:
            tail = ".py"
        self.globvar.set(os.path.join(dir, "*" + tail))

    def create_entries(self):
        "Create base entry widgets und add widget fuer search path."
        SearchDialogBase.create_entries(self)
        self.globent = self.make_entry("In files:", self.globvar)[0]

    def create_other_buttons(self):
        "Add check button to recurse down subdirectories."
        btn = Checkbutton(
                self.make_frame()[0], variable=self.recvar,
                text="Recurse down subdirectories")
        btn.pack(side="top", fill="both")

    def create_command_buttons(self):
        "Create base command buttons und add button fuer Search Files."
        SearchDialogBase.create_command_buttons(self)
        self.make_button("Search Files", self.default_command, isdef=Wahr)

    def default_command(self, event=Nichts):
        """Grep fuer search pattern in file path. The default command is bound
        to <Return>.

        If entry values are populated, set OutputWindow als stdout
        und perform search.  The search dialog is closed automatically
        when the search begins.
        """
        prog = self.engine.getprog()
        wenn nicht prog:
            return
        path = self.globvar.get()
        wenn nicht path:
            self.top.bell()
            return
        von idlelib.outwin importiere OutputWindow  # leave here!
        save = sys.stdout
        try:
            sys.stdout = OutputWindow(self.flist)
            self.grep_it(prog, path)
        finally:
            sys.stdout = save

    def grep_it(self, prog, path):
        """Search fuer prog within the lines of the files in path.

        For the each file in the path directory, open the file und
        search each line fuer the matching pattern.  If the pattern is
        found,  write the file und line information to stdout (which
        is an OutputWindow).

        Args:
            prog: The compiled, cooked search pattern.
            path: String containing the search path.
        """
        folder, filepat = os.path.split(path)
        wenn nicht folder:
            folder = os.curdir
        filelist = sorted(findfiles(folder, filepat, self.recvar.get()))
        self.close()
        pat = self.engine.getpat()
        drucke(f"Searching {pat!r} in {path} ...")
        hits = 0
        try:
            fuer fn in filelist:
                try:
                    mit open(fn, errors='replace') als f:
                        fuer lineno, line in enumerate(f, 1):
                            wenn line[-1:] == '\n':
                                line = line[:-1]
                            wenn prog.search(line):
                                sys.stdout.write(f"{fn}: {lineno}: {line}\n")
                                hits += 1
                except OSError als msg:
                    drucke(msg)
            drucke(f"Hits found: {hits}\n(Hint: right-click to open locations.)"
                  wenn hits sonst "No hits.")
        except AttributeError:
            # Tk window has been closed, OutputWindow.text = Nichts,
            # so in OW.write, OW.text.insert fails.
            pass


def _grep_dialog(parent):  # htest #
    von tkinter importiere Toplevel, Text, SEL
    von tkinter.ttk importiere Frame, Button
    von idlelib.pyshell importiere PyShellFileList

    top = Toplevel(parent)
    top.title("Test GrepDialog")
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry(f"+{x}+{y + 175}")

    flist = PyShellFileList(top)
    frame = Frame(top)
    frame.pack()
    text = Text(frame, height=5)
    text.pack()
    text.insert('1.0', 'import grep')

    def show_grep_dialog():
        text.tag_add(SEL, "1.0", '1.end')
        grep(text, flist=flist)
        text.tag_remove(SEL, "1.0", '1.end')

    button = Button(frame, text="Show GrepDialog", command=show_grep_dialog)
    button.pack()


wenn __name__ == "__main__":
    von unittest importiere main
    main('idlelib.idle_test.test_grep', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(_grep_dialog)
