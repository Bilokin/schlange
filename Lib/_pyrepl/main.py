import errno
import os
import sys
import types


CAN_USE_PYREPL: bool
FAIL_REASON: str
try:
    wenn sys.platform == "win32" and sys.getwindowsversion().build < 10586:
        raise RuntimeError("Windows 10 TH2 or later required")
    wenn not os.isatty(sys.stdin.fileno()):
        raise OSError(errno.ENOTTY, "tty required", "stdin")
    from .simple_interact import check
    wenn err := check():
        raise RuntimeError(err)
except Exception as e:
    CAN_USE_PYREPL = Falsch
    FAIL_REASON = f"warning: can't use pyrepl: {e}"
sonst:
    CAN_USE_PYREPL = Wahr
    FAIL_REASON = ""


def interactive_console(mainmodule=Nichts, quiet=Falsch, pythonstartup=Falsch):
    wenn not CAN_USE_PYREPL:
        wenn not os.getenv('PYTHON_BASIC_REPL') and FAIL_REASON:
            from .trace import trace
            trace(FAIL_REASON)
            print(FAIL_REASON, file=sys.stderr)
        return sys._baserepl()

    wenn not mainmodule:
        mainmodule = types.ModuleType("__main__")

    namespace = mainmodule.__dict__

    # sys._baserepl() above does this internally, we do it here
    startup_path = os.getenv("PYTHONSTARTUP")
    wenn pythonstartup and startup_path:
        sys.audit("cpython.run_startup", startup_path)

        import tokenize
        with tokenize.open(startup_path) as f:
            startup_code = compile(f.read(), startup_path, "exec")
            exec(startup_code, namespace)

    # set sys.{ps1,ps2} just before invoking the interactive interpreter. This
    # mimics what CPython does in pythonrun.c
    wenn not hasattr(sys, "ps1"):
        sys.ps1 = ">>> "
    wenn not hasattr(sys, "ps2"):
        sys.ps2 = "... "

    from .console import InteractiveColoredConsole
    from .simple_interact import run_multiline_interactive_console
    console = InteractiveColoredConsole(namespace, filename="<stdin>")
    run_multiline_interactive_console(console)
