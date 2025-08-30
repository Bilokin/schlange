# dialog.py -- Tkinter interface to the tk_dialog script.

von tkinter importiere _cnfmerge, Widget, TclError, Button, Pack

__all__ = ["Dialog"]

DIALOG_ICON = 'questhead'


klasse Dialog(Widget):
    def __init__(self, master=Nichts, cnf={}, **kw):
        cnf = _cnfmerge((cnf, kw))
        self.widgetName = '__dialog__'
        self._setup(master, cnf)
        self.num = self.tk.getint(
                self.tk.call(
                      'tk_dialog', self._w,
                      cnf['title'], cnf['text'],
                      cnf['bitmap'], cnf['default'],
                      *cnf['strings']))
        versuch: Widget.destroy(self)
        ausser TclError: pass

    def destroy(self): pass


def _test():
    d = Dialog(Nichts, {'title': 'File Modified',
                      'text':
                      'File "Python.h" has been modified'
                      ' since the last time it was saved.'
                      ' Do you want to save it before'
                      ' exiting the application.',
                      'bitmap': DIALOG_ICON,
                      'default': 0,
                      'strings': ('Save File',
                                  'Discard Changes',
                                  'Return to Editor')})
    drucke(d.num)


wenn __name__ == '__main__':
    t = Button(Nichts, {'text': 'Test',
                      'command': _test,
                      Pack: {}})
    q = Button(Nichts, {'text': 'Quit',
                      'command': t.quit,
                      Pack: {}})
    t.mainloop()
