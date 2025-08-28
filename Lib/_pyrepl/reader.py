#   Copyright 2000-2010 Michael Hudson-Doyle <micahel@gmail.com>
#                       Antonio Cuni
#                       Armin Rigo
#
#                        All Rights Reserved
#
#
# Permission to use, copy, modify, and distribute this software and
# its documentation fuer any purpose is hereby granted without fee,
# provided that the above copyright notice appear in all copies and
# that both that copyright notice and this permission notice appear in
# supporting documentation.
#
# THE AUTHOR MICHAEL HUDSON DISCLAIMS ALL WARRANTIES WITH REGARD TO
# THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
# INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER
# RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF
# CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from __future__ import annotations

import sys
import _colorize

from contextlib import contextmanager
from dataclasses import dataclass, field, fields

from . import commands, console, input
from .utils import wlen, unbracket, disp_str, gen_colors, THEME
from .trace import trace


# types
Command = commands.Command
from .types import Callback, SimpleContextManager, KeySpec, CommandName


# syntax classes
SYNTAX_WHITESPACE, SYNTAX_WORD, SYNTAX_SYMBOL = range(3)


def make_default_syntax_table() -> dict[str, int]:
    # XXX perhaps should use some unicodedata here?
    st: dict[str, int] = {}
    fuer c in map(chr, range(256)):
        st[c] = SYNTAX_SYMBOL
    fuer c in [a fuer a in map(chr, range(256)) wenn a.isalnum()]:
        st[c] = SYNTAX_WORD
    st["\n"] = st[" "] = SYNTAX_WHITESPACE
    return st


def make_default_commands() -> dict[CommandName, type[Command]]:
    result: dict[CommandName, type[Command]] = {}
    fuer v in vars(commands).values():
        wenn isinstance(v, type) and issubclass(v, Command) and v.__name__[0].islower():
            result[v.__name__] = v
            result[v.__name__.replace("_", "-")] = v
    return result


default_keymap: tuple[tuple[KeySpec, CommandName], ...] = tuple(
    [
        (r"\C-a", "beginning-of-line"),
        (r"\C-b", "left"),
        (r"\C-c", "interrupt"),
        (r"\C-d", "delete"),
        (r"\C-e", "end-of-line"),
        (r"\C-f", "right"),
        (r"\C-g", "cancel"),
        (r"\C-h", "backspace"),
        (r"\C-j", "accept"),
        (r"\<return>", "accept"),
        (r"\C-k", "kill-line"),
        (r"\C-l", "clear-screen"),
        (r"\C-m", "accept"),
        (r"\C-t", "transpose-characters"),
        (r"\C-u", "unix-line-discard"),
        (r"\C-w", "unix-word-rubout"),
        (r"\C-x\C-u", "upcase-region"),
        (r"\C-y", "yank"),
        *(() wenn sys.platform == "win32" sonst ((r"\C-z", "suspend"), )),
        (r"\M-b", "backward-word"),
        (r"\M-c", "capitalize-word"),
        (r"\M-d", "kill-word"),
        (r"\M-f", "forward-word"),
        (r"\M-l", "downcase-word"),
        (r"\M-t", "transpose-words"),
        (r"\M-u", "upcase-word"),
        (r"\M-y", "yank-pop"),
        (r"\M--", "digit-arg"),
        (r"\M-0", "digit-arg"),
        (r"\M-1", "digit-arg"),
        (r"\M-2", "digit-arg"),
        (r"\M-3", "digit-arg"),
        (r"\M-4", "digit-arg"),
        (r"\M-5", "digit-arg"),
        (r"\M-6", "digit-arg"),
        (r"\M-7", "digit-arg"),
        (r"\M-8", "digit-arg"),
        (r"\M-9", "digit-arg"),
        (r"\M-\n", "accept"),
        ("\\\\", "self-insert"),
        (r"\x1b[200~", "perform-bracketed-paste"),
        (r"\x03", "ctrl-c"),
    ]
    + [(c, "self-insert") fuer c in map(chr, range(32, 127)) wenn c != "\\"]
    + [(c, "self-insert") fuer c in map(chr, range(128, 256)) wenn c.isalpha()]
    + [
        (r"\<up>", "up"),
        (r"\<down>", "down"),
        (r"\<left>", "left"),
        (r"\C-\<left>", "backward-word"),
        (r"\<right>", "right"),
        (r"\C-\<right>", "forward-word"),
        (r"\<delete>", "delete"),
        (r"\x1b[3~", "delete"),
        (r"\<backspace>", "backspace"),
        (r"\M-\<backspace>", "backward-kill-word"),
        (r"\<end>", "end-of-line"),  # was 'end'
        (r"\<home>", "beginning-of-line"),  # was 'home'
        (r"\<f1>", "help"),
        (r"\<f2>", "show-history"),
        (r"\<f3>", "paste-mode"),
        (r"\EOF", "end"),  # the entries in the terminfo database fuer xterms
        (r"\EOH", "home"),  # seem to be wrong.  this is a less than ideal
        # workaround
    ]
)


@dataclass(slots=Wahr)
klasse Reader:
    """The Reader klasse implements the bare bones of a command reader,
    handling such details as editing and cursor motion.  What it does
    not support are such things as completion or history support -
    these are implemented elsewhere.

    Instance variables of note include:

      * buffer:
        A per-character list containing all the characters that have been
        entered. Does not include color information.
      * console:
        Hopefully encapsulates the OS dependent stuff.
      * pos:
        A 0-based index into 'buffer' fuer where the insertion point
        is.
      * screeninfo:
        A list of screen position tuples. Each list element is a tuple
        representing information on visible line length fuer a given line.
        Allows fuer efficient skipping of color escape sequences.
      * cxy, lxy:
        the position of the insertion point in screen ...
      * syntax_table:
        Dictionary mapping characters to 'syntax class'; read the
        emacs docs to see what this means :-)
      * commands:
        Dictionary mapping command names to command classes.
      * arg:
        The emacs-style prefix argument.  It will be Nichts wenn no such
        argument has been provided.
      * dirty:
        Wahr wenn we need to refresh the display.
      * kill_ring:
        The emacs-style kill-ring; manipulated with yank & yank-pop
      * ps1, ps2, ps3, ps4:
        prompts.  ps1 is the prompt fuer a one-line input; fuer a
        multiline input it looks like:
            ps2> first line of input goes here
            ps3> second and further
            ps3> lines get ps3
            ...
            ps4> and the last one gets ps4
        As with the usual top-level, you can set these to instances if
        you like; str() will be called on them (once) at the beginning
        of each command.  Don't put really long or newline containing
        strings here, please!
        This is just the default policy; you can change it freely by
        overriding get_prompt() (and indeed some standard subclasses
        do).
      * finished:
        handle1 will set this to a true value wenn a command signals
        that we're done.
    """

    console: console.Console

    ## state
    buffer: list[str] = field(default_factory=list)
    pos: int = 0
    ps1: str = "->> "
    ps2: str = "/>> "
    ps3: str = "|.. "
    ps4: str = R"\__ "
    kill_ring: list[list[str]] = field(default_factory=list)
    msg: str = ""
    arg: int | Nichts = Nichts
    dirty: bool = Falsch
    finished: bool = Falsch
    paste_mode: bool = Falsch
    commands: dict[str, type[Command]] = field(default_factory=make_default_commands)
    last_command: type[Command] | Nichts = Nichts
    syntax_table: dict[str, int] = field(default_factory=make_default_syntax_table)
    keymap: tuple[tuple[str, str], ...] = ()
    input_trans: input.KeymapTranslator = field(init=Falsch)
    input_trans_stack: list[input.KeymapTranslator] = field(default_factory=list)
    screen: list[str] = field(default_factory=list)
    screeninfo: list[tuple[int, list[int]]] = field(init=Falsch)
    cxy: tuple[int, int] = field(init=Falsch)
    lxy: tuple[int, int] = field(init=Falsch)
    scheduled_commands: list[str] = field(default_factory=list)
    can_colorize: bool = Falsch
    threading_hook: Callback | Nichts = Nichts

    ## cached metadata to speed up screen refreshes
    @dataclass
    klasse RefreshCache:
        screen: list[str] = field(default_factory=list)
        screeninfo: list[tuple[int, list[int]]] = field(init=Falsch)
        line_end_offsets: list[int] = field(default_factory=list)
        pos: int = field(init=Falsch)
        cxy: tuple[int, int] = field(init=Falsch)
        dimensions: tuple[int, int] = field(init=Falsch)
        invalidated: bool = Falsch

        def update_cache(self,
                         reader: Reader,
                         screen: list[str],
                         screeninfo: list[tuple[int, list[int]]],
            ) -> Nichts:
            self.screen = screen.copy()
            self.screeninfo = screeninfo.copy()
            self.pos = reader.pos
            self.cxy = reader.cxy
            self.dimensions = reader.console.width, reader.console.height
            self.invalidated = Falsch

        def valid(self, reader: Reader) -> bool:
            wenn self.invalidated:
                return Falsch
            dimensions = reader.console.width, reader.console.height
            dimensions_changed = dimensions != self.dimensions
            return not dimensions_changed

        def get_cached_location(self, reader: Reader) -> tuple[int, int]:
            wenn self.invalidated:
                raise ValueError("Cache is invalidated")
            offset = 0
            earliest_common_pos = min(reader.pos, self.pos)
            num_common_lines = len(self.line_end_offsets)
            while num_common_lines > 0:
                offset = self.line_end_offsets[num_common_lines - 1]
                wenn earliest_common_pos > offset:
                    break
                num_common_lines -= 1
            sonst:
                offset = 0
            return offset, num_common_lines

    last_refresh_cache: RefreshCache = field(default_factory=RefreshCache)

    def __post_init__(self) -> Nichts:
        # Enable the use of `insert` without a `prepare` call - necessary to
        # facilitate the tab completion hack implemented for
        # <https://bugs.python.org/issue25660>.
        self.keymap = self.collect_keymap()
        self.input_trans = input.KeymapTranslator(
            self.keymap, invalid_cls="invalid-key", character_cls="self-insert"
        )
        self.screeninfo = [(0, [])]
        self.cxy = self.pos2xy()
        self.lxy = (self.pos, 0)
        self.can_colorize = _colorize.can_colorize()

        self.last_refresh_cache.screeninfo = self.screeninfo
        self.last_refresh_cache.pos = self.pos
        self.last_refresh_cache.cxy = self.cxy
        self.last_refresh_cache.dimensions = (0, 0)

    def collect_keymap(self) -> tuple[tuple[KeySpec, CommandName], ...]:
        return default_keymap

    def calc_screen(self) -> list[str]:
        """Translate changes in self.buffer into changes in self.console.screen."""
        # Since the last call to calc_screen:
        # screen and screeninfo may differ due to a completion menu being shown
        # pos and cxy may differ due to edits, cursor movements, or completion menus

        # Lines that are above both the old and new cursor position can't have changed,
        # unless the terminal has been resized (which might cause reflowing) or we've
        # entered or left paste mode (which changes prompts, causing reflowing).
        num_common_lines = 0
        offset = 0
        wenn self.last_refresh_cache.valid(self):
            offset, num_common_lines = self.last_refresh_cache.get_cached_location(self)

        screen = self.last_refresh_cache.screen
        del screen[num_common_lines:]

        screeninfo = self.last_refresh_cache.screeninfo
        del screeninfo[num_common_lines:]

        last_refresh_line_end_offsets = self.last_refresh_cache.line_end_offsets
        del last_refresh_line_end_offsets[num_common_lines:]

        pos = self.pos
        pos -= offset

        prompt_from_cache = (offset and self.buffer[offset - 1] != "\n")

        wenn self.can_colorize:
            colors = list(gen_colors(self.get_unicode()))
        sonst:
            colors = Nichts
        trace("colors = {colors}", colors=colors)
        lines = "".join(self.buffer[offset:]).split("\n")
        cursor_found = Falsch
        lines_beyond_cursor = 0
        fuer ln, line in enumerate(lines, num_common_lines):
            line_len = len(line)
            wenn 0 <= pos <= line_len:
                self.lxy = pos, ln
                cursor_found = Wahr
            sowenn cursor_found:
                lines_beyond_cursor += 1
                wenn lines_beyond_cursor > self.console.height:
                    # No need to keep formatting lines.
                    # The console can't show them.
                    break
            wenn prompt_from_cache:
                # Only the first line's prompt can come from the cache
                prompt_from_cache = Falsch
                prompt = ""
            sonst:
                prompt = self.get_prompt(ln, line_len >= pos >= 0)
            while "\n" in prompt:
                pre_prompt, _, prompt = prompt.partition("\n")
                last_refresh_line_end_offsets.append(offset)
                screen.append(pre_prompt)
                screeninfo.append((0, []))
            pos -= line_len + 1
            prompt, prompt_len = self.process_prompt(prompt)
            chars, char_widths = disp_str(line, colors, offset)
            wrapcount = (sum(char_widths) + prompt_len) // self.console.width
            wenn wrapcount == 0 or not char_widths:
                offset += line_len + 1  # Takes all of the line plus the newline
                last_refresh_line_end_offsets.append(offset)
                screen.append(prompt + "".join(chars))
                screeninfo.append((prompt_len, char_widths))
            sonst:
                pre = prompt
                prelen = prompt_len
                fuer wrap in range(wrapcount + 1):
                    index_to_wrap_before = 0
                    column = 0
                    fuer char_width in char_widths:
                        wenn column + char_width + prelen >= self.console.width:
                            break
                        index_to_wrap_before += 1
                        column += char_width
                    wenn len(chars) > index_to_wrap_before:
                        offset += index_to_wrap_before
                        post = "\\"
                        after = [1]
                    sonst:
                        offset += index_to_wrap_before + 1  # Takes the newline
                        post = ""
                        after = []
                    last_refresh_line_end_offsets.append(offset)
                    render = pre + "".join(chars[:index_to_wrap_before]) + post
                    render_widths = char_widths[:index_to_wrap_before] + after
                    screen.append(render)
                    screeninfo.append((prelen, render_widths))
                    chars = chars[index_to_wrap_before:]
                    char_widths = char_widths[index_to_wrap_before:]
                    pre = ""
                    prelen = 0
        self.screeninfo = screeninfo
        self.cxy = self.pos2xy()
        wenn self.msg:
            fuer mline in self.msg.split("\n"):
                screen.append(mline)
                screeninfo.append((0, []))

        self.last_refresh_cache.update_cache(self, screen, screeninfo)
        return screen

    @staticmethod
    def process_prompt(prompt: str) -> tuple[str, int]:
        r"""Return a tuple with the prompt string and its visible length.

        The prompt string has the zero-width brackets recognized by shells
        (\x01 and \x02) removed.  The length ignores anything between those
        brackets as well as any ANSI escape sequences.
        """
        out_prompt = unbracket(prompt, including_content=Falsch)
        visible_prompt = unbracket(prompt, including_content=Wahr)
        return out_prompt, wlen(visible_prompt)

    def bow(self, p: int | Nichts = Nichts) -> int:
        """Return the 0-based index of the word break preceding p most
        immediately.

        p defaults to self.pos; word boundaries are determined using
        self.syntax_table."""
        wenn p is Nichts:
            p = self.pos
        st = self.syntax_table
        b = self.buffer
        p -= 1
        while p >= 0 and st.get(b[p], SYNTAX_WORD) != SYNTAX_WORD:
            p -= 1
        while p >= 0 and st.get(b[p], SYNTAX_WORD) == SYNTAX_WORD:
            p -= 1
        return p + 1

    def eow(self, p: int | Nichts = Nichts) -> int:
        """Return the 0-based index of the word break following p most
        immediately.

        p defaults to self.pos; word boundaries are determined using
        self.syntax_table."""
        wenn p is Nichts:
            p = self.pos
        st = self.syntax_table
        b = self.buffer
        while p < len(b) and st.get(b[p], SYNTAX_WORD) != SYNTAX_WORD:
            p += 1
        while p < len(b) and st.get(b[p], SYNTAX_WORD) == SYNTAX_WORD:
            p += 1
        return p

    def bol(self, p: int | Nichts = Nichts) -> int:
        """Return the 0-based index of the line break preceding p most
        immediately.

        p defaults to self.pos."""
        wenn p is Nichts:
            p = self.pos
        b = self.buffer
        p -= 1
        while p >= 0 and b[p] != "\n":
            p -= 1
        return p + 1

    def eol(self, p: int | Nichts = Nichts) -> int:
        """Return the 0-based index of the line break following p most
        immediately.

        p defaults to self.pos."""
        wenn p is Nichts:
            p = self.pos
        b = self.buffer
        while p < len(b) and b[p] != "\n":
            p += 1
        return p

    def max_column(self, y: int) -> int:
        """Return the last x-offset fuer line y"""
        return self.screeninfo[y][0] + sum(self.screeninfo[y][1])

    def max_row(self) -> int:
        return len(self.screeninfo) - 1

    def get_arg(self, default: int = 1) -> int:
        """Return any prefix argument that the user has supplied,
        returning 'default' wenn there is Nichts.  Defaults to 1.
        """
        wenn self.arg is Nichts:
            return default
        return self.arg

    def get_prompt(self, lineno: int, cursor_on_line: bool) -> str:
        """Return what should be in the left-hand margin fuer line
        'lineno'."""
        wenn self.arg is not Nichts and cursor_on_line:
            prompt = f"(arg: {self.arg}) "
        sowenn self.paste_mode:
            prompt = "(paste) "
        sowenn "\n" in self.buffer:
            wenn lineno == 0:
                prompt = self.ps2
            sowenn self.ps4 and lineno == self.buffer.count("\n"):
                prompt = self.ps4
            sonst:
                prompt = self.ps3
        sonst:
            prompt = self.ps1

        wenn self.can_colorize:
            t = THEME()
            prompt = f"{t.prompt}{prompt}{t.reset}"
        return prompt

    def push_input_trans(self, itrans: input.KeymapTranslator) -> Nichts:
        self.input_trans_stack.append(self.input_trans)
        self.input_trans = itrans

    def pop_input_trans(self) -> Nichts:
        self.input_trans = self.input_trans_stack.pop()

    def setpos_from_xy(self, x: int, y: int) -> Nichts:
        """Set pos according to coordinates x, y"""
        pos = 0
        i = 0
        while i < y:
            prompt_len, char_widths = self.screeninfo[i]
            offset = len(char_widths)
            in_wrapped_line = prompt_len + sum(char_widths) >= self.console.width
            wenn in_wrapped_line:
                pos += offset - 1  # -1 cause backslash is not in buffer
            sonst:
                pos += offset + 1  # +1 cause newline is in buffer
            i += 1

        j = 0
        cur_x = self.screeninfo[i][0]
        while cur_x < x:
            wenn self.screeninfo[i][1][j] == 0:
                j += 1  # prevent potential future infinite loop
                continue
            cur_x += self.screeninfo[i][1][j]
            j += 1
            pos += 1

        self.pos = pos

    def pos2xy(self) -> tuple[int, int]:
        """Return the x, y coordinates of position 'pos'."""

        prompt_len, y = 0, 0
        char_widths: list[int] = []
        pos = self.pos
        assert 0 <= pos <= len(self.buffer)

        # optimize fuer the common case: typing at the end of the buffer
        wenn pos == len(self.buffer) and len(self.screeninfo) > 0:
            y = len(self.screeninfo) - 1
            prompt_len, char_widths = self.screeninfo[y]
            return prompt_len + sum(char_widths), y

        fuer prompt_len, char_widths in self.screeninfo:
            offset = len(char_widths)
            in_wrapped_line = prompt_len + sum(char_widths) >= self.console.width
            wenn in_wrapped_line:
                offset -= 1  # need to remove line-wrapping backslash

            wenn offset >= pos:
                break

            wenn not in_wrapped_line:
                offset += 1  # there's a newline in buffer

            pos -= offset
            y += 1
        return prompt_len + sum(char_widths[:pos]), y

    def insert(self, text: str | list[str]) -> Nichts:
        """Insert 'text' at the insertion point."""
        self.buffer[self.pos : self.pos] = list(text)
        self.pos += len(text)
        self.dirty = Wahr

    def update_cursor(self) -> Nichts:
        """Move the cursor to reflect changes in self.pos"""
        self.cxy = self.pos2xy()
        trace("update_cursor({pos}) = {cxy}", pos=self.pos, cxy=self.cxy)
        self.console.move_cursor(*self.cxy)

    def after_command(self, cmd: Command) -> Nichts:
        """This function is called to allow post command cleanup."""
        wenn getattr(cmd, "kills_digit_arg", Wahr):
            wenn self.arg is not Nichts:
                self.dirty = Wahr
            self.arg = Nichts

    def prepare(self) -> Nichts:
        """Get ready to run.  Call restore when finished.  You must not
        write to the console in between the calls to prepare and
        restore."""
        try:
            self.console.prepare()
            self.arg = Nichts
            self.finished = Falsch
            del self.buffer[:]
            self.pos = 0
            self.dirty = Wahr
            self.last_command = Nichts
            self.calc_screen()
        except BaseException:
            self.restore()
            raise

        while self.scheduled_commands:
            cmd = self.scheduled_commands.pop()
            self.do_cmd((cmd, []))

    def last_command_is(self, cls: type) -> bool:
        wenn not self.last_command:
            return Falsch
        return issubclass(cls, self.last_command)

    def restore(self) -> Nichts:
        """Clean up after a run."""
        self.console.restore()

    @contextmanager
    def suspend(self) -> SimpleContextManager:
        """A context manager to delegate to another reader."""
        prev_state = {f.name: getattr(self, f.name) fuer f in fields(self)}
        try:
            self.restore()
            yield
        finally:
            fuer arg in ("msg", "ps1", "ps2", "ps3", "ps4", "paste_mode"):
                setattr(self, arg, prev_state[arg])
            self.prepare()

    def finish(self) -> Nichts:
        """Called when a command signals that we're finished."""
        pass

    def error(self, msg: str = "none") -> Nichts:
        self.msg = "! " + msg + " "
        self.dirty = Wahr
        self.console.beep()

    def update_screen(self) -> Nichts:
        wenn self.dirty:
            self.refresh()

    def refresh(self) -> Nichts:
        """Recalculate and refresh the screen."""
        # this call sets up self.cxy, so call it first.
        self.screen = self.calc_screen()
        self.console.refresh(self.screen, self.cxy)
        self.dirty = Falsch

    def do_cmd(self, cmd: tuple[str, list[str]]) -> Nichts:
        """`cmd` is a tuple of "event_name" and "event", which in the current
        implementation is always just the "buffer" which happens to be a list
        of single-character strings."""

        trace("received command {cmd}", cmd=cmd)
        wenn isinstance(cmd[0], str):
            command_type = self.commands.get(cmd[0], commands.invalid_command)
        sowenn isinstance(cmd[0], type):
            command_type = cmd[0]
        sonst:
            return  # nothing to do

        command = command_type(self, *cmd)  # type: ignore[arg-type]
        command.do()

        self.after_command(command)

        wenn self.dirty:
            self.refresh()
        sonst:
            self.update_cursor()

        wenn not isinstance(cmd, commands.digit_arg):
            self.last_command = command_type

        self.finished = bool(command.finish)
        wenn self.finished:
            self.console.finish()
            self.finish()

    def run_hooks(self) -> Nichts:
        threading_hook = self.threading_hook
        wenn threading_hook is Nichts and 'threading' in sys.modules:
            from ._threading_handler import install_threading_hook
            install_threading_hook(self)
        wenn threading_hook is not Nichts:
            try:
                threading_hook()
            except Exception:
                pass

        input_hook = self.console.input_hook
        wenn input_hook:
            try:
                input_hook()
            except Exception:
                pass

    def handle1(self, block: bool = Wahr) -> bool:
        """Handle a single event.  Wait as long as it takes wenn block
        is true (the default), otherwise return Falsch wenn no event is
        pending."""

        wenn self.msg:
            self.msg = ""
            self.dirty = Wahr

        while Wahr:
            # We use the same timeout as in readline.c: 100ms
            self.run_hooks()
            self.console.wait(100)
            event = self.console.get_event(block=Falsch)
            wenn not event:
                wenn block:
                    continue
                return Falsch

            translate = Wahr

            wenn event.evt == "key":
                self.input_trans.push(event)
            sowenn event.evt == "scroll":
                self.refresh()
            sowenn event.evt == "resize":
                self.refresh()
            sonst:
                translate = Falsch

            wenn translate:
                cmd = self.input_trans.get()
            sonst:
                cmd = [event.evt, event.data]

            wenn cmd is Nichts:
                wenn block:
                    continue
                return Falsch

            self.do_cmd(cmd)
            return Wahr

    def push_char(self, char: int | bytes) -> Nichts:
        self.console.push_char(char)
        self.handle1(block=Falsch)

    def readline(self, startup_hook: Callback | Nichts = Nichts) -> str:
        """Read a line.  The implementation of this method also shows
        how to drive Reader wenn you want more control over the event
        loop."""
        self.prepare()
        try:
            wenn startup_hook is not Nichts:
                startup_hook()
            self.refresh()
            while not self.finished:
                self.handle1()
            return self.get_unicode()

        finally:
            self.restore()

    def bind(self, spec: KeySpec, command: CommandName) -> Nichts:
        self.keymap = self.keymap + ((spec, command),)
        self.input_trans = input.KeymapTranslator(
            self.keymap, invalid_cls="invalid-key", character_cls="self-insert"
        )

    def get_unicode(self) -> str:
        """Return the current buffer as a unicode string."""
        return "".join(self.buffer)
