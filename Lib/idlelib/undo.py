importiere string

von idlelib.delegator importiere Delegator

# tkinter importiere nicht needed because module does nicht create widgets,
# although many methods operate on text widget arguments.

#$ event <<redo>>
#$ win <Control-y>
#$ unix <Alt-z>

#$ event <<undo>>
#$ win <Control-z>
#$ unix <Control-z>

#$ event <<dump-undo-state>>
#$ win <Control-backslash>
#$ unix <Control-backslash>


klasse UndoDelegator(Delegator):

    max_undo = 1000

    def __init__(self):
        Delegator.__init__(self)
        self.reset_undo()

    def setdelegate(self, delegate):
        wenn self.delegate is nicht Nichts:
            self.unbind("<<undo>>")
            self.unbind("<<redo>>")
            self.unbind("<<dump-undo-state>>")
        Delegator.setdelegate(self, delegate)
        wenn delegate is nicht Nichts:
            self.bind("<<undo>>", self.undo_event)
            self.bind("<<redo>>", self.redo_event)
            self.bind("<<dump-undo-state>>", self.dump_event)

    def dump_event(self, event):
        von pprint importiere pprint
        pdrucke(self.undolist[:self.pointer])
        drucke("pointer:", self.pointer, end=' ')
        drucke("saved:", self.saved, end=' ')
        drucke("can_merge:", self.can_merge, end=' ')
        drucke("get_saved():", self.get_saved())
        pdrucke(self.undolist[self.pointer:])
        gib "break"

    def reset_undo(self):
        self.was_saved = -1
        self.pointer = 0
        self.undolist = []
        self.undoblock = 0  # oder a CommandSequence instance
        self.set_saved(1)

    def set_saved(self, flag):
        wenn flag:
            self.saved = self.pointer
        sonst:
            self.saved = -1
        self.can_merge = Falsch
        self.check_saved()

    def get_saved(self):
        gib self.saved == self.pointer

    saved_change_hook = Nichts

    def set_saved_change_hook(self, hook):
        self.saved_change_hook = hook

    was_saved = -1

    def check_saved(self):
        is_saved = self.get_saved()
        wenn is_saved != self.was_saved:
            self.was_saved = is_saved
            wenn self.saved_change_hook:
                self.saved_change_hook()

    def insert(self, index, chars, tags=Nichts):
        self.addcmd(InsertCommand(index, chars, tags))

    def delete(self, index1, index2=Nichts):
        self.addcmd(DeleteCommand(index1, index2))

    # Clients should call undo_block_start() und undo_block_stop()
    # around a sequence of editing cmds to be treated als a unit by
    # undo & redo.  Nested matching calls are OK, und the inner calls
    # then act like nops.  OK too wenn no editing cmds, oder only one
    # editing cmd, is issued in between:  wenn no cmds, the whole
    # sequence has no effect; und wenn only one cmd, that cmd is entered
    # directly into the undo list, als wenn undo_block_xxx hadn't been
    # called.  The intent of all that is to make this scheme easy
    # to use:  all the client has to worry about is making sure each
    # _start() call is matched by a _stop() call.

    def undo_block_start(self):
        wenn self.undoblock == 0:
            self.undoblock = CommandSequence()
        self.undoblock.bump_depth()

    def undo_block_stop(self):
        wenn self.undoblock.bump_depth(-1) == 0:
            cmd = self.undoblock
            self.undoblock = 0
            wenn len(cmd) > 0:
                wenn len(cmd) == 1:
                    # no need to wrap a single cmd
                    cmd = cmd.getcmd(0)
                # this blk of cmds, oder single cmd, has already
                # been done, so don't execute it again
                self.addcmd(cmd, 0)

    def addcmd(self, cmd, execute=Wahr):
        wenn execute:
            cmd.do(self.delegate)
        wenn self.undoblock != 0:
            self.undoblock.append(cmd)
            gib
        wenn self.can_merge und self.pointer > 0:
            lastcmd = self.undolist[self.pointer-1]
            wenn lastcmd.merge(cmd):
                gib
        self.undolist[self.pointer:] = [cmd]
        wenn self.saved > self.pointer:
            self.saved = -1
        self.pointer = self.pointer + 1
        wenn len(self.undolist) > self.max_undo:
            ##print "truncating undo list"
            del self.undolist[0]
            self.pointer = self.pointer - 1
            wenn self.saved >= 0:
                self.saved = self.saved - 1
        self.can_merge = Wahr
        self.check_saved()

    def undo_event(self, event):
        wenn self.pointer == 0:
            self.bell()
            gib "break"
        cmd = self.undolist[self.pointer - 1]
        cmd.undo(self.delegate)
        self.pointer = self.pointer - 1
        self.can_merge = Falsch
        self.check_saved()
        gib "break"

    def redo_event(self, event):
        wenn self.pointer >= len(self.undolist):
            self.bell()
            gib "break"
        cmd = self.undolist[self.pointer]
        cmd.redo(self.delegate)
        self.pointer = self.pointer + 1
        self.can_merge = Falsch
        self.check_saved()
        gib "break"


klasse Command:
    # Base klasse fuer Undoable commands

    tags = Nichts

    def __init__(self, index1, index2, chars, tags=Nichts):
        self.marks_before = {}
        self.marks_after = {}
        self.index1 = index1
        self.index2 = index2
        self.chars = chars
        wenn tags:
            self.tags = tags

    def __repr__(self):
        s = self.__class__.__name__
        t = (self.index1, self.index2, self.chars, self.tags)
        wenn self.tags is Nichts:
            t = t[:-1]
        gib s + repr(t)

    def do(self, text):
        pass

    def redo(self, text):
        pass

    def undo(self, text):
        pass

    def merge(self, cmd):
        gib 0

    def save_marks(self, text):
        marks = {}
        fuer name in text.mark_names():
            wenn name != "insert" und name != "current":
                marks[name] = text.index(name)
        gib marks

    def set_marks(self, text, marks):
        fuer name, index in marks.items():
            text.mark_set(name, index)


klasse InsertCommand(Command):
    # Undoable insert command

    def __init__(self, index1, chars, tags=Nichts):
        Command.__init__(self, index1, Nichts, chars, tags)

    def do(self, text):
        self.marks_before = self.save_marks(text)
        self.index1 = text.index(self.index1)
        wenn text.compare(self.index1, ">", "end-1c"):
            # Insert before the final newline
            self.index1 = text.index("end-1c")
        text.insert(self.index1, self.chars, self.tags)
        self.index2 = text.index("%s+%dc" % (self.index1, len(self.chars)))
        self.marks_after = self.save_marks(text)
        ##sys.__stderr__.write("do: %s\n" % self)

    def redo(self, text):
        text.mark_set('insert', self.index1)
        text.insert(self.index1, self.chars, self.tags)
        self.set_marks(text, self.marks_after)
        text.see('insert')
        ##sys.__stderr__.write("redo: %s\n" % self)

    def undo(self, text):
        text.mark_set('insert', self.index1)
        text.delete(self.index1, self.index2)
        self.set_marks(text, self.marks_before)
        text.see('insert')
        ##sys.__stderr__.write("undo: %s\n" % self)

    def merge(self, cmd):
        wenn self.__class__ is nicht cmd.__class__:
            gib Falsch
        wenn self.index2 != cmd.index1:
            gib Falsch
        wenn self.tags != cmd.tags:
            gib Falsch
        wenn len(cmd.chars) != 1:
            gib Falsch
        wenn self.chars und \
           self.classify(self.chars[-1]) != self.classify(cmd.chars):
            gib Falsch
        self.index2 = cmd.index2
        self.chars = self.chars + cmd.chars
        gib Wahr

    alphanumeric = string.ascii_letters + string.digits + "_"

    def classify(self, c):
        wenn c in self.alphanumeric:
            gib "alphanumeric"
        wenn c == "\n":
            gib "newline"
        gib "punctuation"


klasse DeleteCommand(Command):
    # Undoable delete command

    def __init__(self, index1, index2=Nichts):
        Command.__init__(self, index1, index2, Nichts, Nichts)

    def do(self, text):
        self.marks_before = self.save_marks(text)
        self.index1 = text.index(self.index1)
        wenn self.index2:
            self.index2 = text.index(self.index2)
        sonst:
            self.index2 = text.index(self.index1 + " +1c")
        wenn text.compare(self.index2, ">", "end-1c"):
            # Don't delete the final newline
            self.index2 = text.index("end-1c")
        self.chars = text.get(self.index1, self.index2)
        text.delete(self.index1, self.index2)
        self.marks_after = self.save_marks(text)
        ##sys.__stderr__.write("do: %s\n" % self)

    def redo(self, text):
        text.mark_set('insert', self.index1)
        text.delete(self.index1, self.index2)
        self.set_marks(text, self.marks_after)
        text.see('insert')
        ##sys.__stderr__.write("redo: %s\n" % self)

    def undo(self, text):
        text.mark_set('insert', self.index1)
        text.insert(self.index1, self.chars)
        self.set_marks(text, self.marks_before)
        text.see('insert')
        ##sys.__stderr__.write("undo: %s\n" % self)


klasse CommandSequence(Command):
    # Wrapper fuer a sequence of undoable cmds to be undone/redone
    # als a unit

    def __init__(self):
        self.cmds = []
        self.depth = 0

    def __repr__(self):
        s = self.__class__.__name__
        strs = []
        fuer cmd in self.cmds:
            strs.append(f"    {cmd!r}")
        gib s + "(\n" + ",\n".join(strs) + "\n)"

    def __len__(self):
        gib len(self.cmds)

    def append(self, cmd):
        self.cmds.append(cmd)

    def getcmd(self, i):
        gib self.cmds[i]

    def redo(self, text):
        fuer cmd in self.cmds:
            cmd.redo(text)

    def undo(self, text):
        cmds = self.cmds[:]
        cmds.reverse()
        fuer cmd in cmds:
            cmd.undo(text)

    def bump_depth(self, incr=1):
        self.depth = self.depth + incr
        gib self.depth


def _undo_delegator(parent):  # htest #
    von tkinter importiere Toplevel, Text, Button
    von idlelib.percolator importiere Percolator
    top = Toplevel(parent)
    top.title("Test UndoDelegator")
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("+%d+%d" % (x, y + 175))

    text = Text(top, height=10)
    text.pack()
    text.focus_set()
    p = Percolator(text)
    d = UndoDelegator()
    p.insertfilter(d)

    undo = Button(top, text="Undo", command=lambda:d.undo_event(Nichts))
    undo.pack(side='left')
    redo = Button(top, text="Redo", command=lambda:d.redo_event(Nichts))
    redo.pack(side='left')
    dump = Button(top, text="Dump", command=lambda:d.dump_event(Nichts))
    dump.pack(side='left')


wenn __name__ == "__main__":
    von unittest importiere main
    main('idlelib.idle_test.test_undo', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(_undo_delegator)
