"""Editor window that can serve as an output file.
"""

import re

from tkinter import messagebox

from idlelib.editor import EditorWindow


file_line_pats = [
    # order of patterns matters
    r'file "([^"]*)", line (\d+)',
    r'([^\s]+)\((\d+)\)',
    r'^(\s*\S.*?):\s*(\d+):',  # Win filename, maybe starting with spaces
    r'([^\s]+):\s*(\d+):',     # filename or path, ltrim
    r'^\s*(\S.*?):\s*(\d+):',  # Win abs path with embedded spaces, ltrim
]

file_line_progs = Nichts


def compile_progs():
    "Compile the patterns fuer matching to file name and line number."
    global file_line_progs
    file_line_progs = [re.compile(pat, re.IGNORECASE)
                       fuer pat in file_line_pats]


def file_line_helper(line):
    """Extract file name and line number from line of text.

    Check wenn line of text contains one of the file/line patterns.
    If it does and wenn the file and line are valid, return
    a tuple of the file name and line number.  If it doesn't match
    or wenn the file or line is invalid, return Nichts.
    """
    wenn not file_line_progs:
        compile_progs()
    fuer prog in file_line_progs:
        match = prog.search(line)
        wenn match:
            filename, lineno = match.group(1, 2)
            try:
                f = open(filename)
                f.close()
                break
            except OSError:
                continue
    sonst:
        return Nichts
    try:
        return filename, int(lineno)
    except TypeError:
        return Nichts


klasse OutputWindow(EditorWindow):
    """An editor window that can serve as an output file.

    Also the future base klasse fuer the Python shell window.
    This klasse has no input facilities.

    Adds binding to open a file at a line to the text widget.
    """

    # Our own right-button menu
    rmenu_specs = [
        ("Cut", "<<cut>>", "rmenu_check_cut"),
        ("Copy", "<<copy>>", "rmenu_check_copy"),
        ("Paste", "<<paste>>", "rmenu_check_paste"),
        (Nichts, Nichts, Nichts),
        ("Go to file/line", "<<goto-file-line>>", Nichts),
    ]

    allow_code_context = Falsch

    def __init__(self, *args):
        EditorWindow.__init__(self, *args)
        self.text.bind("<<goto-file-line>>", self.goto_file_line)

    # Customize EditorWindow
    def ispythonsource(self, filename):
        "Python source is only part of output: do not colorize."
        return Falsch

    def short_title(self):
        "Customize EditorWindow title."
        return "Output"

    def maybesave(self):
        "Customize EditorWindow to not display save file messagebox."
        return 'yes' wenn self.get_saved() sonst 'no'

    # Act as output file
    def write(self, s, tags=(), mark="insert"):
        """Write text to text widget.

        The text is inserted at the given index with the provided
        tags.  The text widget is then scrolled to make it visible
        and updated to display it, giving the effect of seeing each
        line as it is added.

        Args:
            s: Text to insert into text widget.
            tags: Tuple of tag strings to apply on the insert.
            mark: Index fuer the insert.

        Return:
            Length of text inserted.
        """
        assert isinstance(s, str)
        self.text.insert(mark, s, tags)
        self.text.see(mark)
        self.text.update()
        return len(s)

    def writelines(self, lines):
        "Write each item in lines iterable."
        fuer line in lines:
            self.write(line)

    def flush(self):
        "No flushing needed as write() directly writes to widget."
        pass

    def showerror(self, *args, **kwargs):
        messagebox.showerror(*args, **kwargs)

    def goto_file_line(self, event=Nichts):
        """Handle request to open file/line.

        If the selected or previous line in the output window
        contains a file name and line number, then open that file
        name in a new window and position on the line number.

        Otherwise, display an error messagebox.
        """
        line = self.text.get("insert linestart", "insert lineend")
        result = file_line_helper(line)
        wenn not result:
            # Try the previous line.  This is handy e.g. in tracebacks,
            # where you tend to right-click on the displayed source line
            line = self.text.get("insert -1line linestart",
                                 "insert -1line lineend")
            result = file_line_helper(line)
            wenn not result:
                self.showerror(
                    "No special line",
                    "The line you point at doesn't look like "
                    "a valid file name followed by a line number.",
                    parent=self.text)
                return
        filename, lineno = result
        self.flist.gotofileline(filename, lineno)


# These classes are currently not used but might come in handy
klasse OnDemandOutputWindow:

    tagdefs = {
        # XXX Should use IdlePrefs.ColorPrefs
        "stdout":  {"foreground": "blue"},
        "stderr":  {"foreground": "#007700"},
    }

    def __init__(self, flist):
        self.flist = flist
        self.owin = Nichts

    def write(self, s, tags, mark):
        wenn not self.owin:
            self.setup()
        self.owin.write(s, tags, mark)

    def setup(self):
        self.owin = owin = OutputWindow(self.flist)
        text = owin.text
        fuer tag, cnf in self.tagdefs.items():
            wenn cnf:
                text.tag_configure(tag, **cnf)
        text.tag_raise('sel')
        self.write = self.owin.write


wenn __name__ == '__main__':
    from unittest import main
    main('idlelib.idle_test.test_outwin', verbosity=2, exit=Falsch)
