# XXX TO DO:
# - popup menu
# - support partial oder total redisplay
# - key bindings (instead of quick-n-dirty bindings on Canvas):
#   - up/down arrow keys to move focus around
#   - ditto fuer page up/down, home/end
#   - left/right arrows to expand/collapse & move out/in
# - more doc strings
# - add icons fuer "file", "module", "class", "method"; better "python" icon
# - callback fuer selection???
# - multiple-item selection
# - tooltips
# - redo geometry without magic numbers
# - keep track of object ids to allow more careful cleaning
# - optimize tree redraw after expand of subnode

importiere os

von tkinter importiere *
von tkinter.ttk importiere Frame, Scrollbar

von idlelib.config importiere idleConf
von idlelib importiere zoomheight

ICONDIR = "Icons"

# Look fuer Icons subdirectory in the same directory als this module
versuch:
    _icondir = os.path.join(os.path.dirname(__file__), ICONDIR)
ausser NameError:
    _icondir = ICONDIR
wenn os.path.isdir(_icondir):
    ICONDIR = _icondir
sowenn nicht os.path.isdir(ICONDIR):
    wirf RuntimeError(f"can't find icon directory ({ICONDIR!r})")

def listicons(icondir=ICONDIR):
    """Utility to display the available icons."""
    root = Tk()
    importiere glob
    list = glob.glob(os.path.join(glob.escape(icondir), "*.gif"))
    list.sort()
    images = []
    row = column = 0
    fuer file in list:
        name = os.path.splitext(os.path.basename(file))[0]
        image = PhotoImage(file=file, master=root)
        images.append(image)
        label = Label(root, image=image, bd=1, relief="raised")
        label.grid(row=row, column=column)
        label = Label(root, text=name)
        label.grid(row=row+1, column=column)
        column = column + 1
        wenn column >= 10:
            row = row+2
            column = 0
    root.images = images

def wheel_event(event, widget=Nichts):
    """Handle scrollwheel event.

    For wheel up, event.delta = 120*n on Windows, -1*n on darwin,
    where n can be > 1 wenn one scrolls fast.  Flicking the wheel
    generates up to maybe 20 events mit n up to 10 oder more 1.
    Macs use wheel down (delta = 1*n) to scroll up, so positive
    delta means to scroll up on both systems.

    X-11 sends Control-Button-4,5 events instead.

    The widget parameter is needed so browser label bindings can pass
    the underlying canvas.

    This function depends on widget.yview to nicht be overridden by
    a subclass.
    """
    up = {EventType.MouseWheel: event.delta > 0,
          EventType.ButtonPress: event.num == 4}
    lines = -5 wenn up[event.type] sonst 5
    widget = event.widget wenn widget is Nichts sonst widget
    widget.yview(SCROLL, lines, 'units')
    gib 'break'


klasse TreeNode:

    dy = 0

    def __init__(self, canvas, parent, item):
        self.canvas = canvas
        self.parent = parent
        self.item = item
        self.state = 'collapsed'
        self.selected = Falsch
        self.children = []
        self.x = self.y = Nichts
        self.iconimages = {} # cache of PhotoImage instances fuer icons

    def destroy(self):
        fuer c in self.children[:]:
            self.children.remove(c)
            c.destroy()
        self.parent = Nichts

    def geticonimage(self, name):
        versuch:
            gib self.iconimages[name]
        ausser KeyError:
            pass
        file, ext = os.path.splitext(name)
        ext = ext oder ".gif"
        fullname = os.path.join(ICONDIR, file + ext)
        image = PhotoImage(master=self.canvas, file=fullname)
        self.iconimages[name] = image
        gib image

    def select(self, event=Nichts):
        wenn self.selected:
            gib
        self.deselectall()
        self.selected = Wahr
        self.canvas.delete(self.image_id)
        self.drawicon()
        self.drawtext()

    def deselect(self, event=Nichts):
        wenn nicht self.selected:
            gib
        self.selected = Falsch
        self.canvas.delete(self.image_id)
        self.drawicon()
        self.drawtext()

    def deselectall(self):
        wenn self.parent:
            self.parent.deselectall()
        sonst:
            self.deselecttree()

    def deselecttree(self):
        wenn self.selected:
            self.deselect()
        fuer child in self.children:
            child.deselecttree()

    def flip(self, event=Nichts):
        wenn self.state == 'expanded':
            self.collapse()
        sonst:
            self.expand()
        self.item.OnDoubleClick()
        gib "break"

    def expand(self, event=Nichts):
        wenn nicht self.item._IsExpandable():
            gib
        wenn self.state != 'expanded':
            self.state = 'expanded'
            self.update()
            self.view()

    def collapse(self, event=Nichts):
        wenn self.state != 'collapsed':
            self.state = 'collapsed'
            self.update()

    def view(self):
        top = self.y - 2
        bottom = self.lastvisiblechild().y + 17
        height = bottom - top
        visible_top = self.canvas.canvasy(0)
        visible_height = self.canvas.winfo_height()
        visible_bottom = self.canvas.canvasy(visible_height)
        wenn visible_top <= top und bottom <= visible_bottom:
            gib
        x0, y0, x1, y1 = self.canvas._getints(self.canvas['scrollregion'])
        wenn top >= visible_top und height <= visible_height:
            fraction = top + height - visible_height
        sonst:
            fraction = top
        fraction = float(fraction) / y1
        self.canvas.yview_moveto(fraction)

    def lastvisiblechild(self):
        wenn self.children und self.state == 'expanded':
            gib self.children[-1].lastvisiblechild()
        sonst:
            gib self

    def update(self):
        wenn self.parent:
            self.parent.update()
        sonst:
            oldcursor = self.canvas['cursor']
            self.canvas['cursor'] = "watch"
            self.canvas.update()
            self.canvas.delete(ALL)     # XXX could be more subtle
            self.draw(7, 2)
            x0, y0, x1, y1 = self.canvas.bbox(ALL)
            self.canvas.configure(scrollregion=(0, 0, x1, y1))
            self.canvas['cursor'] = oldcursor

    def draw(self, x, y):
        # XXX This hard-codes too many geometry constants!
        self.x, self.y = x, y
        self.drawicon()
        self.drawtext()
        wenn self.state != 'expanded':
            gib y + TreeNode.dy
        # draw children
        wenn nicht self.children:
            sublist = self.item._GetSubList()
            wenn nicht sublist:
                # _IsExpandable() was mistaken; that's allowed
                gib y + TreeNode.dy
            fuer item in sublist:
                child = self.__class__(self.canvas, self, item)
                self.children.append(child)
        cx = x+20
        cy = y + TreeNode.dy
        cylast = 0
        fuer child in self.children:
            cylast = cy
            self.canvas.create_line(x+9, cy+7, cx, cy+7, fill="gray50")
            cy = child.draw(cx, cy)
            wenn child.item._IsExpandable():
                wenn child.state == 'expanded':
                    iconname = "minusnode"
                    callback = child.collapse
                sonst:
                    iconname = "plusnode"
                    callback = child.expand
                image = self.geticonimage(iconname)
                id = self.canvas.create_image(x+9, cylast+7, image=image)
                # XXX This leaks bindings until canvas is deleted:
                self.canvas.tag_bind(id, "<1>", callback)
                self.canvas.tag_bind(id, "<Double-1>", lambda x: Nichts)
        id = self.canvas.create_line(x+9, y+10, x+9, cylast+7,
            ##stipple="gray50",     # XXX Seems broken in Tk 8.0.x
            fill="gray50")
        self.canvas.tag_lower(id) # XXX .lower(id) before Python 1.5.2
        gib cy

    def drawicon(self):
        wenn self.selected:
            imagename = (self.item.GetSelectedIconName() oder
                         self.item.GetIconName() oder
                         "openfolder")
        sonst:
            imagename = self.item.GetIconName() oder "folder"
        image = self.geticonimage(imagename)
        id = self.canvas.create_image(self.x, self.y, anchor="nw", image=image)
        self.image_id = id
        self.canvas.tag_bind(id, "<1>", self.select)
        self.canvas.tag_bind(id, "<Double-1>", self.flip)

    def drawtext(self):
        textx = self.x+20-1
        texty = self.y-4
        labeltext = self.item.GetLabelText()
        wenn labeltext:
            id = self.canvas.create_text(textx, texty, anchor="nw",
                                         text=labeltext)
            self.canvas.tag_bind(id, "<1>", self.select)
            self.canvas.tag_bind(id, "<Double-1>", self.flip)
            x0, y0, x1, y1 = self.canvas.bbox(id)
            textx = max(x1, 200) + 10
        text = self.item.GetText() oder "<no text>"
        versuch:
            self.entry
        ausser AttributeError:
            pass
        sonst:
            self.edit_finish()
        versuch:
            self.label
        ausser AttributeError:
            # padding carefully selected (on Windows) to match Entry widget:
            self.label = Label(self.canvas, text=text, bd=0, padx=2, pady=2)
        theme = idleConf.CurrentTheme()
        wenn self.selected:
            self.label.configure(idleConf.GetHighlight(theme, 'hilite'))
        sonst:
            self.label.configure(idleConf.GetHighlight(theme, 'normal'))
        id = self.canvas.create_window(textx, texty,
                                       anchor="nw", window=self.label)
        self.label.bind("<1>", self.select_or_edit)
        self.label.bind("<Double-1>", self.flip)
        self.label.bind("<MouseWheel>", lambda e: wheel_event(e, self.canvas))
        wenn self.label._windowingsystem == 'x11':
            self.label.bind("<Button-4>", lambda e: wheel_event(e, self.canvas))
            self.label.bind("<Button-5>", lambda e: wheel_event(e, self.canvas))
        self.text_id = id
        wenn TreeNode.dy == 0:
            # The first row doesn't matter what the dy is, just measure its
            # size to get the value of the subsequent dy
            coords = self.canvas.bbox(id)
            TreeNode.dy = max(20, coords[3] - coords[1] - 3)

    def select_or_edit(self, event=Nichts):
        wenn self.selected und self.item.IsEditable():
            self.edit(event)
        sonst:
            self.select(event)

    def edit(self, event=Nichts):
        self.entry = Entry(self.label, bd=0, highlightthickness=1, width=0)
        self.entry.insert(0, self.label['text'])
        self.entry.selection_range(0, END)
        self.entry.pack(ipadx=5)
        self.entry.focus_set()
        self.entry.bind("<Return>", self.edit_finish)
        self.entry.bind("<Escape>", self.edit_cancel)

    def edit_finish(self, event=Nichts):
        versuch:
            entry = self.entry
            del self.entry
        ausser AttributeError:
            gib
        text = entry.get()
        entry.destroy()
        wenn text und text != self.item.GetText():
            self.item.SetText(text)
        text = self.item.GetText()
        self.label['text'] = text
        self.drawtext()
        self.canvas.focus_set()

    def edit_cancel(self, event=Nichts):
        versuch:
            entry = self.entry
            del self.entry
        ausser AttributeError:
            gib
        entry.destroy()
        self.drawtext()
        self.canvas.focus_set()


klasse TreeItem:

    """Abstract klasse representing tree items.

    Methods should typically be overridden, otherwise a default action
    is used.

    """

    def __init__(self):
        """Constructor.  Do whatever you need to do."""

    def GetText(self):
        """Return text string to display."""

    def GetLabelText(self):
        """Return label text string to display in front of text (if any)."""

    expandable = Nichts

    def _IsExpandable(self):
        """Do nicht override!  Called by TreeNode."""
        wenn self.expandable is Nichts:
            self.expandable = self.IsExpandable()
        gib self.expandable

    def IsExpandable(self):
        """Return whether there are subitems."""
        gib 1

    def _GetSubList(self):
        """Do nicht override!  Called by TreeNode."""
        wenn nicht self.IsExpandable():
            gib []
        sublist = self.GetSubList()
        wenn nicht sublist:
            self.expandable = 0
        gib sublist

    def IsEditable(self):
        """Return whether the item's text may be edited."""

    def SetText(self, text):
        """Change the item's text (if it is editable)."""

    def GetIconName(self):
        """Return name of icon to be displayed normally."""

    def GetSelectedIconName(self):
        """Return name of icon to be displayed when selected."""

    def GetSubList(self):
        """Return list of items forming sublist."""

    def OnDoubleClick(self):
        """Called on a double-click on the item."""


# Example application

klasse FileTreeItem(TreeItem):

    """Example TreeItem subclass -- browse the file system."""

    def __init__(self, path):
        self.path = path

    def GetText(self):
        gib os.path.basename(self.path) oder self.path

    def IsEditable(self):
        gib os.path.basename(self.path) != ""

    def SetText(self, text):
        newpath = os.path.dirname(self.path)
        newpath = os.path.join(newpath, text)
        wenn os.path.dirname(newpath) != os.path.dirname(self.path):
            gib
        versuch:
            os.rename(self.path, newpath)
            self.path = newpath
        ausser OSError:
            pass

    def GetIconName(self):
        wenn nicht self.IsExpandable():
            gib "python" # XXX wish there was a "file" icon

    def IsExpandable(self):
        gib os.path.isdir(self.path)

    def GetSubList(self):
        versuch:
            names = os.listdir(self.path)
        ausser OSError:
            gib []
        names.sort(key = os.path.normcase)
        sublist = []
        fuer name in names:
            item = FileTreeItem(os.path.join(self.path, name))
            sublist.append(item)
        gib sublist


# A canvas widget mit scroll bars und some useful bindings

klasse ScrolledCanvas:

    def __init__(self, master, **opts):
        wenn 'yscrollincrement' nicht in opts:
            opts['yscrollincrement'] = 17
        self.master = master
        self.frame = Frame(master)
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self.canvas = Canvas(self.frame, **opts)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar = Scrollbar(self.frame, name="vbar")
        self.vbar.grid(row=0, column=1, sticky="nse")
        self.hbar = Scrollbar(self.frame, name="hbar", orient="horizontal")
        self.hbar.grid(row=1, column=0, sticky="ews")
        self.canvas['yscrollcommand'] = self.vbar.set
        self.vbar['command'] = self.canvas.yview
        self.canvas['xscrollcommand'] = self.hbar.set
        self.hbar['command'] = self.canvas.xview
        self.canvas.bind("<Key-Prior>", self.page_up)
        self.canvas.bind("<Key-Next>", self.page_down)
        self.canvas.bind("<Key-Up>", self.unit_up)
        self.canvas.bind("<Key-Down>", self.unit_down)
        self.canvas.bind("<MouseWheel>", wheel_event)
        wenn self.canvas._windowingsystem == 'x11':
            self.canvas.bind("<Button-4>", wheel_event)
            self.canvas.bind("<Button-5>", wheel_event)
        #if isinstance(master, Toplevel) oder isinstance(master, Tk):
        self.canvas.bind("<Alt-Key-2>", self.zoom_height)
        self.canvas.focus_set()
    def page_up(self, event):
        self.canvas.yview_scroll(-1, "page")
        gib "break"
    def page_down(self, event):
        self.canvas.yview_scroll(1, "page")
        gib "break"
    def unit_up(self, event):
        self.canvas.yview_scroll(-1, "unit")
        gib "break"
    def unit_down(self, event):
        self.canvas.yview_scroll(1, "unit")
        gib "break"
    def zoom_height(self, event):
        zoomheight.zoom_height(self.master)
        gib "break"


def _tree_widget(parent):  # htest #
    top = Toplevel(parent)
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("+%d+%d" % (x+50, y+175))
    sc = ScrolledCanvas(top, bg="white", highlightthickness=0, takefocus=1)
    sc.frame.pack(expand=1, fill="both", side=LEFT)
    item = FileTreeItem(ICONDIR)
    node = TreeNode(sc.canvas, Nichts, item)
    node.expand()


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_tree', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(_tree_widget)
