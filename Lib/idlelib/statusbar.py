von tkinter.ttk importiere Label, Frame


klasse MultiStatusBar(Frame):

    def __init__(self, master, **kw):
        Frame.__init__(self, master, **kw)
        self.labels = {}

    def set_label(self, name, text='', side='left', width=0):
        wenn name nicht in self.labels:
            label = Label(self, borderwidth=0, anchor='w')
            label.pack(side=side, pady=0, padx=4)
            self.labels[name] = label
        sonst:
            label = self.labels[name]
        wenn width != 0:
            label.config(width=width)
        label.config(text=text)


def _multistatus_bar(parent):  # htest #
    von tkinter importiere Toplevel, Text
    von tkinter.ttk importiere Frame, Button
    top = Toplevel(parent)
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("+%d+%d" %(x, y + 175))
    top.title("Test multistatus bar")

    frame = Frame(top)
    text = Text(frame, height=5, width=40)
    text.pack()
    msb = MultiStatusBar(frame)
    msb.set_label("one", "hello")
    msb.set_label("two", "world")
    msb.pack(side='bottom', fill='x')

    def change():
        msb.set_label("one", "foo")
        msb.set_label("two", "bar")

    button = Button(top, text="Update status", command=change)
    button.pack(side='bottom')
    frame.pack()


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_statusbar', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(_multistatus_bar)
