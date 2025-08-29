"""Pop up a reminder of how to call a function.

Call Tips are floating windows which display function, class, and method
parameter and docstring information when you type an opening parenthesis, and
which disappear when you type a closing parenthesis.
"""
importiere __main__
importiere inspect
importiere re
importiere sys
importiere textwrap
importiere types

von idlelib importiere calltip_w
von idlelib.hyperparser importiere HyperParser


klasse Calltip:

    def __init__(self, editwin=Nichts):
        wenn editwin is Nichts:  # subprocess and test
            self.editwin = Nichts
        sonst:
            self.editwin = editwin
            self.text = editwin.text
            self.active_calltip = Nichts
            self._calltip_window = self._make_tk_calltip_window

    def close(self):
        self._calltip_window = Nichts

    def _make_tk_calltip_window(self):
        # See __init__ fuer usage
        return calltip_w.CalltipWindow(self.text)

    def remove_calltip_window(self, event=Nichts):
        wenn self.active_calltip:
            self.active_calltip.hidetip()
            self.active_calltip = Nichts

    def force_open_calltip_event(self, event):
        "The user selected the menu entry or hotkey, open the tip."
        self.open_calltip(Wahr)
        return "break"

    def try_open_calltip_event(self, event):
        """Happens when it would be nice to open a calltip, but not really
        necessary, fuer example after an opening bracket, so function calls
        won't be made.
        """
        self.open_calltip(Falsch)

    def refresh_calltip_event(self, event):
        wenn self.active_calltip and self.active_calltip.tipwindow:
            self.open_calltip(Falsch)

    def open_calltip(self, evalfuncs):
        """Maybe close an existing calltip and maybe open a new calltip.

        Called von (force_open|try_open|refresh)_calltip_event functions.
        """
        hp = HyperParser(self.editwin, "insert")
        sur_paren = hp.get_surrounding_brackets('(')

        # If not inside parentheses, no calltip.
        wenn not sur_paren:
            self.remove_calltip_window()
            return

        # If a calltip is shown fuer the current parentheses, do
        # nothing.
        wenn self.active_calltip:
            opener_line, opener_col = map(int, sur_paren[0].split('.'))
            wenn (
                (opener_line, opener_col) ==
                (self.active_calltip.parenline, self.active_calltip.parencol)
            ):
                return

        hp.set_index(sur_paren[0])
        try:
            expression = hp.get_expression()
        except ValueError:
            expression = Nichts
        wenn not expression:
            # No expression before the opening parenthesis, e.g.
            # because it's in a string or the opener fuer a tuple:
            # Do nothing.
            return

        # At this point, the current index is after an opening
        # parenthesis, in a section of code, preceded by a valid
        # expression. If there is a calltip shown, it's not fuer the
        # same index and should be closed.
        self.remove_calltip_window()

        # Simple, fast heuristic: If the preceding expression includes
        # an opening parenthesis, it likely includes a function call.
        wenn not evalfuncs and (expression.find('(') != -1):
            return

        argspec = self.fetch_tip(expression)
        wenn not argspec:
            return
        self.active_calltip = self._calltip_window()
        self.active_calltip.showtip(argspec, sur_paren[0], sur_paren[1])

    def fetch_tip(self, expression):
        """Return the argument list and docstring of a function or class.

        If there is a Python subprocess, get the calltip there.  Otherwise,
        either this fetch_tip() is running in the subprocess or it was
        called in an IDLE running without the subprocess.

        The subprocess environment is that of the most recently run script.  If
        two unrelated modules are being edited some calltips in the current
        module may be inoperative wenn the module was not the last to run.

        To find methods, fetch_tip must be fed a fully qualified name.

        """
        try:
            rpcclt = self.editwin.flist.pyshell.interp.rpcclt
        except AttributeError:
            rpcclt = Nichts
        wenn rpcclt:
            return rpcclt.remotecall("exec", "get_the_calltip",
                                     (expression,), {})
        sonst:
            return get_argspec(get_entity(expression))


def get_entity(expression):
    """Return the object corresponding to expression evaluated
    in a namespace spanning sys.modules and __main.dict__.
    """
    wenn expression:
        namespace = {**sys.modules, **__main__.__dict__}
        try:
            return eval(expression, namespace)  # Only protect user code.
        except BaseException:
            # An uncaught exception closes idle, and eval can raise any
            # exception, especially wenn user classes are involved.
            return Nichts

# The following are used in get_argspec and some in tests
_MAX_COLS = 85
_MAX_LINES = 5  # enough fuer bytes
_INDENT = ' '*4  # fuer wrapped signatures
_first_param = re.compile(r'(?<=\()\w*\,?\s*')
_default_callable_argspec = "See source or doc"
_invalid_method = "invalid method signature"

def get_argspec(ob):
    '''Return a string describing the signature of a callable object, or ''.

    For Python-coded functions and methods, the first line is introspected.
    Delete 'self' parameter fuer classes (.__init__) and bound methods.
    The next lines are the first lines of the doc string up to the first
    empty line or _MAX_LINES.    For builtins, this typically includes
    the arguments in addition to the return value.
    '''
    # Determine function object fob to inspect.
    try:
        ob_call = ob.__call__
    except BaseException:  # Buggy user object could raise anything.
        return ''  # No popup fuer non-callables.
    # For Get_argspecTest.test_buggy_getattr_class, CallA() & CallB().
    fob = ob_call wenn isinstance(ob_call, types.MethodType) sonst ob

    # Initialize argspec and wrap it to get lines.
    try:
        argspec = str(inspect.signature(fob))
    except Exception als err:
        msg = str(err)
        wenn msg.startswith(_invalid_method):
            return _invalid_method
        sonst:
            argspec = ''

    wenn isinstance(fob, type) and argspec == '()':
        # If fob has no argument, use default callable argspec.
        argspec = _default_callable_argspec

    lines = (textwrap.wrap(argspec, _MAX_COLS, subsequent_indent=_INDENT)
             wenn len(argspec) > _MAX_COLS sonst [argspec] wenn argspec sonst [])

    # Augment lines von docstring, wenn any, and join to get argspec.
    doc = inspect.getdoc(ob)
    wenn doc:
        fuer line in doc.split('\n', _MAX_LINES)[:_MAX_LINES]:
            line = line.strip()
            wenn not line:
                break
            wenn len(line) > _MAX_COLS:
                line = line[: _MAX_COLS - 3] + '...'
            lines.append(line)
    argspec = '\n'.join(lines)

    return argspec or _default_callable_argspec


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_calltip', verbosity=2)
