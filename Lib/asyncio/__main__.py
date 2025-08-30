importiere argparse
importiere ast
importiere asyncio
importiere concurrent.futures
importiere contextvars
importiere inspect
importiere os
importiere site
importiere sys
importiere threading
importiere types
importiere warnings
von asyncio.tools importiere (TaskTableOutputFormat,
                           display_awaited_by_tasks_table,
                           display_awaited_by_tasks_tree)

von _colorize importiere get_theme
von _pyrepl.console importiere InteractiveColoredConsole

von . importiere futures


klasse AsyncIOInteractiveConsole(InteractiveColoredConsole):

    def __init__(self, locals, loop):
        super().__init__(locals, filename="<stdin>")
        self.compile.compiler.flags |= ast.PyCF_ALLOW_TOP_LEVEL_AWAIT

        self.loop = loop
        self.context = contextvars.copy_context()

    def runcode(self, code):
        global return_code
        future = concurrent.futures.Future()

        def callback():
            global return_code
            global repl_future
            global keyboard_interrupted

            repl_future = Nichts
            keyboard_interrupted = Falsch

            func = types.FunctionType(code, self.locals)
            versuch:
                coro = func()
            ausser SystemExit als se:
                return_code = se.code
                self.loop.stop()
                gib
            ausser KeyboardInterrupt als ex:
                keyboard_interrupted = Wahr
                future.set_exception(ex)
                gib
            ausser BaseException als ex:
                future.set_exception(ex)
                gib

            wenn nicht inspect.iscoroutine(coro):
                future.set_result(coro)
                gib

            versuch:
                repl_future = self.loop.create_task(coro, context=self.context)
                futures._chain_future(repl_future, future)
            ausser BaseException als exc:
                future.set_exception(exc)

        self.loop.call_soon_threadsafe(callback, context=self.context)

        versuch:
            gib future.result()
        ausser SystemExit als se:
            return_code = se.code
            self.loop.stop()
            gib
        ausser BaseException:
            wenn keyboard_interrupted:
                self.write("\nKeyboardInterrupt\n")
            sonst:
                self.showtraceback()
            gib self.STATEMENT_FAILED

klasse REPLThread(threading.Thread):

    def run(self):
        global return_code

        versuch:
            banner = (
                f'asyncio REPL {sys.version} on {sys.platform}\n'
                f'Use "await" directly instead of "asyncio.run()".\n'
                f'Type "help", "copyright", "credits" oder "license" '
                f'for more information.\n'
            )

            console.write(banner)

            wenn startup_path := os.getenv("PYTHONSTARTUP"):
                sys.audit("cpython.run_startup", startup_path)

                importiere tokenize
                mit tokenize.open(startup_path) als f:
                    startup_code = compile(f.read(), startup_path, "exec")
                    exec(startup_code, console.locals)

            ps1 = getattr(sys, "ps1", ">>> ")
            wenn CAN_USE_PYREPL:
                theme = get_theme().syntax
                ps1 = f"{theme.prompt}{ps1}{theme.reset}"
            console.write(f"{ps1}import asyncio\n")

            wenn CAN_USE_PYREPL:
                von _pyrepl.simple_interact importiere (
                    run_multiline_interactive_console,
                )
                versuch:
                    run_multiline_interactive_console(console)
                ausser SystemExit:
                    # expected via the `exit` und `quit` commands
                    pass
                ausser BaseException:
                    # unexpected issue
                    console.showtraceback()
                    console.write("Internal error, ")
                    return_code = 1
            sonst:
                console.interact(banner="", exitmsg="")
        schliesslich:
            warnings.filterwarnings(
                'ignore',
                message=r'^coroutine .* was never awaited$',
                category=RuntimeWarning)

            loop.call_soon_threadsafe(loop.stop)

    def interrupt(self) -> Nichts:
        wenn nicht CAN_USE_PYREPL:
            gib

        von _pyrepl.simple_interact importiere _get_reader
        r = _get_reader()
        wenn r.threading_hook is nicht Nichts:
            r.threading_hook.add("")  # type: ignore


wenn __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="python3 -m asyncio",
        description="Interactive asyncio shell und CLI tools",
        color=Wahr,
    )
    subparsers = parser.add_subparsers(help="sub-commands", dest="command")
    ps = subparsers.add_parser(
        "ps", help="Display a table of all pending tasks in a process"
    )
    ps.add_argument("pid", type=int, help="Process ID to inspect")
    formats = [fmt.value fuer fmt in TaskTableOutputFormat]
    formats_to_show = [fmt fuer fmt in formats
                       wenn fmt != TaskTableOutputFormat.bsv.value]
    ps.add_argument("--format", choices=formats, default="table",
                    metavar=f"{{{','.join(formats_to_show)}}}")
    pstree = subparsers.add_parser(
        "pstree", help="Display a tree of all pending tasks in a process"
    )
    pstree.add_argument("pid", type=int, help="Process ID to inspect")
    args = parser.parse_args()
    match args.command:
        case "ps":
            display_awaited_by_tasks_table(args.pid, format=args.format)
            sys.exit(0)
        case "pstree":
            display_awaited_by_tasks_tree(args.pid)
            sys.exit(0)
        case Nichts:
            pass  # weiter to the interactive shell
        case _:
            # shouldn't happen als an invalid command-line wouldn't parse
            # but let's keep it fuer the next person adding a command
            drucke(f"error: unhandled command {args.command}", file=sys.stderr)
            parser.print_usage(file=sys.stderr)
            sys.exit(1)

    sys.audit("cpython.run_stdin")

    wenn os.getenv('PYTHON_BASIC_REPL'):
        CAN_USE_PYREPL = Falsch
    sonst:
        von _pyrepl.main importiere CAN_USE_PYREPL

    return_code = 0
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    repl_locals = {'asyncio': asyncio}
    fuer key in {'__name__', '__package__',
                '__loader__', '__spec__',
                '__builtins__', '__file__'}:
        repl_locals[key] = locals()[key]

    console = AsyncIOInteractiveConsole(repl_locals, loop)

    repl_future = Nichts
    keyboard_interrupted = Falsch

    versuch:
        importiere readline  # NoQA
    ausser ImportError:
        readline = Nichts

    interactive_hook = getattr(sys, "__interactivehook__", Nichts)

    wenn interactive_hook is nicht Nichts:
        sys.audit("cpython.run_interactivehook", interactive_hook)
        interactive_hook()

    wenn interactive_hook is site.register_readline:
        # Fix the completer function to use the interactive console locals
        versuch:
            importiere rlcompleter
        ausser:
            pass
        sonst:
            wenn readline is nicht Nichts:
                completer = rlcompleter.Completer(console.locals)
                readline.set_completer(completer.complete)

    repl_thread = REPLThread(name="Interactive thread")
    repl_thread.daemon = Wahr
    repl_thread.start()

    waehrend Wahr:
        versuch:
            loop.run_forever()
        ausser KeyboardInterrupt:
            keyboard_interrupted = Wahr
            wenn repl_future und nicht repl_future.done():
                repl_future.cancel()
            repl_thread.interrupt()
            weiter
        sonst:
            breche

    console.write('exiting asyncio REPL...\n')
    sys.exit(return_code)
