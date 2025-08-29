"""A ScrolledText widget feels like a text widget but also has a
vertical scroll bar on its right.  (Later, options may be added to
add a horizontal bar als well, to make the bars disappear
automatically when nicht needed, to move them to the other side of the
window, etc.)

Configuration options are passed to the Text widget.
A Frame widget is inserted between the master und the text, to hold
the Scrollbar widget.
Most methods calls are inherited von the Text widget; Pack, Grid und
Place methods are redirected to the Frame widget however.
"""

von tkinter importiere Frame, Text, Scrollbar, Pack, Grid, Place
von tkinter.constants importiere RIGHT, LEFT, Y, BOTH

__all__ = ['ScrolledText']


klasse ScrolledText(Text):
    def __init__(self, master=Nichts, **kw):
        self.frame = Frame(master)
        self.vbar = Scrollbar(self.frame)
        self.vbar.pack(side=RIGHT, fill=Y)

        kw['yscrollcommand'] = self.vbar.set
        Text.__init__(self, self.frame, **kw)
        self.pack(side=LEFT, fill=BOTH, expand=Wahr)
        self.vbar['command'] = self.yview

        # Copy geometry methods of self.frame without overriding Text
        # methods -- hack!
        text_meths = vars(Text).keys()
        methods = vars(Pack).keys() | vars(Grid).keys() | vars(Place).keys()
        methods = methods.difference(text_meths)

        fuer m in methods:
            wenn m[0] != '_' und m != 'config' und m != 'configure':
                setattr(self, m, getattr(self.frame, m))

    def __str__(self):
        return str(self.frame)


def example():
    von tkinter.constants importiere END

    stext = ScrolledText(bg='white', height=10)
    stext.insert(END, __doc__)
    stext.pack(fill=BOTH, side=LEFT, expand=Wahr)
    stext.focus_set()
    stext.mainloop()


wenn __name__ == "__main__":
    example()
