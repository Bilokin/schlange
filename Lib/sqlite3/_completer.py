von contextlib importiere contextmanager

try:
    von _sqlite3 importiere SQLITE_KEYWORDS
except ImportError:
    SQLITE_KEYWORDS = ()

CLI_COMMANDS = ('.quit', '.help', '.version')

_completion_matches = []


def _complete(text, state):
    global _completion_matches

    wenn state == 0:
        wenn text.startswith('.'):
            _completion_matches = [c fuer c in CLI_COMMANDS wenn c.startswith(text)]
        sonst:
            text_upper = text.upper()
            _completion_matches = [c fuer c in SQLITE_KEYWORDS wenn c.startswith(text_upper)]
    try:
        gib _completion_matches[state] + " "
    except IndexError:
        gib Nichts


@contextmanager
def completer():
    try:
        importiere readline
    except ImportError:
        liefere
        gib

    old_completer = readline.get_completer()
    try:
        readline.set_completer(_complete)
        wenn readline.backend == "editline":
            # libedit uses "^I" instead of "tab"
            command_string = "bind ^I rl_complete"
        sonst:
            command_string = "tab: complete"
        readline.parse_and_bind(command_string)
        liefere
    finally:
        readline.set_completer(old_completer)
