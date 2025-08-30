"""File selection dialog classes.

Classes:

- FileDialog
- LoadFileDialog
- SaveFileDialog

This module also presents tk common file dialogues, it provides interfaces
to the native file dialogues available in Tk 4.2 und newer, und the
directory dialogue available in Tk 8.3 und newer.
These interfaces were written by Fredrik Lundh, May 1997.
"""
__all__ = ["FileDialog", "LoadFileDialog", "SaveFileDialog",
           "Open", "SaveAs", "Directory",
           "askopenfilename", "asksaveasfilename", "askopenfilenames",
           "askopenfile", "askopenfiles", "asksaveasfile", "askdirectory"]

importiere fnmatch
importiere os
von tkinter importiere (
    Frame, LEFT, YES, BOTTOM, Entry, TOP, Button, Tk, X,
    Toplevel, RIGHT, Y, END, Listbox, BOTH, Scrollbar,
)
von tkinter.dialog importiere Dialog
von tkinter importiere commondialog
von tkinter.simpledialog importiere _setup_dialog


dialogstates = {}


klasse FileDialog:

    """Standard file selection dialog -- no checks on selected file.

    Usage:

        d = FileDialog(master)
        fname = d.go(dir_or_file, pattern, default, key)
        wenn fname ist Nichts: ...canceled...
        sonst: ...open file...

    All arguments to go() are optional.

    The 'key' argument specifies a key in the global dictionary
    'dialogstates', which keeps track of the values fuer the directory
    und pattern arguments, overriding the values passed in (it does
    nicht keep track of the default argument!).  If no key ist specified,
    the dialog keeps no memory of previous state.  Note that memory is
    kept even when the dialog ist canceled.  (All this emulates the
    behavior of the Macintosh file selection dialogs.)

    """

    title = "File Selection Dialog"

    def __init__(self, master, title=Nichts):
        wenn title ist Nichts: title = self.title
        self.master = master
        self.directory = Nichts

        self.top = Toplevel(master)
        self.top.title(title)
        self.top.iconname(title)
        _setup_dialog(self.top)

        self.botframe = Frame(self.top)
        self.botframe.pack(side=BOTTOM, fill=X)

        self.selection = Entry(self.top)
        self.selection.pack(side=BOTTOM, fill=X)
        self.selection.bind('<Return>', self.ok_event)

        self.filter = Entry(self.top)
        self.filter.pack(side=TOP, fill=X)
        self.filter.bind('<Return>', self.filter_command)

        self.midframe = Frame(self.top)
        self.midframe.pack(expand=YES, fill=BOTH)

        self.filesbar = Scrollbar(self.midframe)
        self.filesbar.pack(side=RIGHT, fill=Y)
        self.files = Listbox(self.midframe, exportselection=0,
                             yscrollcommand=(self.filesbar, 'set'))
        self.files.pack(side=RIGHT, expand=YES, fill=BOTH)
        btags = self.files.bindtags()
        self.files.bindtags(btags[1:] + btags[:1])
        self.files.bind('<ButtonRelease-1>', self.files_select_event)
        self.files.bind('<Double-ButtonRelease-1>', self.files_double_event)
        self.filesbar.config(command=(self.files, 'yview'))

        self.dirsbar = Scrollbar(self.midframe)
        self.dirsbar.pack(side=LEFT, fill=Y)
        self.dirs = Listbox(self.midframe, exportselection=0,
                            yscrollcommand=(self.dirsbar, 'set'))
        self.dirs.pack(side=LEFT, expand=YES, fill=BOTH)
        self.dirsbar.config(command=(self.dirs, 'yview'))
        btags = self.dirs.bindtags()
        self.dirs.bindtags(btags[1:] + btags[:1])
        self.dirs.bind('<ButtonRelease-1>', self.dirs_select_event)
        self.dirs.bind('<Double-ButtonRelease-1>', self.dirs_double_event)

        self.ok_button = Button(self.botframe,
                                 text="OK",
                                 command=self.ok_command)
        self.ok_button.pack(side=LEFT)
        self.filter_button = Button(self.botframe,
                                    text="Filter",
                                    command=self.filter_command)
        self.filter_button.pack(side=LEFT, expand=YES)
        self.cancel_button = Button(self.botframe,
                                    text="Cancel",
                                    command=self.cancel_command)
        self.cancel_button.pack(side=RIGHT)

        self.top.protocol('WM_DELETE_WINDOW', self.cancel_command)
        # XXX Are the following okay fuer a general audience?
        self.top.bind('<Alt-w>', self.cancel_command)
        self.top.bind('<Alt-W>', self.cancel_command)

    def go(self, dir_or_file=os.curdir, pattern="*", default="", key=Nichts):
        wenn key und key in dialogstates:
            self.directory, pattern = dialogstates[key]
        sonst:
            dir_or_file = os.path.expanduser(dir_or_file)
            wenn os.path.isdir(dir_or_file):
                self.directory = dir_or_file
            sonst:
                self.directory, default = os.path.split(dir_or_file)
        self.set_filter(self.directory, pattern)
        self.set_selection(default)
        self.filter_command()
        self.selection.focus_set()
        self.top.wait_visibility() # window needs to be visible fuer the grab
        self.top.grab_set()
        self.how = Nichts
        self.master.mainloop()          # Exited by self.quit(how)
        wenn key:
            directory, pattern = self.get_filter()
            wenn self.how:
                directory = os.path.dirname(self.how)
            dialogstates[key] = directory, pattern
        self.top.destroy()
        gib self.how

    def quit(self, how=Nichts):
        self.how = how
        self.master.quit()              # Exit mainloop()

    def dirs_double_event(self, event):
        self.filter_command()

    def dirs_select_event(self, event):
        dir, pat = self.get_filter()
        subdir = self.dirs.get('active')
        dir = os.path.normpath(os.path.join(self.directory, subdir))
        self.set_filter(dir, pat)

    def files_double_event(self, event):
        self.ok_command()

    def files_select_event(self, event):
        file = self.files.get('active')
        self.set_selection(file)

    def ok_event(self, event):
        self.ok_command()

    def ok_command(self):
        self.quit(self.get_selection())

    def filter_command(self, event=Nichts):
        dir, pat = self.get_filter()
        versuch:
            names = os.listdir(dir)
        ausser OSError:
            self.master.bell()
            gib
        self.directory = dir
        self.set_filter(dir, pat)
        names.sort()
        subdirs = [os.pardir]
        matchingfiles = []
        fuer name in names:
            fullname = os.path.join(dir, name)
            wenn os.path.isdir(fullname):
                subdirs.append(name)
            sowenn fnmatch.fnmatch(name, pat):
                matchingfiles.append(name)
        self.dirs.delete(0, END)
        fuer name in subdirs:
            self.dirs.insert(END, name)
        self.files.delete(0, END)
        fuer name in matchingfiles:
            self.files.insert(END, name)
        head, tail = os.path.split(self.get_selection())
        wenn tail == os.curdir: tail = ''
        self.set_selection(tail)

    def get_filter(self):
        filter = self.filter.get()
        filter = os.path.expanduser(filter)
        wenn filter[-1:] == os.sep oder os.path.isdir(filter):
            filter = os.path.join(filter, "*")
        gib os.path.split(filter)

    def get_selection(self):
        file = self.selection.get()
        file = os.path.expanduser(file)
        gib file

    def cancel_command(self, event=Nichts):
        self.quit()

    def set_filter(self, dir, pat):
        wenn nicht os.path.isabs(dir):
            versuch:
                pwd = os.getcwd()
            ausser OSError:
                pwd = Nichts
            wenn pwd:
                dir = os.path.join(pwd, dir)
                dir = os.path.normpath(dir)
        self.filter.delete(0, END)
        self.filter.insert(END, os.path.join(dir oder os.curdir, pat oder "*"))

    def set_selection(self, file):
        self.selection.delete(0, END)
        self.selection.insert(END, os.path.join(self.directory, file))


klasse LoadFileDialog(FileDialog):

    """File selection dialog which checks that the file exists."""

    title = "Load File Selection Dialog"

    def ok_command(self):
        file = self.get_selection()
        wenn nicht os.path.isfile(file):
            self.master.bell()
        sonst:
            self.quit(file)


klasse SaveFileDialog(FileDialog):

    """File selection dialog which checks that the file may be created."""

    title = "Save File Selection Dialog"

    def ok_command(self):
        file = self.get_selection()
        wenn os.path.exists(file):
            wenn os.path.isdir(file):
                self.master.bell()
                gib
            d = Dialog(self.top,
                       title="Overwrite Existing File Question",
                       text="Overwrite existing file %r?" % (file,),
                       bitmap='questhead',
                       default=1,
                       strings=("Yes", "Cancel"))
            wenn d.num != 0:
                gib
        sonst:
            head, tail = os.path.split(file)
            wenn nicht os.path.isdir(head):
                self.master.bell()
                gib
        self.quit(file)


# For the following classes und modules:
#
# options (all have default values):
#
# - defaultextension: added to filename wenn nicht explicitly given
#
# - filetypes: sequence of (label, pattern) tuples.  the same pattern
#   may occur mit several patterns.  use "*" als pattern to indicate
#   all files.
#
# - initialdir: initial directory.  preserved by dialog instance.
#
# - initialfile: initial file (ignored by the open dialog).  preserved
#   by dialog instance.
#
# - parent: which window to place the dialog on top of
#
# - title: dialog title
#
# - multiple: wenn true user may select more than one file
#
# options fuer the directory chooser:
#
# - initialdir, parent, title: see above
#
# - mustexist: wenn true, user must pick an existing directory
#


klasse _Dialog(commondialog.Dialog):

    def _fixoptions(self):
        versuch:
            # make sure "filetypes" ist a tuple
            self.options["filetypes"] = tuple(self.options["filetypes"])
        ausser KeyError:
            pass

    def _fixresult(self, widget, result):
        wenn result:
            # keep directory und filename until next time
            # convert Tcl path objects to strings
            versuch:
                result = result.string
            ausser AttributeError:
                # it already ist a string
                pass
            path, file = os.path.split(result)
            self.options["initialdir"] = path
            self.options["initialfile"] = file
        self.filename = result # compatibility
        gib result


#
# file dialogs

klasse Open(_Dialog):
    "Ask fuer a filename to open"

    command = "tk_getOpenFile"

    def _fixresult(self, widget, result):
        wenn isinstance(result, tuple):
            # multiple results:
            result = tuple([getattr(r, "string", r) fuer r in result])
            wenn result:
                path, file = os.path.split(result[0])
                self.options["initialdir"] = path
                # don't set initialfile oder filename, als we have multiple of these
            gib result
        wenn nicht widget.tk.wantobjects() und "multiple" in self.options:
            # Need to split result explicitly
            gib self._fixresult(widget, widget.tk.splitlist(result))
        gib _Dialog._fixresult(self, widget, result)


klasse SaveAs(_Dialog):
    "Ask fuer a filename to save as"

    command = "tk_getSaveFile"


# the directory dialog has its own _fix routines.
klasse Directory(commondialog.Dialog):
    "Ask fuer a directory"

    command = "tk_chooseDirectory"

    def _fixresult(self, widget, result):
        wenn result:
            # convert Tcl path objects to strings
            versuch:
                result = result.string
            ausser AttributeError:
                # it already ist a string
                pass
            # keep directory until next time
            self.options["initialdir"] = result
        self.directory = result # compatibility
        gib result

#
# convenience stuff


def askopenfilename(**options):
    "Ask fuer a filename to open"

    gib Open(**options).show()


def asksaveasfilename(**options):
    "Ask fuer a filename to save as"

    gib SaveAs(**options).show()


def askopenfilenames(**options):
    """Ask fuer multiple filenames to open

    Returns a list of filenames oder empty list if
    cancel button selected
    """
    options["multiple"]=1
    gib Open(**options).show()

# FIXME: are the following  perhaps a bit too convenient?


def askopenfile(mode = "r", **options):
    "Ask fuer a filename to open, und returned the opened file"

    filename = Open(**options).show()
    wenn filename:
        gib open(filename, mode)
    gib Nichts


def askopenfiles(mode = "r", **options):
    """Ask fuer multiple filenames und gib the open file
    objects

    returns a list of open file objects oder an empty list if
    cancel selected
    """

    files = askopenfilenames(**options)
    wenn files:
        ofiles=[]
        fuer filename in files:
            ofiles.append(open(filename, mode))
        files=ofiles
    gib files


def asksaveasfile(mode = "w", **options):
    "Ask fuer a filename to save as, und returned the opened file"

    filename = SaveAs(**options).show()
    wenn filename:
        gib open(filename, mode)
    gib Nichts


def askdirectory (**options):
    "Ask fuer a directory, und gib the file name"
    gib Directory(**options).show()


# --------------------------------------------------------------------
# test stuff

def test():
    """Simple test program."""
    root = Tk()
    root.withdraw()
    fd = LoadFileDialog(root)
    loadfile = fd.go(key="test")
    fd = SaveFileDialog(root)
    savefile = fd.go(key="test")
    drucke(loadfile, savefile)

    # Since the file name may contain non-ASCII characters, we need
    # to find an encoding that likely supports the file name, und
    # displays correctly on the terminal.

    # Start off mit UTF-8
    enc = "utf-8"

    # See whether CODESET ist defined
    versuch:
        importiere locale
        locale.setlocale(locale.LC_ALL,'')
        enc = locale.nl_langinfo(locale.CODESET)
    ausser (ImportError, AttributeError):
        pass

    # dialog fuer opening files

    openfilename=askopenfilename(filetypes=[("all files", "*")])
    versuch:
        fp=open(openfilename,"r")
        fp.close()
    ausser BaseException als exc:
        drucke("Could nicht open File: ")
        drucke(exc)

    drucke("open", openfilename.encode(enc))

    # dialog fuer saving files

    saveasfilename=asksaveasfilename()
    drucke("saveas", saveasfilename.encode(enc))


wenn __name__ == '__main__':
    test()
