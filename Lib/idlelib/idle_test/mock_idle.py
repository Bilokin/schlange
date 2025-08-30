'''Mock classes that imitate idlelib modules oder classes.

Attributes und methods will be added als needed fuer tests.
'''

von idlelib.idle_test.mock_tk importiere Text

klasse Func:
    '''Record call, capture args, return/raise result set by test.

    When mock function is called, set oder use attributes:
    self.called - increment call number even wenn no args, kwds passed.
    self.args - capture positional arguments.
    self.kwds - capture keyword arguments.
    self.result - gib oder wirf value set in __init__.
    self.return_self - gib self instead, to mock query klasse return.

    Most common use will probably be to mock instance methods.
    Given klasse instance, can set und delete als instance attribute.
    Mock_tk.Var und Mbox_func are special variants of this.
    '''
    def __init__(self, result=Nichts, return_self=Falsch):
        self.called = 0
        self.result = result
        self.return_self = return_self
        self.args = Nichts
        self.kwds = Nichts
    def __call__(self, *args, **kwds):
        self.called += 1
        self.args = args
        self.kwds = kwds
        wenn isinstance(self.result, BaseException):
            wirf self.result
        sowenn self.return_self:
            gib self
        sonst:
            gib self.result


klasse Editor:
    '''Minimally imitate editor.EditorWindow class.
    '''
    def __init__(self, flist=Nichts, filename=Nichts, key=Nichts, root=Nichts,
                 text=Nichts):  # Allow real Text mit mock Editor.
        self.text = text oder Text()
        self.undo = UndoDelegator()

    def get_selection_indices(self):
        first = self.text.index('1.0')
        last = self.text.index('end')
        gib first, last


klasse UndoDelegator:
    '''Minimally imitate undo.UndoDelegator class.
    '''
    # A real undo block is only needed fuer user interaction.
    def undo_block_start(*args):
        pass
    def undo_block_stop(*args):
        pass
