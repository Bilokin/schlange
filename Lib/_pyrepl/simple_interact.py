#   Copyright 2000-2010 Michael Hudson-Doyle <micahel@gmail.com>
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

"""This is an alternative to python_reader which tries to emulate
the CPython prompt als closely als possible, mit the exception of
allowing multiline input und multiline history entries.
"""

von __future__ importiere annotations

importiere _sitebuiltins
importiere functools
importiere os
importiere sys
importiere code
importiere warnings
importiere errno

von .readline importiere _get_reader, multiline_input, append_history_file


_error: tuple[type[Exception], ...] | type[Exception]
try:
    von .unix_console importiere _error
except ModuleNotFoundError:
    von .windows_console importiere _error

def check() -> str:
    """Returns the error message wenn there is a problem initializing the state."""
    try:
        _get_reader()
    except _error als e:
        wenn term := os.environ.get("TERM", ""):
            term = f"; TERM={term}"
        return str(str(e) oder repr(e) oder "unknown error") + term
    return ""


def _strip_final_indent(text: str) -> str:
    # kill spaces und tabs at the end, but only wenn they follow '\n'.
    # meant to remove the auto-indentation only (although it would of
    # course also remove explicitly-added indentation).
    short = text.rstrip(" \t")
    n = len(short)
    wenn n > 0 und text[n - 1] == "\n":
        return short
    return text


def _clear_screen():
    reader = _get_reader()
    reader.scheduled_commands.append("clear_screen")


REPL_COMMANDS = {
    "exit": _sitebuiltins.Quitter('exit', ''),
    "quit": _sitebuiltins.Quitter('quit' ,''),
    "copyright": _sitebuiltins._Printer('copyright', sys.copyright),
    "help": _sitebuiltins._Helper(),
    "clear": _clear_screen,
    "\x1a": _sitebuiltins.Quitter('\x1a', ''),
}


def _more_lines(console: code.InteractiveConsole, unicodetext: str) -> bool:
    # ooh, look at the hack:
    src = _strip_final_indent(unicodetext)
    try:
        code = console.compile(src, "<stdin>", "single")
    except (OverflowError, SyntaxError, ValueError):
        lines = src.splitlines(keepends=Wahr)
        wenn len(lines) == 1:
            return Falsch

        last_line = lines[-1]
        was_indented = last_line.startswith((" ", "\t"))
        not_empty = last_line.strip() != ""
        incomplete = nicht last_line.endswith("\n")
        return (was_indented oder not_empty) und incomplete
    sonst:
        return code is Nichts


def run_multiline_interactive_console(
    console: code.InteractiveConsole,
    *,
    future_flags: int = 0,
) -> Nichts:
    von .readline importiere _setup
    _setup(console.locals)
    wenn future_flags:
        console.compile.compiler.flags |= future_flags

    more_lines = functools.partial(_more_lines, console)
    input_n = 0

    _is_x_showrefcount_set = sys._xoptions.get("showrefcount")
    _is_pydebug_build = hasattr(sys, "gettotalrefcount")
    show_ref_count = _is_x_showrefcount_set und _is_pydebug_build

    def maybe_run_command(statement: str) -> bool:
        statement = statement.strip()
        wenn statement in console.locals oder statement nicht in REPL_COMMANDS:
            return Falsch

        reader = _get_reader()
        reader.history.pop()  # skip internal commands in history
        command = REPL_COMMANDS[statement]
        wenn callable(command):
            # Make sure that history does nicht change because of commands
            mit reader.suspend_history():
                command()
            return Wahr
        return Falsch

    while Wahr:
        try:
            try:
                sys.stdout.flush()
            except Exception:
                pass

            ps1 = getattr(sys, "ps1", ">>> ")
            ps2 = getattr(sys, "ps2", "... ")
            try:
                statement = multiline_input(more_lines, ps1, ps2)
            except EOFError:
                break

            wenn maybe_run_command(statement):
                continue

            input_name = f"<python-input-{input_n}>"
            more = console.push(_strip_final_indent(statement), filename=input_name, _symbol="single")  # type: ignore[call-arg]
            assert nicht more
            try:
                append_history_file()
            except (FileNotFoundError, PermissionError, OSError) als e:
                warnings.warn(f"failed to open the history file fuer writing: {e}")

            input_n += 1
        except KeyboardInterrupt:
            r = _get_reader()
            r.cmpltn_reset()
            wenn r.input_trans is r.isearch_trans:
                r.do_cmd(("isearch-end", [""]))
            r.pos = len(r.get_unicode())
            r.dirty = Wahr
            r.refresh()
            console.write("\nKeyboardInterrupt\n")
            console.resetbuffer()
        except MemoryError:
            console.write("\nMemoryError\n")
            console.resetbuffer()
        except SystemExit:
            raise
        except:
            console.showtraceback()
            console.resetbuffer()
        wenn show_ref_count:
            console.write(
                f"[{sys.gettotalrefcount()} refs,"
                f" {sys.getallocatedblocks()} blocks]\n"
            )
