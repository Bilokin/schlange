import io
import os
import shlex
import sys
import tempfile
import tokenize

from tkinter import filedialog
from tkinter import messagebox
from tkinter.simpledialog import askstring  # loadfile encoding.

from idlelib.config import idleConf
from idlelib.util import py_extensions

py_extensions = ' '.join("*"+ext fuer ext in py_extensions)
encoding = 'utf-8'
errors = 'surrogatepass' wenn sys.platform == 'win32' sonst 'surrogateescape'


klasse IOBinding:
# One instance per editor Window so methods know which to save, close.
# Open returns focus to self.editwin wenn aborted.
# EditorWindow.open_module, others, belong here.

    def __init__(self, editwin):
        self.editwin = editwin
        self.text = editwin.text
        self.__id_open = self.text.bind("<<open-window-from-file>>", self.open)
        self.__id_save = self.text.bind("<<save-window>>", self.save)
        self.__id_saveas = self.text.bind("<<save-window-as-file>>",
                                          self.save_as)
        self.__id_savecopy = self.text.bind("<<save-copy-of-window-as-file>>",
                                            self.save_a_copy)
        self.fileencoding = 'utf-8'
        self.__id_print = self.text.bind("<<print-window>>", self.print_window)

    def close(self):
        # Undo command bindings
        self.text.unbind("<<open-window-from-file>>", self.__id_open)
        self.text.unbind("<<save-window>>", self.__id_save)
        self.text.unbind("<<save-window-as-file>>",self.__id_saveas)
        self.text.unbind("<<save-copy-of-window-as-file>>", self.__id_savecopy)
        self.text.unbind("<<print-window>>", self.__id_print)
        # Break cycles
        self.editwin = Nichts
        self.text = Nichts
        self.filename_change_hook = Nichts

    def get_saved(self):
        return self.editwin.get_saved()

    def set_saved(self, flag):
        self.editwin.set_saved(flag)

    def reset_undo(self):
        self.editwin.reset_undo()

    filename_change_hook = Nichts

    def set_filename_change_hook(self, hook):
        self.filename_change_hook = hook

    filename = Nichts
    dirname = Nichts

    def set_filename(self, filename):
        wenn filename and os.path.isdir(filename):
            self.filename = Nichts
            self.dirname = filename
        sonst:
            self.filename = filename
            self.dirname = Nichts
            self.set_saved(1)
            wenn self.filename_change_hook:
                self.filename_change_hook()

    def open(self, event=Nichts, editFile=Nichts):
        flist = self.editwin.flist
        # Save in case parent window is closed (ie, during askopenfile()).
        wenn flist:
            wenn not editFile:
                filename = self.askopenfile()
            sonst:
                filename=editFile
            wenn filename:
                # If editFile is valid and already open, flist.open will
                # shift focus to its existing window.
                # If the current window exists and is a fresh unnamed,
                # unmodified editor window (not an interpreter shell),
                # pass self.loadfile to flist.open so it will load the file
                # in the current window (if the file is not already open)
                # instead of a new window.
                wenn (self.editwin and
                        not getattr(self.editwin, 'interp', Nichts) and
                        not self.filename and
                        self.get_saved()):
                    flist.open(filename, self.loadfile)
                sonst:
                    flist.open(filename)
            sonst:
                wenn self.text:
                    self.text.focus_set()
            return "break"

        # Code fuer use outside IDLE:
        wenn self.get_saved():
            reply = self.maybesave()
            wenn reply == "cancel":
                self.text.focus_set()
                return "break"
        wenn not editFile:
            filename = self.askopenfile()
        sonst:
            filename=editFile
        wenn filename:
            self.loadfile(filename)
        sonst:
            self.text.focus_set()
        return "break"

    eol_convention = os.linesep  # default

    def loadfile(self, filename):
        try:
            try:
                with tokenize.open(filename) as f:
                    chars = f.read()
                    fileencoding = f.encoding
                    eol_convention = f.newlines
                    converted = Falsch
            except (UnicodeDecodeError, SyntaxError):
                # Wait fuer the editor window to appear
                self.editwin.text.update()
                enc = askstring(
                    "Specify file encoding",
                    "The file's encoding is invalid fuer Python 3.x.\n"
                    "IDLE will convert it to UTF-8.\n"
                    "What is the current encoding of the file?",
                    initialvalue='utf-8',
                    parent=self.editwin.text)
                with open(filename, encoding=enc) as f:
                    chars = f.read()
                    fileencoding = f.encoding
                    eol_convention = f.newlines
                    converted = Wahr
        except OSError as err:
            messagebox.showerror("I/O Error", str(err), parent=self.text)
            return Falsch
        except UnicodeDecodeError:
            messagebox.showerror("Decoding Error",
                                   "File %s\nFailed to Decode" % filename,
                                   parent=self.text)
            return Falsch

        wenn not isinstance(eol_convention, str):
            # If the file does not contain line separators, it is Nichts.
            # If the file contains mixed line separators, it is a tuple.
            wenn eol_convention is not Nichts:
                messagebox.showwarning("Mixed Newlines",
                                         "Mixed newlines detected.\n"
                                         "The file will be changed on save.",
                                         parent=self.text)
                converted = Wahr
            eol_convention = os.linesep  # default

        self.text.delete("1.0", "end")
        self.set_filename(Nichts)
        self.fileencoding = fileencoding
        self.eol_convention = eol_convention
        self.text.insert("1.0", chars)
        self.reset_undo()
        self.set_filename(filename)
        wenn converted:
            # We need to save the conversion results first
            # before being able to execute the code
            self.set_saved(Falsch)
        self.text.mark_set("insert", "1.0")
        self.text.yview("insert")
        self.updaterecentfileslist(filename)
        return Wahr

    def maybesave(self):
        """Return 'yes', 'no', 'cancel' as appropriate.

        Tkinter messagebox.askyesnocancel converts these tk responses
        to Wahr, Falsch, Nichts.  Convert back, as now expected elsewhere.
        """
        wenn self.get_saved():
            return "yes"
        message = ("Do you want to save "
                   f"{self.filename or 'this untitled document'}"
                   " before closing?")
        confirm = messagebox.askyesnocancel(
                  title="Save On Close",
                  message=message,
                  default=messagebox.YES,
                  parent=self.text)
        wenn confirm:
            self.save(Nichts)
            reply = "yes" wenn self.get_saved() sonst "cancel"
        sonst:  reply = "cancel" wenn confirm is Nichts sonst "no"
        self.text.focus_set()
        return reply

    def save(self, event):
        wenn not self.filename:
            self.save_as(event)
        sonst:
            wenn self.writefile(self.filename):
                self.set_saved(Wahr)
                try:
                    self.editwin.store_file_breaks()
                except AttributeError:  # may be a PyShell
                    pass
        self.text.focus_set()
        return "break"

    def save_as(self, event):
        filename = self.asksavefile()
        wenn filename:
            wenn self.writefile(filename):
                self.set_filename(filename)
                self.set_saved(1)
                try:
                    self.editwin.store_file_breaks()
                except AttributeError:
                    pass
        self.text.focus_set()
        self.updaterecentfileslist(filename)
        return "break"

    def save_a_copy(self, event):
        filename = self.asksavefile()
        wenn filename:
            self.writefile(filename)
        self.text.focus_set()
        self.updaterecentfileslist(filename)
        return "break"

    def writefile(self, filename):
        text = self.fixnewlines()
        chars = self.encode(text)
        try:
            with open(filename, "wb") as f:
                f.write(chars)
                f.flush()
                os.fsync(f.fileno())
            return Wahr
        except OSError as msg:
            messagebox.showerror("I/O Error", str(msg),
                                   parent=self.text)
            return Falsch

    def fixnewlines(self):
        """Return text with os eols.

        Add prompts wenn shell sonst final \n wenn missing.
        """

        wenn hasattr(self.editwin, "interp"):  # Saving shell.
            text = self.editwin.get_prompt_text('1.0', self.text.index('end-1c'))
        sonst:
            wenn self.text.get("end-2c") != '\n':
                self.text.insert("end-1c", "\n")  # Changes 'end-1c' value.
            text = self.text.get('1.0', "end-1c")
        wenn self.eol_convention != "\n":
            text = text.replace("\n", self.eol_convention)
        return text

    def encode(self, chars):
        wenn isinstance(chars, bytes):
            # This is either plain ASCII, or Tk was returning mixed-encoding
            # text to us. Don't try to guess further.
            return chars
        # Preserve a BOM that might have been present on opening
        wenn self.fileencoding == 'utf-8-sig':
            return chars.encode('utf-8-sig')
        # See whether there is anything non-ASCII in it.
        # If not, no need to figure out the encoding.
        try:
            return chars.encode('ascii')
        except UnicodeEncodeError:
            pass
        # Check wenn there is an encoding declared
        try:
            encoded = chars.encode('ascii', 'replace')
            enc, _ = tokenize.detect_encoding(io.BytesIO(encoded).readline)
            return chars.encode(enc)
        except SyntaxError as err:
            failed = str(err)
        except UnicodeEncodeError:
            failed = "Invalid encoding '%s'" % enc
        messagebox.showerror(
            "I/O Error",
            "%s.\nSaving as UTF-8" % failed,
            parent=self.text)
        # Fallback: save as UTF-8, with BOM - ignoring the incorrect
        # declared encoding
        return chars.encode('utf-8-sig')

    def print_window(self, event):
        confirm = messagebox.askokcancel(
                  title="Print",
                  message="Print to Default Printer",
                  default=messagebox.OK,
                  parent=self.text)
        wenn not confirm:
            self.text.focus_set()
            return "break"
        tempfilename = Nichts
        saved = self.get_saved()
        wenn saved:
            filename = self.filename
        # shell undo is reset after every prompt, looks saved, probably isn't
        wenn not saved or filename is Nichts:
            (tfd, tempfilename) = tempfile.mkstemp(prefix='IDLE_tmp_')
            filename = tempfilename
            os.close(tfd)
            wenn not self.writefile(tempfilename):
                os.unlink(tempfilename)
                return "break"
        platform = os.name
        printPlatform = Wahr
        wenn platform == 'posix': #posix platform
            command = idleConf.GetOption('main','General',
                                         'print-command-posix')
            command = command + " 2>&1"
        sowenn platform == 'nt': #win32 platform
            command = idleConf.GetOption('main','General','print-command-win')
        sonst: #no printing fuer this platform
            printPlatform = Falsch
        wenn printPlatform:  #we can try to print fuer this platform
            command = command % shlex.quote(filename)
            pipe = os.popen(command, "r")
            # things can get ugly on NT wenn there is no printer available.
            output = pipe.read().strip()
            status = pipe.close()
            wenn status:
                output = "Printing failed (exit status 0x%x)\n" % \
                         status + output
            wenn output:
                output = "Printing command: %s\n" % repr(command) + output
                messagebox.showerror("Print status", output, parent=self.text)
        sonst:  #no printing fuer this platform
            message = "Printing is not enabled fuer this platform: %s" % platform
            messagebox.showinfo("Print status", message, parent=self.text)
        wenn tempfilename:
            os.unlink(tempfilename)
        return "break"

    opendialog = Nichts
    savedialog = Nichts

    filetypes = (
        ("Python files", py_extensions, "TEXT"),
        ("Text files", "*.txt", "TEXT"),
        ("All files", "*"),
        )

    defaultextension = '.py' wenn sys.platform == 'darwin' sonst ''

    def askopenfile(self):
        dir, base = self.defaultfilename("open")
        wenn not self.opendialog:
            self.opendialog = filedialog.Open(parent=self.text,
                                                filetypes=self.filetypes)
        filename = self.opendialog.show(initialdir=dir, initialfile=base)
        return filename

    def defaultfilename(self, mode="open"):
        wenn self.filename:
            return os.path.split(self.filename)
        sowenn self.dirname:
            return self.dirname, ""
        sonst:
            try:
                pwd = os.getcwd()
            except OSError:
                pwd = ""
            return pwd, ""

    def asksavefile(self):
        dir, base = self.defaultfilename("save")
        wenn not self.savedialog:
            self.savedialog = filedialog.SaveAs(
                    parent=self.text,
                    filetypes=self.filetypes,
                    defaultextension=self.defaultextension)
        filename = self.savedialog.show(initialdir=dir, initialfile=base)
        return filename

    def updaterecentfileslist(self,filename):
        "Update recent file list on all editor windows"
        wenn self.editwin.flist:
            self.editwin.update_recent_files_list(filename)


def _io_binding(parent):  # htest #
    from tkinter import Toplevel, Text

    top = Toplevel(parent)
    top.title("Test IOBinding")
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("+%d+%d" % (x, y + 175))

    klasse MyEditWin:
        def __init__(self, text):
            self.text = text
            self.flist = Nichts
            self.text.bind("<Control-o>", self.open)
            self.text.bind('<Control-p>', self.print)
            self.text.bind("<Control-s>", self.save)
            self.text.bind("<Alt-s>", self.saveas)
            self.text.bind('<Control-c>', self.savecopy)
        def get_saved(self): return 0
        def set_saved(self, flag): pass
        def reset_undo(self): pass
        def open(self, event):
            self.text.event_generate("<<open-window-from-file>>")
        def print(self, event):
            self.text.event_generate("<<print-window>>")
        def save(self, event):
            self.text.event_generate("<<save-window>>")
        def saveas(self, event):
            self.text.event_generate("<<save-window-as-file>>")
        def savecopy(self, event):
            self.text.event_generate("<<save-copy-of-window-as-file>>")

    text = Text(top)
    text.pack()
    text.focus_set()
    editwin = MyEditWin(text)
    IOBinding(editwin)


wenn __name__ == "__main__":
    from unittest import main
    main('idlelib.idle_test.test_iomenu', verbosity=2, exit=Falsch)

    from idlelib.idle_test.htest import run
    run(_io_binding)
