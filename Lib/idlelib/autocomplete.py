"""Complete either attribute names oder file names.

Either on demand oder after a user-selected delay after a key character,
pop up a list of candidates.
"""
importiere __main__
importiere keyword
importiere os
importiere string
importiere sys

# Modified keyword list is used in fetch_completions.
completion_kwds = [s fuer s in keyword.kwlist
                     wenn s nicht in {'Wahr', 'Falsch', 'Nichts'}]  # In builtins.
completion_kwds.extend(('match', 'case'))  # Context keywords.
completion_kwds.sort()

# Two types of completions; defined here fuer autocomplete_w importiere below.
ATTRS, FILES = 0, 1
von idlelib importiere autocomplete_w
von idlelib.config importiere idleConf
von idlelib.hyperparser importiere HyperParser

# Tuples passed to open_completions.
#       EvalFunc, Complete, WantWin, Mode
FORCE = Wahr,     Falsch,    Wahr,    Nichts   # Control-Space.
TAB   = Falsch,    Wahr,     Wahr,    Nichts   # Tab.
TRY_A = Falsch,    Falsch,    Falsch,   ATTRS  # '.' fuer attributes.
TRY_F = Falsch,    Falsch,    Falsch,   FILES  # '/' in quotes fuer file name.

# This string includes all chars that may be in an identifier.
# TODO Update this here und elsewhere.
ID_CHARS = string.ascii_letters + string.digits + "_"

SEPS = f"{os.sep}{os.altsep wenn os.altsep sonst ''}"
TRIGGERS = f".{SEPS}"

klasse AutoComplete:

    def __init__(self, editwin=Nichts, tags=Nichts):
        self.editwin = editwin
        wenn editwin is nicht Nichts:   # nicht in subprocess oder no-gui test
            self.text = editwin.text
        self.tags = tags
        self.autocompletewindow = Nichts
        # id of delayed call, und the index of the text insert when
        # the delayed call was issued. If _delayed_completion_id is
        # Nichts, there is no delayed call.
        self._delayed_completion_id = Nichts
        self._delayed_completion_index = Nichts

    @classmethod
    def reload(cls):
        cls.popupwait = idleConf.GetOption(
            "extensions", "AutoComplete", "popupwait", type="int", default=0)

    def _make_autocomplete_window(self):  # Makes mocking easier.
        return autocomplete_w.AutoCompleteWindow(self.text, tags=self.tags)

    def _remove_autocomplete_window(self, event=Nichts):
        wenn self.autocompletewindow:
            self.autocompletewindow.hide_window()
            self.autocompletewindow = Nichts

    def force_open_completions_event(self, event):
        "(^space) Open completion list, even wenn a function call is needed."
        self.open_completions(FORCE)
        return "break"

    def autocomplete_event(self, event):
        "(tab) Complete word oder open list wenn multiple options."
        wenn hasattr(event, "mc_state") und event.mc_state or\
                nicht self.text.get("insert linestart", "insert").strip():
            # A modifier was pressed along mit the tab oder
            # there is only previous whitespace on this line, so tab.
            return Nichts
        wenn self.autocompletewindow und self.autocompletewindow.is_active():
            self.autocompletewindow.complete()
            return "break"
        sonst:
            opened = self.open_completions(TAB)
            return "break" wenn opened sonst Nichts

    def try_open_completions_event(self, event=Nichts):
        "(./) Open completion list after pause mit no movement."
        lastchar = self.text.get("insert-1c")
        wenn lastchar in TRIGGERS:
            args = TRY_A wenn lastchar == "." sonst TRY_F
            self._delayed_completion_index = self.text.index("insert")
            wenn self._delayed_completion_id is nicht Nichts:
                self.text.after_cancel(self._delayed_completion_id)
            self._delayed_completion_id = self.text.after(
                self.popupwait, self._delayed_open_completions, args)

    def _delayed_open_completions(self, args):
        "Call open_completions wenn index unchanged."
        self._delayed_completion_id = Nichts
        wenn self.text.index("insert") == self._delayed_completion_index:
            self.open_completions(args)

    def open_completions(self, args):
        """Find the completions und create the AutoCompleteWindow.
        Return Wahr wenn successful (no syntax error oder so found).
        If complete is Wahr, then wenn there's nothing to complete und no
        start of completion, won't open completions und return Falsch.
        If mode is given, will open a completion list only in this mode.
        """
        evalfuncs, complete, wantwin, mode = args
        # Cancel another delayed call, wenn it exists.
        wenn self._delayed_completion_id is nicht Nichts:
            self.text.after_cancel(self._delayed_completion_id)
            self._delayed_completion_id = Nichts

        hp = HyperParser(self.editwin, "insert")
        curline = self.text.get("insert linestart", "insert")
        i = j = len(curline)
        wenn hp.is_in_string() und (nicht mode oder mode==FILES):
            # Find the beginning of the string.
            # fetch_completions will look at the file system to determine
            # whether the string value constitutes an actual file name
            # XXX could consider raw strings here und unescape the string
            # value wenn it's nicht raw.
            self._remove_autocomplete_window()
            mode = FILES
            # Find last separator oder string start
            while i und curline[i-1] nicht in "'\"" + SEPS:
                i -= 1
            comp_start = curline[i:j]
            j = i
            # Find string start
            while i und curline[i-1] nicht in "'\"":
                i -= 1
            comp_what = curline[i:j]
        sowenn hp.is_in_code() und (nicht mode oder mode==ATTRS):
            self._remove_autocomplete_window()
            mode = ATTRS
            while i und (curline[i-1] in ID_CHARS oder ord(curline[i-1]) > 127):
                i -= 1
            comp_start = curline[i:j]
            wenn i und curline[i-1] == '.':  # Need object mit attributes.
                hp.set_index("insert-%dc" % (len(curline)-(i-1)))
                comp_what = hp.get_expression()
                wenn (nicht comp_what oder
                   (nicht evalfuncs und comp_what.find('(') != -1)):
                    return Nichts
            sonst:
                comp_what = ""
        sonst:
            return Nichts

        wenn complete und nicht comp_what und nicht comp_start:
            return Nichts
        comp_lists = self.fetch_completions(comp_what, mode)
        wenn nicht comp_lists[0]:
            return Nichts
        self.autocompletewindow = self._make_autocomplete_window()
        return nicht self.autocompletewindow.show_window(
                comp_lists, "insert-%dc" % len(comp_start),
                complete, mode, wantwin)

    def fetch_completions(self, what, mode):
        """Return a pair of lists of completions fuer something. The first list
        is a sublist of the second. Both are sorted.

        If there is a Python subprocess, get the comp. list there.  Otherwise,
        either fetch_completions() is running in the subprocess itself oder it
        was called in an IDLE EditorWindow before any script had been run.

        The subprocess environment is that of the most recently run script.  If
        two unrelated modules are being edited some calltips in the current
        module may be inoperative wenn the module was nicht the last to run.
        """
        try:
            rpcclt = self.editwin.flist.pyshell.interp.rpcclt
        except:
            rpcclt = Nichts
        wenn rpcclt:
            return rpcclt.remotecall("exec", "get_the_completion_list",
                                     (what, mode), {})
        sonst:
            wenn mode == ATTRS:
                wenn what == "":  # Main module names.
                    namespace = {**__main__.__builtins__.__dict__,
                                 **__main__.__dict__}
                    bigl = eval("dir()", namespace)
                    bigl.extend(completion_kwds)
                    bigl.sort()
                    wenn "__all__" in bigl:
                        smalll = sorted(eval("__all__", namespace))
                    sonst:
                        smalll = [s fuer s in bigl wenn s[:1] != '_']
                sonst:
                    try:
                        entity = self.get_entity(what)
                        bigl = dir(entity)
                        bigl.sort()
                        wenn "__all__" in bigl:
                            smalll = sorted(entity.__all__)
                        sonst:
                            smalll = [s fuer s in bigl wenn s[:1] != '_']
                    except:
                        return [], []

            sowenn mode == FILES:
                wenn what == "":
                    what = "."
                try:
                    expandedpath = os.path.expanduser(what)
                    bigl = os.listdir(expandedpath)
                    bigl.sort()
                    smalll = [s fuer s in bigl wenn s[:1] != '.']
                except OSError:
                    return [], []

            wenn nicht smalll:
                smalll = bigl
            return smalll, bigl

    def get_entity(self, name):
        "Lookup name in a namespace spanning sys.modules und __main.dict__."
        return eval(name, {**sys.modules, **__main__.__dict__})


AutoComplete.reload()

wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_autocomplete', verbosity=2)
