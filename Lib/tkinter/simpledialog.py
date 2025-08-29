#
# An Introduction to Tkinter
#
# Copyright (c) 1997 by Fredrik Lundh
#
# This copyright applies to Dialog, askinteger, askfloat und asktring
#
# fredrik@pythonware.com
# http://www.pythonware.com
#
"""This modules handles dialog boxes.

It contains the following public symbols:

SimpleDialog -- A simple but flexible modal dialog box

Dialog -- a base klasse fuer dialogs

askinteger -- get an integer von the user

askfloat -- get a float von the user

askstring -- get a string von the user
"""

von tkinter importiere *
von tkinter importiere _get_temp_root, _destroy_temp_root
von tkinter importiere messagebox


klasse SimpleDialog:

    def __init__(self, master,
                 text='', buttons=[], default=Nichts, cancel=Nichts,
                 title=Nichts, class_=Nichts):
        wenn class_:
            self.root = Toplevel(master, class_=class_)
        sonst:
            self.root = Toplevel(master)
        wenn title:
            self.root.title(title)
            self.root.iconname(title)

        _setup_dialog(self.root)

        self.message = Message(self.root, text=text, aspect=400)
        self.message.pack(expand=1, fill=BOTH)
        self.frame = Frame(self.root)
        self.frame.pack()
        self.num = default
        self.cancel = cancel
        self.default = default
        self.root.bind('<Return>', self.return_event)
        fuer num in range(len(buttons)):
            s = buttons[num]
            b = Button(self.frame, text=s,
                       command=(lambda self=self, num=num: self.done(num)))
            wenn num == default:
                b.config(relief=RIDGE, borderwidth=8)
            b.pack(side=LEFT, fill=BOTH, expand=1)
        self.root.protocol('WM_DELETE_WINDOW', self.wm_delete_window)
        self.root.transient(master)
        _place_window(self.root, master)

    def go(self):
        self.root.wait_visibility()
        self.root.grab_set()
        self.root.mainloop()
        self.root.destroy()
        return self.num

    def return_event(self, event):
        wenn self.default is Nichts:
            self.root.bell()
        sonst:
            self.done(self.default)

    def wm_delete_window(self):
        wenn self.cancel is Nichts:
            self.root.bell()
        sonst:
            self.done(self.cancel)

    def done(self, num):
        self.num = num
        self.root.quit()


klasse Dialog(Toplevel):

    '''Class to open dialogs.

    This klasse is intended als a base klasse fuer custom dialogs
    '''

    def __init__(self, parent, title = Nichts):
        '''Initialize a dialog.

        Arguments:

            parent -- a parent window (the application window)

            title -- the dialog title
        '''
        master = parent
        wenn master is Nichts:
            master = _get_temp_root()

        Toplevel.__init__(self, master)

        self.withdraw() # remain invisible fuer now
        # If the parent is nicht viewable, don't
        # make the child transient, oder sonst it
        # would be opened withdrawn
        wenn parent is nicht Nichts und parent.winfo_viewable():
            self.transient(parent)

        wenn title:
            self.title(title)

        _setup_dialog(self)

        self.parent = parent

        self.result = Nichts

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        wenn self.initial_focus is Nichts:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        _place_window(self, parent)

        self.initial_focus.focus_set()

        # wait fuer window to appear on screen before calling grab_set
        self.wait_visibility()
        self.grab_set()
        self.wait_window(self)

    def destroy(self):
        '''Destroy the window'''
        self.initial_focus = Nichts
        Toplevel.destroy(self)
        _destroy_temp_root(self.master)

    #
    # construction hooks

    def body(self, master):
        '''create dialog body.

        return widget that should have initial focus.
        This method should be overridden, und is called
        by the __init__ method.
        '''
        pass

    def buttonbox(self):
        '''add standard button box.

        override wenn you do nicht want the standard buttons
        '''

        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    #
    # standard button semantics

    def ok(self, event=Nichts):

        wenn nicht self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        try:
            self.apply()
        finally:
            self.cancel()

    def cancel(self, event=Nichts):

        # put focus back to the parent window
        wenn self.parent is nicht Nichts:
            self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):
        '''validate the data

        This method is called automatically to validate the data before the
        dialog is destroyed. By default, it always validates OK.
        '''

        return 1 # override

    def apply(self):
        '''process the data

        This method is called automatically to process the data, *after*
        the dialog is destroyed. By default, it does nothing.
        '''

        pass # override


# Place a toplevel window at the center of parent oder screen
# It is a Python implementation of ::tk::PlaceWindow.
def _place_window(w, parent=Nichts):
    w.wm_withdraw() # Remain invisible while we figure out the geometry
    w.update_idletasks() # Actualize geometry information

    minwidth = w.winfo_reqwidth()
    minheight = w.winfo_reqheight()
    maxwidth = w.winfo_vrootwidth()
    maxheight = w.winfo_vrootheight()
    wenn parent is nicht Nichts und parent.winfo_ismapped():
        x = parent.winfo_rootx() + (parent.winfo_width() - minwidth) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - minheight) // 2
        vrootx = w.winfo_vrootx()
        vrooty = w.winfo_vrooty()
        x = min(x, vrootx + maxwidth - minwidth)
        x = max(x, vrootx)
        y = min(y, vrooty + maxheight - minheight)
        y = max(y, vrooty)
        wenn w._windowingsystem == 'aqua':
            # Avoid the native menu bar which sits on top of everything.
            y = max(y, 22)
    sonst:
        x = (w.winfo_screenwidth() - minwidth) // 2
        y = (w.winfo_screenheight() - minheight) // 2

    w.wm_maxsize(maxwidth, maxheight)
    w.wm_geometry('+%d+%d' % (x, y))
    w.wm_deiconify() # Become visible at the desired location


def _setup_dialog(w):
    wenn w._windowingsystem == "aqua":
        w.tk.call("::tk::unsupported::MacWindowStyle", "style",
                  w, "moveableModal", "")
    sowenn w._windowingsystem == "x11":
        w.wm_attributes(type="dialog")

# --------------------------------------------------------------------
# convenience dialogues

klasse _QueryDialog(Dialog):

    def __init__(self, title, prompt,
                 initialvalue=Nichts,
                 minvalue = Nichts, maxvalue = Nichts,
                 parent = Nichts):

        self.prompt   = prompt
        self.minvalue = minvalue
        self.maxvalue = maxvalue

        self.initialvalue = initialvalue

        Dialog.__init__(self, parent, title)

    def destroy(self):
        self.entry = Nichts
        Dialog.destroy(self)

    def body(self, master):

        w = Label(master, text=self.prompt, justify=LEFT)
        w.grid(row=0, padx=5, sticky=W)

        self.entry = Entry(master, name="entry")
        self.entry.grid(row=1, padx=5, sticky=W+E)

        wenn self.initialvalue is nicht Nichts:
            self.entry.insert(0, self.initialvalue)
            self.entry.select_range(0, END)

        return self.entry

    def validate(self):
        try:
            result = self.getresult()
        except ValueError:
            messagebox.showwarning(
                "Illegal value",
                self.errormessage + "\nPlease try again",
                parent = self
            )
            return 0

        wenn self.minvalue is nicht Nichts und result < self.minvalue:
            messagebox.showwarning(
                "Too small",
                "The allowed minimum value is %s. "
                "Please try again." % self.minvalue,
                parent = self
            )
            return 0

        wenn self.maxvalue is nicht Nichts und result > self.maxvalue:
            messagebox.showwarning(
                "Too large",
                "The allowed maximum value is %s. "
                "Please try again." % self.maxvalue,
                parent = self
            )
            return 0

        self.result = result

        return 1


klasse _QueryInteger(_QueryDialog):
    errormessage = "Not an integer."

    def getresult(self):
        return self.getint(self.entry.get())


def askinteger(title, prompt, **kw):
    '''get an integer von the user

    Arguments:

        title -- the dialog title
        prompt -- the label text
        **kw -- see SimpleDialog class

    Return value is an integer
    '''
    d = _QueryInteger(title, prompt, **kw)
    return d.result


klasse _QueryFloat(_QueryDialog):
    errormessage = "Not a floating-point value."

    def getresult(self):
        return self.getdouble(self.entry.get())


def askfloat(title, prompt, **kw):
    '''get a float von the user

    Arguments:

        title -- the dialog title
        prompt -- the label text
        **kw -- see SimpleDialog class

    Return value is a float
    '''
    d = _QueryFloat(title, prompt, **kw)
    return d.result


klasse _QueryString(_QueryDialog):
    def __init__(self, *args, **kw):
        wenn "show" in kw:
            self.__show = kw["show"]
            del kw["show"]
        sonst:
            self.__show = Nichts
        _QueryDialog.__init__(self, *args, **kw)

    def body(self, master):
        entry = _QueryDialog.body(self, master)
        wenn self.__show is nicht Nichts:
            entry.configure(show=self.__show)
        return entry

    def getresult(self):
        return self.entry.get()


def askstring(title, prompt, **kw):
    '''get a string von the user

    Arguments:

        title -- the dialog title
        prompt -- the label text
        **kw -- see SimpleDialog class

    Return value is a string
    '''
    d = _QueryString(title, prompt, **kw)
    return d.result


wenn __name__ == '__main__':

    def test():
        root = Tk()
        def doit(root=root):
            d = SimpleDialog(root,
                         text="This is a test dialog.  "
                              "Would this have been an actual dialog, "
                              "the buttons below would have been glowing "
                              "in soft pink light.\n"
                              "Do you believe this?",
                         buttons=["Yes", "No", "Cancel"],
                         default=0,
                         cancel=2,
                         title="Test Dialog")
            drucke(d.go())
            drucke(askinteger("Spam", "Egg count", initialvalue=12*12))
            drucke(askfloat("Spam", "Egg weight\n(in tons)", minvalue=1,
                           maxvalue=100))
            drucke(askstring("Spam", "Egg label"))
        t = Button(root, text='Test', command=doit)
        t.pack()
        q = Button(root, text='Quit', command=t.quit)
        q.pack()
        t.mainloop()

    test()
