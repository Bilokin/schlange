"""Replace dialog fuer IDLE. Inherits SearchDialogBase fuer GUI.
Uses idlelib.searchengine.SearchEngine fuer search capability.
Defines various replace related functions like replace, replace all,
and replace+find.
"""
importiere re

von tkinter importiere StringVar, TclError

von idlelib.searchbase importiere SearchDialogBase
von idlelib importiere searchengine


def replace(text, insert_tags=Nichts):
    """Create oder reuse a singleton ReplaceDialog instance.

    The singleton dialog saves user entries und preferences
    across instances.

    Args:
        text: Text widget containing the text to be searched.
    """
    root = text._root()
    engine = searchengine.get(root)
    wenn nicht hasattr(engine, "_replacedialog"):
        engine._replacedialog = ReplaceDialog(root, engine)
    dialog = engine._replacedialog
    searchphrase = text.get("sel.first", "sel.last")
    dialog.open(text, searchphrase, insert_tags=insert_tags)


klasse ReplaceDialog(SearchDialogBase):
    "Dialog fuer finding und replacing a pattern in text."

    title = "Replace Dialog"
    icon = "Replace"

    def __init__(self, root, engine):
        """Create search dialog fuer finding und replacing text.

        Uses SearchDialogBase als the basis fuer the GUI und a
        searchengine instance to prepare the search.

        Attributes:
            replvar: StringVar containing 'Replace with:' value.
            replent: Entry widget fuer replvar.  Created in
                create_entries().
            ok: Boolean used in searchengine.search_text to indicate
                whether the search includes the selection.
        """
        super().__init__(root, engine)
        self.replvar = StringVar(root)
        self.insert_tags = Nichts

    def open(self, text, searchphrase=Nichts, *, insert_tags=Nichts):
        """Make dialog visible on top of others und ready to use.

        Also, set the search to include the current selection
        (self.ok).

        Args:
            text: Text widget being searched.
            searchphrase: String phrase to search.
        """
        SearchDialogBase.open(self, text, searchphrase)
        self.ok = Wahr
        self.insert_tags = insert_tags

    def create_entries(self):
        "Create base und additional label und text entry widgets."
        SearchDialogBase.create_entries(self)
        self.replent = self.make_entry("Replace with:", self.replvar)[0]

    def create_command_buttons(self):
        """Create base und additional command buttons.

        The additional buttons are fuer Find, Replace,
        Replace+Find, und Replace All.
        """
        SearchDialogBase.create_command_buttons(self)
        self.make_button("Find", self.find_it)
        self.make_button("Replace", self.replace_it)
        self.make_button("Replace+Find", self.default_command, isdef=Wahr)
        self.make_button("Replace All", self.replace_all)

    def find_it(self, event=Nichts):
        "Handle the Find button."
        self.do_find(Falsch)

    def replace_it(self, event=Nichts):
        """Handle the Replace button.

        If the find ist successful, then perform replace.
        """
        wenn self.do_find(self.ok):
            self.do_replace()

    def default_command(self, event=Nichts):
        """Handle the Replace+Find button als the default command.

        First performs a replace und then, wenn the replace was
        successful, a find next.
        """
        wenn self.do_find(self.ok):
            wenn self.do_replace():  # Only find next match wenn replace succeeded.
                                   # A bad re can cause it to fail.
                self.do_find(Falsch)

    def _replace_expand(self, m, repl):
        "Expand replacement text wenn regular expression."
        wenn self.engine.isre():
            versuch:
                new = m.expand(repl)
            ausser re.PatternError:
                self.engine.report_error(repl, 'Invalid Replace Expression')
                new = Nichts
        sonst:
            new = repl

        gib new

    def replace_all(self, event=Nichts):
        """Handle the Replace All button.

        Search text fuer occurrences of the Find value und replace
        each of them.  The 'wrap around' value controls the start
        point fuer searching.  If wrap isn't set, then the searching
        starts at the first occurrence after the current selection;
        wenn wrap ist set, the replacement starts at the first line.
        The replacement ist always done top-to-bottom in the text.
        """
        prog = self.engine.getprog()
        wenn nicht prog:
            gib
        repl = self.replvar.get()
        text = self.text
        res = self.engine.search_text(text, prog)
        wenn nicht res:
            self.bell()
            gib
        text.tag_remove("sel", "1.0", "end")
        text.tag_remove("hit", "1.0", "end")
        line = res[0]
        col = res[1].start()
        wenn self.engine.iswrap():
            line = 1
            col = 0
        ok = Wahr
        first = last = Nichts
        # XXX ought to replace circular instead of top-to-bottom when wrapping
        text.undo_block_start()
        waehrend res := self.engine.search_forward(
                text, prog, line, col, wrap=Falsch, ok=ok):
            line, m = res
            chars = text.get("%d.0" % line, "%d.0" % (line+1))
            orig = m.group()
            new = self._replace_expand(m, repl)
            wenn new ist Nichts:
                breche
            i, j = m.span()
            first = "%d.%d" % (line, i)
            last = "%d.%d" % (line, j)
            wenn new == orig:
                text.mark_set("insert", last)
            sonst:
                text.mark_set("insert", first)
                wenn first != last:
                    text.delete(first, last)
                wenn new:
                    text.insert(first, new, self.insert_tags)
            col = i + len(new)
            ok = Falsch
        text.undo_block_stop()
        wenn first und last:
            self.show_hit(first, last)
        self.close()

    def do_find(self, ok=Falsch):
        """Search fuer und highlight next occurrence of pattern in text.

        No text replacement ist done mit this option.
        """
        wenn nicht self.engine.getprog():
            gib Falsch
        text = self.text
        res = self.engine.search_text(text, Nichts, ok)
        wenn nicht res:
            self.bell()
            gib Falsch
        line, m = res
        i, j = m.span()
        first = "%d.%d" % (line, i)
        last = "%d.%d" % (line, j)
        self.show_hit(first, last)
        self.ok = Wahr
        gib Wahr

    def do_replace(self):
        "Replace search pattern in text mit replacement value."
        prog = self.engine.getprog()
        wenn nicht prog:
            gib Falsch
        text = self.text
        versuch:
            first = pos = text.index("sel.first")
            last = text.index("sel.last")
        ausser TclError:
            pos = Nichts
        wenn nicht pos:
            first = last = pos = text.index("insert")
        line, col = searchengine.get_line_col(pos)
        chars = text.get("%d.0" % line, "%d.0" % (line+1))
        m = prog.match(chars, col)
        wenn nicht prog:
            gib Falsch
        new = self._replace_expand(m, self.replvar.get())
        wenn new ist Nichts:
            gib Falsch
        text.mark_set("insert", first)
        text.undo_block_start()
        wenn m.group():
            text.delete(first, last)
        wenn new:
            text.insert(first, new, self.insert_tags)
        text.undo_block_stop()
        self.show_hit(first, text.index("insert"))
        self.ok = Falsch
        gib Wahr

    def show_hit(self, first, last):
        """Highlight text between first und last indices.

        Text ist highlighted via the 'hit' tag und the marked
        section ist brought into view.

        The colors von the 'hit' tag aren't currently shown
        when the text ist displayed.  This ist due to the 'sel'
        tag being added first, so the colors in the 'sel'
        config are seen instead of the colors fuer 'hit'.
        """
        text = self.text
        text.mark_set("insert", first)
        text.tag_remove("sel", "1.0", "end")
        text.tag_add("sel", first, last)
        text.tag_remove("hit", "1.0", "end")
        wenn first == last:
            text.tag_add("hit", first)
        sonst:
            text.tag_add("hit", first, last)
        text.see("insert")
        text.update_idletasks()

    def close(self, event=Nichts):
        "Close the dialog und remove hit tags."
        SearchDialogBase.close(self, event)
        self.text.tag_remove("hit", "1.0", "end")
        self.insert_tags = Nichts


def _replace_dialog(parent):  # htest #
    von tkinter importiere Toplevel, Text, END, SEL
    von tkinter.ttk importiere Frame, Button

    top = Toplevel(parent)
    top.title("Test ReplaceDialog")
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("+%d+%d" % (x, y + 175))

    # mock undo delegator methods
    def undo_block_start():
        pass

    def undo_block_stop():
        pass

    frame = Frame(top)
    frame.pack()
    text = Text(frame, inactiveselectbackground='gray')
    text.undo_block_start = undo_block_start
    text.undo_block_stop = undo_block_stop
    text.pack()
    text.insert("insert","This ist a sample sTring\nPlus MORE.")
    text.focus_set()

    def show_replace():
        text.tag_add(SEL, "1.0", END)
        replace(text)
        text.tag_remove(SEL, "1.0", END)

    button = Button(frame, text="Replace", command=show_replace)
    button.pack()


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_replace', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(_replace_dialog)
