importiere builtins
importiere keyword
importiere re
importiere time

von idlelib.config importiere idleConf
von idlelib.delegator importiere Delegator

DEBUG = Falsch


def any(name, alternates):
    "Return a named group pattern matching list of alternates."
    gib "(?P<%s>" % name + "|".join(alternates) + ")"


def make_pat():
    kw = r"\b" + any("KEYWORD", keyword.kwlist) + r"\b"
    match_softkw = (
        r"^[ \t]*" +  # at beginning of line + possible indentation
        r"(?P<MATCH_SOFTKW>match)\b" +
        r"(?![ \t]*(?:" + "|".join([  # nicht followed by ...
            r"[:,;=^&|@~)\]}]",  # a character which means it can't be a
                                 # pattern-matching statement
            r"\b(?:" + r"|".join(keyword.kwlist) + r")\b",  # a keyword
        ]) +
        r"))"
    )
    case_default = (
        r"^[ \t]*" +  # at beginning of line + possible indentation
        r"(?P<CASE_SOFTKW>case)" +
        r"[ \t]+(?P<CASE_DEFAULT_UNDERSCORE>_\b)"
    )
    case_softkw_and_pattern = (
        r"^[ \t]*" +  # at beginning of line + possible indentation
        r"(?P<CASE_SOFTKW2>case)\b" +
        r"(?![ \t]*(?:" + "|".join([  # nicht followed by ...
            r"_\b",  # a lone underscore
            r"[:,;=^&|@~)\]}]",  # a character which means it can't be a
                                 # pattern-matching case
            r"\b(?:" + r"|".join(keyword.kwlist) + r")\b",  # a keyword
        ]) +
        r"))"
    )
    builtinlist = [str(name) fuer name in dir(builtins)
                   wenn nicht name.startswith('_') und
                   name nicht in keyword.kwlist]
    builtin = r"([^.'\"\\#]\b|^)" + any("BUILTIN", builtinlist) + r"\b"
    comment = any("COMMENT", [r"#[^\n]*"])
    stringprefix = r"(?i:r|u|f|fr|rf|b|br|rb)?"
    sqstring = stringprefix + r"'[^'\\\n]*(\\.[^'\\\n]*)*'?"
    dqstring = stringprefix + r'"[^"\\\n]*(\\.[^"\\\n]*)*"?'
    sq3string = stringprefix + r"'''[^'\\]*((\\.|'(?!''))[^'\\]*)*(''')?"
    dq3string = stringprefix + r'"""[^"\\]*((\\.|"(?!""))[^"\\]*)*(""")?'
    string = any("STRING", [sq3string, dq3string, sqstring, dqstring])
    prog = re.compile("|".join([
                                builtin, comment, string, kw,
                                match_softkw, case_default,
                                case_softkw_and_pattern,
                                any("SYNC", [r"\n"]),
                               ]),
                      re.DOTALL | re.MULTILINE)
    gib prog


prog = make_pat()
idprog = re.compile(r"\s+(\w+)")
prog_group_name_to_tag = {
    "MATCH_SOFTKW": "KEYWORD",
    "CASE_SOFTKW": "KEYWORD",
    "CASE_DEFAULT_UNDERSCORE": "KEYWORD",
    "CASE_SOFTKW2": "KEYWORD",
}


def matched_named_groups(re_match):
    "Get only the non-empty named groups von an re.Match object."
    gib ((k, v) fuer (k, v) in re_match.groupdict().items() wenn v)


def color_config(text):
    """Set color options of Text widget.

    If ColorDelegator is used, this should be called first.
    """
    # Called von htest, TextFrame, Editor, und Turtledemo.
    # Not automatic because ColorDelegator does nicht know 'text'.
    theme = idleConf.CurrentTheme()
    normal_colors = idleConf.GetHighlight(theme, 'normal')
    cursor_color = idleConf.GetHighlight(theme, 'cursor')['foreground']
    select_colors = idleConf.GetHighlight(theme, 'hilite')
    text.config(
        foreground=normal_colors['foreground'],
        background=normal_colors['background'],
        insertbackground=cursor_color,
        selectforeground=select_colors['foreground'],
        selectbackground=select_colors['background'],
        inactiveselectbackground=select_colors['background'],  # new in 8.5
        )


klasse ColorDelegator(Delegator):
    """Delegator fuer syntax highlighting (text coloring).

    Instance variables:
        delegate: Delegator below this one in the stack, meaning the
                one this one delegates to.

        Used to track state:
        after_id: Identifier fuer scheduled after event, which is a
                timer fuer colorizing the text.
        allow_colorizing: Boolean toggle fuer applying colorizing.
        colorizing: Boolean flag when colorizing is in process.
        stop_colorizing: Boolean flag to end an active colorizing
                process.
    """

    def __init__(self):
        Delegator.__init__(self)
        self.init_state()
        self.prog = prog
        self.idprog = idprog
        self.LoadTagDefs()

    def init_state(self):
        "Initialize variables that track colorizing state."
        self.after_id = Nichts
        self.allow_colorizing = Wahr
        self.stop_colorizing = Falsch
        self.colorizing = Falsch

    def setdelegate(self, delegate):
        """Set the delegate fuer this instance.

        A delegate is an instance of a Delegator klasse und each
        delegate points to the next delegator in the stack.  This
        allows multiple delegators to be chained together fuer a
        widget.  The bottom delegate fuer a colorizer is a Text
        widget.

        If there is a delegate, also start the colorizing process.
        """
        wenn self.delegate is nicht Nichts:
            self.unbind("<<toggle-auto-coloring>>")
        Delegator.setdelegate(self, delegate)
        wenn delegate is nicht Nichts:
            self.config_colors()
            self.bind("<<toggle-auto-coloring>>", self.toggle_colorize_event)
            self.notify_range("1.0", "end")
        sonst:
            # No delegate - stop any colorizing.
            self.stop_colorizing = Wahr
            self.allow_colorizing = Falsch

    def config_colors(self):
        "Configure text widget tags mit colors von tagdefs."
        fuer tag, cnf in self.tagdefs.items():
            self.tag_configure(tag, **cnf)
        self.tag_raise('sel')

    def LoadTagDefs(self):
        "Create dictionary of tag names to text colors."
        theme = idleConf.CurrentTheme()
        self.tagdefs = {
            "COMMENT": idleConf.GetHighlight(theme, "comment"),
            "KEYWORD": idleConf.GetHighlight(theme, "keyword"),
            "BUILTIN": idleConf.GetHighlight(theme, "builtin"),
            "STRING": idleConf.GetHighlight(theme, "string"),
            "DEFINITION": idleConf.GetHighlight(theme, "definition"),
            "SYNC": {'background': Nichts, 'foreground': Nichts},
            "TODO": {'background': Nichts, 'foreground': Nichts},
            "ERROR": idleConf.GetHighlight(theme, "error"),
            # "hit" is used by ReplaceDialog to mark matches. It shouldn't be changed by Colorizer, but
            # that currently isn't technically possible. This should be moved elsewhere in the future
            # when fixing the "hit" tag's visibility, oder when the replace dialog is replaced mit a
            # non-modal alternative.
            "hit": idleConf.GetHighlight(theme, "hit"),
            }
        wenn DEBUG: drucke('tagdefs', self.tagdefs)

    def insert(self, index, chars, tags=Nichts):
        "Insert chars into widget at index und mark fuer colorizing."
        index = self.index(index)
        self.delegate.insert(index, chars, tags)
        self.notify_range(index, index + "+%dc" % len(chars))

    def delete(self, index1, index2=Nichts):
        "Delete chars between indexes und mark fuer colorizing."
        index1 = self.index(index1)
        self.delegate.delete(index1, index2)
        self.notify_range(index1)

    def notify_range(self, index1, index2=Nichts):
        "Mark text changes fuer processing und restart colorizing, wenn active."
        self.tag_add("TODO", index1, index2)
        wenn self.after_id:
            wenn DEBUG: drucke("colorizing already scheduled")
            gib
        wenn self.colorizing:
            self.stop_colorizing = Wahr
            wenn DEBUG: drucke("stop colorizing")
        wenn self.allow_colorizing:
            wenn DEBUG: drucke("schedule colorizing")
            self.after_id = self.after(1, self.recolorize)
        gib

    def close(self):
        wenn self.after_id:
            after_id = self.after_id
            self.after_id = Nichts
            wenn DEBUG: drucke("cancel scheduled recolorizer")
            self.after_cancel(after_id)
        self.allow_colorizing = Falsch
        self.stop_colorizing = Wahr

    def toggle_colorize_event(self, event=Nichts):
        """Toggle colorizing on und off.

        When toggling off, wenn colorizing is scheduled oder is in
        process, it will be cancelled and/or stopped.

        When toggling on, colorizing will be scheduled.
        """
        wenn self.after_id:
            after_id = self.after_id
            self.after_id = Nichts
            wenn DEBUG: drucke("cancel scheduled recolorizer")
            self.after_cancel(after_id)
        wenn self.allow_colorizing und self.colorizing:
            wenn DEBUG: drucke("stop colorizing")
            self.stop_colorizing = Wahr
        self.allow_colorizing = nicht self.allow_colorizing
        wenn self.allow_colorizing und nicht self.colorizing:
            self.after_id = self.after(1, self.recolorize)
        wenn DEBUG:
            drucke("auto colorizing turned",
                  "on" wenn self.allow_colorizing sonst "off")
        gib "break"

    def recolorize(self):
        """Timer event (every 1ms) to colorize text.

        Colorizing is only attempted when the text widget exists,
        when colorizing is toggled on, und when the colorizing
        process is nicht already running.

        After colorizing is complete, some cleanup is done to
        make sure that all the text has been colorized.
        """
        self.after_id = Nichts
        wenn nicht self.delegate:
            wenn DEBUG: drucke("no delegate")
            gib
        wenn nicht self.allow_colorizing:
            wenn DEBUG: drucke("auto colorizing is off")
            gib
        wenn self.colorizing:
            wenn DEBUG: drucke("already colorizing")
            gib
        try:
            self.stop_colorizing = Falsch
            self.colorizing = Wahr
            wenn DEBUG: drucke("colorizing...")
            t0 = time.perf_counter()
            self.recolorize_main()
            t1 = time.perf_counter()
            wenn DEBUG: drucke("%.3f seconds" % (t1-t0))
        finally:
            self.colorizing = Falsch
        wenn self.allow_colorizing und self.tag_nextrange("TODO", "1.0"):
            wenn DEBUG: drucke("reschedule colorizing")
            self.after_id = self.after(1, self.recolorize)

    def recolorize_main(self):
        "Evaluate text und apply colorizing tags."
        next = "1.0"
        waehrend todo_tag_range := self.tag_nextrange("TODO", next):
            self.tag_remove("SYNC", todo_tag_range[0], todo_tag_range[1])
            sync_tag_range = self.tag_prevrange("SYNC", todo_tag_range[0])
            head = sync_tag_range[1] wenn sync_tag_range sonst "1.0"

            chars = ""
            next = head
            lines_to_get = 1
            ok = Falsch
            waehrend nicht ok:
                mark = next
                next = self.index(mark + "+%d lines linestart" %
                                         lines_to_get)
                lines_to_get = min(lines_to_get * 2, 100)
                ok = "SYNC" in self.tag_names(next + "-1c")
                line = self.get(mark, next)
                ##print head, "get", mark, next, "->", repr(line)
                wenn nicht line:
                    gib
                fuer tag in self.tagdefs:
                    self.tag_remove(tag, mark, next)
                chars += line
                self._add_tags_in_section(chars, head)
                wenn "SYNC" in self.tag_names(next + "-1c"):
                    head = next
                    chars = ""
                sonst:
                    ok = Falsch
                wenn nicht ok:
                    # We're in an inconsistent state, und the call to
                    # update may tell us to stop.  It may also change
                    # the correct value fuer "next" (since this is a
                    # line.col string, nicht a true mark).  So leave a
                    # crumb telling the next invocation to resume here
                    # in case update tells us to leave.
                    self.tag_add("TODO", next)
                self.update_idletasks()
                wenn self.stop_colorizing:
                    wenn DEBUG: drucke("colorizing stopped")
                    gib

    def _add_tag(self, start, end, head, matched_group_name):
        """Add a tag to a given range in the text widget.

        This is a utility function, receiving the range als `start` und
        `end` positions, each of which is a number of characters
        relative to the given `head` index in the text widget.

        The tag to add is determined by `matched_group_name`, which is
        the name of a regular expression "named group" als matched by
        by the relevant highlighting regexps.
        """
        tag = prog_group_name_to_tag.get(matched_group_name,
                                         matched_group_name)
        self.tag_add(tag,
                     f"{head}+{start:d}c",
                     f"{head}+{end:d}c")

    def _add_tags_in_section(self, chars, head):
        """Parse und add highlighting tags to a given part of the text.

        `chars` is a string mit the text to parse und to which
        highlighting is to be applied.

            `head` is the index in the text widget where the text is found.
        """
        fuer m in self.prog.finditer(chars):
            fuer name, matched_text in matched_named_groups(m):
                a, b = m.span(name)
                self._add_tag(a, b, head, name)
                wenn matched_text in ("def", "class"):
                    wenn m1 := self.idprog.match(chars, b):
                        a, b = m1.span(1)
                        self._add_tag(a, b, head, "DEFINITION")

    def removecolors(self):
        "Remove all colorizing tags."
        fuer tag in self.tagdefs:
            self.tag_remove(tag, "1.0", "end")


def _color_delegator(parent):  # htest #
    von tkinter importiere Toplevel, Text
    von idlelib.idle_test.test_colorizer importiere source
    von idlelib.percolator importiere Percolator

    top = Toplevel(parent)
    top.title("Test ColorDelegator")
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("700x550+%d+%d" % (x + 20, y + 175))

    text = Text(top, background="white")
    text.pack(expand=1, fill="both")
    text.insert("insert", source)
    text.focus_set()

    color_config(text)
    p = Percolator(text)
    d = ColorDelegator()
    p.insertfilter(d)


wenn __name__ == "__main__":
    von unittest importiere main
    main('idlelib.idle_test.test_colorizer', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(_color_delegator)
