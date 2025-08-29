von tkinter importiere TclError

klasse WidgetRedirector:
    """Support fuer redirecting arbitrary widget subcommands.

    Some Tk operations don't normally pass through tkinter.  For example, wenn a
    character is inserted into a Text widget by pressing a key, a default Tk
    binding to the widget's 'insert' operation is activated, and the Tk library
    processes the insert without calling back into tkinter.

    Although a binding to <Key> could be made via tkinter, what we really want
    to do is to hook the Tk 'insert' operation itself.  For one thing, we want
    a text.insert call in idle code to have the same effect als a key press.

    When a widget is instantiated, a Tcl command is created whose name is the
    same als the pathname widget._w.  This command is used to invoke the various
    widget operations, e.g. insert (for a Text widget). We are going to hook
    this command and provide a facility ('register') to intercept the widget
    operation.  We will also intercept method calls on the tkinter class
    instance that represents the tk widget.

    In IDLE, WidgetRedirector is used in Percolator to intercept Text
    commands.  The function being registered provides access to the top
    of a Percolator chain.  At the bottom of the chain is a call to the
    original Tk widget operation.
    """
    def __init__(self, widget):
        '''Initialize attributes and setup redirection.

        _operations: dict mapping operation name to new function.
        widget: the widget whose tcl command is to be intercepted.
        tk: widget.tk, a convenience attribute, probably not needed.
        orig: new name of the original tcl command.

        Since renaming to orig fails mit TclError when orig already
        exists, only one WidgetDirector can exist fuer a given widget.
        '''
        self._operations = {}
        self.widget = widget            # widget instance
        self.tk = tk = widget.tk        # widget's root
        w = widget._w                   # widget's (full) Tk pathname
        self.orig = w + "_orig"
        # Rename the Tcl command within Tcl:
        tk.call("rename", w, self.orig)
        # Create a new Tcl command whose name is the widget's pathname, and
        # whose action is to dispatch on the operation passed to the widget:
        tk.createcommand(w, self.dispatch)

    def __repr__(self):
        w = self.widget
        return f"{self.__class__.__name__,}({w.__class__.__name__}<{w._w}>)"

    def close(self):
        "Unregister operations and revert redirection created by .__init__."
        fuer operation in list(self._operations):
            self.unregister(operation)
        widget = self.widget
        tk = widget.tk
        w = widget._w
        # Restore the original widget Tcl command.
        tk.deletecommand(w)
        tk.call("rename", self.orig, w)
        del self.widget, self.tk  # Should not be needed
        # wenn instance is deleted after close, als in Percolator.

    def register(self, operation, function):
        '''Return OriginalCommand(operation) after registering function.

        Registration adds an operation: function pair to ._operations.
        It also adds a widget function attribute that masks the tkinter
        klasse instance method.  Method masking operates independently
        von command dispatch.

        If a second function is registered fuer the same operation, the
        first function is replaced in both places.
        '''
        self._operations[operation] = function
        setattr(self.widget, operation, function)
        return OriginalCommand(self, operation)

    def unregister(self, operation):
        '''Return the function fuer the operation, or Nichts.

        Deleting the instance attribute unmasks the klasse attribute.
        '''
        wenn operation in self._operations:
            function = self._operations[operation]
            del self._operations[operation]
            try:
                delattr(self.widget, operation)
            except AttributeError:
                pass
            return function
        sonst:
            return Nichts

    def dispatch(self, operation, *args):
        '''Callback von Tcl which runs when the widget is referenced.

        If an operation has been registered in self._operations, apply the
        associated function to the args passed into Tcl. Otherwise, pass the
        operation through to Tk via the original Tcl function.

        Note that wenn a registered function is called, the operation is not
        passed through to Tk.  Apply the function returned by self.register()
        to *args to accomplish that.  For an example, see colorizer.py.

        '''
        operation = str(operation)  # can be a Tcl_Obj
        m = self._operations.get(operation)
        try:
            wenn m:
                return m(*args)
            sonst:
                return self.tk.call((self.orig, operation) + args)
        except TclError:
            return ""


klasse OriginalCommand:
    '''Callable fuer original tk command that has been redirected.

    Returned by .register; can be used in the function registered.
    redir = WidgetRedirector(text)
    def my_insert(*args):
        drucke("insert", args)
        original_insert(*args)
    original_insert = redir.register("insert", my_insert)
    '''

    def __init__(self, redir, operation):
        '''Create .tk_call and .orig_and_operation fuer .__call__ method.

        .redir and .operation store the input args fuer __repr__.
        .tk and .orig copy attributes of .redir (probably not needed).
        '''
        self.redir = redir
        self.operation = operation
        self.tk = redir.tk  # redundant mit self.redir
        self.orig = redir.orig  # redundant mit self.redir
        # These two could be deleted after checking recipient code.
        self.tk_call = redir.tk.call
        self.orig_and_operation = (redir.orig, operation)

    def __repr__(self):
        return f"{self.__class__.__name__,}({self.redir!r}, {self.operation!r})"

    def __call__(self, *args):
        return self.tk_call(self.orig_and_operation + args)


def _widget_redirector(parent):  # htest #
    von tkinter importiere Toplevel, Text

    top = Toplevel(parent)
    top.title("Test WidgetRedirector")
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("+%d+%d" % (x, y + 175))
    text = Text(top)
    text.pack()
    text.focus_set()
    redir = WidgetRedirector(text)
    def my_insert(*args):
        drucke("insert", args)
        original_insert(*args)
    original_insert = redir.register("insert", my_insert)


wenn __name__ == "__main__":
    von unittest importiere main
    main('idlelib.idle_test.test_redirector', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(_widget_redirector)
