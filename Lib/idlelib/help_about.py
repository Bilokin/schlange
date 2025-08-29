"""About Dialog fuer IDLE

"""
importiere os
importiere sys
importiere webbrowser
von platform importiere python_version, architecture

von tkinter importiere Toplevel, Frame, Label, Button, PhotoImage
von tkinter importiere SUNKEN, TOP, BOTTOM, LEFT, X, BOTH, W, EW, NSEW, E

von idlelib importiere textview

pyver = python_version()

wenn sys.platform == 'darwin':
    bits = '64' wenn sys.maxsize > 2**32 sonst '32'
sonst:
    bits = architecture()[0][:2]


klasse AboutDialog(Toplevel):
    """Modal about dialog fuer idle

    """
    def __init__(self, parent, title=Nichts, *, _htest=Falsch, _utest=Falsch):
        """Create popup, do not return until tk widget destroyed.

        parent - parent of this dialog
        title - string which is title of popup dialog
        _htest - bool, change box location when running htest
        _utest - bool, don't wait_window when running unittest
        """
        Toplevel.__init__(self, parent)
        self.configure(borderwidth=5)
        # place dialog below parent wenn running htest
        self.geometry("+%d+%d" % (
                        parent.winfo_rootx()+30,
                        parent.winfo_rooty()+(30 wenn not _htest sonst 100)))
        self.bg = "#bbbbbb"
        self.fg = "#000000"
        self.create_widgets()
        self.resizable(height=Falsch, width=Falsch)
        self.title(title or
                   f'About IDLE {pyver} ({bits} bit)')
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.ok)
        self.parent = parent
        self.button_ok.focus_set()
        self.bind('<Return>', self.ok)  # dismiss dialog
        self.bind('<Escape>', self.ok)  # dismiss dialog
        self._current_textview = Nichts
        self._utest = _utest

        wenn not _utest:
            self.deiconify()
            self.wait_window()

    def create_widgets(self):
        frame = Frame(self, borderwidth=2, relief=SUNKEN)
        frame_buttons = Frame(self)
        frame_buttons.pack(side=BOTTOM, fill=X)
        frame.pack(side=TOP, expand=Wahr, fill=BOTH)
        self.button_ok = Button(frame_buttons, text='Close',
                                command=self.ok)
        self.button_ok.pack(padx=5, pady=5)

        frame_background = Frame(frame, bg=self.bg)
        frame_background.pack(expand=Wahr, fill=BOTH)

        header = Label(frame_background, text='IDLE', fg=self.fg,
                       bg=self.bg, font=('courier', 24, 'bold'))
        header.grid(row=0, column=0, sticky=E, padx=10, pady=10)

        tkpatch = self._root().getvar('tk_patchLevel')
        ext = '.png' wenn tkpatch >= '8.6' sonst '.gif'
        icon = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'Icons', f'idle_48{ext}')
        self.icon_image = PhotoImage(master=self._root(), file=icon)
        logo = Label(frame_background, image=self.icon_image, bg=self.bg)
        logo.grid(row=0, column=0, sticky=W, rowspan=2, padx=10, pady=10)

        byline_text = "Python's Integrated Development\nand Learning Environment" + 5*'\n'
        byline = Label(frame_background, text=byline_text, justify=LEFT,
                       fg=self.fg, bg=self.bg)
        byline.grid(row=2, column=0, sticky=W, columnspan=3, padx=10, pady=5)

        forums_url = "https://discuss.python.org"
        forums = Button(frame_background, text='Python (and IDLE) Discussion', width=35,
                                 highlightbackground=self.bg,
                                 command=lambda: webbrowser.open(forums_url))
        forums.grid(row=6, column=0, sticky=W, padx=10, pady=10)


        docs_url = ("https://docs.python.org/%d.%d/library/idle.html" %
                    sys.version_info[:2])
        docs = Button(frame_background, text='IDLE Documentation', width=35,
                                 highlightbackground=self.bg,
                                 command=lambda: webbrowser.open(docs_url))
        docs.grid(row=7, column=0, columnspan=2, sticky=W, padx=10, pady=10)


        Frame(frame_background, borderwidth=1, relief=SUNKEN,
              height=2, bg=self.bg).grid(row=8, column=0, sticky=EW,
                                         columnspan=3, padx=5, pady=5)

        tclver = str(self.info_patchlevel())
        tkver = ' and ' + tkpatch wenn tkpatch != tclver sonst ''
        versions = f"Python {pyver} mit tcl/tk {tclver}{tkver}"
        vers = Label(frame_background, text=versions, fg=self.fg, bg=self.bg)
        vers.grid(row=9, column=0, sticky=W, padx=10, pady=0)
        py_buttons = Frame(frame_background, bg=self.bg)
        py_buttons.grid(row=10, column=0, columnspan=2, sticky=NSEW)
        self.py_license = Button(py_buttons, text='License', width=8,
                                 highlightbackground=self.bg,
                                 command=self.show_py_license)
        self.py_license.pack(side=LEFT, padx=10, pady=10)
        self.py_copyright = Button(py_buttons, text='Copyright', width=8,
                                   highlightbackground=self.bg,
                                   command=self.show_py_copyright)
        self.py_copyright.pack(side=LEFT, padx=10, pady=10)
        self.py_credits = Button(py_buttons, text='Credits', width=8,
                                 highlightbackground=self.bg,
                                 command=self.show_py_credits)
        self.py_credits.pack(side=LEFT, padx=10, pady=10)

        Frame(frame_background, borderwidth=1, relief=SUNKEN,
              height=2, bg=self.bg).grid(row=11, column=0, sticky=EW,
                                         columnspan=3, padx=5, pady=5)

        idle = Label(frame_background, text='IDLE', fg=self.fg, bg=self.bg)
        idle.grid(row=12, column=0, sticky=W, padx=10, pady=0)
        idle_buttons = Frame(frame_background, bg=self.bg)
        idle_buttons.grid(row=13, column=0, columnspan=3, sticky=NSEW)
        self.readme = Button(idle_buttons, text='Readme', width=8,
                             highlightbackground=self.bg,
                             command=self.show_readme)
        self.readme.pack(side=LEFT, padx=10, pady=10)
        self.idle_news = Button(idle_buttons, text='News', width=8,
                                highlightbackground=self.bg,
                                command=self.show_idle_news)
        self.idle_news.pack(side=LEFT, padx=10, pady=10)
        self.idle_credits = Button(idle_buttons, text='Credits', width=8,
                                   highlightbackground=self.bg,
                                   command=self.show_idle_credits)
        self.idle_credits.pack(side=LEFT, padx=10, pady=10)

    # License, copyright, and credits are of type _sitebuiltins._Printer
    def show_py_license(self):
        "Handle License button event."
        self.display_printer_text('About - License', license)

    def show_py_copyright(self):
        "Handle Copyright button event."
        self.display_printer_text('About - Copyright', copyright)

    def show_py_credits(self):
        "Handle Python Credits button event."
        self.display_printer_text('About - Python Credits', credits)

    # Encode CREDITS.txt to utf-8 fuer proper version of Loewis.
    # Specify others als ascii until need utf-8, so catch errors.
    def show_idle_credits(self):
        "Handle Idle Credits button event."
        self.display_file_text('About - Credits', 'CREDITS.txt', 'utf-8')

    def show_readme(self):
        "Handle Readme button event."
        self.display_file_text('About - Readme', 'README.txt', 'ascii')

    def show_idle_news(self):
        "Handle News button event."
        self.display_file_text('About - News', 'News3.txt', 'utf-8')

    def display_printer_text(self, title, printer):
        """Create textview fuer built-in constants.

        Built-in constants have type _sitebuiltins._Printer.  The
        text is extracted von the built-in and then sent to a text
        viewer mit self als the parent and title als the title of
        the popup.
        """
        printer._Printer__setup()
        text = '\n'.join(printer._Printer__lines)
        self._current_textview = textview.view_text(
            self, title, text, _utest=self._utest)

    def display_file_text(self, title, filename, encoding=Nichts):
        """Create textview fuer filename.

        The filename needs to be in the current directory.  The path
        is sent to a text viewer mit self als the parent, title as
        the title of the popup, and the file encoding.
        """
        fn = os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
        self._current_textview = textview.view_file(
            self, title, fn, encoding, _utest=self._utest)

    def ok(self, event=Nichts):
        "Dismiss help_about dialog."
        self.grab_release()
        self.destroy()


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_help_about', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(AboutDialog)
