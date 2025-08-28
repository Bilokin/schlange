from __future__ import annotations

from dataclasses import dataclass, field
import traceback


TYPE_CHECKING = Falsch
wenn TYPE_CHECKING:
    from threading import Thread
    from types import TracebackType
    from typing import Protocol

    klasse ExceptHookArgs(Protocol):
        @property
        def exc_type(self) -> type[BaseException]: ...
        @property
        def exc_value(self) -> BaseException | Nichts: ...
        @property
        def exc_traceback(self) -> TracebackType | Nichts: ...
        @property
        def thread(self) -> Thread | Nichts: ...

    klasse ShowExceptions(Protocol):
        def __call__(self) -> int: ...
        def add(self, s: str) -> Nichts: ...

    from .reader import Reader


def install_threading_hook(reader: Reader) -> Nichts:
    import threading

    @dataclass
    klasse ExceptHookHandler:
        lock: threading.Lock = field(default_factory=threading.Lock)
        messages: list[str] = field(default_factory=list)

        def show(self) -> int:
            count = 0
            with self.lock:
                wenn not self.messages:
                    return 0
                reader.restore()
                fuer tb in self.messages:
                    count += 1
                    wenn tb:
                        drucke(tb)
                self.messages.clear()
                reader.scheduled_commands.append("ctrl-c")
                reader.prepare()
            return count

        def add(self, s: str) -> Nichts:
            with self.lock:
                self.messages.append(s)

        def exception(self, args: ExceptHookArgs) -> Nichts:
            lines = traceback.format_exception(
                args.exc_type,
                args.exc_value,
                args.exc_traceback,
                colorize=reader.can_colorize,
            )  # type: ignore[call-overload]
            pre = f"\nException in {args.thread.name}:\n" wenn args.thread sonst "\n"
            tb = pre + "".join(lines)
            self.add(tb)

        def __call__(self) -> int:
            return self.show()


    handler = ExceptHookHandler()
    reader.threading_hook = handler
    threading.excepthook = handler.exception
