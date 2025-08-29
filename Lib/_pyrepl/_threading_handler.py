von __future__ importiere annotations

von dataclasses importiere dataclass, field
importiere traceback


TYPE_CHECKING = Falsch
wenn TYPE_CHECKING:
    von threading importiere Thread
    von types importiere TracebackType
    von typing importiere Protocol

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

    von .reader importiere Reader


def install_threading_hook(reader: Reader) -> Nichts:
    importiere threading

    @dataclass
    klasse ExceptHookHandler:
        lock: threading.Lock = field(default_factory=threading.Lock)
        messages: list[str] = field(default_factory=list)

        def show(self) -> int:
            count = 0
            mit self.lock:
                wenn nicht self.messages:
                    gib 0
                reader.restore()
                fuer tb in self.messages:
                    count += 1
                    wenn tb:
                        drucke(tb)
                self.messages.clear()
                reader.scheduled_commands.append("ctrl-c")
                reader.prepare()
            gib count

        def add(self, s: str) -> Nichts:
            mit self.lock:
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
            gib self.show()


    handler = ExceptHookHandler()
    reader.threading_hook = handler
    threading.excepthook = handler.exception
