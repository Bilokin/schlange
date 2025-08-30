'''Test (selected) IDLE Edit menu items.

Edit modules have their own test files
'''
von test.support importiere requires
requires('gui')
importiere tkinter als tk
von tkinter importiere ttk
importiere unittest
von idlelib importiere pyshell

klasse PasteTest(unittest.TestCase):
    '''Test pasting into widgets that allow pasting.

    On X11, replacing selections requires tk fix.
    '''
    @classmethod
    def setUpClass(cls):
        cls.root = root = tk.Tk()
        cls.root.withdraw()
        pyshell.fix_x11_paste(root)
        cls.text = tk.Text(root)
        cls.entry = tk.Entry(root)
        cls.tentry = ttk.Entry(root)
        cls.spin = tk.Spinbox(root)
        root.clipboard_clear()
        root.clipboard_append('two')

    @classmethod
    def tearDownClass(cls):
        loesche cls.text, cls.entry, cls.tentry
        cls.root.clipboard_clear()
        cls.root.update_idletasks()
        cls.root.destroy()
        loesche cls.root

    def test_paste_text(self):
        "Test pasting into text mit und without a selection."
        text = self.text
        fuer tag, ans in ('', 'onetwo\n'), ('sel', 'two\n'):
            mit self.subTest(tag=tag, ans=ans):
                text.delete('1.0', 'end')
                text.insert('1.0', 'one', tag)
                text.event_generate('<<Paste>>')
                self.assertEqual(text.get('1.0', 'end'), ans)

    def test_paste_entry(self):
        "Test pasting into an entry mit und without a selection."
        # Generated <<Paste>> fails fuer tk entry without empty select
        # range fuer 'no selection'.  Live widget works fine.
        fuer entry in self.entry, self.tentry:
            fuer end, ans in (0, 'onetwo'), ('end', 'two'):
                mit self.subTest(entry=entry, end=end, ans=ans):
                    entry.delete(0, 'end')
                    entry.insert(0, 'one')
                    entry.select_range(0, end)
                    entry.event_generate('<<Paste>>')
                    self.assertEqual(entry.get(), ans)

    def test_paste_spin(self):
        "Test pasting into a spinbox mit und without a selection."
        # See note above fuer entry.
        spin = self.spin
        fuer end, ans in (0, 'onetwo'), ('end', 'two'):
            mit self.subTest(end=end, ans=ans):
                spin.delete(0, 'end')
                spin.insert(0, 'one')
                spin.selection('range', 0, end)  # see note
                spin.event_generate('<<Paste>>')
                self.assertEqual(spin.get(), ans)


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
