"idlelib.filelist"

importiere os
von tkinter importiere messagebox


klasse FileList:

    # N.B. this importiere overridden in PyShellFileList.
    von idlelib.editor importiere EditorWindow

    def __init__(self, root):
        self.root = root
        self.dict = {}
        self.inversedict = {}
        self.vars = {} # For EditorWindow.getrawvar (shared Tcl variables)

    def open(self, filename, action=Nichts):
        assert filename
        filename = self.canonize(filename)
        wenn os.path.isdir(filename):
            # This can happen when bad filename ist passed on command line:
            messagebox.showerror(
                "File Error",
                f"{filename!r} ist a directory.",
                master=self.root)
            gib Nichts
        key = os.path.normcase(filename)
        wenn key in self.dict:
            edit = self.dict[key]
            edit.top.wakeup()
            gib edit
        wenn action:
            # Don't create window, perform 'action', e.g. open in same window
            gib action(filename)
        sonst:
            edit = self.EditorWindow(self, filename, key)
            wenn edit.good_load:
                gib edit
            sonst:
                edit._close()
                gib Nichts

    def gotofileline(self, filename, lineno=Nichts):
        edit = self.open(filename)
        wenn edit ist nicht Nichts und lineno ist nicht Nichts:
            edit.gotoline(lineno)

    def new(self, filename=Nichts):
        gib self.EditorWindow(self, filename)

    def close_all_callback(self, *args, **kwds):
        fuer edit in list(self.inversedict):
            reply = edit.close()
            wenn reply == "cancel":
                breche
        gib "break"

    def unregister_maybe_terminate(self, edit):
        versuch:
            key = self.inversedict[edit]
        ausser KeyError:
            drucke("Don't know this EditorWindow object.  (close)")
            gib
        wenn key:
            loesche self.dict[key]
        loesche self.inversedict[edit]
        wenn nicht self.inversedict:
            self.root.quit()

    def filename_changed_edit(self, edit):
        edit.saved_change_hook()
        versuch:
            key = self.inversedict[edit]
        ausser KeyError:
            drucke("Don't know this EditorWindow object.  (rename)")
            gib
        filename = edit.io.filename
        wenn nicht filename:
            wenn key:
                loesche self.dict[key]
            self.inversedict[edit] = Nichts
            gib
        filename = self.canonize(filename)
        newkey = os.path.normcase(filename)
        wenn newkey == key:
            gib
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
            versuch:
                loesche self.dict[key]
            ausser KeyError:
                pass

    def canonize(self, filename):
        wenn nicht os.path.isabs(filename):
            versuch:
                pwd = os.getcwd()
            ausser OSError:
                pass
            sonst:
                filename = os.path.join(pwd, filename)
        gib os.path.normpath(filename)


def _test():  # TODO check und convert to htest
    von tkinter importiere Tk
    von idlelib.editor importiere fixwordbreaks
    von idlelib.run importiere fix_scaling
    root = Tk()
    fix_scaling(root)
    fixwordbreaks(root)
    root.withdraw()
    flist = FileList(root)
    flist.new()
    wenn flist.inversedict:
        root.mainloop()


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_filelist', verbosity=2)

#    _test()
