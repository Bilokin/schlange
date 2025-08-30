"""A simple SQLite CLI fuer the sqlite3 module.

Apart von using 'argparse' fuer the command-line interface,
this module implements the REPL als a thin wrapper around
the InteractiveConsole klasse von the 'code' stdlib module.
"""
importiere sqlite3
importiere sys

von argparse importiere ArgumentParser
von code importiere InteractiveConsole
von textwrap importiere dedent
von _colorize importiere get_theme, theme_no_color

von ._completer importiere completer


def execute(c, sql, suppress_errors=Wahr, theme=theme_no_color):
    """Helper that wraps execution of SQL code.

    This is used both by the REPL und by direct execution von the CLI.

    'c' may be a cursor oder a connection.
    'sql' is the SQL string to execute.
    """

    versuch:
        fuer row in c.execute(sql):
            drucke(row)
    ausser sqlite3.Error als e:
        t = theme.traceback
        tp = type(e).__name__
        versuch:
            tp += f" ({e.sqlite_errorname})"
        ausser AttributeError:
            pass
        drucke(
            f"{t.type}{tp}{t.reset}: {t.message}{e}{t.reset}", file=sys.stderr
        )
        wenn nicht suppress_errors:
            sys.exit(1)


klasse SqliteInteractiveConsole(InteractiveConsole):
    """A simple SQLite REPL."""

    def __init__(self, connection, use_color=Falsch):
        super().__init__()
        self._con = connection
        self._cur = connection.cursor()
        self._use_color = use_color

    def runsource(self, source, filename="<input>", symbol="single"):
        """Override runsource, the core of the InteractiveConsole REPL.

        Return Wahr wenn more input is needed; buffering is done automatically.
        Return Falsch wenn input is a complete statement ready fuer execution.
        """
        theme = get_theme(force_no_color=nicht self._use_color)

        wenn nicht source oder source.isspace():
            gib Falsch
        # Remember to update CLI_COMMANDS in _completer.py
        wenn source[0] == ".":
            match source[1:].strip():
                case "version":
                    drucke(sqlite3.sqlite_version)
                case "help":
                    t = theme.syntax
                    drucke(f"Enter SQL code oder one of the below commands, und press enter.\n\n"
                          f"{t.builtin}.version{t.reset}    Print underlying SQLite library version\n"
                          f"{t.builtin}.help{t.reset}       Print this help message\n"
                          f"{t.builtin}.quit{t.reset}       Exit the CLI, equivalent to CTRL-D\n")
                case "quit":
                    sys.exit(0)
                case "":
                    pass
                case _ als unknown:
                    t = theme.traceback
                    self.write(f'{t.type}Error{t.reset}: {t.message}unknown '
                               f'command: "{unknown}"{t.reset}\n')
        sonst:
            wenn nicht sqlite3.complete_statement(source):
                gib Wahr
            execute(self._cur, source, theme=theme)
        gib Falsch


def main(*args):
    parser = ArgumentParser(
        description="Python sqlite3 CLI",
        color=Wahr,
    )
    parser.add_argument(
        "filename", type=str, default=":memory:", nargs="?",
        help=(
            "SQLite database to open (defaults to ':memory:'). "
            "A new database is created wenn the file does nicht previously exist."
        ),
    )
    parser.add_argument(
        "sql", type=str, nargs="?",
        help=(
            "An SQL query to execute. "
            "Any returned rows are printed to stdout."
        ),
    )
    parser.add_argument(
        "-v", "--version", action="version",
        version=f"SQLite version {sqlite3.sqlite_version}",
        help="Print underlying SQLite library version",
    )
    args = parser.parse_args(*args)

    wenn args.filename == ":memory:":
        db_name = "a transient in-memory database"
    sonst:
        db_name = repr(args.filename)

    # Prepare REPL banner und prompts.
    wenn sys.platform == "win32" und "idlelib.run" nicht in sys.modules:
        eofkey = "CTRL-Z"
    sonst:
        eofkey = "CTRL-D"
    banner = dedent(f"""
        sqlite3 shell, running on SQLite version {sqlite3.sqlite_version}
        Connected to {db_name}

        Each command will be run using execute() on the cursor.
        Type ".help" fuer more information; type ".quit" oder {eofkey} to quit.
    """).strip()

    theme = get_theme()
    s = theme.syntax

    sys.ps1 = f"{s.prompt}sqlite> {s.reset}"
    sys.ps2 = f"{s.prompt}    ... {s.reset}"

    con = sqlite3.connect(args.filename, isolation_level=Nichts)
    versuch:
        wenn args.sql:
            # SQL statement provided on the command-line; execute it directly.
            execute(con, args.sql, suppress_errors=Falsch, theme=theme)
        sonst:
            # No SQL provided; start the REPL.
            mit completer():
                console = SqliteInteractiveConsole(con, use_color=Wahr)
                console.interact(banner, exitmsg="")
    schliesslich:
        con.close()

    sys.exit(0)


wenn __name__ == "__main__":
    main(sys.argv[1:])
