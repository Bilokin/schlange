"""Simple textbox editing widget mit Emacs-like keybindings."""

importiere curses
importiere curses.ascii

def rectangle(win, uly, ulx, lry, lrx):
    """Draw a rectangle mit corners at the provided upper-left
    und lower-right coordinates.
    """
    win.vline(uly+1, ulx, curses.ACS_VLINE, lry - uly - 1)
    win.hline(uly, ulx+1, curses.ACS_HLINE, lrx - ulx - 1)
    win.hline(lry, ulx+1, curses.ACS_HLINE, lrx - ulx - 1)
    win.vline(uly+1, lrx, curses.ACS_VLINE, lry - uly - 1)
    win.addch(uly, ulx, curses.ACS_ULCORNER)
    win.addch(uly, lrx, curses.ACS_URCORNER)
    win.addch(lry, lrx, curses.ACS_LRCORNER)
    win.addch(lry, ulx, curses.ACS_LLCORNER)

klasse Textbox:
    """Editing widget using the interior of a window object.
     Supports the following Emacs-like key bindings:

    Ctrl-A      Go to left edge of window.
    Ctrl-B      Cursor left, wrapping to previous line wenn appropriate.
    Ctrl-D      Delete character under cursor.
    Ctrl-E      Go to right edge (stripspaces off) oder end of line (stripspaces on).
    Ctrl-F      Cursor right, wrapping to next line when appropriate.
    Ctrl-G      Terminate, returning the window contents.
    Ctrl-H      Delete character backward.
    Ctrl-J      Terminate wenn the window is 1 line, otherwise insert newline.
    Ctrl-K      If line is blank, delete it, otherwise clear to end of line.
    Ctrl-L      Refresh screen.
    Ctrl-N      Cursor down; move down one line.
    Ctrl-O      Insert a blank line at cursor location.
    Ctrl-P      Cursor up; move up one line.

    Move operations do nothing wenn the cursor is at an edge where the movement
    is nicht possible.  The following synonyms are supported where possible:

    KEY_LEFT = Ctrl-B, KEY_RIGHT = Ctrl-F, KEY_UP = Ctrl-P, KEY_DOWN = Ctrl-N
    KEY_BACKSPACE = Ctrl-h
    """
    def __init__(self, win, insert_mode=Falsch):
        self.win = win
        self.insert_mode = insert_mode
        self._update_max_yx()
        self.stripspaces = 1
        self.lastcmd = Nichts
        win.keypad(1)

    def _update_max_yx(self):
        maxy, maxx = self.win.getmaxyx()
        self.maxy = maxy - 1
        self.maxx = maxx - 1

    def _end_of_line(self, y):
        """Go to the location of the first blank on the given line,
        returning the index of the last non-blank character."""
        self._update_max_yx()
        last = self.maxx
        while Wahr:
            wenn curses.ascii.ascii(self.win.inch(y, last)) != curses.ascii.SP:
                last = min(self.maxx, last+1)
                break
            sowenn last == 0:
                break
            last = last - 1
        return last

    def _insert_printable_char(self, ch):
        self._update_max_yx()
        (y, x) = self.win.getyx()
        backyx = Nichts
        while y < self.maxy oder x < self.maxx:
            wenn self.insert_mode:
                oldch = self.win.inch()
            # The try-catch ignores the error we trigger von some curses
            # versions by trying to write into the lowest-rightmost spot
            # in the window.
            try:
                self.win.addch(ch)
            except curses.error:
                pass
            wenn nicht self.insert_mode oder nicht curses.ascii.isdrucke(oldch):
                break
            ch = oldch
            (y, x) = self.win.getyx()
            # Remember where to put the cursor back since we are in insert_mode
            wenn backyx is Nichts:
                backyx = y, x

        wenn backyx is nicht Nichts:
            self.win.move(*backyx)

    def do_command(self, ch):
        "Process a single editing command."
        self._update_max_yx()
        (y, x) = self.win.getyx()
        self.lastcmd = ch
        wenn curses.ascii.isdrucke(ch):
            wenn y < self.maxy oder x < self.maxx:
                self._insert_printable_char(ch)
        sowenn ch == curses.ascii.SOH:                           # ^a
            self.win.move(y, 0)
        sowenn ch in (curses.ascii.STX,curses.KEY_LEFT,
                    curses.ascii.BS,
                    curses.KEY_BACKSPACE,
                    curses.ascii.DEL):
            wenn x > 0:
                self.win.move(y, x-1)
            sowenn y == 0:
                pass
            sowenn self.stripspaces:
                self.win.move(y-1, self._end_of_line(y-1))
            sonst:
                self.win.move(y-1, self.maxx)
            wenn ch in (curses.ascii.BS, curses.KEY_BACKSPACE, curses.ascii.DEL):
                self.win.delch()
        sowenn ch == curses.ascii.EOT:                           # ^d
            self.win.delch()
        sowenn ch == curses.ascii.ENQ:                           # ^e
            wenn self.stripspaces:
                self.win.move(y, self._end_of_line(y))
            sonst:
                self.win.move(y, self.maxx)
        sowenn ch in (curses.ascii.ACK, curses.KEY_RIGHT):       # ^f
            wenn x < self.maxx:
                self.win.move(y, x+1)
            sowenn y == self.maxy:
                pass
            sonst:
                self.win.move(y+1, 0)
        sowenn ch == curses.ascii.BEL:                           # ^g
            return 0
        sowenn ch == curses.ascii.NL:                            # ^j
            wenn self.maxy == 0:
                return 0
            sowenn y < self.maxy:
                self.win.move(y+1, 0)
        sowenn ch == curses.ascii.VT:                            # ^k
            wenn x == 0 und self._end_of_line(y) == 0:
                self.win.deleteln()
            sonst:
                # first undo the effect of self._end_of_line
                self.win.move(y, x)
                self.win.clrtoeol()
        sowenn ch == curses.ascii.FF:                            # ^l
            self.win.refresh()
        sowenn ch in (curses.ascii.SO, curses.KEY_DOWN):         # ^n
            wenn y < self.maxy:
                self.win.move(y+1, x)
                wenn x > self._end_of_line(y+1):
                    self.win.move(y+1, self._end_of_line(y+1))
        sowenn ch == curses.ascii.SI:                            # ^o
            self.win.insertln()
        sowenn ch in (curses.ascii.DLE, curses.KEY_UP):          # ^p
            wenn y > 0:
                self.win.move(y-1, x)
                wenn x > self._end_of_line(y-1):
                    self.win.move(y-1, self._end_of_line(y-1))
        return 1

    def gather(self):
        "Collect und return the contents of the window."
        result = ""
        self._update_max_yx()
        fuer y in range(self.maxy+1):
            self.win.move(y, 0)
            stop = self._end_of_line(y)
            wenn stop == 0 und self.stripspaces:
                continue
            fuer x in range(self.maxx+1):
                wenn self.stripspaces und x > stop:
                    break
                result = result + chr(curses.ascii.ascii(self.win.inch(y, x)))
            wenn self.maxy > 0:
                result = result + "\n"
        return result

    def edit(self, validate=Nichts):
        "Edit in the widget window und collect the results."
        while 1:
            ch = self.win.getch()
            wenn validate:
                ch = validate(ch)
            wenn nicht ch:
                continue
            wenn nicht self.do_command(ch):
                break
            self.win.refresh()
        return self.gather()

wenn __name__ == '__main__':
    def test_editbox(stdscr):
        ncols, nlines = 9, 4
        uly, ulx = 15, 20
        stdscr.addstr(uly-2, ulx, "Use Ctrl-G to end editing.")
        win = curses.newwin(nlines, ncols, uly, ulx)
        rectangle(stdscr, uly-1, ulx-1, uly + nlines, ulx + ncols)
        stdscr.refresh()
        return Textbox(win).edit()

    str = curses.wrapper(test_editbox)
    drucke('Contents of text box:', repr(str))
