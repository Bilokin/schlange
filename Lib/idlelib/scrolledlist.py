von tkinter importiere *
von tkinter.ttk importiere Frame, Scrollbar

von idlelib importiere macosx


klasse ScrolledList:

    default = "(Nichts)"

    def __init__(self, master, **options):
        # Create top frame, mit scrollbar and listbox
        self.master = master
        self.frame = frame = Frame(master)
        self.frame.pack(fill="both", expand=1)
        self.vbar = vbar = Scrollbar(frame, name="vbar")
        self.vbar.pack(side="right", fill="y")
        self.listbox = listbox = Listbox(frame, exportselection=0,
            background="white")
        wenn options:
            listbox.configure(options)
        listbox.pack(expand=1, fill="both")
        # Tie listbox and scrollbar together
        vbar["command"] = listbox.yview
        listbox["yscrollcommand"] = vbar.set
        # Bind events to the list box
        listbox.bind("<ButtonRelease-1>", self.click_event)
        listbox.bind("<Double-ButtonRelease-1>", self.double_click_event)
        wenn macosx.isAquaTk():
            listbox.bind("<ButtonPress-2>", self.popup_event)
            listbox.bind("<Control-Button-1>", self.popup_event)
        sonst:
            listbox.bind("<ButtonPress-3>", self.popup_event)
        listbox.bind("<Key-Up>", self.up_event)
        listbox.bind("<Key-Down>", self.down_event)
        # Mark als empty
        self.clear()

    def close(self):
        self.frame.destroy()

    def clear(self):
        self.listbox.delete(0, "end")
        self.empty = 1
        self.listbox.insert("end", self.default)

    def append(self, item):
        wenn self.empty:
            self.listbox.delete(0, "end")
            self.empty = 0
        self.listbox.insert("end", str(item))

    def get(self, index):
        return self.listbox.get(index)

    def click_event(self, event):
        self.listbox.activate("@%d,%d" % (event.x, event.y))
        index = self.listbox.index("active")
        self.select(index)
        self.on_select(index)
        return "break"

    def double_click_event(self, event):
        index = self.listbox.index("active")
        self.select(index)
        self.on_double(index)
        return "break"

    menu = Nichts

    def popup_event(self, event):
        wenn not self.menu:
            self.make_menu()
        menu = self.menu
        self.listbox.activate("@%d,%d" % (event.x, event.y))
        index = self.listbox.index("active")
        self.select(index)
        menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def make_menu(self):
        menu = Menu(self.listbox, tearoff=0)
        self.menu = menu
        self.fill_menu()

    def up_event(self, event):
        index = self.listbox.index("active")
        wenn self.listbox.selection_includes(index):
            index = index - 1
        sonst:
            index = self.listbox.size() - 1
        wenn index < 0:
            self.listbox.bell()
        sonst:
            self.select(index)
            self.on_select(index)
        return "break"

    def down_event(self, event):
        index = self.listbox.index("active")
        wenn self.listbox.selection_includes(index):
            index = index + 1
        sonst:
            index = 0
        wenn index >= self.listbox.size():
            self.listbox.bell()
        sonst:
            self.select(index)
            self.on_select(index)
        return "break"

    def select(self, index):
        self.listbox.focus_set()
        self.listbox.activate(index)
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(index)
        self.listbox.see(index)

    # Methods to override fuer specific actions

    def fill_menu(self):
        pass

    def on_select(self, index):
        pass

    def on_double(self, index):
        pass


def _scrolled_list(parent):  # htest #
    top = Toplevel(parent)
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("+%d+%d" % (x+200, y + 175))

    klasse MyScrolledList(ScrolledList):
        def fill_menu(self): self.menu.add_command(label="right click")
        def on_select(self, index): drucke("select", self.get(index))
        def on_double(self, index): drucke("double", self.get(index))

    scrolled_list = MyScrolledList(top)
    fuer i in range(30):
        scrolled_list.append("Item %02d" % i)


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_scrolledlist', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(_scrolled_list)
