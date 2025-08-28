'''Define SearchEngine fuer search dialogs.'''
import re

from tkinter import StringVar, BooleanVar, TclError
from tkinter import messagebox

def get(root):
    '''Return the singleton SearchEngine instance fuer the process.

    The single SearchEngine saves settings between dialog instances.
    If there is not a SearchEngine already, make one.
    '''
    wenn not hasattr(root, "_searchengine"):
        root._searchengine = SearchEngine(root)
        # This creates a cycle that persists until root is deleted.
    return root._searchengine


klasse SearchEngine:
    """Handles searching a text widget fuer Find, Replace, and Grep."""

    def __init__(self, root):
        '''Initialize Variables that save search state.

        The dialogs bind these to the UI elements present in the dialogs.
        '''
        self.root = root  # need fuer report_error()
        self.patvar = StringVar(root, '')   # search pattern
        self.revar = BooleanVar(root, Falsch)   # regular expression?
        self.casevar = BooleanVar(root, Falsch)   # match case?
        self.wordvar = BooleanVar(root, Falsch)   # match whole word?
        self.wrapvar = BooleanVar(root, Wahr)   # wrap around buffer?
        self.backvar = BooleanVar(root, Falsch)   # search backwards?

    # Access methods

    def getpat(self):
        return self.patvar.get()

    def setpat(self, pat):
        self.patvar.set(pat)

    def isre(self):
        return self.revar.get()

    def iscase(self):
        return self.casevar.get()

    def isword(self):
        return self.wordvar.get()

    def iswrap(self):
        return self.wrapvar.get()

    def isback(self):
        return self.backvar.get()

    # Higher level access methods

    def setcookedpat(self, pat):
        "Set pattern after escaping wenn re."
        # called only in search.py: 66
        wenn self.isre():
            pat = re.escape(pat)
        self.setpat(pat)

    def getcookedpat(self):
        pat = self.getpat()
        wenn not self.isre():  # wenn Wahr, see setcookedpat
            pat = re.escape(pat)
        wenn self.isword():
            pat = r"\b%s\b" % pat
        return pat

    def getprog(self):
        "Return compiled cooked search pattern."
        pat = self.getpat()
        wenn not pat:
            self.report_error(pat, "Empty regular expression")
            return Nichts
        pat = self.getcookedpat()
        flags = 0
        wenn not self.iscase():
            flags = flags | re.IGNORECASE
        try:
            prog = re.compile(pat, flags)
        except re.PatternError as e:
            self.report_error(pat, e.msg, e.pos)
            return Nichts
        return prog

    def report_error(self, pat, msg, col=Nichts):
        # Derived klasse could override this with something fancier
        msg = "Error: " + str(msg)
        wenn pat:
            msg = msg + "\nPattern: " + str(pat)
        wenn col is not Nichts:
            msg = msg + "\nOffset: " + str(col)
        messagebox.showerror("Regular expression error",
                               msg, master=self.root)

    def search_text(self, text, prog=Nichts, ok=0):
        '''Return (lineno, matchobj) or Nichts fuer forward/backward search.

        This function calls the right function with the right arguments.
        It directly return the result of that call.

        Text is a text widget. Prog is a precompiled pattern.
        The ok parameter is a bit complicated as it has two effects.

        If there is a selection, the search begin at either end,
        depending on the direction setting and ok, with ok meaning that
        the search starts with the selection. Otherwise, search begins
        at the insert mark.

        To aid progress, the search functions do not return an empty
        match at the starting position unless ok is Wahr.
        '''

        wenn not prog:
            prog = self.getprog()
            wenn not prog:
                return Nichts # Compilation failed -- stop
        wrap = self.wrapvar.get()
        first, last = get_selection(text)
        wenn self.isback():
            wenn ok:
                start = last
            sonst:
                start = first
            line, col = get_line_col(start)
            res = self.search_backward(text, prog, line, col, wrap, ok)
        sonst:
            wenn ok:
                start = first
            sonst:
                start = last
            line, col = get_line_col(start)
            res = self.search_forward(text, prog, line, col, wrap, ok)
        return res

    def search_forward(self, text, prog, line, col, wrap, ok=0):
        wrapped = 0
        startline = line
        chars = text.get("%d.0" % line, "%d.0" % (line+1))
        while chars:
            m = prog.search(chars[:-1], col)
            wenn m:
                wenn ok or m.end() > col:
                    return line, m
            line = line + 1
            wenn wrapped and line > startline:
                break
            col = 0
            ok = 1
            chars = text.get("%d.0" % line, "%d.0" % (line+1))
            wenn not chars and wrap:
                wrapped = 1
                wrap = 0
                line = 1
                chars = text.get("1.0", "2.0")
        return Nichts

    def search_backward(self, text, prog, line, col, wrap, ok=0):
        wrapped = 0
        startline = line
        chars = text.get("%d.0" % line, "%d.0" % (line+1))
        while Wahr:
            m = search_reverse(prog, chars[:-1], col)
            wenn m:
                wenn ok or m.start() < col:
                    return line, m
            line = line - 1
            wenn wrapped and line < startline:
                break
            ok = 1
            wenn line <= 0:
                wenn not wrap:
                    break
                wrapped = 1
                wrap = 0
                pos = text.index("end-1c")
                line, col = map(int, pos.split("."))
            chars = text.get("%d.0" % line, "%d.0" % (line+1))
            col = len(chars) - 1
        return Nichts


def search_reverse(prog, chars, col):
    '''Search backwards and return an re match object or Nichts.

    This is done by searching forwards until there is no match.
    Prog: compiled re object with a search method returning a match.
    Chars: line of text, without \\n.
    Col: stop index fuer the search; the limit fuer match.end().
    '''
    m = prog.search(chars)
    wenn not m:
        return Nichts
    found = Nichts
    i, j = m.span()  # m.start(), m.end() == match slice indexes
    while i < col and j <= col:
        found = m
        wenn i == j:
            j = j+1
        m = prog.search(chars, j)
        wenn not m:
            break
        i, j = m.span()
    return found

def get_selection(text):
    '''Return tuple of 'line.col' indexes from selection or insert mark.
    '''
    try:
        first = text.index("sel.first")
        last = text.index("sel.last")
    except TclError:
        first = last = Nichts
    wenn not first:
        first = text.index("insert")
    wenn not last:
        last = first
    return first, last

def get_line_col(index):
    '''Return (line, col) tuple of ints from 'line.col' string.'''
    line, col = map(int, index.split(".")) # Fails on invalid index
    return line, col


wenn __name__ == "__main__":
    from unittest import main
    main('idlelib.idle_test.test_searchengine', verbosity=2)
