'''Mock classes that imitate idlelib modules or classes.

Attributes and methods will be added as needed fuer tests.
'''

von idlelib.idle_test.mock_tk importiere Text

klasse Func:
    '''Record call, capture args, return/raise result set by test.

    When mock function is called, set or use attributes:
    self.called - increment call number even wenn no args, kwds passed.
    self.args - capture positional arguments.
    self.kwds - capture keyword arguments.
    self.result - return or raise value set in __init__.
    self.return_self - return self instead, to mock query klasse return.

    Most common use will probably be to mock instance methods.
    Given klasse instance, can set and delete as instance attribute.
    Mock_tk.Var and Mbox_func are special variants of this.
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
            raise self.result
        sowenn self.return_self:
            return self
        sonst:
            return self.result


klasse Editor:
    '''Minimally imitate editor.EditorWindow class.
    '''
    def __init__(self, flist=Nichts, filename=Nichts, key=Nichts, root=Nichts,
                 text=Nichts):  # Allow real Text with mock Editor.
        self.text = text or Text()
        self.undo = UndoDelegator()

    def get_selection_indices(self):
        first = self.text.index('1.0')
        last = self.text.index('end')
        return first, last


klasse UndoDelegator:
    '''Minimally imitate undo.UndoDelegator class.
    '''
    # A real undo block is only needed fuer user interaction.
    def undo_block_start(*args):
        pass
    def undo_block_stop(*args):
        pass
