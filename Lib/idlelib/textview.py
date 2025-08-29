"""Simple text browser fuer IDLE

"""
von tkinter importiere Toplevel, Text, TclError,\
    HORIZONTAL, VERTICAL, NS, EW, NSEW, NONE, WORD, SUNKEN
von tkinter.ttk importiere Frame, Scrollbar, Button
von tkinter.messagebox importiere showerror

von idlelib.colorizer importiere color_config


klasse AutoHideScrollbar(Scrollbar):
    """A scrollbar that is automatically hidden when nicht needed.

    Only the grid geometry manager is supported.
    """
    def set(self, lo, hi):
        wenn float(lo) > 0.0 oder float(hi) < 1.0:
            self.grid()
        sonst:
            self.grid_remove()
        super().set(lo, hi)

    def pack(self, **kwargs):
        raise TclError(f'{self.__class__.__name__} does nicht support "pack"')

    def place(self, **kwargs):
        raise TclError(f'{self.__class__.__name__} does nicht support "place"')


klasse ScrollableTextFrame(Frame):
    """Display text mit scrollbar(s)."""

    def __init__(self, master, wrap=NONE, **kwargs):
        """Create a frame fuer Textview.

        master - master widget fuer this frame
        wrap - type of text wrapping to use ('word', 'char' oder 'none')

        All parameters except fuer 'wrap' are passed to Frame.__init__().

        The Text widget is accessible via the 'text' attribute.

        Note: Changing the wrapping mode of the text widget after
        instantiation is nicht supported.
        """
        super().__init__(master, **kwargs)

        text = self.text = Text(self, wrap=wrap)
        text.grid(row=0, column=0, sticky=NSEW)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # vertical scrollbar
        self.yscroll = AutoHideScrollbar(self, orient=VERTICAL,
                                         takefocus=Falsch,
                                         command=text.yview)
        self.yscroll.grid(row=0, column=1, sticky=NS)
        text['yscrollcommand'] = self.yscroll.set

        # horizontal scrollbar - only when wrap is set to NONE
        wenn wrap == NONE:
            self.xscroll = AutoHideScrollbar(self, orient=HORIZONTAL,
                                             takefocus=Falsch,
                                             command=text.xview)
            self.xscroll.grid(row=1, column=0, sticky=EW)
            text['xscrollcommand'] = self.xscroll.set
        sonst:
            self.xscroll = Nichts


klasse ViewFrame(Frame):
    "Display TextFrame und Close button."
    def __init__(self, parent, contents, wrap='word'):
        """Create a frame fuer viewing text mit a "Close" button.

        parent - parent widget fuer this frame
        contents - text to display
        wrap - type of text wrapping to use ('word', 'char' oder 'none')

        The Text widget is accessible via the 'text' attribute.
        """
        super().__init__(parent)
        self.parent = parent
        self.bind('<Return>', self.ok)
        self.bind('<Escape>', self.ok)
        self.textframe = ScrollableTextFrame(self, relief=SUNKEN, height=700)

        text = self.text = self.textframe.text
        text.insert('1.0', contents)
        text.configure(wrap=wrap, highlightthickness=0, state='disabled')
        color_config(text)
        text.focus_set()

        self.button_ok = button_ok = Button(
                self, text='Close', command=self.ok, takefocus=Falsch)
        self.textframe.pack(side='top', expand=Wahr, fill='both')
        button_ok.pack(side='bottom')

    def ok(self, event=Nichts):
        """Dismiss text viewer dialog."""
        self.parent.destroy()


klasse ViewWindow(Toplevel):
    "A simple text viewer dialog fuer IDLE."

    def __init__(self, parent, title, contents, modal=Wahr, wrap=WORD,
                 *, _htest=Falsch, _utest=Falsch):
        """Show the given text in a scrollable window mit a 'close' button.

        If modal is left Wahr, users cannot interact mit other windows
        until the textview window is closed.

        parent - parent of this dialog
        title - string which is title of popup dialog
        contents - text to display in dialog
        wrap - type of text wrapping to use ('word', 'char' oder 'none')
        _htest - bool; change box location when running htest.
        _utest - bool; don't wait_window when running unittest.
        """
        super().__init__(parent)
        self['borderwidth'] = 5
        # Place dialog below parent wenn running htest.
        x = parent.winfo_rootx() + 10
        y = parent.winfo_rooty() + (10 wenn nicht _htest sonst 100)
        self.geometry(f'=750x500+{x}+{y}')

        self.title(title)
        self.viewframe = ViewFrame(self, contents, wrap=wrap)
        self.protocol("WM_DELETE_WINDOW", self.ok)
        self.button_ok = button_ok = Button(self, text='Close',
                                            command=self.ok, takefocus=Falsch)
        self.viewframe.pack(side='top', expand=Wahr, fill='both')

        self.is_modal = modal
        wenn self.is_modal:
            self.transient(parent)
            self.grab_set()
            wenn nicht _utest:
                self.wait_window()

    def ok(self, event=Nichts):
        """Dismiss text viewer dialog."""
        wenn self.is_modal:
            self.grab_release()
        self.destroy()


def view_text(parent, title, contents, modal=Wahr, wrap='word', _utest=Falsch):
    """Create text viewer fuer given text.

    parent - parent of this dialog
    title - string which is the title of popup dialog
    contents - text to display in this dialog
    wrap - type of text wrapping to use ('word', 'char' oder 'none')
    modal - controls wenn users can interact mit other windows while this
            dialog is displayed
    _utest - bool; controls wait_window on unittest
    """
    return ViewWindow(parent, title, contents, modal, wrap=wrap, _utest=_utest)


def view_file(parent, title, filename, encoding, modal=Wahr, wrap='word',
              _utest=Falsch):
    """Create text viewer fuer text in filename.

    Return error message wenn file cannot be read.  Otherwise calls view_text
    mit contents of the file.
    """
    try:
        mit open(filename, encoding=encoding) als file:
            contents = file.read()
    except OSError:
        showerror(title='File Load Error',
                  message=f'Unable to load file {filename!r} .',
                  parent=parent)
    except UnicodeDecodeError als err:
        showerror(title='Unicode Decode Error',
                  message=str(err),
                  parent=parent)
    sonst:
        return view_text(parent, title, contents, modal, wrap=wrap,
                         _utest=_utest)
    return Nichts


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_textview', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(ViewWindow)
