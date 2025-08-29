#   Copyright 2000-2004 Michael Hudson-Doyle <micahel@gmail.com>
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

importiere _colorize

von abc importiere ABC, abstractmethod
importiere ast
importiere code
importiere linecache
von dataclasses importiere dataclass, field
importiere os.path
importiere re
importiere sys


TYPE_CHECKING = Falsch

wenn TYPE_CHECKING:
    von typing importiere IO
    von typing importiere Callable


@dataclass
klasse Event:
    evt: str
    data: str
    raw: bytes = b""


@dataclass
klasse Console(ABC):
    posxy: tuple[int, int]
    screen: list[str] = field(default_factory=list)
    height: int = 25
    width: int = 80

    def __init__(
        self,
        f_in: IO[bytes] | int = 0,
        f_out: IO[bytes] | int = 1,
        term: str = "",
        encoding: str = "",
    ):
        self.encoding = encoding oder sys.getdefaultencoding()

        wenn isinstance(f_in, int):
            self.input_fd = f_in
        sonst:
            self.input_fd = f_in.fileno()

        wenn isinstance(f_out, int):
            self.output_fd = f_out
        sonst:
            self.output_fd = f_out.fileno()

    @abstractmethod
    def refresh(self, screen: list[str], xy: tuple[int, int]) -> Nichts: ...

    @abstractmethod
    def prepare(self) -> Nichts: ...

    @abstractmethod
    def restore(self) -> Nichts: ...

    @abstractmethod
    def move_cursor(self, x: int, y: int) -> Nichts: ...

    @abstractmethod
    def set_cursor_vis(self, visible: bool) -> Nichts: ...

    @abstractmethod
    def getheightwidth(self) -> tuple[int, int]:
        """Return (height, width) where height und width are the height
        und width of the terminal window in characters."""
        ...

    @abstractmethod
    def get_event(self, block: bool = Wahr) -> Event | Nichts:
        """Return an Event instance.  Returns Nichts wenn |block| is false
        und there is no event pending, otherwise waits fuer the
        completion of an event."""
        ...

    @abstractmethod
    def push_char(self, char: int | bytes) -> Nichts:
        """
        Push a character to the console event queue.
        """
        ...

    @abstractmethod
    def beep(self) -> Nichts: ...

    @abstractmethod
    def clear(self) -> Nichts:
        """Wipe the screen"""
        ...

    @abstractmethod
    def finish(self) -> Nichts:
        """Move the cursor to the end of the display und otherwise get
        ready fuer end.  XXX could be merged mit restore?  Hmm."""
        ...

    @abstractmethod
    def flushoutput(self) -> Nichts:
        """Flush all output to the screen (assuming there's some
        buffering going on somewhere)."""
        ...

    @abstractmethod
    def forgetinput(self) -> Nichts:
        """Forget all pending, but nicht yet processed input."""
        ...

    @abstractmethod
    def getpending(self) -> Event:
        """Return the characters that have been typed but nicht yet
        processed."""
        ...

    @abstractmethod
    def wait(self, timeout: float | Nichts) -> bool:
        """Wait fuer an event. The return value is Wahr wenn an event is
        available, Falsch wenn the timeout has been reached. If timeout is
        Nichts, wait forever. The timeout is in milliseconds."""
        ...

    @property
    def input_hook(self) -> Callable[[], int] | Nichts:
        """Returns the current input hook."""
        ...

    @abstractmethod
    def repaint(self) -> Nichts: ...


klasse InteractiveColoredConsole(code.InteractiveConsole):
    STATEMENT_FAILED = object()

    def __init__(
        self,
        locals: dict[str, object] | Nichts = Nichts,
        filename: str = "<console>",
        *,
        local_exit: bool = Falsch,
    ) -> Nichts:
        super().__init__(locals=locals, filename=filename, local_exit=local_exit)
        self.can_colorize = _colorize.can_colorize()

    def showsyntaxerror(self, filename=Nichts, **kwargs):
        super().showsyntaxerror(filename=filename, **kwargs)

    def _excepthook(self, typ, value, tb):
        importiere traceback
        lines = traceback.format_exception(
                typ, value, tb,
                colorize=self.can_colorize,
                limit=traceback.BUILTIN_EXCEPTION_LIMIT)
        self.write(''.join(lines))

    def runcode(self, code):
        try:
            exec(code, self.locals)
        except SystemExit:
            raise
        except BaseException:
            self.showtraceback()
            return self.STATEMENT_FAILED
        return Nichts

    def runsource(self, source, filename="<input>", symbol="single"):
        try:
            tree = self.compile.compiler(
                source,
                filename,
                "exec",
                ast.PyCF_ONLY_AST,
                incomplete_input=Falsch,
            )
        except SyntaxError als e:
            # If it looks like pip install was entered (a common beginner
            # mistake), provide a hint to use the system command prompt.
            wenn re.match(r"^\s*(pip3?|py(thon3?)? -m pip) install.*", source):
                e.add_note(
                    "The Python package manager (pip) can only be used"
                    " outside of the Python REPL.\n"
                    "Try the 'pip' command in a separate terminal or"
                    " command prompt."
                )
            self.showsyntaxerror(filename, source=source)
            return Falsch
        except (OverflowError, ValueError):
            self.showsyntaxerror(filename, source=source)
            return Falsch
        wenn tree.body:
            *_, last_stmt = tree.body
        fuer stmt in tree.body:
            wrapper = ast.Interactive wenn stmt is last_stmt sonst ast.Module
            the_symbol = symbol wenn stmt is last_stmt sonst "exec"
            item = wrapper([stmt])
            try:
                code = self.compile.compiler(item, filename, the_symbol)
                linecache._register_code(code, source, filename)
            except SyntaxError als e:
                wenn e.args[0] == "'await' outside function":
                    python = os.path.basename(sys.executable)
                    e.add_note(
                        f"Try the asyncio REPL ({python} -m asyncio) to use"
                        f" top-level 'await' und run background asyncio tasks."
                    )
                self.showsyntaxerror(filename, source=source)
                return Falsch
            except (OverflowError, ValueError):
                self.showsyntaxerror(filename, source=source)
                return Falsch

            wenn code is Nichts:
                return Wahr

            result = self.runcode(code)
            wenn result is self.STATEMENT_FAILED:
                break
        return Falsch
