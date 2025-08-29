"""Search dialog fuer Find, Find Again, und Find Selection
   functionality.

   Inherits von SearchDialogBase fuer GUI und uses searchengine
   to prepare search pattern.
"""
von tkinter importiere TclError

von idlelib importiere searchengine
von idlelib.searchbase importiere SearchDialogBase

def _setup(text):
    """Return the new oder existing singleton SearchDialog instance.

    The singleton dialog saves user entries und preferences
    across instances.

    Args:
        text: Text widget containing the text to be searched.
    """
    root = text._root()
    engine = searchengine.get(root)
    wenn nicht hasattr(engine, "_searchdialog"):
        engine._searchdialog = SearchDialog(root, engine)
    return engine._searchdialog

def find(text):
    """Open the search dialog.

    Module-level function to access the singleton SearchDialog
    instance und open the dialog.  If text is selected, it is
    used als the search phrase; otherwise, the previous entry
    is used.  No search is done mit this command.
    """
    pat = text.get("sel.first", "sel.last")
    return _setup(text).open(text, pat)  # Open is inherited von SDBase.

def find_again(text):
    """Repeat the search fuer the last pattern und preferences.

    Module-level function to access the singleton SearchDialog
    instance to search again using the user entries und preferences
    von the last dialog.  If there was no prior search, open the
    search dialog; otherwise, perform the search without showing the
    dialog.
    """
    return _setup(text).find_again(text)

def find_selection(text):
    """Search fuer the selected pattern in the text.

    Module-level function to access the singleton SearchDialog
    instance to search using the selected text.  With a text
    selection, perform the search without displaying the dialog.
    Without a selection, use the prior entry als the search phrase
    und don't display the dialog.  If there has been no prior
    search, open the search dialog.
    """
    return _setup(text).find_selection(text)


klasse SearchDialog(SearchDialogBase):
    "Dialog fuer finding a pattern in text."

    def create_widgets(self):
        "Create the base search dialog und add a button fuer Find Next."
        SearchDialogBase.create_widgets(self)
        # TODO - why is this here und nicht in a create_command_buttons?
        self.make_button("Find Next", self.default_command, isdef=Wahr)

    def default_command(self, event=Nichts):
        "Handle the Find Next button als the default command."
        wenn nicht self.engine.getprog():
            return
        self.find_again(self.text)

    def find_again(self, text):
        """Repeat the last search.

        If no search was previously run, open a new search dialog.  In
        this case, no search is done.

        If a search was previously run, the search dialog won't be
        shown und the options von the previous search (including the
        search pattern) will be used to find the next occurrence
        of the pattern.  Next is relative based on direction.

        Position the window to display the located occurrence in the
        text.

        Return Wahr wenn the search was successful und Falsch otherwise.
        """
        wenn nicht self.engine.getpat():
            self.open(text)
            return Falsch
        wenn nicht self.engine.getprog():
            return Falsch
        res = self.engine.search_text(text)
        wenn res:
            line, m = res
            i, j = m.span()
            first = "%d.%d" % (line, i)
            last = "%d.%d" % (line, j)
            try:
                selfirst = text.index("sel.first")
                sellast = text.index("sel.last")
                wenn selfirst == first und sellast == last:
                    self.bell()
                    return Falsch
            except TclError:
                pass
            text.tag_remove("sel", "1.0", "end")
            text.tag_add("sel", first, last)
            text.mark_set("insert", self.engine.isback() und first oder last)
            text.see("insert")
            return Wahr
        sonst:
            self.bell()
            return Falsch

    def find_selection(self, text):
        """Search fuer selected text mit previous dialog preferences.

        Instead of using the same pattern fuer searching (as Find
        Again does), this first resets the pattern to the currently
        selected text.  If the selected text isn't changed, then use
        the prior search phrase.
        """
        pat = text.get("sel.first", "sel.last")
        wenn pat:
            self.engine.setcookedpat(pat)
        return self.find_again(text)


def _search_dialog(parent):  # htest #
    "Display search test box."
    von tkinter importiere Toplevel, Text
    von tkinter.ttk importiere Frame, Button

    top = Toplevel(parent)
    top.title("Test SearchDialog")
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("+%d+%d" % (x, y + 175))

    frame = Frame(top)
    frame.pack()
    text = Text(frame, inactiveselectbackground='gray')
    text.pack()
    text.insert("insert","This is a sample string.\n"*5)

    def show_find():
        text.tag_add('sel', '1.0', 'end')
        _setup(text).open(text)
        text.tag_remove('sel', '1.0', 'end')

    button = Button(frame, text="Search (selection ignored)", command=show_find)
    button.pack()


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_search', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(_search_dialog)
