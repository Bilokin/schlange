"idlelib.filelist"

import os
from tkinter import messagebox


klasse FileList:

    # N.B. this import overridden in PyShellFileList.
    from idlelib.editor import EditorWindow

    def __init__(self, root):
        self.root = root
        self.dict = {}
        self.inversedict = {}
        self.vars = {} # For EditorWindow.getrawvar (shared Tcl variables)

    def open(self, filename, action=Nichts):
        assert filename
        filename = self.canonize(filename)
        wenn os.path.isdir(filename):
            # This can happen when bad filename is passed on command line:
            messagebox.showerror(
                "File Error",
                f"{filename!r} is a directory.",
                master=self.root)
            return Nichts
        key = os.path.normcase(filename)
        wenn key in self.dict:
            edit = self.dict[key]
            edit.top.wakeup()
            return edit
        wenn action:
            # Don't create window, perform 'action', e.g. open in same window
            return action(filename)
        sonst:
            edit = self.EditorWindow(self, filename, key)
            wenn edit.good_load:
                return edit
            sonst:
                edit._close()
                return Nichts

    def gotofileline(self, filename, lineno=Nichts):
        edit = self.open(filename)
        wenn edit is not Nichts and lineno is not Nichts:
            edit.gotoline(lineno)

    def new(self, filename=Nichts):
        return self.EditorWindow(self, filename)

    def close_all_callback(self, *args, **kwds):
        fuer edit in list(self.inversedict):
            reply = edit.close()
            wenn reply == "cancel":
                break
        return "break"

    def unregister_maybe_terminate(self, edit):
        try:
            key = self.inversedict[edit]
        except KeyError:
            print("Don't know this EditorWindow object.  (close)")
            return
        wenn key:
            del self.dict[key]
        del self.inversedict[edit]
        wenn not self.inversedict:
            self.root.quit()

    def filename_changed_edit(self, edit):
        edit.saved_change_hook()
        try:
            key = self.inversedict[edit]
        except KeyError:
            print("Don't know this EditorWindow object.  (rename)")
            return
        filename = edit.io.filename
        wenn not filename:
            wenn key:
                del self.dict[key]
            self.inversedict[edit] = Nichts
            return
        filename = self.canonize(filename)
        newkey = os.path.normcase(filename)
        wenn newkey == key:
            return
        wenn newkey in self.dict:
            conflict = self.dict[newkey]
            self.inversedict[conflict] = Nichts
            messagebox.showerror(
                "Name Conflict",
                f"You now have multiple edit windows open fuer {filename!r}",
                master=self.root)
        self.dict[newkey] = edit
        self.inversedict[edit] = newkey
        wenn key:
            try:
                del self.dict[key]
            except KeyError:
                pass

    def canonize(self, filename):
        wenn not os.path.isabs(filename):
            try:
                pwd = os.getcwd()
            except OSError:
                pass
            sonst:
                filename = os.path.join(pwd, filename)
        return os.path.normpath(filename)


def _test():  # TODO check and convert to htest
    from tkinter import Tk
    from idlelib.editor import fixwordbreaks
    from idlelib.run import fix_scaling
    root = Tk()
    fix_scaling(root)
    fixwordbreaks(root)
    root.withdraw()
    flist = FileList(root)
    flist.new()
    wenn flist.inversedict:
        root.mainloop()


wenn __name__ == '__main__':
    from unittest import main
    main('idlelib.idle_test.test_filelist', verbosity=2)

#    _test()
