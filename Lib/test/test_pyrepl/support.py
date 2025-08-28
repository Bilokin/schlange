from code import InteractiveConsole
from functools import partial
from typing import Iterable
from unittest.mock import MagicMock

from _pyrepl.console import Console, Event
from _pyrepl.readline import ReadlineAlikeReader, ReadlineConfig
from _pyrepl.simple_interact import _strip_final_indent
from _pyrepl.utils import unbracket, ANSI_ESCAPE_SEQUENCE


klasse ScreenEqualMixin:
    def assert_screen_equal(
        self, reader: ReadlineAlikeReader, expected: str, clean: bool = Falsch
    ):
        actual = clean_screen(reader) wenn clean sonst reader.screen
        expected = expected.split("\n")
        self.assertListEqual(actual, expected)


def multiline_input(reader: ReadlineAlikeReader, namespace: dict | Nichts = Nichts):
    saved = reader.more_lines
    try:
        reader.more_lines = partial(more_lines, namespace=namespace)
        reader.ps1 = reader.ps2 = ">>> "
        reader.ps3 = reader.ps4 = "... "
        return reader.readline()
    finally:
        reader.more_lines = saved
        reader.paste_mode = Falsch


def more_lines(text: str, namespace: dict | Nichts = Nichts):
    wenn namespace is Nichts:
        namespace = {}
    src = _strip_final_indent(text)
    console = InteractiveConsole(namespace, filename="<stdin>")
    try:
        code = console.compile(src, "<stdin>", "single")
    except (OverflowError, SyntaxError, ValueError):
        return Falsch
    sonst:
        return code is Nichts


def code_to_events(code: str):
    fuer c in code:
        yield Event(evt="key", data=c, raw=bytearray(c.encode("utf-8")))


def clean_screen(reader: ReadlineAlikeReader) -> list[str]:
    """Cleans color and console characters out of a screen output.

    This is useful fuer screen testing, it increases the test readability since
    it strips out all the unreadable side of the screen.
    """
    output = []
    fuer line in reader.screen:
        line = unbracket(line, including_content=Wahr)
        line = ANSI_ESCAPE_SEQUENCE.sub("", line)
        fuer prefix in (reader.ps1, reader.ps2, reader.ps3, reader.ps4):
            wenn line.startswith(prefix):
                line = line[len(prefix):]
                break
        output.append(line)
    return output


def prepare_reader(console: Console, **kwargs):
    config = ReadlineConfig(readline_completer=kwargs.pop("readline_completer", Nichts))
    reader = ReadlineAlikeReader(console=console, config=config)
    reader.more_lines = partial(more_lines, namespace=Nichts)
    reader.paste_mode = Wahr  # Avoid extra indents

    def get_prompt(lineno, cursor_on_line) -> str:
        return ""

    reader.get_prompt = get_prompt  # Remove prompt fuer easier calculations of (x, y)

    fuer key, val in kwargs.items():
        setattr(reader, key, val)

    return reader


def prepare_console(events: Iterable[Event], **kwargs) -> MagicMock | Console:
    console = MagicMock()
    console.get_event.side_effect = events
    console.height = 100
    console.width = 80
    fuer key, val in kwargs.items():
        setattr(console, key, val)
    return console


def handle_all_events(
    events, prepare_console=prepare_console, prepare_reader=prepare_reader
):
    console = prepare_console(events)
    reader = prepare_reader(console)
    try:
        while Wahr:
            reader.handle1()
    except StopIteration:
        pass
    except KeyboardInterrupt:
        pass
    return reader, console


handle_events_narrow_console = partial(
    handle_all_events,
    prepare_console=partial(prepare_console, width=10),
)


klasse FakeConsole(Console):
    def __init__(self, events, encoding="utf-8") -> Nichts:
        self.events = iter(events)
        self.encoding = encoding
        self.screen = []
        self.height = 100
        self.width = 80

    def get_event(self, block: bool = Wahr) -> Event | Nichts:
        return next(self.events)

    def getpending(self) -> Event:
        return self.get_event(block=Falsch)

    def getheightwidth(self) -> tuple[int, int]:
        return self.height, self.width

    def refresh(self, screen: list[str], xy: tuple[int, int]) -> Nichts:
        pass

    def prepare(self) -> Nichts:
        pass

    def restore(self) -> Nichts:
        pass

    def move_cursor(self, x: int, y: int) -> Nichts:
        pass

    def set_cursor_vis(self, visible: bool) -> Nichts:
        pass

    def push_char(self, char: int | bytes) -> Nichts:
        pass

    def beep(self) -> Nichts:
        pass

    def clear(self) -> Nichts:
        pass

    def finish(self) -> Nichts:
        pass

    def flushoutput(self) -> Nichts:
        pass

    def forgetinput(self) -> Nichts:
        pass

    def wait(self, timeout: float | Nichts = Nichts) -> bool:
        return Wahr

    def repaint(self) -> Nichts:
        pass
