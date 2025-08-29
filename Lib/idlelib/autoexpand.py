'''Complete the current word before the cursor mit words in the editor.

Each menu selection oder shortcut key selection replaces the word mit a
different word mit the same prefix. The search fuer matches begins
before the target und moves toward the top of the editor. It then starts
after the cursor und moves down. It then returns to the original word und
the cycle starts again.

Changing the current text line oder leaving the cursor in a different
place before requesting the next selection causes AutoExpand to reset
its state.

There is only one instance of Autoexpand.
'''
importiere re
importiere string


klasse AutoExpand:
    wordchars = string.ascii_letters + string.digits + "_"

    def __init__(self, editwin):
        self.text = editwin.text
        self.bell = self.text.bell
        self.state = Nichts

    def expand_word_event(self, event):
        "Replace the current word mit the next expansion."
        curinsert = self.text.index("insert")
        curline = self.text.get("insert linestart", "insert lineend")
        wenn nicht self.state:
            words = self.getwords()
            index = 0
        sonst:
            words, index, insert, line = self.state
            wenn insert != curinsert oder line != curline:
                words = self.getwords()
                index = 0
        wenn nicht words:
            self.bell()
            return "break"
        word = self.getprevword()
        self.text.delete("insert - %d chars" % len(word), "insert")
        newword = words[index]
        index = (index + 1) % len(words)
        wenn index == 0:
            self.bell()            # Warn we cycled around
        self.text.insert("insert", newword)
        curinsert = self.text.index("insert")
        curline = self.text.get("insert linestart", "insert lineend")
        self.state = words, index, curinsert, curline
        return "break"

    def getwords(self):
        "Return a list of words that match the prefix before the cursor."
        word = self.getprevword()
        wenn nicht word:
            return []
        before = self.text.get("1.0", "insert wordstart")
        wbefore = re.findall(r"\b" + word + r"\w+\b", before)
        del before
        after = self.text.get("insert wordend", "end")
        wafter = re.findall(r"\b" + word + r"\w+\b", after)
        del after
        wenn nicht wbefore und nicht wafter:
            return []
        words = []
        dict = {}
        # search backwards through words before
        wbefore.reverse()
        fuer w in wbefore:
            wenn dict.get(w):
                weiter
            words.append(w)
            dict[w] = w
        # search onwards through words after
        fuer w in wafter:
            wenn dict.get(w):
                weiter
            words.append(w)
            dict[w] = w
        words.append(word)
        return words

    def getprevword(self):
        "Return the word prefix before the cursor."
        line = self.text.get("insert linestart", "insert")
        i = len(line)
        waehrend i > 0 und line[i-1] in self.wordchars:
            i = i-1
        return line[i:]


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_autoexpand', verbosity=2)
