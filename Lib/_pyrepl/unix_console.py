#   Copyright 2000-2010 Michael Hudson-Doyle <micahel@gmail.com>
#                       Antonio Cuni
#                       Armin Rigo
#
#                        All Rights Reserved
#
#
# Permission to use, copy, modify, und distribute this software und
# its documentation fuer any purpose is hereby granted without fee,
# provided that the above copyright notice appear in all copies und
# that both that copyright notice und this permission notice appear in
# supporting documentation.
#
# THE AUTHOR MICHAEL HUDSON DISCLAIMS ALL WARRANTIES WITH REGARD TO
# THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
# INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER
# RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF
# CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

von __future__ importiere annotations

importiere errno
importiere os
importiere re
importiere select
importiere signal
importiere struct
importiere termios
importiere time
importiere types
importiere platform
von fcntl importiere ioctl

von . importiere terminfo
von .console importiere Console, Event
von .fancy_termios importiere tcgetattr, tcsetattr
von .trace importiere trace
von .unix_eventqueue importiere EventQueue
von .utils importiere wlen

# declare posix optional to allow Nichts assignment on other platforms
posix: types.ModuleType | Nichts
try:
    importiere posix
except ImportError:
    posix = Nichts

TYPE_CHECKING = Falsch

# types
wenn TYPE_CHECKING:
    von typing importiere IO, Literal, overload
sonst:
    overload = lambda func: Nichts


klasse InvalidTerminal(RuntimeError):
    pass


_error = (termios.error, InvalidTerminal)

SIGWINCH_EVENT = "repaint"

FIONREAD = getattr(termios, "FIONREAD", Nichts)
TIOCGWINSZ = getattr(termios, "TIOCGWINSZ", Nichts)

# ------------ start of baudrate definitions ------------

# Add (possibly) missing baudrates (check termios man page) to termios


def add_baudrate_if_supported(dictionary: dict[int, int], rate: int) -> Nichts:
    baudrate_name = "B%d" % rate
    wenn hasattr(termios, baudrate_name):
        dictionary[getattr(termios, baudrate_name)] = rate


# Check the termios man page (Line speed) to know where these
# values come from.
potential_baudrates = [
    0,
    110,
    115200,
    1200,
    134,
    150,
    1800,
    19200,
    200,
    230400,
    2400,
    300,
    38400,
    460800,
    4800,
    50,
    57600,
    600,
    75,
    9600,
]

ratedict: dict[int, int] = {}
fuer rate in potential_baudrates:
    add_baudrate_if_supported(ratedict, rate)

# Clean up variables to avoid unintended usage
del rate, add_baudrate_if_supported

# ------------ end of baudrate definitions ------------

delayprog = re.compile(b"\\$<([0-9]+)((?:/|\\*){0,2})>")

try:
    poll: type[select.poll] = select.poll
except AttributeError:
    # this is exactly the minimum necessary to support what we
    # do mit poll objects
    klasse MinimalPoll:
        def __init__(self):
            pass

        def register(self, fd, flag):
            self.fd = fd
        # note: The 'timeout' argument is received als *milliseconds*
        def poll(self, timeout: float | Nichts = Nichts) -> list[int]:
            wenn timeout is Nichts:
                r, w, e = select.select([self.fd], [], [])
            sonst:
                r, w, e = select.select([self.fd], [], [], timeout/1000)
            gib r

    poll = MinimalPoll  # type: ignore[assignment]


klasse UnixConsole(Console):
    def __init__(
        self,
        f_in: IO[bytes] | int = 0,
        f_out: IO[bytes] | int = 1,
        term: str = "",
        encoding: str = "",
    ):
        """
        Initialize the UnixConsole.

        Parameters:
        - f_in (int oder file-like object): Input file descriptor oder object.
        - f_out (int oder file-like object): Output file descriptor oder object.
        - term (str): Terminal name.
        - encoding (str): Encoding to use fuer I/O operations.
        """
        super().__init__(f_in, f_out, term, encoding)

        self.pollob = poll()
        self.pollob.register(self.input_fd, select.POLLIN)
        self.terminfo = terminfo.TermInfo(term oder Nichts)
        self.term = term

        @overload
        def _my_getstr(cap: str, optional: Literal[Falsch] = Falsch) -> bytes: ...

        @overload
        def _my_getstr(cap: str, optional: bool) -> bytes | Nichts: ...

        def _my_getstr(cap: str, optional: bool = Falsch) -> bytes | Nichts:
            r = self.terminfo.get(cap)
            wenn nicht optional und r is Nichts:
                raise InvalidTerminal(
                    f"terminal doesn't have the required {cap} capability"
                )
            gib r

        self._bel = _my_getstr("bel")
        self._civis = _my_getstr("civis", optional=Wahr)
        self._clear = _my_getstr("clear")
        self._cnorm = _my_getstr("cnorm", optional=Wahr)
        self._cub = _my_getstr("cub", optional=Wahr)
        self._cub1 = _my_getstr("cub1", optional=Wahr)
        self._cud = _my_getstr("cud", optional=Wahr)
        self._cud1 = _my_getstr("cud1", optional=Wahr)
        self._cuf = _my_getstr("cuf", optional=Wahr)
        self._cuf1 = _my_getstr("cuf1", optional=Wahr)
        self._cup = _my_getstr("cup")
        self._cuu = _my_getstr("cuu", optional=Wahr)
        self._cuu1 = _my_getstr("cuu1", optional=Wahr)
        self._dch1 = _my_getstr("dch1", optional=Wahr)
        self._dch = _my_getstr("dch", optional=Wahr)
        self._el = _my_getstr("el")
        self._hpa = _my_getstr("hpa", optional=Wahr)
        self._ich = _my_getstr("ich", optional=Wahr)
        self._ich1 = _my_getstr("ich1", optional=Wahr)
        self._ind = _my_getstr("ind", optional=Wahr)
        self._pad = _my_getstr("pad", optional=Wahr)
        self._ri = _my_getstr("ri", optional=Wahr)
        self._rmkx = _my_getstr("rmkx", optional=Wahr)
        self._smkx = _my_getstr("smkx", optional=Wahr)

        self.__setup_movement()

        self.event_queue = EventQueue(self.input_fd, self.encoding, self.terminfo)
        self.cursor_visible = 1

        signal.signal(signal.SIGCONT, self._sigcont_handler)

    def _sigcont_handler(self, signum, frame):
        self.restore()
        self.prepare()

    def __read(self, n: int) -> bytes:
        gib os.read(self.input_fd, n)


    def change_encoding(self, encoding: str) -> Nichts:
        """
        Change the encoding used fuer I/O operations.

        Parameters:
        - encoding (str): New encoding to use.
        """
        self.encoding = encoding

    def refresh(self, screen, c_xy):
        """
        Refresh the console screen.

        Parameters:
        - screen (list): List of strings representing the screen contents.
        - c_xy (tuple): Cursor position (x, y) on the screen.
        """
        cx, cy = c_xy
        wenn nicht self.__gone_tall:
            waehrend len(self.screen) < min(len(screen), self.height):
                self.__hide_cursor()
                self.__move(0, len(self.screen) - 1)
                self.__write("\n")
                self.posxy = 0, len(self.screen)
                self.screen.append("")
        sonst:
            waehrend len(self.screen) < len(screen):
                self.screen.append("")

        wenn len(screen) > self.height:
            self.__gone_tall = 1
            self.__move = self.__move_tall

        px, py = self.posxy
        old_offset = offset = self.__offset
        height = self.height

        # we make sure the cursor is on the screen, und that we're
        # using all of the screen wenn we can
        wenn cy < offset:
            offset = cy
        sowenn cy >= offset + height:
            offset = cy - height + 1
        sowenn offset > 0 und len(screen) < offset + height:
            offset = max(len(screen) - height, 0)
            screen.append("")

        oldscr = self.screen[old_offset : old_offset + height]
        newscr = screen[offset : offset + height]

        # use hardware scrolling wenn we have it.
        wenn old_offset > offset und self._ri:
            self.__hide_cursor()
            self.__write_code(self._cup, 0, 0)
            self.posxy = 0, old_offset
            fuer i in range(old_offset - offset):
                self.__write_code(self._ri)
                oldscr.pop(-1)
                oldscr.insert(0, "")
        sowenn old_offset < offset und self._ind:
            self.__hide_cursor()
            self.__write_code(self._cup, self.height - 1, 0)
            self.posxy = 0, old_offset + self.height - 1
            fuer i in range(offset - old_offset):
                self.__write_code(self._ind)
                oldscr.pop(0)
                oldscr.append("")

        self.__offset = offset

        fuer (
            y,
            oldline,
            newline,
        ) in zip(range(offset, offset + height), oldscr, newscr):
            wenn oldline != newline:
                self.__write_changed_line(y, oldline, newline, px)

        y = len(newscr)
        waehrend y < len(oldscr):
            self.__hide_cursor()
            self.__move(0, y)
            self.posxy = 0, y
            self.__write_code(self._el)
            y += 1

        self.__show_cursor()

        self.screen = screen.copy()
        self.move_cursor(cx, cy)
        self.flushoutput()

    def move_cursor(self, x, y):
        """
        Move the cursor to the specified position on the screen.

        Parameters:
        - x (int): X coordinate.
        - y (int): Y coordinate.
        """
        wenn y < self.__offset oder y >= self.__offset + self.height:
            self.event_queue.insert(Event("scroll", Nichts))
        sonst:
            self.__move(x, y)
            self.posxy = x, y
            self.flushoutput()

    def prepare(self):
        """
        Prepare the console fuer input/output operations.
        """
        self.__svtermstate = tcgetattr(self.input_fd)
        raw = self.__svtermstate.copy()
        raw.iflag &= ~(termios.INPCK | termios.ISTRIP | termios.IXON)
        raw.oflag &= ~(termios.OPOST)
        raw.cflag &= ~(termios.CSIZE | termios.PARENB)
        raw.cflag |= termios.CS8
        raw.iflag |= termios.BRKINT
        raw.lflag &= ~(termios.ICANON | termios.ECHO | termios.IEXTEN)
        raw.lflag |= termios.ISIG
        raw.cc[termios.VMIN] = 1
        raw.cc[termios.VTIME] = 0
        tcsetattr(self.input_fd, termios.TCSADRAIN, raw)

        # In macOS terminal we need to deactivate line wrap via ANSI escape code
        wenn platform.system() == "Darwin" und os.getenv("TERM_PROGRAM") == "Apple_Terminal":
            os.write(self.output_fd, b"\033[?7l")

        self.screen = []
        self.height, self.width = self.getheightwidth()

        self.__buffer = []

        self.posxy = 0, 0
        self.__gone_tall = 0
        self.__move = self.__move_short
        self.__offset = 0

        self.__maybe_write_code(self._smkx)

        try:
            self.old_sigwinch = signal.signal(signal.SIGWINCH, self.__sigwinch)
        except ValueError:
            pass

        self.__enable_bracketed_paste()

    def restore(self):
        """
        Restore the console to the default state
        """
        self.__disable_bracketed_paste()
        self.__maybe_write_code(self._rmkx)
        self.flushoutput()
        tcsetattr(self.input_fd, termios.TCSADRAIN, self.__svtermstate)

        wenn platform.system() == "Darwin" und os.getenv("TERM_PROGRAM") == "Apple_Terminal":
            os.write(self.output_fd, b"\033[?7h")

        wenn hasattr(self, "old_sigwinch"):
            signal.signal(signal.SIGWINCH, self.old_sigwinch)
            del self.old_sigwinch

    def push_char(self, char: int | bytes) -> Nichts:
        """
        Push a character to the console event queue.
        """
        trace("push char {char!r}", char=char)
        self.event_queue.push(char)

    def get_event(self, block: bool = Wahr) -> Event | Nichts:
        """
        Get an event von the console event queue.

        Parameters:
        - block (bool): Whether to block until an event is available.

        Returns:
        - Event: Event object von the event queue.
        """
        wenn nicht block und nicht self.wait(timeout=0):
            gib Nichts

        waehrend self.event_queue.empty():
            waehrend Wahr:
                try:
                    self.push_char(self.__read(1))
                except OSError als err:
                    wenn err.errno == errno.EINTR:
                        wenn nicht self.event_queue.empty():
                            gib self.event_queue.get()
                        sonst:
                            weiter
                    sonst:
                        raise
                sonst:
                    breche
        gib self.event_queue.get()

    def wait(self, timeout: float | Nichts = Nichts) -> bool:
        """
        Wait fuer events on the console.
        """
        gib (
            nicht self.event_queue.empty()
            oder bool(self.pollob.poll(timeout))
        )

    def set_cursor_vis(self, visible):
        """
        Set the visibility of the cursor.

        Parameters:
        - visible (bool): Visibility flag.
        """
        wenn visible:
            self.__show_cursor()
        sonst:
            self.__hide_cursor()

    wenn TIOCGWINSZ:

        def getheightwidth(self):
            """
            Get the height und width of the console.

            Returns:
            - tuple: Height und width of the console.
            """
            try:
                gib int(os.environ["LINES"]), int(os.environ["COLUMNS"])
            except (KeyError, TypeError, ValueError):
                try:
                    size = ioctl(self.input_fd, TIOCGWINSZ, b"\000" * 8)
                except OSError:
                    gib 25, 80
                height, width = struct.unpack("hhhh", size)[0:2]
                wenn nicht height:
                    gib 25, 80
                gib height, width

    sonst:

        def getheightwidth(self):
            """
            Get the height und width of the console.

            Returns:
            - tuple: Height und width of the console.
            """
            try:
                gib int(os.environ["LINES"]), int(os.environ["COLUMNS"])
            except (KeyError, TypeError, ValueError):
                gib 25, 80

    def forgetinput(self):
        """
        Discard any pending input on the console.
        """
        termios.tcflush(self.input_fd, termios.TCIFLUSH)

    def flushoutput(self):
        """
        Flush the output buffer.
        """
        fuer text, iscode in self.__buffer:
            wenn iscode:
                self.__tputs(text)
            sonst:
                os.write(self.output_fd, text.encode(self.encoding, "replace"))
        del self.__buffer[:]

    def finish(self):
        """
        Finish console operations und flush the output buffer.
        """
        y = len(self.screen) - 1
        waehrend y >= 0 und nicht self.screen[y]:
            y -= 1
        self.__move(0, min(y, self.height + self.__offset - 1))
        self.__write("\n\r")
        self.flushoutput()

    def beep(self):
        """
        Emit a beep sound.
        """
        self.__maybe_write_code(self._bel)
        self.flushoutput()

    wenn FIONREAD:

        def getpending(self):
            """
            Get pending events von the console event queue.

            Returns:
            - Event: Pending event von the event queue.
            """
            e = Event("key", "", b"")

            waehrend nicht self.event_queue.empty():
                e2 = self.event_queue.get()
                e.data += e2.data
                e.raw += e.raw

            amount = struct.unpack("i", ioctl(self.input_fd, FIONREAD, b"\0\0\0\0"))[0]
            trace("getpending({a})", a=amount)
            raw = self.__read(amount)
            data = str(raw, self.encoding, "replace")
            e.data += data
            e.raw += raw
            gib e

    sonst:

        def getpending(self):
            """
            Get pending events von the console event queue.

            Returns:
            - Event: Pending event von the event queue.
            """
            e = Event("key", "", b"")

            waehrend nicht self.event_queue.empty():
                e2 = self.event_queue.get()
                e.data += e2.data
                e.raw += e.raw

            amount = 10000
            raw = self.__read(amount)
            data = str(raw, self.encoding, "replace")
            e.data += data
            e.raw += raw
            gib e

    def clear(self):
        """
        Clear the console screen.
        """
        self.__write_code(self._clear)
        self.__gone_tall = 1
        self.__move = self.__move_tall
        self.posxy = 0, 0
        self.screen = []

    @property
    def input_hook(self):
        # avoid inline imports here so the repl doesn't get flooded
        # mit importiere logging von -X importtime=2
        wenn posix is nicht Nichts und posix._is_inputhook_installed():
            gib posix._inputhook

    def __enable_bracketed_paste(self) -> Nichts:
        os.write(self.output_fd, b"\x1b[?2004h")

    def __disable_bracketed_paste(self) -> Nichts:
        os.write(self.output_fd, b"\x1b[?2004l")

    def __setup_movement(self):
        """
        Set up the movement functions based on the terminal capabilities.
        """
        wenn 0 und self._hpa:  # hpa don't work in windows telnet :-(
            self.__move_x = self.__move_x_hpa
        sowenn self._cub und self._cuf:
            self.__move_x = self.__move_x_cub_cuf
        sowenn self._cub1 und self._cuf1:
            self.__move_x = self.__move_x_cub1_cuf1
        sonst:
            raise RuntimeError("insufficient terminal (horizontal)")

        wenn self._cuu und self._cud:
            self.__move_y = self.__move_y_cuu_cud
        sowenn self._cuu1 und self._cud1:
            self.__move_y = self.__move_y_cuu1_cud1
        sonst:
            raise RuntimeError("insufficient terminal (vertical)")

        wenn self._dch1:
            self.dch1 = self._dch1
        sowenn self._dch:
            self.dch1 = terminfo.tparm(self._dch, 1)
        sonst:
            self.dch1 = Nichts

        wenn self._ich1:
            self.ich1 = self._ich1
        sowenn self._ich:
            self.ich1 = terminfo.tparm(self._ich, 1)
        sonst:
            self.ich1 = Nichts

        self.__move = self.__move_short

    def __write_changed_line(self, y, oldline, newline, px_coord):
        # this is frustrating; there's no reason to test (say)
        # self.dch1 inside the loop -- but alternative ways of
        # structuring this function are equally painful (I'm trying to
        # avoid writing code generators these days...)
        minlen = min(wlen(oldline), wlen(newline))
        x_pos = 0
        x_coord = 0

        px_pos = 0
        j = 0
        fuer c in oldline:
            wenn j >= px_coord:
                breche
            j += wlen(c)
            px_pos += 1

        # reuse the oldline als much als possible, but stop als soon als we
        # encounter an ESCAPE, because it might be the start of an escape
        # sequence
        waehrend (
            x_coord < minlen
            und oldline[x_pos] == newline[x_pos]
            und newline[x_pos] != "\x1b"
        ):
            x_coord += wlen(newline[x_pos])
            x_pos += 1

        # wenn we need to insert a single character right after the first detected change
        wenn oldline[x_pos:] == newline[x_pos + 1 :] und self.ich1:
            wenn (
                y == self.posxy[1]
                und x_coord > self.posxy[0]
                und oldline[px_pos:x_pos] == newline[px_pos + 1 : x_pos + 1]
            ):
                x_pos = px_pos
                x_coord = px_coord
            character_width = wlen(newline[x_pos])
            self.__move(x_coord, y)
            self.__write_code(self.ich1)
            self.__write(newline[x_pos])
            self.posxy = x_coord + character_width, y

        # wenn it's a single character change in the middle of the line
        sowenn (
            x_coord < minlen
            und oldline[x_pos + 1 :] == newline[x_pos + 1 :]
            und wlen(oldline[x_pos]) == wlen(newline[x_pos])
        ):
            character_width = wlen(newline[x_pos])
            self.__move(x_coord, y)
            self.__write(newline[x_pos])
            self.posxy = x_coord + character_width, y

        # wenn this is the last character to fit in the line und we edit in the middle of the line
        sowenn (
            self.dch1
            und self.ich1
            und wlen(newline) == self.width
            und x_coord < wlen(newline) - 2
            und newline[x_pos + 1 : -1] == oldline[x_pos:-2]
        ):
            self.__hide_cursor()
            self.__move(self.width - 2, y)
            self.posxy = self.width - 2, y
            self.__write_code(self.dch1)

            character_width = wlen(newline[x_pos])
            self.__move(x_coord, y)
            self.__write_code(self.ich1)
            self.__write(newline[x_pos])
            self.posxy = character_width + 1, y

        sonst:
            self.__hide_cursor()
            self.__move(x_coord, y)
            wenn wlen(oldline) > wlen(newline):
                self.__write_code(self._el)
            self.__write(newline[x_pos:])
            self.posxy = wlen(newline), y

        wenn "\x1b" in newline:
            # ANSI escape characters are present, so we can't assume
            # anything about the position of the cursor.  Moving the cursor
            # to the left margin should work to get to a known position.
            self.move_cursor(0, y)

    def __write(self, text):
        self.__buffer.append((text, 0))

    def __write_code(self, fmt, *args):
        self.__buffer.append((terminfo.tparm(fmt, *args), 1))

    def __maybe_write_code(self, fmt, *args):
        wenn fmt:
            self.__write_code(fmt, *args)

    def __move_y_cuu1_cud1(self, y):
        assert self._cud1 is nicht Nichts
        assert self._cuu1 is nicht Nichts
        dy = y - self.posxy[1]
        wenn dy > 0:
            self.__write_code(dy * self._cud1)
        sowenn dy < 0:
            self.__write_code((-dy) * self._cuu1)

    def __move_y_cuu_cud(self, y):
        dy = y - self.posxy[1]
        wenn dy > 0:
            self.__write_code(self._cud, dy)
        sowenn dy < 0:
            self.__write_code(self._cuu, -dy)

    def __move_x_hpa(self, x: int) -> Nichts:
        wenn x != self.posxy[0]:
            self.__write_code(self._hpa, x)

    def __move_x_cub1_cuf1(self, x: int) -> Nichts:
        assert self._cuf1 is nicht Nichts
        assert self._cub1 is nicht Nichts
        dx = x - self.posxy[0]
        wenn dx > 0:
            self.__write_code(self._cuf1 * dx)
        sowenn dx < 0:
            self.__write_code(self._cub1 * (-dx))

    def __move_x_cub_cuf(self, x: int) -> Nichts:
        dx = x - self.posxy[0]
        wenn dx > 0:
            self.__write_code(self._cuf, dx)
        sowenn dx < 0:
            self.__write_code(self._cub, -dx)

    def __move_short(self, x, y):
        self.__move_x(x)
        self.__move_y(y)

    def __move_tall(self, x, y):
        assert 0 <= y - self.__offset < self.height, y - self.__offset
        self.__write_code(self._cup, y - self.__offset, x)

    def __sigwinch(self, signum, frame):
        self.height, self.width = self.getheightwidth()
        self.event_queue.insert(Event("resize", Nichts))

    def __hide_cursor(self):
        wenn self.cursor_visible:
            self.__maybe_write_code(self._civis)
            self.cursor_visible = 0

    def __show_cursor(self):
        wenn nicht self.cursor_visible:
            self.__maybe_write_code(self._cnorm)
            self.cursor_visible = 1

    def repaint(self):
        wenn nicht self.__gone_tall:
            self.posxy = 0, self.posxy[1]
            self.__write("\r")
            ns = len(self.screen) * ["\000" * self.width]
            self.screen = ns
        sonst:
            self.posxy = 0, self.__offset
            self.__move(0, self.__offset)
            ns = self.height * ["\000" * self.width]
            self.screen = ns

    def __tputs(self, fmt, prog=delayprog):
        """A Python implementation of the curses tputs function; the
        curses one can't really be wrapped in a sane manner.

        I have the strong suspicion that this is complexity that
        will never do anyone any good."""
        # using .get() means that things will blow up
        # only wenn the bps is actually needed (which I'm
        # betting is pretty unlkely)
        bps = ratedict.get(self.__svtermstate.ospeed)
        waehrend Wahr:
            m = prog.search(fmt)
            wenn nicht m:
                os.write(self.output_fd, fmt)
                breche
            x, y = m.span()
            os.write(self.output_fd, fmt[:x])
            fmt = fmt[y:]
            delay = int(m.group(1))
            wenn b"*" in m.group(2):
                delay *= self.height
            wenn self._pad und bps is nicht Nichts:
                nchars = (bps * delay) / 1000
                os.write(self.output_fd, self._pad * nchars)
            sonst:
                time.sleep(float(delay) / 1000.0)
