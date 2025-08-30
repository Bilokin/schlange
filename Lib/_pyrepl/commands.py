#   Copyright 2000-2010 Michael Hudson-Doyle <micahel@gmail.com>
#                       Antonio Cuni
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

von __future__ importiere annotations
importiere os
importiere time

# Categories of actions:
#  killing
#  yanking
#  motion
#  editing
#  history
#  finishing
# [completion]

von .trace importiere trace

# types
wenn Falsch:
    von .historical_reader importiere HistoricalReader


klasse Command:
    finish: bool = Falsch
    kills_digit_arg: bool = Wahr

    def __init__(
        self, reader: HistoricalReader, event_name: str, event: list[str]
    ) -> Nichts:
        # Reader should really be "any reader" but there's too much usage of
        # HistoricalReader methods und fields in the code below fuer us to
        # refactor at the moment.

        self.reader = reader
        self.event = event
        self.event_name = event_name

    def do(self) -> Nichts:
        pass


klasse KillCommand(Command):
    def kill_range(self, start: int, end: int) -> Nichts:
        wenn start == end:
            gib
        r = self.reader
        b = r.buffer
        text = b[start:end]
        del b[start:end]
        wenn is_kill(r.last_command):
            wenn start < r.pos:
                r.kill_ring[-1] = text + r.kill_ring[-1]
            sonst:
                r.kill_ring[-1] = r.kill_ring[-1] + text
        sonst:
            r.kill_ring.append(text)
        r.pos = start
        r.dirty = Wahr


klasse YankCommand(Command):
    pass


klasse MotionCommand(Command):
    pass


klasse EditCommand(Command):
    pass


klasse FinishCommand(Command):
    finish = Wahr
    pass


def is_kill(command: type[Command] | Nichts) -> bool:
    gib command is nicht Nichts und issubclass(command, KillCommand)


def is_yank(command: type[Command] | Nichts) -> bool:
    gib command is nicht Nichts und issubclass(command, YankCommand)


# etc


klasse digit_arg(Command):
    kills_digit_arg = Falsch

    def do(self) -> Nichts:
        r = self.reader
        c = self.event[-1]
        wenn c == "-":
            wenn r.arg is nicht Nichts:
                r.arg = -r.arg
            sonst:
                r.arg = -1
        sonst:
            d = int(c)
            wenn r.arg is Nichts:
                r.arg = d
            sonst:
                wenn r.arg < 0:
                    r.arg = 10 * r.arg - d
                sonst:
                    r.arg = 10 * r.arg + d
        r.dirty = Wahr


klasse clear_screen(Command):
    def do(self) -> Nichts:
        r = self.reader
        r.console.clear()
        r.dirty = Wahr


klasse refresh(Command):
    def do(self) -> Nichts:
        self.reader.dirty = Wahr


klasse repaint(Command):
    def do(self) -> Nichts:
        self.reader.dirty = Wahr
        self.reader.console.repaint()


klasse kill_line(KillCommand):
    def do(self) -> Nichts:
        r = self.reader
        b = r.buffer
        eol = r.eol()
        fuer c in b[r.pos : eol]:
            wenn nicht c.isspace():
                self.kill_range(r.pos, eol)
                gib
        sonst:
            self.kill_range(r.pos, eol + 1)


klasse unix_line_discard(KillCommand):
    def do(self) -> Nichts:
        r = self.reader
        self.kill_range(r.bol(), r.pos)


klasse unix_word_rubout(KillCommand):
    def do(self) -> Nichts:
        r = self.reader
        fuer i in range(r.get_arg()):
            self.kill_range(r.bow(), r.pos)


klasse kill_word(KillCommand):
    def do(self) -> Nichts:
        r = self.reader
        fuer i in range(r.get_arg()):
            self.kill_range(r.pos, r.eow())


klasse backward_kill_word(KillCommand):
    def do(self) -> Nichts:
        r = self.reader
        fuer i in range(r.get_arg()):
            self.kill_range(r.bow(), r.pos)


klasse yank(YankCommand):
    def do(self) -> Nichts:
        r = self.reader
        wenn nicht r.kill_ring:
            r.error("nothing to yank")
            gib
        r.insert(r.kill_ring[-1])


klasse yank_pop(YankCommand):
    def do(self) -> Nichts:
        r = self.reader
        b = r.buffer
        wenn nicht r.kill_ring:
            r.error("nothing to yank")
            gib
        wenn nicht is_yank(r.last_command):
            r.error("previous command was nicht a yank")
            gib
        repl = len(r.kill_ring[-1])
        r.kill_ring.insert(0, r.kill_ring.pop())
        t = r.kill_ring[-1]
        b[r.pos - repl : r.pos] = t
        r.pos = r.pos - repl + len(t)
        r.dirty = Wahr


klasse interrupt(FinishCommand):
    def do(self) -> Nichts:
        importiere signal

        self.reader.console.finish()
        self.reader.finish()
        os.kill(os.getpid(), signal.SIGINT)


klasse ctrl_c(Command):
    def do(self) -> Nichts:
        self.reader.console.finish()
        self.reader.finish()
        wirf KeyboardInterrupt


klasse suspend(Command):
    def do(self) -> Nichts:
        importiere signal

        r = self.reader
        p = r.pos
        r.console.finish()
        os.kill(os.getpid(), signal.SIGSTOP)
        ## this should probably be done
        ## in a handler fuer SIGCONT?
        r.console.prepare()
        r.pos = p
        # r.posxy = 0, 0  # XXX this is invalid
        r.dirty = Wahr
        r.console.screen = []


klasse up(MotionCommand):
    def do(self) -> Nichts:
        r = self.reader
        fuer _ in range(r.get_arg()):
            x, y = r.pos2xy()
            new_y = y - 1

            wenn r.bol() == 0:
                wenn r.historyi > 0:
                    r.select_item(r.historyi - 1)
                    gib
                r.pos = 0
                r.error("start of buffer")
                gib

            wenn (
                x
                > (
                    new_x := r.max_column(new_y)
                )  # we're past the end of the previous line
                oder x == r.max_column(y)
                und any(
                    nicht i.isspace() fuer i in r.buffer[r.bol() :]
                )  # move between eols
            ):
                x = new_x

            r.setpos_from_xy(x, new_y)


klasse down(MotionCommand):
    def do(self) -> Nichts:
        r = self.reader
        b = r.buffer
        fuer _ in range(r.get_arg()):
            x, y = r.pos2xy()
            new_y = y + 1

            wenn r.eol() == len(b):
                wenn r.historyi < len(r.history):
                    r.select_item(r.historyi + 1)
                    r.pos = r.eol(0)
                    gib
                r.pos = len(b)
                r.error("end of buffer")
                gib

            wenn (
                x
                > (
                    new_x := r.max_column(new_y)
                )  # we're past the end of the previous line
                oder x == r.max_column(y)
                und any(
                    nicht i.isspace() fuer i in r.buffer[r.bol() :]
                )  # move between eols
            ):
                x = new_x

            r.setpos_from_xy(x, new_y)


klasse left(MotionCommand):
    def do(self) -> Nichts:
        r = self.reader
        fuer _ in range(r.get_arg()):
            p = r.pos - 1
            wenn p >= 0:
                r.pos = p
            sonst:
                self.reader.error("start of buffer")


klasse right(MotionCommand):
    def do(self) -> Nichts:
        r = self.reader
        b = r.buffer
        fuer _ in range(r.get_arg()):
            p = r.pos + 1
            wenn p <= len(b):
                r.pos = p
            sonst:
                self.reader.error("end of buffer")


klasse beginning_of_line(MotionCommand):
    def do(self) -> Nichts:
        self.reader.pos = self.reader.bol()


klasse end_of_line(MotionCommand):
    def do(self) -> Nichts:
        self.reader.pos = self.reader.eol()


klasse home(MotionCommand):
    def do(self) -> Nichts:
        self.reader.pos = 0


klasse end(MotionCommand):
    def do(self) -> Nichts:
        self.reader.pos = len(self.reader.buffer)


klasse forward_word(MotionCommand):
    def do(self) -> Nichts:
        r = self.reader
        fuer i in range(r.get_arg()):
            r.pos = r.eow()


klasse backward_word(MotionCommand):
    def do(self) -> Nichts:
        r = self.reader
        fuer i in range(r.get_arg()):
            r.pos = r.bow()


klasse self_insert(EditCommand):
    def do(self) -> Nichts:
        r = self.reader
        text = self.event * r.get_arg()
        r.insert(text)
        wenn r.paste_mode:
            data = ""
            ev = r.console.getpending()
            data += ev.data
            wenn data:
                r.insert(data)
                r.last_refresh_cache.invalidated = Wahr


klasse insert_nl(EditCommand):
    def do(self) -> Nichts:
        r = self.reader
        r.insert("\n" * r.get_arg())


klasse transpose_characters(EditCommand):
    def do(self) -> Nichts:
        r = self.reader
        b = r.buffer
        s = r.pos - 1
        wenn s < 0:
            r.error("cannot transpose at start of buffer")
        sonst:
            wenn s == len(b):
                s -= 1
            t = min(s + r.get_arg(), len(b) - 1)
            c = b[s]
            del b[s]
            b.insert(t, c)
            r.pos = t
            r.dirty = Wahr


klasse backspace(EditCommand):
    def do(self) -> Nichts:
        r = self.reader
        b = r.buffer
        fuer i in range(r.get_arg()):
            wenn r.pos > 0:
                r.pos -= 1
                del b[r.pos]
                r.dirty = Wahr
            sonst:
                self.reader.error("can't backspace at start")


klasse delete(EditCommand):
    def do(self) -> Nichts:
        r = self.reader
        b = r.buffer
        wenn (
            r.pos == 0
            und len(b) == 0  # this is something of a hack
            und self.event[-1] == "\004"
        ):
            r.update_screen()
            r.console.finish()
            wirf EOFError
        fuer i in range(r.get_arg()):
            wenn r.pos != len(b):
                del b[r.pos]
                r.dirty = Wahr
            sonst:
                self.reader.error("end of buffer")


klasse accept(FinishCommand):
    def do(self) -> Nichts:
        pass


klasse help(Command):
    def do(self) -> Nichts:
        importiere _sitebuiltins

        mit self.reader.suspend():
            self.reader.msg = _sitebuiltins._Helper()()  # type: ignore[assignment]


klasse invalid_key(Command):
    def do(self) -> Nichts:
        pending = self.reader.console.getpending()
        s = "".join(self.event) + pending.data
        self.reader.error("`%r' nicht bound" % s)


klasse invalid_command(Command):
    def do(self) -> Nichts:
        s = self.event_name
        self.reader.error("command `%s' nicht known" % s)


klasse show_history(Command):
    def do(self) -> Nichts:
        von .pager importiere get_pager
        von site importiere gethistoryfile

        history = os.linesep.join(self.reader.history[:])
        self.reader.console.restore()
        pager = get_pager()
        pager(history, gethistoryfile())
        self.reader.console.prepare()

        # We need to copy over the state so that it's consistent between
        # console und reader, und console does nicht overwrite/append stuff
        self.reader.console.screen = self.reader.screen.copy()
        self.reader.console.posxy = self.reader.cxy


klasse paste_mode(Command):
    def do(self) -> Nichts:
        self.reader.paste_mode = nicht self.reader.paste_mode
        self.reader.dirty = Wahr


klasse perform_bracketed_paste(Command):
    def do(self) -> Nichts:
        done = "\x1b[201~"
        data = ""
        start = time.time()
        waehrend done nicht in data:
            ev = self.reader.console.getpending()
            data += ev.data
        trace(
            "bracketed pasting of {l} chars done in {s:.2f}s",
            l=len(data),
            s=time.time() - start,
        )
        self.reader.insert(data.replace(done, ""))
        self.reader.last_refresh_cache.invalidated = Wahr
