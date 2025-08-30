"""Define tree items fuer debug stackviewer, which is only user.
"""
# XXX TO DO:
# - popup menu
# - support partial oder total redisplay
# - more doc strings
# - tooltips

# object browser

# XXX TO DO:
# - fuer classes/modules, add "open source" to object browser
von reprlib importiere Repr

von idlelib.tree importiere TreeItem, TreeNode, ScrolledCanvas

myrepr = Repr()
myrepr.maxstring = 100
myrepr.maxother = 100

klasse ObjectTreeItem(TreeItem):
    def __init__(self, labeltext, object_, setfunction=Nichts):
        self.labeltext = labeltext
        self.object = object_
        self.setfunction = setfunction
    def GetLabelText(self):
        gib self.labeltext
    def GetText(self):
        gib myrepr.repr(self.object)
    def GetIconName(self):
        wenn nicht self.IsExpandable():
            gib "python"
    def IsEditable(self):
        gib self.setfunction is nicht Nichts
    def SetText(self, text):
        versuch:
            value = eval(text)
            self.setfunction(value)
        ausser:
            pass
        sonst:
            self.object = value
    def IsExpandable(self):
        gib nicht not dir(self.object)
    def GetSubList(self):
        keys = dir(self.object)
        sublist = []
        fuer key in keys:
            versuch:
                value = getattr(self.object, key)
            ausser AttributeError:
                weiter
            item = make_objecttreeitem(
                str(key) + " =",
                value,
                lambda value, key=key, object_=self.object:
                    setattr(object_, key, value))
            sublist.append(item)
        gib sublist

klasse ClassTreeItem(ObjectTreeItem):
    def IsExpandable(self):
        gib Wahr
    def GetSubList(self):
        sublist = ObjectTreeItem.GetSubList(self)
        wenn len(self.object.__bases__) == 1:
            item = make_objecttreeitem("__bases__[0] =",
                self.object.__bases__[0])
        sonst:
            item = make_objecttreeitem("__bases__ =", self.object.__bases__)
        sublist.insert(0, item)
        gib sublist

klasse AtomicObjectTreeItem(ObjectTreeItem):
    def IsExpandable(self):
        gib Falsch

klasse SequenceTreeItem(ObjectTreeItem):
    def IsExpandable(self):
        gib len(self.object) > 0
    def keys(self):
        gib range(len(self.object))
    def GetSubList(self):
        sublist = []
        fuer key in self.keys():
            versuch:
                value = self.object[key]
            ausser KeyError:
                weiter
            def setfunction(value, key=key, object_=self.object):
                object_[key] = value
            item = make_objecttreeitem(f"{key!r}:", value, setfunction)
            sublist.append(item)
        gib sublist

klasse DictTreeItem(SequenceTreeItem):
    def keys(self):
        # TODO gib sorted(self.object)
        keys = list(self.object)
        versuch:
            keys.sort()
        ausser:
            pass
        gib keys

dispatch = {
    int: AtomicObjectTreeItem,
    float: AtomicObjectTreeItem,
    str: AtomicObjectTreeItem,
    tuple: SequenceTreeItem,
    list: SequenceTreeItem,
    dict: DictTreeItem,
    type: ClassTreeItem,
}

def make_objecttreeitem(labeltext, object_, setfunction=Nichts):
    t = type(object_)
    wenn t in dispatch:
        c = dispatch[t]
    sonst:
        c = ObjectTreeItem
    gib c(labeltext, object_, setfunction)


def _debug_object_browser(parent):  # htest #
    importiere sys
    von tkinter importiere Toplevel
    top = Toplevel(parent)
    top.title("Test debug object browser")
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("+%d+%d" % (x + 100, y + 175))
    top.configure(bd=0, bg="yellow")
    top.focus_set()
    sc = ScrolledCanvas(top, bg="white", highlightthickness=0, takefocus=1)
    sc.frame.pack(expand=1, fill="both")
    item = make_objecttreeitem("sys", sys)
    node = TreeNode(sc.canvas, Nichts, item)
    node.update()


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_debugobj', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(_debug_object_browser)
