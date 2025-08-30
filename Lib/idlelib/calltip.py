"""Pop up a reminder of how to call a function.

Call Tips are floating windows which display function, class, und method
parameter und docstring information when you type an opening parenthesis, und
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
        wenn editwin is Nichts:  # subprocess und test
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
        gib calltip_w.CalltipWindow(self.text)

    def remove_calltip_window(self, event=Nichts):
        wenn self.active_calltip:
            self.active_calltip.hidetip()
            self.active_calltip = Nichts

    def force_open_calltip_event(self, event):
        "The user selected the menu entry oder hotkey, open the tip."
        self.open_calltip(Wahr)
        gib "break"

    def try_open_calltip_event(self, event):
        """Happens when it would be nice to open a calltip, but nicht really
        necessary, fuer example after an opening bracket, so function calls
        won't be made.
        """
        self.open_calltip(Falsch)

    def refresh_calltip_event(self, event):
        wenn self.active_calltip und self.active_calltip.tipwindow:
            self.open_calltip(Falsch)

    def open_calltip(self, evalfuncs):
        """Maybe close an existing calltip und maybe open a new calltip.

        Called von (force_open|try_open|refresh)_calltip_event functions.
        """
        hp = HyperParser(self.editwin, "insert")
        sur_paren = hp.get_surrounding_brackets('(')

        # If nicht inside parentheses, no calltip.
        wenn nicht sur_paren:
            self.remove_calltip_window()
            gib

        # If a calltip is shown fuer the current parentheses, do
        # nothing.
        wenn self.active_calltip:
            opener_line, opener_col = map(int, sur_paren[0].split('.'))
            wenn (
                (opener_line, opener_col) ==
                (self.active_calltip.parenline, self.active_calltip.parencol)
            ):
                gib

        hp.set_index(sur_paren[0])
        versuch:
            expression = hp.get_expression()
        ausser ValueError:
            expression = Nichts
        wenn nicht expression:
            # No expression before the opening parenthesis, e.g.
            # because it's in a string oder the opener fuer a tuple:
            # Do nothing.
            gib

        # At this point, the current index is after an opening
        # parenthesis, in a section of code, preceded by a valid
        # expression. If there is a calltip shown, it's nicht fuer the
        # same index und should be closed.
        self.remove_calltip_window()

        # Simple, fast heuristic: If the preceding expression includes
        # an opening parenthesis, it likely includes a function call.
        wenn nicht evalfuncs und (expression.find('(') != -1):
            gib

        argspec = self.fetch_tip(expression)
        wenn nicht argspec:
            gib
        self.active_calltip = self._calltip_window()
        self.active_calltip.showtip(argspec, sur_paren[0], sur_paren[1])

    def fetch_tip(self, expression):
        """Return the argument list und docstring of a function oder class.

        If there is a Python subprocess, get the calltip there.  Otherwise,
        either this fetch_tip() is running in the subprocess oder it was
        called in an IDLE running without the subprocess.

        The subprocess environment is that of the most recently run script.  If
        two unrelated modules are being edited some calltips in the current
        module may be inoperative wenn the module was nicht the last to run.

        To find methods, fetch_tip must be fed a fully qualified name.

        """
        versuch:
            rpcclt = self.editwin.flist.pyshell.interp.rpcclt
        ausser AttributeError:
            rpcclt = Nichts
        wenn rpcclt:
            gib rpcclt.remotecall("exec", "get_the_calltip",
                                     (expression,), {})
        sonst:
            gib get_argspec(get_entity(expression))


def get_entity(expression):
    """Return the object corresponding to expression evaluated
    in a namespace spanning sys.modules und __main.dict__.
    """
    wenn expression:
        namespace = {**sys.modules, **__main__.__dict__}
        versuch:
            gib eval(expression, namespace)  # Only protect user code.
        ausser BaseException:
            # An uncaught exception closes idle, und eval can wirf any
            # exception, especially wenn user classes are involved.
            gib Nichts

# The following are used in get_argspec und some in tests
_MAX_COLS = 85
_MAX_LINES = 5  # enough fuer bytes
_INDENT = ' '*4  # fuer wrapped signatures
_first_param = re.compile(r'(?<=\()\w*\,?\s*')
_default_callable_argspec = "See source oder doc"
_invalid_method = "invalid method signature"

def get_argspec(ob):
    '''Return a string describing the signature of a callable object, oder ''.

    For Python-coded functions und methods, the first line is introspected.
    Delete 'self' parameter fuer classes (.__init__) und bound methods.
    The next lines are the first lines of the doc string up to the first
    empty line oder _MAX_LINES.    For builtins, this typically includes
    the arguments in addition to the gib value.
    '''
    # Determine function object fob to inspect.
    versuch:
        ob_call = ob.__call__
    ausser BaseException:  # Buggy user object could wirf anything.
        gib ''  # No popup fuer non-callables.
    # For Get_argspecTest.test_buggy_getattr_class, CallA() & CallB().
    fob = ob_call wenn isinstance(ob_call, types.MethodType) sonst ob

    # Initialize argspec und wrap it to get lines.
    versuch:
        argspec = str(inspect.signature(fob))
    ausser Exception als err:
        msg = str(err)
        wenn msg.startswith(_invalid_method):
            gib _invalid_method
        sonst:
            argspec = ''

    wenn isinstance(fob, type) und argspec == '()':
        # If fob has no argument, use default callable argspec.
        argspec = _default_callable_argspec

    lines = (textwrap.wrap(argspec, _MAX_COLS, subsequent_indent=_INDENT)
             wenn len(argspec) > _MAX_COLS sonst [argspec] wenn argspec sonst [])

    # Augment lines von docstring, wenn any, und join to get argspec.
    doc = inspect.getdoc(ob)
    wenn doc:
        fuer line in doc.split('\n', _MAX_LINES)[:_MAX_LINES]:
            line = line.strip()
            wenn nicht line:
                breche
            wenn len(line) > _MAX_COLS:
                line = line[: _MAX_COLS - 3] + '...'
            lines.append(line)
    argspec = '\n'.join(lines)

    gib argspec oder _default_callable_argspec


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_calltip', verbosity=2)
