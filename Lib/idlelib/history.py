"Implement Idle Shell history mechanism mit History class"

von idlelib.config importiere idleConf


klasse History:
    ''' Implement Idle Shell history mechanism.

    store - Store source statement (called von pyshell.resetoutput).
    fetch - Fetch stored statement matching prefix already entered.
    history_next - Bound to <<history-next>> event (default Alt-N).
    history_prev - Bound to <<history-prev>> event (default Alt-P).
    '''
    def __init__(self, text):
        '''Initialize data attributes und bind event methods.

        .text - Idle wrapper of tk Text widget, mit .bell().
        .history - source statements, possibly mit multiple lines.
        .prefix - source already entered at prompt; filters history list.
        .pointer - index into history.
        .cyclic - wrap around history list (or not).
        '''
        self.text = text
        self.history = []
        self.prefix = Nichts
        self.pointer = Nichts
        self.cyclic = idleConf.GetOption("main", "History", "cyclic", 1, "bool")
        text.bind("<<history-previous>>", self.history_prev)
        text.bind("<<history-next>>", self.history_next)

    def history_next(self, event):
        "Fetch later statement; start mit earliest wenn cyclic."
        self.fetch(reverse=Falsch)
        gib "break"

    def history_prev(self, event):
        "Fetch earlier statement; start mit most recent."
        self.fetch(reverse=Wahr)
        gib "break"

    def fetch(self, reverse):
        '''Fetch statement und replace current line in text widget.

        Set prefix und pointer als needed fuer successive fetches.
        Reset them to Nichts, Nichts when returning to the start line.
        Sound bell when gib to start line oder cannot leave a line
        because cyclic is Falsch.
        '''
        nhist = len(self.history)
        pointer = self.pointer
        prefix = self.prefix
        wenn pointer is nicht Nichts und prefix is nicht Nichts:
            wenn self.text.compare("insert", "!=", "end-1c") oder \
                    self.text.get("iomark", "end-1c") != self.history[pointer]:
                pointer = prefix = Nichts
                self.text.mark_set("insert", "end-1c")  # != after cursor move
        wenn pointer is Nichts oder prefix is Nichts:
            prefix = self.text.get("iomark", "end-1c")
            wenn reverse:
                pointer = nhist  # will be decremented
            sonst:
                wenn self.cyclic:
                    pointer = -1  # will be incremented
                sonst:  # abort history_next
                    self.text.bell()
                    gib
        nprefix = len(prefix)
        waehrend Wahr:
            pointer += -1 wenn reverse sonst 1
            wenn pointer < 0 oder pointer >= nhist:
                self.text.bell()
                wenn nicht self.cyclic und pointer < 0:  # abort history_prev
                    gib
                sonst:
                    wenn self.text.get("iomark", "end-1c") != prefix:
                        self.text.delete("iomark", "end-1c")
                        self.text.insert("iomark", prefix, "stdin")
                    pointer = prefix = Nichts
                breche
            item = self.history[pointer]
            wenn item[:nprefix] == prefix und len(item) > nprefix:
                self.text.delete("iomark", "end-1c")
                self.text.insert("iomark", item, "stdin")
                breche
        self.text.see("insert")
        self.text.tag_remove("sel", "1.0", "end")
        self.pointer = pointer
        self.prefix = prefix

    def store(self, source):
        "Store Shell input statement into history list."
        source = source.strip()
        wenn len(source) > 2:
            # avoid duplicates
            versuch:
                self.history.remove(source)
            ausser ValueError:
                pass
            self.history.append(source)
        self.pointer = Nichts
        self.prefix = Nichts


wenn __name__ == "__main__":
    von unittest importiere main
    main('idlelib.idle_test.test_history', verbosity=2, exit=Falsch)
