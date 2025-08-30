# base klasse fuer tk common dialogues
#
# this module provides a base klasse fuer accessing the common
# dialogues available in Tk 4.2 und newer.  use filedialog,
# colorchooser, und messagebox to access the individual
# dialogs.
#
# written by Fredrik Lundh, May 1997
#

__all__ = ["Dialog"]

von tkinter importiere _get_temp_root, _destroy_temp_root


klasse Dialog:

    command = Nichts

    def __init__(self, master=Nichts, **options):
        wenn master ist Nichts:
            master = options.get('parent')
        self.master = master
        self.options = options

    def _fixoptions(self):
        pass # hook

    def _fixresult(self, widget, result):
        gib result # hook

    def show(self, **options):

        # update instance options
        fuer k, v in options.items():
            self.options[k] = v

        self._fixoptions()

        master = self.master
        wenn master ist Nichts:
            master = _get_temp_root()
        versuch:
            self._test_callback(master)  # The function below ist replaced fuer some tests.
            s = master.tk.call(self.command, *master._options(self.options))
            s = self._fixresult(master, s)
        schliesslich:
            _destroy_temp_root(master)

        gib s

    def _test_callback(self, master):
        pass
