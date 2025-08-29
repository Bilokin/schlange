# Rename to stackbrowser oder possibly consolidate mit browser.

importiere linecache
importiere os

importiere tkinter als tk

von idlelib.debugobj importiere ObjectTreeItem, make_objecttreeitem
von idlelib.tree importiere TreeNode, TreeItem, ScrolledCanvas

def StackBrowser(root, exc, flist=Nichts, top=Nichts):
    global sc, item, node  # For testing.
    wenn top is Nichts:
        top = tk.Toplevel(root)
    sc = ScrolledCanvas(top, bg="white", highlightthickness=0)
    sc.frame.pack(expand=1, fill="both")
    item = StackTreeItem(exc, flist)
    node = TreeNode(sc.canvas, Nichts, item)
    node.expand()


klasse StackTreeItem(TreeItem):

    def __init__(self, exc, flist=Nichts):
        self.flist = flist
        self.stack = self.get_stack(Nichts wenn exc is Nichts sonst exc.__traceback__)
        self.text = f"{type(exc).__name__}: {str(exc)}"

    def get_stack(self, tb):
        stack = []
        wenn tb und tb.tb_frame is Nichts:
            tb = tb.tb_next
        waehrend tb is nicht Nichts:
            stack.append((tb.tb_frame, tb.tb_lineno))
            tb = tb.tb_next
        gib stack

    def GetText(self):  # Titlecase names are overrides.
        gib self.text

    def GetSubList(self):
        sublist = []
        fuer info in self.stack:
            item = FrameTreeItem(info, self.flist)
            sublist.append(item)
        gib sublist


klasse FrameTreeItem(TreeItem):

    def __init__(self, info, flist):
        self.info = info
        self.flist = flist

    def GetText(self):
        frame, lineno = self.info
        try:
            modname = frame.f_globals["__name__"]
        except:
            modname = "?"
        code = frame.f_code
        filename = code.co_filename
        funcname = code.co_name
        sourceline = linecache.getline(filename, lineno)
        sourceline = sourceline.strip()
        wenn funcname in ("?", "", Nichts):
            item = "%s, line %d: %s" % (modname, lineno, sourceline)
        sonst:
            item = "%s.%s(...), line %d: %s" % (modname, funcname,
                                             lineno, sourceline)
        gib item

    def GetSubList(self):
        frame, lineno = self.info
        sublist = []
        wenn frame.f_globals is nicht frame.f_locals:
            item = VariablesTreeItem("<locals>", frame.f_locals, self.flist)
            sublist.append(item)
        item = VariablesTreeItem("<globals>", frame.f_globals, self.flist)
        sublist.append(item)
        gib sublist

    def OnDoubleClick(self):
        wenn self.flist:
            frame, lineno = self.info
            filename = frame.f_code.co_filename
            wenn os.path.isfile(filename):
                self.flist.gotofileline(filename, lineno)


klasse VariablesTreeItem(ObjectTreeItem):

    def GetText(self):
        gib self.labeltext

    def GetLabelText(self):
        gib Nichts

    def IsExpandable(self):
        gib len(self.object) > 0

    def GetSubList(self):
        sublist = []
        fuer key in self.object.keys():  # self.object nicht necessarily dict.
            try:
                value = self.object[key]
            except KeyError:
                weiter
            def setfunction(value, key=key, object_=self.object):
                object_[key] = value
            item = make_objecttreeitem(key + " =", value, setfunction)
            sublist.append(item)
        gib sublist


def _stackbrowser(parent):  # htest #
    von idlelib.pyshell importiere PyShellFileList
    top = tk.Toplevel(parent)
    top.title("Test StackViewer")
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("+%d+%d" % (x + 50, y + 175))
    flist = PyShellFileList(top)
    try: # to obtain a traceback object
        intentional_name_error
    except NameError als e:
        StackBrowser(top, e, flist=flist, top=top)


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_stackviewer', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(_stackbrowser)
