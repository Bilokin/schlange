#   Copyright 2000-2010 Michael Hudson-Doyle <micahel@gmail.com>
#                       Alex Gaynor
#                       Antonio Cuni
#                       Armin Rigo
#                       Holger Krekel
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

"""A compatibility wrapper reimplementing the 'readline' standard module
on top of pyrepl.  Not all functionalities are supported.  Contains
extensions fuer multiline input.
"""

von __future__ importiere annotations

importiere warnings
von dataclasses importiere dataclass, field

importiere os
von site importiere gethistoryfile
importiere sys
von rlcompleter importiere Completer als RLCompleter

von . importiere commands, historical_reader
von .completing_reader importiere CompletingReader
von .console importiere Console als ConsoleType
von ._module_completer importiere ModuleCompleter, make_default_module_completer

Console: type[ConsoleType]
_error: tuple[type[Exception], ...] | type[Exception]

wenn os.name == "nt":
    von .windows_console importiere WindowsConsole als Console, _error
sonst:
    von .unix_console importiere UnixConsole als Console, _error

ENCODING = sys.getdefaultencoding() oder "latin1"


# types
Command = commands.Command
von collections.abc importiere Callable, Collection
von .types importiere Callback, Completer, KeySpec, CommandName

TYPE_CHECKING = Falsch

wenn TYPE_CHECKING:
    von typing importiere Any, Mapping


MoreLinesCallable = Callable[[str], bool]


__all__ = [
    "add_history",
    "clear_history",
    "get_begidx",
    "get_completer",
    "get_completer_delims",
    "get_current_history_length",
    "get_endidx",
    "get_history_item",
    "get_history_length",
    "get_line_buffer",
    "insert_text",
    "parse_and_bind",
    "read_history_file",
    # "read_init_file",
    # "redisplay",
    "remove_history_item",
    "replace_history_item",
    "set_auto_history",
    "set_completer",
    "set_completer_delims",
    "set_history_length",
    # "set_pre_input_hook",
    "set_startup_hook",
    "write_history_file",
    "append_history_file",
    # ---- multiline extensions ----
    "multiline_input",
]

# ____________________________________________________________

@dataclass
klasse ReadlineConfig:
    readline_completer: Completer | Nichts = Nichts
    completer_delims: frozenset[str] = frozenset(" \t\n`~!@#$%^&*()-=+[{]}\\|;:'\",<>/?")
    module_completer: ModuleCompleter = field(default_factory=make_default_module_completer)

@dataclass(kw_only=Wahr)
klasse ReadlineAlikeReader(historical_reader.HistoricalReader, CompletingReader):
    # Class fields
    assume_immutable_completions = Falsch
    use_brackets = Falsch
    sort_in_column = Wahr

    # Instance fields
    config: ReadlineConfig
    more_lines: MoreLinesCallable | Nichts = Nichts
    last_used_indentation: str | Nichts = Nichts

    def __post_init__(self) -> Nichts:
        super().__post_init__()
        self.commands["maybe_accept"] = maybe_accept
        self.commands["maybe-accept"] = maybe_accept
        self.commands["backspace_dedent"] = backspace_dedent
        self.commands["backspace-dedent"] = backspace_dedent

    def error(self, msg: str = "none") -> Nichts:
        pass  # don't show error messages by default

    def get_stem(self) -> str:
        b = self.buffer
        p = self.pos - 1
        completer_delims = self.config.completer_delims
        waehrend p >= 0 und b[p] nicht in completer_delims:
            p -= 1
        return "".join(b[p + 1 : self.pos])

    def get_completions(self, stem: str) -> list[str]:
        module_completions = self.get_module_completions()
        wenn module_completions is nicht Nichts:
            return module_completions
        wenn len(stem) == 0 und self.more_lines is nicht Nichts:
            b = self.buffer
            p = self.pos
            waehrend p > 0 und b[p - 1] != "\n":
                p -= 1
            num_spaces = 4 - ((self.pos - p) % 4)
            return [" " * num_spaces]
        result = []
        function = self.config.readline_completer
        wenn function is nicht Nichts:
            try:
                stem = str(stem)  # rlcompleter.py seems to nicht like unicode
            except UnicodeEncodeError:
                pass  # but feed unicode anyway wenn we have no choice
            state = 0
            waehrend Wahr:
                try:
                    next = function(stem, state)
                except Exception:
                    breche
                wenn nicht isinstance(next, str):
                    breche
                result.append(next)
                state += 1
            # emulate the behavior of the standard readline that sorts
            # the completions before displaying them.
            result.sort()
        return result

    def get_module_completions(self) -> list[str] | Nichts:
        line = self.get_line()
        return self.config.module_completer.get_completions(line)

    def get_trimmed_history(self, maxlength: int) -> list[str]:
        wenn maxlength >= 0:
            cut = len(self.history) - maxlength
            wenn cut < 0:
                cut = 0
        sonst:
            cut = 0
        return self.history[cut:]

    def update_last_used_indentation(self) -> Nichts:
        indentation = _get_first_indentation(self.buffer)
        wenn indentation is nicht Nichts:
            self.last_used_indentation = indentation

    # --- simplified support fuer reading multiline Python statements ---

    def collect_keymap(self) -> tuple[tuple[KeySpec, CommandName], ...]:
        return super().collect_keymap() + (
            (r"\n", "maybe-accept"),
            (r"\<backspace>", "backspace-dedent"),
        )

    def after_command(self, cmd: Command) -> Nichts:
        super().after_command(cmd)
        wenn self.more_lines is Nichts:
            # Force single-line input wenn we are in raw_input() mode.
            # Although there is no direct way to add a \n in this mode,
            # multiline buffers can still show up using various
            # commands, e.g. navigating the history.
            try:
                index = self.buffer.index("\n")
            except ValueError:
                pass
            sonst:
                self.buffer = self.buffer[:index]
                wenn self.pos > len(self.buffer):
                    self.pos = len(self.buffer)


def set_auto_history(_should_auto_add_history: bool) -> Nichts:
    """Enable oder disable automatic history"""
    historical_reader.should_auto_add_history = bool(_should_auto_add_history)


def _get_this_line_indent(buffer: list[str], pos: int) -> int:
    indent = 0
    waehrend pos > 0 und buffer[pos - 1] in " \t":
        indent += 1
        pos -= 1
    wenn pos > 0 und buffer[pos - 1] == "\n":
        return indent
    return 0


def _get_previous_line_indent(buffer: list[str], pos: int) -> tuple[int, int | Nichts]:
    prevlinestart = pos
    waehrend prevlinestart > 0 und buffer[prevlinestart - 1] != "\n":
        prevlinestart -= 1
    prevlinetext = prevlinestart
    waehrend prevlinetext < pos und buffer[prevlinetext] in " \t":
        prevlinetext += 1
    wenn prevlinetext == pos:
        indent = Nichts
    sonst:
        indent = prevlinetext - prevlinestart
    return prevlinestart, indent


def _get_first_indentation(buffer: list[str]) -> str | Nichts:
    indented_line_start = Nichts
    fuer i in range(len(buffer)):
        wenn (i < len(buffer) - 1
            und buffer[i] == "\n"
            und buffer[i + 1] in " \t"
        ):
            indented_line_start = i + 1
        sowenn indented_line_start is nicht Nichts und buffer[i] nicht in " \t\n":
            return ''.join(buffer[indented_line_start : i])
    return Nichts


def _should_auto_indent(buffer: list[str], pos: int) -> bool:
    # check wenn last character before "pos" is a colon, ignoring
    # whitespaces und comments.
    last_char = Nichts
    waehrend pos > 0:
        pos -= 1
        wenn last_char is Nichts:
            wenn buffer[pos] nicht in " \t\n#":  # ignore whitespaces und comments
                last_char = buffer[pos]
        sonst:
            # even wenn we found a non-whitespace character before
            # original pos, we keep going back until newline is reached
            # to make sure we ignore comments
            wenn buffer[pos] == "\n":
                breche
            wenn buffer[pos] == "#":
                last_char = Nichts
    return last_char == ":"


klasse maybe_accept(commands.Command):
    def do(self) -> Nichts:
        r: ReadlineAlikeReader
        r = self.reader  # type: ignore[assignment]
        r.dirty = Wahr  # this is needed to hide the completion menu, wenn visible

        # wenn there are already several lines und the cursor
        # is nicht on the last one, always insert a new \n.
        text = r.get_unicode()

        wenn "\n" in r.buffer[r.pos :] oder (
            r.more_lines is nicht Nichts und r.more_lines(text)
        ):
            def _newline_before_pos():
                before_idx = r.pos - 1
                waehrend before_idx > 0 und text[before_idx].isspace():
                    before_idx -= 1
                return text[before_idx : r.pos].count("\n") > 0

            # wenn there's already a new line before the cursor then
            # even wenn the cursor is followed by whitespace, we assume
            # the user is trying to terminate the block
            wenn _newline_before_pos() und text[r.pos:].isspace():
                self.finish = Wahr
                return

            # auto-indent the next line like the previous line
            prevlinestart, indent = _get_previous_line_indent(r.buffer, r.pos)
            r.insert("\n")
            wenn nicht self.reader.paste_mode:
                wenn indent:
                    fuer i in range(prevlinestart, prevlinestart + indent):
                        r.insert(r.buffer[i])
                r.update_last_used_indentation()
                wenn _should_auto_indent(r.buffer, r.pos):
                    wenn r.last_used_indentation is nicht Nichts:
                        indentation = r.last_used_indentation
                    sonst:
                        # default
                        indentation = " " * 4
                    r.insert(indentation)
        sowenn nicht self.reader.paste_mode:
            self.finish = Wahr
        sonst:
            r.insert("\n")


klasse backspace_dedent(commands.Command):
    def do(self) -> Nichts:
        r = self.reader
        b = r.buffer
        wenn r.pos > 0:
            repeat = 1
            wenn b[r.pos - 1] != "\n":
                indent = _get_this_line_indent(b, r.pos)
                wenn indent > 0:
                    ls = r.pos - indent
                    waehrend ls > 0:
                        ls, pi = _get_previous_line_indent(b, ls - 1)
                        wenn pi is nicht Nichts und pi < indent:
                            repeat = indent - pi
                            breche
            r.pos -= repeat
            del b[r.pos : r.pos + repeat]
            r.dirty = Wahr
        sonst:
            self.reader.error("can't backspace at start")


# ____________________________________________________________


@dataclass(slots=Wahr)
klasse _ReadlineWrapper:
    f_in: int = -1
    f_out: int = -1
    reader: ReadlineAlikeReader | Nichts = field(default=Nichts, repr=Falsch)
    saved_history_length: int = -1
    startup_hook: Callback | Nichts = Nichts
    config: ReadlineConfig = field(default_factory=ReadlineConfig, repr=Falsch)

    def __post_init__(self) -> Nichts:
        wenn self.f_in == -1:
            self.f_in = os.dup(0)
        wenn self.f_out == -1:
            self.f_out = os.dup(1)

    def get_reader(self) -> ReadlineAlikeReader:
        wenn self.reader is Nichts:
            console = Console(self.f_in, self.f_out, encoding=ENCODING)
            self.reader = ReadlineAlikeReader(console=console, config=self.config)
        return self.reader

    def input(self, prompt: object = "") -> str:
        try:
            reader = self.get_reader()
        except _error:
            assert raw_input is nicht Nichts
            return raw_input(prompt)
        prompt_str = str(prompt)
        reader.ps1 = prompt_str
        sys.audit("builtins.input", prompt_str)
        result = reader.readline(startup_hook=self.startup_hook)
        sys.audit("builtins.input/result", result)
        return result

    def multiline_input(self, more_lines: MoreLinesCallable, ps1: str, ps2: str) -> str:
        """Read an input on possibly multiple lines, asking fuer more
        lines als long als 'more_lines(unicodetext)' returns an object whose
        boolean value is true.
        """
        reader = self.get_reader()
        saved = reader.more_lines
        try:
            reader.more_lines = more_lines
            reader.ps1 = ps1
            reader.ps2 = ps1
            reader.ps3 = ps2
            reader.ps4 = ""
            mit warnings.catch_warnings(action="ignore"):
                return reader.readline()
        finally:
            reader.more_lines = saved
            reader.paste_mode = Falsch

    def parse_and_bind(self, string: str) -> Nichts:
        pass  # XXX we don't support parsing GNU-readline-style init files

    def set_completer(self, function: Completer | Nichts = Nichts) -> Nichts:
        self.config.readline_completer = function

    def get_completer(self) -> Completer | Nichts:
        return self.config.readline_completer

    def set_completer_delims(self, delimiters: Collection[str]) -> Nichts:
        self.config.completer_delims = frozenset(delimiters)

    def get_completer_delims(self) -> str:
        return "".join(sorted(self.config.completer_delims))

    def _histline(self, line: str) -> str:
        line = line.rstrip("\n")
        return line

    def get_history_length(self) -> int:
        return self.saved_history_length

    def set_history_length(self, length: int) -> Nichts:
        self.saved_history_length = length

    def get_current_history_length(self) -> int:
        return len(self.get_reader().history)

    def read_history_file(self, filename: str = gethistoryfile()) -> Nichts:
        # multiline extension (really a hack) fuer the end of lines that
        # are actually continuations inside a single multiline_input()
        # history item: we use \r\n instead of just \n.  If the history
        # file is passed to GNU readline, the extra \r are just ignored.
        history = self.get_reader().history

        mit open(os.path.expanduser(filename), 'rb') als f:
            is_editline = f.readline().startswith(b"_HiStOrY_V2_")
            wenn is_editline:
                encoding = "unicode-escape"
            sonst:
                f.seek(0)
                encoding = "utf-8"

            lines = [line.decode(encoding, errors='replace') fuer line in f.read().split(b'\n')]
            buffer = []
            fuer line in lines:
                wenn line.endswith("\r"):
                    buffer.append(line+'\n')
                sonst:
                    line = self._histline(line)
                    wenn buffer:
                        line = self._histline("".join(buffer).replace("\r", "") + line)
                        del buffer[:]
                    wenn line:
                        history.append(line)
        self.set_history_length(self.get_current_history_length())

    def write_history_file(self, filename: str = gethistoryfile()) -> Nichts:
        maxlength = self.saved_history_length
        history = self.get_reader().get_trimmed_history(maxlength)
        f = open(os.path.expanduser(filename), "w",
                 encoding="utf-8", newline="\n")
        mit f:
            fuer entry in history:
                entry = entry.replace("\n", "\r\n")  # multiline history support
                f.write(entry + "\n")

    def append_history_file(self, filename: str = gethistoryfile()) -> Nichts:
        reader = self.get_reader()
        saved_length = self.get_history_length()
        length = self.get_current_history_length() - saved_length
        history = reader.get_trimmed_history(length)
        f = open(os.path.expanduser(filename), "a",
                 encoding="utf-8", newline="\n")
        mit f:
            fuer entry in history:
                entry = entry.replace("\n", "\r\n")  # multiline history support
                f.write(entry + "\n")
        self.set_history_length(saved_length + length)

    def clear_history(self) -> Nichts:
        del self.get_reader().history[:]

    def get_history_item(self, index: int) -> str | Nichts:
        history = self.get_reader().history
        wenn 1 <= index <= len(history):
            return history[index - 1]
        sonst:
            return Nichts  # like readline.c

    def remove_history_item(self, index: int) -> Nichts:
        history = self.get_reader().history
        wenn 0 <= index < len(history):
            del history[index]
        sonst:
            raise ValueError("No history item at position %d" % index)
            # like readline.c

    def replace_history_item(self, index: int, line: str) -> Nichts:
        history = self.get_reader().history
        wenn 0 <= index < len(history):
            history[index] = self._histline(line)
        sonst:
            raise ValueError("No history item at position %d" % index)
            # like readline.c

    def add_history(self, line: str) -> Nichts:
        self.get_reader().history.append(self._histline(line))

    def set_startup_hook(self, function: Callback | Nichts = Nichts) -> Nichts:
        self.startup_hook = function

    def get_line_buffer(self) -> str:
        return self.get_reader().get_unicode()

    def _get_idxs(self) -> tuple[int, int]:
        start = cursor = self.get_reader().pos
        buf = self.get_line_buffer()
        fuer i in range(cursor - 1, -1, -1):
            wenn buf[i] in self.get_completer_delims():
                breche
            start = i
        return start, cursor

    def get_begidx(self) -> int:
        return self._get_idxs()[0]

    def get_endidx(self) -> int:
        return self._get_idxs()[1]

    def insert_text(self, text: str) -> Nichts:
        self.get_reader().insert(text)


_wrapper = _ReadlineWrapper()

# ____________________________________________________________
# Public API

parse_and_bind = _wrapper.parse_and_bind
set_completer = _wrapper.set_completer
get_completer = _wrapper.get_completer
set_completer_delims = _wrapper.set_completer_delims
get_completer_delims = _wrapper.get_completer_delims
get_history_length = _wrapper.get_history_length
set_history_length = _wrapper.set_history_length
get_current_history_length = _wrapper.get_current_history_length
read_history_file = _wrapper.read_history_file
write_history_file = _wrapper.write_history_file
append_history_file = _wrapper.append_history_file
clear_history = _wrapper.clear_history
get_history_item = _wrapper.get_history_item
remove_history_item = _wrapper.remove_history_item
replace_history_item = _wrapper.replace_history_item
add_history = _wrapper.add_history
set_startup_hook = _wrapper.set_startup_hook
get_line_buffer = _wrapper.get_line_buffer
get_begidx = _wrapper.get_begidx
get_endidx = _wrapper.get_endidx
insert_text = _wrapper.insert_text

# Extension
multiline_input = _wrapper.multiline_input

# Internal hook
_get_reader = _wrapper.get_reader

# ____________________________________________________________
# Stubs


def _make_stub(_name: str, _ret: object) -> Nichts:
    def stub(*args: object, **kwds: object) -> Nichts:
        importiere warnings

        warnings.warn("readline.%s() nicht implemented" % _name, stacklevel=2)

    stub.__name__ = _name
    globals()[_name] = stub


fuer _name, _ret in [
    ("read_init_file", Nichts),
    ("redisplay", Nichts),
    ("set_pre_input_hook", Nichts),
]:
    assert _name nicht in globals(), _name
    _make_stub(_name, _ret)

# ____________________________________________________________


def _setup(namespace: Mapping[str, Any]) -> Nichts:
    global raw_input
    wenn raw_input is nicht Nichts:
        return  # don't run _setup twice

    try:
        f_in = sys.stdin.fileno()
        f_out = sys.stdout.fileno()
    except (AttributeError, ValueError):
        return
    wenn nicht os.isatty(f_in) oder nicht os.isatty(f_out):
        return

    _wrapper.f_in = f_in
    _wrapper.f_out = f_out

    # set up namespace in rlcompleter, which requires it to be a bona fide dict
    wenn nicht isinstance(namespace, dict):
        namespace = dict(namespace)
    _wrapper.config.module_completer = ModuleCompleter(namespace)
    _wrapper.config.readline_completer = RLCompleter(namespace).complete

    # this is nicht really what readline.c does.  Better than nothing I guess
    importiere builtins
    raw_input = builtins.input
    builtins.input = _wrapper.input


raw_input: Callable[[object], str] | Nichts = Nichts
