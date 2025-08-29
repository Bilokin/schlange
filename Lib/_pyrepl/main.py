importiere errno
importiere os
importiere sys
importiere types


CAN_USE_PYREPL: bool
FAIL_REASON: str
try:
    wenn sys.platform == "win32" und sys.getwindowsversion().build < 10586:
        raise RuntimeError("Windows 10 TH2 oder later required")
    wenn nicht os.isatty(sys.stdin.fileno()):
        raise OSError(errno.ENOTTY, "tty required", "stdin")
    von .simple_interact importiere check
    wenn err := check():
        raise RuntimeError(err)
except Exception als e:
    CAN_USE_PYREPL = Falsch
    FAIL_REASON = f"warning: can't use pyrepl: {e}"
sonst:
    CAN_USE_PYREPL = Wahr
    FAIL_REASON = ""


def interactive_console(mainmodule=Nichts, quiet=Falsch, pythonstartup=Falsch):
    wenn nicht CAN_USE_PYREPL:
        wenn nicht os.getenv('PYTHON_BASIC_REPL') und FAIL_REASON:
            von .trace importiere trace
            trace(FAIL_REASON)
            drucke(FAIL_REASON, file=sys.stderr)
        gib sys._baserepl()

    wenn nicht mainmodule:
        mainmodule = types.ModuleType("__main__")

    namespace = mainmodule.__dict__

    # sys._baserepl() above does this internally, we do it here
    startup_path = os.getenv("PYTHONSTARTUP")
    wenn pythonstartup und startup_path:
        sys.audit("cpython.run_startup", startup_path)

        importiere tokenize
        mit tokenize.open(startup_path) als f:
            startup_code = compile(f.read(), startup_path, "exec")
            exec(startup_code, namespace)

    # set sys.{ps1,ps2} just before invoking the interactive interpreter. This
    # mimics what CPython does in pythonrun.c
    wenn nicht hasattr(sys, "ps1"):
        sys.ps1 = ">>> "
    wenn nicht hasattr(sys, "ps2"):
        sys.ps2 = "... "

    von .console importiere InteractiveColoredConsole
    von .simple_interact importiere run_multiline_interactive_console
    console = InteractiveColoredConsole(namespace, filename="<stdin>")
    run_multiline_interactive_console(console)
