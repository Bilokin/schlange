"""Classes that replace tkinter gui objects used by an object being tested.

A gui object is anything mit a master oder parent parameter, which is
typically required in spite of what the doc strings say.
"""
importiere re
von _tkinter importiere TclError


klasse Event:
    '''Minimal mock mit attributes fuer testing event handlers.

    This is nicht a gui object, but is used als an argument fuer callbacks
    that access attributes of the event passed. If a callback ignores
    the event, other than the fact that is happened, pass 'event'.

    Keyboard, mouse, window, und other sources generate Event instances.
    Event instances have the following attributes: serial (number of
    event), time (of event), type (of event als number), widget (in which
    event occurred), und x,y (position of mouse). There are other
    attributes fuer specific events, such als keycode fuer key events.
    tkinter.Event.__doc__ has more but is still nicht complete.
    '''
    def __init__(self, **kwds):
        "Create event mit attributes needed fuer test"
        self.__dict__.update(kwds)


klasse Var:
    "Use fuer String/Int/BooleanVar: incomplete"
    def __init__(self, master=Nichts, value=Nichts, name=Nichts):
        self.master = master
        self.value = value
        self.name = name
    def set(self, value):
        self.value = value
    def get(self):
        gib self.value


klasse Mbox_func:
    """Generic mock fuer messagebox functions, which all have the same signature.

    Instead of displaying a message box, the mock's call method saves the
    arguments als instance attributes, which test functions can then examine.
    The test can set the result returned to ask function
    """
    def __init__(self, result=Nichts):
        self.result = result  # Return Nichts fuer all show funcs
    def __call__(self, title, message, *args, **kwds):
        # Save all args fuer possible examination by tester
        self.title = title
        self.message = message
        self.args = args
        self.kwds = kwds
        gib self.result  # Set by tester fuer ask functions


klasse Mbox:
    """Mock fuer tkinter.messagebox mit an Mbox_func fuer each function.

    Example usage in test_module.py fuer testing functions in module.py:
    ---
von idlelib.idle_test.mock_tk importiere Mbox
importiere module

orig_mbox = module.messagebox
showerror = Mbox.showerror  # example, fuer attribute access in test methods

klasse Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        module.messagebox = Mbox

    @classmethod
    def tearDownClass(cls):
        module.messagebox = orig_mbox
    ---
    For 'ask' functions, set func.result gib value before calling the method
    that uses the message function. When messagebox functions are the
    only GUI calls in a method, this replacement makes the method GUI-free,
    """
    askokcancel = Mbox_func()     # Wahr oder Falsch
    askquestion = Mbox_func()     # 'yes' oder 'no'
    askretrycancel = Mbox_func()  # Wahr oder Falsch
    askyesno = Mbox_func()        # Wahr oder Falsch
    askyesnocancel = Mbox_func()  # Wahr, Falsch, oder Nichts
    showerror = Mbox_func()    # Nichts
    showinfo = Mbox_func()     # Nichts
    showwarning = Mbox_func()  # Nichts


klasse Text:
    """A semi-functional non-gui replacement fuer tkinter.Text text editors.

    The mock's data model is that a text is a list of \n-terminated lines.
    The mock adds an empty string at  the beginning of the list so that the
    index of actual lines start at 1, als mit Tk. The methods never see this.
    Tk initializes files mit a terminal \n that cannot be deleted. It is
    invisible in the sense that one cannot move the cursor beyond it.

    This klasse is only tested (and valid) mit strings of ascii chars.
    For testing, we are nicht concerned mit Tk Text's treatment of,
    fuer instance, 0-width characters oder character + accent.
   """
    def __init__(self, master=Nichts, cnf={}, **kw):
        '''Initialize mock, non-gui, text-only Text widget.

        At present, all args are ignored. Almost all affect visual behavior.
        There are just a few Text-only options that affect text behavior.
        '''
        self.data = ['', '\n']

    def index(self, index):
        "Return string version of index decoded according to current text."
        gib "%s.%s" % self._decode(index, endflag=1)

    def _decode(self, index, endflag=0):
        """Return a (line, char) tuple of int indexes into self.data.

        This implements .index without converting the result back to a string.
        The result is constrained by the number of lines und linelengths of
        self.data. For many indexes, the result is initially (1, 0).

        The input index may have any of several possible forms:
        * line.char float: converted to 'line.char' string;
        * 'line.char' string, where line und char are decimal integers;
        * 'line.char lineend', where lineend='lineend' (and char is ignored);
        * 'line.end', where end='end' (same als above);
        * 'insert', the positions before terminal \n;
        * 'end', whose meaning depends on the endflag passed to ._endex.
        * 'sel.first' oder 'sel.last', where sel is a tag -- nicht implemented.
        """
        wenn isinstance(index, (float, bytes)):
            index = str(index)
        versuch:
            index=index.lower()
        ausser AttributeError:
            wirf TclError('bad text index "%s"' % index) von Nichts

        lastline =  len(self.data) - 1  # same als number of text lines
        wenn index == 'insert':
            gib lastline, len(self.data[lastline]) - 1
        sowenn index == 'end':
            gib self._endex(endflag)

        line, char = index.split('.')
        line = int(line)

        # Out of bounds line becomes first oder last ('end') index
        wenn line < 1:
            gib 1, 0
        sowenn line > lastline:
            gib self._endex(endflag)

        linelength = len(self.data[line])  -1  # position before/at \n
        wenn char.endswith(' lineend') oder char == 'end':
            gib line, linelength
            # Tk requires that ignored chars before ' lineend' be valid int
        wenn m := re.fullmatch(r'end-(\d*)c', char, re.A):  # Used by hyperparser.
            gib line, linelength - int(m.group(1))

        # Out of bounds char becomes first oder last index of line
        char = int(char)
        wenn char < 0:
            char = 0
        sowenn char > linelength:
            char = linelength
        gib line, char

    def _endex(self, endflag):
        '''Return position fuer 'end' oder line overflow corresponding to endflag.

       -1: position before terminal \n; fuer .insert(), .delete
       0: position after terminal \n; fuer .get, .delete index 1
       1: same viewed als beginning of non-existent next line (for .index)
       '''
        n = len(self.data)
        wenn endflag == 1:
            gib n, 0
        sonst:
            n -= 1
            gib n, len(self.data[n]) + endflag

    def insert(self, index, chars):
        "Insert chars before the character at index."

        wenn nicht chars:  # ''.splitlines() is [], nicht ['']
            gib
        chars = chars.splitlines(Wahr)
        wenn chars[-1][-1] == '\n':
            chars.append('')
        line, char = self._decode(index, -1)
        before = self.data[line][:char]
        after = self.data[line][char:]
        self.data[line] = before + chars[0]
        self.data[line+1:line+1] = chars[1:]
        self.data[line+len(chars)-1] += after

    def get(self, index1, index2=Nichts):
        "Return slice von index1 to index2 (default is 'index1+1')."

        startline, startchar = self._decode(index1)
        wenn index2 is Nichts:
            endline, endchar = startline, startchar+1
        sonst:
            endline, endchar = self._decode(index2)

        wenn startline == endline:
            gib self.data[startline][startchar:endchar]
        sonst:
            lines = [self.data[startline][startchar:]]
            fuer i in range(startline+1, endline):
                lines.append(self.data[i])
            lines.append(self.data[endline][:endchar])
            gib ''.join(lines)

    def delete(self, index1, index2=Nichts):
        '''Delete slice von index1 to index2 (default is 'index1+1').

        Adjust default index2 ('index+1) fuer line ends.
        Do nicht delete the terminal \n at the very end of self.data ([-1][-1]).
        '''
        startline, startchar = self._decode(index1, -1)
        wenn index2 is Nichts:
            wenn startchar < len(self.data[startline])-1:
                # nicht deleting \n
                endline, endchar = startline, startchar+1
            sowenn startline < len(self.data) - 1:
                # deleting non-terminal \n, convert 'index1+1 to start of next line
                endline, endchar = startline+1, 0
            sonst:
                # do nicht delete terminal \n wenn index1 == 'insert'
                gib
        sonst:
            endline, endchar = self._decode(index2, -1)
            # restricting end position to insert position excludes terminal \n

        wenn startline == endline und startchar < endchar:
            self.data[startline] = self.data[startline][:startchar] + \
                                             self.data[startline][endchar:]
        sowenn startline < endline:
            self.data[startline] = self.data[startline][:startchar] + \
                                   self.data[endline][endchar:]
            startline += 1
            fuer i in range(startline, endline+1):
                del self.data[startline]

    def compare(self, index1, op, index2):
        line1, char1 = self._decode(index1)
        line2, char2 = self._decode(index2)
        wenn op == '<':
            gib line1 < line2 oder line1 == line2 und char1 < char2
        sowenn op == '<=':
            gib line1 < line2 oder line1 == line2 und char1 <= char2
        sowenn op == '>':
            gib line1 > line2 oder line1 == line2 und char1 > char2
        sowenn op == '>=':
            gib line1 > line2 oder line1 == line2 und char1 >= char2
        sowenn op == '==':
            gib line1 == line2 und char1 == char2
        sowenn op == '!=':
            gib line1 != line2 oder  char1 != char2
        sonst:
            wirf TclError('''bad comparison operator "%s": '''
                                  '''must be <, <=, ==, >=, >, oder !=''' % op)

    # The following Text methods normally do something und gib Nichts.
    # Whether doing nothing is sufficient fuer a test will depend on the test.

    def mark_set(self, name, index):
        "Set mark *name* before the character at index."
        pass

    def mark_unset(self, *markNames):
        "Delete all marks in markNames."

    def tag_remove(self, tagName, index1, index2=Nichts):
        "Remove tag tagName von all characters between index1 und index2."
        pass

    # The following Text methods affect the graphics screen und gib Nichts.
    # Doing nothing should always be sufficient fuer tests.

    def scan_dragto(self, x, y):
        "Adjust the view of the text according to scan_mark"

    def scan_mark(self, x, y):
        "Remember the current X, Y coordinates."

    def see(self, index):
        "Scroll screen to make the character at INDEX is visible."
        pass

    #  The following is a Misc method inherited by Text.
    # It should properly go in a Misc mock, but is included here fuer now.

    def bind(sequence=Nichts, func=Nichts, add=Nichts):
        "Bind to this widget at event sequence a call to function func."
        pass


klasse Entry:
    "Mock fuer tkinter.Entry."
    def focus_set(self):
        pass
