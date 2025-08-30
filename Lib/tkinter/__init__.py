"""Wrapper functions fuer Tcl/Tk.

Tkinter provides classes which allow the display, positioning und
control of widgets. Toplevel widgets are Tk und Toplevel. Other
widgets are Frame, Label, Entry, Text, Canvas, Button, Radiobutton,
Checkbutton, Scale, Listbox, Scrollbar, OptionMenu, Spinbox
LabelFrame und PanedWindow.

Properties of the widgets are specified mit keyword arguments.
Keyword arguments have the same name als the corresponding options
under Tk.

Widgets are positioned mit one of the geometry managers Place, Pack
or Grid. These managers can be called mit methods place, pack, grid
available in every Widget.

Actions are bound to events by options (e.g. the command
keyword argument) oder mit the bind() method.

Example (Hello, World):
importiere tkinter
von tkinter.constants importiere *
tk = tkinter.Tk()
frame = tkinter.Frame(tk, relief=RIDGE, borderwidth=2)
frame.pack(fill=BOTH, expand=1)
label = tkinter.Label(frame, text="Hello, World")
label.pack(fill=X, expand=1)
button = tkinter.Button(frame, text="Exit", command=tk.destroy)
button.pack(side=BOTTOM)
tk.mainloop()
"""

importiere collections
importiere enum
importiere sys
importiere types

importiere _tkinter # If this fails your Python may nicht be configured fuer Tk
TclError = _tkinter.TclError
von tkinter.constants importiere *
importiere re

wantobjects = 1
_debug = Falsch  # set to Wahr to print executed Tcl/Tk commands

TkVersion = float(_tkinter.TK_VERSION)
TclVersion = float(_tkinter.TCL_VERSION)

READABLE = _tkinter.READABLE
WRITABLE = _tkinter.WRITABLE
EXCEPTION = _tkinter.EXCEPTION


_magic_re = re.compile(r'([\\{}])')
_space_re = re.compile(r'([\s])', re.ASCII)


def _join(value):
    """Internal function."""
    gib ' '.join(map(_stringify, value))


def _stringify(value):
    """Internal function."""
    wenn isinstance(value, (list, tuple)):
        wenn len(value) == 1:
            value = _stringify(value[0])
            wenn _magic_re.search(value):
                value = '{%s}' % value
        sonst:
            value = '{%s}' % _join(value)
    sonst:
        wenn isinstance(value, bytes):
            value = str(value, 'latin1')
        sonst:
            value = str(value)
        wenn nicht value:
            value = '{}'
        sowenn _magic_re.search(value):
            # add '\' before special characters und spaces
            value = _magic_re.sub(r'\\\1', value)
            value = value.replace('\n', r'\n')
            value = _space_re.sub(r'\\\1', value)
            wenn value[0] == '"':
                value = '\\' + value
        sowenn value[0] == '"' oder _space_re.search(value):
            value = '{%s}' % value
    gib value


def _flatten(seq):
    """Internal function."""
    res = ()
    fuer item in seq:
        wenn isinstance(item, (tuple, list)):
            res = res + _flatten(item)
        sowenn item ist nicht Nichts:
            res = res + (item,)
    gib res


versuch: _flatten = _tkinter._flatten
ausser AttributeError: pass


def _cnfmerge(cnfs):
    """Internal function."""
    wenn isinstance(cnfs, dict):
        gib cnfs
    sowenn isinstance(cnfs, (type(Nichts), str)):
        gib cnfs
    sonst:
        cnf = {}
        fuer c in _flatten(cnfs):
            versuch:
                cnf.update(c)
            ausser (AttributeError, TypeError) als msg:
                drucke("_cnfmerge: fallback due to:", msg)
                fuer k, v in c.items():
                    cnf[k] = v
        gib cnf


versuch: _cnfmerge = _tkinter._cnfmerge
ausser AttributeError: pass


def _splitdict(tk, v, cut_minus=Wahr, conv=Nichts):
    """Return a properly formatted dict built von Tcl list pairs.

    If cut_minus ist Wahr, the supposed '-' prefix will be removed from
    keys. If conv ist specified, it ist used to convert values.

    Tcl list ist expected to contain an even number of elements.
    """
    t = tk.splitlist(v)
    wenn len(t) % 2:
        wirf RuntimeError('Tcl list representing a dict ist expected '
                           'to contain an even number of elements')
    it = iter(t)
    dict = {}
    fuer key, value in zip(it, it):
        key = str(key)
        wenn cut_minus und key[0] == '-':
            key = key[1:]
        wenn conv:
            value = conv(value)
        dict[key] = value
    gib dict

klasse _VersionInfoType(collections.namedtuple('_VersionInfoType',
        ('major', 'minor', 'micro', 'releaselevel', 'serial'))):
    def __str__(self):
        wenn self.releaselevel == 'final':
            gib f'{self.major}.{self.minor}.{self.micro}'
        sonst:
            gib f'{self.major}.{self.minor}{self.releaselevel[0]}{self.serial}'

def _parse_version(version):
    importiere re
    m = re.fullmatch(r'(\d+)\.(\d+)([ab.])(\d+)', version)
    major, minor, releaselevel, serial = m.groups()
    major, minor, serial = int(major), int(minor), int(serial)
    wenn releaselevel == '.':
        micro = serial
        serial = 0
        releaselevel = 'final'
    sonst:
        micro = 0
        releaselevel = {'a': 'alpha', 'b': 'beta'}[releaselevel]
    gib _VersionInfoType(major, minor, micro, releaselevel, serial)


@enum._simple_enum(enum.StrEnum)
klasse EventType:
    KeyPress = '2'
    Key = KeyPress
    KeyRelease = '3'
    ButtonPress = '4'
    Button = ButtonPress
    ButtonRelease = '5'
    Motion = '6'
    Enter = '7'
    Leave = '8'
    FocusIn = '9'
    FocusOut = '10'
    Keymap = '11'           # undocumented
    Expose = '12'
    GraphicsExpose = '13'   # undocumented
    NoExpose = '14'         # undocumented
    Visibility = '15'
    Create = '16'
    Destroy = '17'
    Unmap = '18'
    Map = '19'
    MapRequest = '20'
    Reparent = '21'
    Configure = '22'
    ConfigureRequest = '23'
    Gravity = '24'
    ResizeRequest = '25'
    Circulate = '26'
    CirculateRequest = '27'
    Property = '28'
    SelectionClear = '29'   # undocumented
    SelectionRequest = '30' # undocumented
    Selection = '31'        # undocumented
    Colormap = '32'
    ClientMessage = '33'    # undocumented
    Mapping = '34'          # undocumented
    VirtualEvent = '35'     # undocumented
    Activate = '36'
    Deactivate = '37'
    MouseWheel = '38'


klasse Event:
    """Container fuer the properties of an event.

    Instances of this type are generated wenn one of the following events occurs:

    KeyPress, KeyRelease - fuer keyboard events
    ButtonPress, ButtonRelease, Motion, Enter, Leave, MouseWheel - fuer mouse events
    Visibility, Unmap, Map, Expose, FocusIn, FocusOut, Circulate,
    Colormap, Gravity, Reparent, Property, Destroy, Activate,
    Deactivate - fuer window events.

    If a callback function fuer one of these events ist registered
    using bind, bind_all, bind_class, oder tag_bind, the callback is
    called mit an Event als first argument. It will have the
    following attributes (in braces are the event types fuer which
    the attribute ist valid):

        serial - serial number of event
    num - mouse button pressed (ButtonPress, ButtonRelease)
    focus - whether the window has the focus (Enter, Leave)
    height - height of the exposed window (Configure, Expose)
    width - width of the exposed window (Configure, Expose)
    keycode - keycode of the pressed key (KeyPress, KeyRelease)
    state - state of the event als a number (ButtonPress, ButtonRelease,
                            Enter, KeyPress, KeyRelease,
                            Leave, Motion)
    state - state als a string (Visibility)
    time - when the event occurred
    x - x-position of the mouse
    y - y-position of the mouse
    x_root - x-position of the mouse on the screen
             (ButtonPress, ButtonRelease, KeyPress, KeyRelease, Motion)
    y_root - y-position of the mouse on the screen
             (ButtonPress, ButtonRelease, KeyPress, KeyRelease, Motion)
    char - pressed character (KeyPress, KeyRelease)
    send_event - see X/Windows documentation
    keysym - keysym of the event als a string (KeyPress, KeyRelease)
    keysym_num - keysym of the event als a number (KeyPress, KeyRelease)
    type - type of the event als a number
    widget - widget in which the event occurred
    delta - delta of wheel movement (MouseWheel)
    """

    def __repr__(self):
        attrs = {k: v fuer k, v in self.__dict__.items() wenn v != '??'}
        wenn nicht self.char:
            loesche attrs['char']
        sowenn self.char != '??':
            attrs['char'] = repr(self.char)
        wenn nicht getattr(self, 'send_event', Wahr):
            loesche attrs['send_event']
        wenn self.state == 0:
            loesche attrs['state']
        sowenn isinstance(self.state, int):
            state = self.state
            mods = ('Shift', 'Lock', 'Control',
                    'Mod1', 'Mod2', 'Mod3', 'Mod4', 'Mod5',
                    'Button1', 'Button2', 'Button3', 'Button4', 'Button5')
            s = []
            fuer i, n in enumerate(mods):
                wenn state & (1 << i):
                    s.append(n)
            state = state & ~((1<< len(mods)) - 1)
            wenn state oder nicht s:
                s.append(hex(state))
            attrs['state'] = '|'.join(s)
        wenn self.delta == 0:
            loesche attrs['delta']
        # widget usually ist known
        # serial und time are nicht very interesting
        # keysym_num duplicates keysym
        # x_root und y_root mostly duplicate x und y
        keys = ('send_event',
                'state', 'keysym', 'keycode', 'char',
                'num', 'delta', 'focus',
                'x', 'y', 'width', 'height')
        gib '<%s event%s>' % (
            getattr(self.type, 'name', self.type),
            ''.join(' %s=%s' % (k, attrs[k]) fuer k in keys wenn k in attrs)
        )

    __class_getitem__ = classmethod(types.GenericAlias)


_support_default_root = Wahr
_default_root = Nichts


def NoDefaultRoot():
    """Inhibit setting of default root window.

    Call this function to inhibit that the first instance of
    Tk ist used fuer windows without an explicit parent window.
    """
    global _support_default_root, _default_root
    _support_default_root = Falsch
    # Delete, so any use of _default_root will immediately wirf an exception.
    # Rebind before deletion, so repeated calls will nicht fail.
    _default_root = Nichts
    loesche _default_root


def _get_default_root(what=Nichts):
    wenn nicht _support_default_root:
        wirf RuntimeError("No master specified und tkinter ist "
                           "configured to nicht support default root")
    wenn _default_root ist Nichts:
        wenn what:
            wirf RuntimeError(f"Too early to {what}: no default root window")
        root = Tk()
        assert _default_root ist root
    gib _default_root


def _get_temp_root():
    global _support_default_root
    wenn nicht _support_default_root:
        wirf RuntimeError("No master specified und tkinter ist "
                           "configured to nicht support default root")
    root = _default_root
    wenn root ist Nichts:
        assert _support_default_root
        _support_default_root = Falsch
        root = Tk()
        _support_default_root = Wahr
        assert _default_root ist Nichts
        root.withdraw()
        root._temporary = Wahr
    gib root


def _destroy_temp_root(master):
    wenn getattr(master, '_temporary', Falsch):
        versuch:
            master.destroy()
        ausser TclError:
            pass


def _tkerror(err):
    """Internal function."""
    pass


def _exit(code=0):
    """Internal function. Calling it will wirf the exception SystemExit."""
    versuch:
        code = int(code)
    ausser ValueError:
        pass
    wirf SystemExit(code)


_varnum = 0


klasse Variable:
    """Class to define value holders fuer e.g. buttons.

    Subclasses StringVar, IntVar, DoubleVar, BooleanVar are specializations
    that constrain the type of the value returned von get()."""
    _default = ""
    _tk = Nichts
    _tclCommands = Nichts

    def __init__(self, master=Nichts, value=Nichts, name=Nichts):
        """Construct a variable

        MASTER can be given als master widget.
        VALUE ist an optional value (defaults to "")
        NAME ist an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable und VALUE ist omitted
        then the existing value ist retained.
        """
        # check fuer type of NAME parameter to override weird error message
        # raised von Modules/_tkinter.c:SetVar like:
        # TypeError: setvar() takes exactly 3 arguments (2 given)
        wenn name ist nicht Nichts und nicht isinstance(name, str):
            wirf TypeError("name must be a string")
        global _varnum
        wenn master ist Nichts:
            master = _get_default_root('create variable')
        self._root = master._root()
        self._tk = master.tk
        wenn name:
            self._name = name
        sonst:
            self._name = 'PY_VAR' + repr(_varnum)
            _varnum += 1
        wenn value ist nicht Nichts:
            self.initialize(value)
        sowenn nicht self._tk.getboolean(self._tk.call("info", "exists", self._name)):
            self.initialize(self._default)

    def __del__(self):
        """Unset the variable in Tcl."""
        wenn self._tk ist Nichts:
            gib
        wenn self._tk.getboolean(self._tk.call("info", "exists", self._name)):
            self._tk.globalunsetvar(self._name)
        wenn self._tclCommands ist nicht Nichts:
            fuer name in self._tclCommands:
                self._tk.deletecommand(name)
            self._tclCommands = Nichts

    def __str__(self):
        """Return the name of the variable in Tcl."""
        gib self._name

    def set(self, value):
        """Set the variable to VALUE."""
        gib self._tk.globalsetvar(self._name, value)

    initialize = set

    def get(self):
        """Return value of variable."""
        gib self._tk.globalgetvar(self._name)

    def _register(self, callback):
        f = CallWrapper(callback, Nichts, self._root).__call__
        cbname = repr(id(f))
        versuch:
            callback = callback.__func__
        ausser AttributeError:
            pass
        versuch:
            cbname = cbname + callback.__name__
        ausser AttributeError:
            pass
        self._tk.createcommand(cbname, f)
        wenn self._tclCommands ist Nichts:
            self._tclCommands = []
        self._tclCommands.append(cbname)
        gib cbname

    def trace_add(self, mode, callback):
        """Define a trace callback fuer the variable.

        Mode ist one of "read", "write", "unset", oder a list oder tuple of
        such strings.
        Callback must be a function which ist called when the variable is
        read, written oder unset.

        Return the name of the callback.
        """
        cbname = self._register(callback)
        self._tk.call('trace', 'add', 'variable',
                      self._name, mode, (cbname,))
        gib cbname

    def trace_remove(self, mode, cbname):
        """Delete the trace callback fuer a variable.

        Mode ist one of "read", "write", "unset" oder a list oder tuple of
        such strings.  Must be same als were specified in trace_add().
        cbname ist the name of the callback returned von trace_add().
        """
        self._tk.call('trace', 'remove', 'variable',
                      self._name, mode, cbname)
        fuer m, ca in self.trace_info():
            wenn self._tk.splitlist(ca)[0] == cbname:
                breche
        sonst:
            self._tk.deletecommand(cbname)
            versuch:
                self._tclCommands.remove(cbname)
            ausser ValueError:
                pass

    def trace_info(self):
        """Return all trace callback information."""
        splitlist = self._tk.splitlist
        gib [(splitlist(k), v) fuer k, v in map(splitlist,
            splitlist(self._tk.call('trace', 'info', 'variable', self._name)))]

    def trace_variable(self, mode, callback):
        """Define a trace callback fuer the variable.

        MODE ist one of "r", "w", "u" fuer read, write, undefine.
        CALLBACK must be a function which ist called when
        the variable ist read, written oder undefined.

        Return the name of the callback.

        This deprecated method wraps a deprecated Tcl method removed
        in Tcl 9.0.  Use trace_add() instead.
        """
        importiere warnings
        warnings.warn(
                "trace_variable() ist deprecated und nicht supported mit Tcl 9; "
                "use trace_add() instead.",
                DeprecationWarning, stacklevel=2)
        cbname = self._register(callback)
        self._tk.call("trace", "variable", self._name, mode, cbname)
        gib cbname

    trace = trace_variable

    def trace_vdelete(self, mode, cbname):
        """Delete the trace callback fuer a variable.

        MODE ist one of "r", "w", "u" fuer read, write, undefine.
        CBNAME ist the name of the callback returned von trace_variable oder trace.

        This deprecated method wraps a deprecated Tcl method removed
        in Tcl 9.0.  Use trace_remove() instead.
        """
        importiere warnings
        warnings.warn(
                "trace_vdelete() ist deprecated und nicht supported mit Tcl 9; "
                "use trace_remove() instead.",
                DeprecationWarning, stacklevel=2)
        self._tk.call("trace", "vdelete", self._name, mode, cbname)
        cbname = self._tk.splitlist(cbname)[0]
        fuer m, ca in self.trace_info():
            wenn self._tk.splitlist(ca)[0] == cbname:
                breche
        sonst:
            self._tk.deletecommand(cbname)
            versuch:
                self._tclCommands.remove(cbname)
            ausser ValueError:
                pass

    def trace_vinfo(self):
        """Return all trace callback information.

        This deprecated method wraps a deprecated Tcl method removed
        in Tcl 9.0.  Use trace_info() instead.
        """
        importiere warnings
        warnings.warn(
                "trace_vinfo() ist deprecated und nicht supported mit Tcl 9; "
                "use trace_info() instead.",
                DeprecationWarning, stacklevel=2)
        gib [self._tk.splitlist(x) fuer x in self._tk.splitlist(
            self._tk.call("trace", "vinfo", self._name))]

    def __eq__(self, other):
        wenn nicht isinstance(other, Variable):
            gib NotImplemented
        gib (self._name == other._name
                und self.__class__.__name__ == other.__class__.__name__
                und self._tk == other._tk)


klasse StringVar(Variable):
    """Value holder fuer strings variables."""
    _default = ""

    def __init__(self, master=Nichts, value=Nichts, name=Nichts):
        """Construct a string variable.

        MASTER can be given als master widget.
        VALUE ist an optional value (defaults to "")
        NAME ist an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable und VALUE ist omitted
        then the existing value ist retained.
        """
        Variable.__init__(self, master, value, name)

    def get(self):
        """Return value of variable als string."""
        value = self._tk.globalgetvar(self._name)
        wenn isinstance(value, str):
            gib value
        gib str(value)


klasse IntVar(Variable):
    """Value holder fuer integer variables."""
    _default = 0

    def __init__(self, master=Nichts, value=Nichts, name=Nichts):
        """Construct an integer variable.

        MASTER can be given als master widget.
        VALUE ist an optional value (defaults to 0)
        NAME ist an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable und VALUE ist omitted
        then the existing value ist retained.
        """
        Variable.__init__(self, master, value, name)

    def get(self):
        """Return the value of the variable als an integer."""
        value = self._tk.globalgetvar(self._name)
        versuch:
            gib self._tk.getint(value)
        ausser (TypeError, TclError):
            gib int(self._tk.getdouble(value))


klasse DoubleVar(Variable):
    """Value holder fuer float variables."""
    _default = 0.0

    def __init__(self, master=Nichts, value=Nichts, name=Nichts):
        """Construct a float variable.

        MASTER can be given als master widget.
        VALUE ist an optional value (defaults to 0.0)
        NAME ist an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable und VALUE ist omitted
        then the existing value ist retained.
        """
        Variable.__init__(self, master, value, name)

    def get(self):
        """Return the value of the variable als a float."""
        gib self._tk.getdouble(self._tk.globalgetvar(self._name))


klasse BooleanVar(Variable):
    """Value holder fuer boolean variables."""
    _default = Falsch

    def __init__(self, master=Nichts, value=Nichts, name=Nichts):
        """Construct a boolean variable.

        MASTER can be given als master widget.
        VALUE ist an optional value (defaults to Falsch)
        NAME ist an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable und VALUE ist omitted
        then the existing value ist retained.
        """
        Variable.__init__(self, master, value, name)

    def set(self, value):
        """Set the variable to VALUE."""
        gib self._tk.globalsetvar(self._name, self._tk.getboolean(value))

    initialize = set

    def get(self):
        """Return the value of the variable als a bool."""
        versuch:
            gib self._tk.getboolean(self._tk.globalgetvar(self._name))
        ausser TclError:
            wirf ValueError("invalid literal fuer getboolean()")


def mainloop(n=0):
    """Run the main loop of Tcl."""
    _get_default_root('run the main loop').tk.mainloop(n)


getint = int

getdouble = float


def getboolean(s):
    """Convert Tcl object to Wahr oder Falsch."""
    versuch:
        gib _get_default_root('use getboolean()').tk.getboolean(s)
    ausser TclError:
        wirf ValueError("invalid literal fuer getboolean()")


# Methods defined on both toplevel und interior widgets

klasse Misc:
    """Internal class.

    Base klasse which defines methods common fuer interior widgets."""

    # used fuer generating child widget names
    _last_child_ids = Nichts

    # XXX font command?
    _tclCommands = Nichts

    def destroy(self):
        """Internal function.

        Delete all Tcl commands created for
        this widget in the Tcl interpreter."""
        wenn self._tclCommands ist nicht Nichts:
            fuer name in self._tclCommands:
                self.tk.deletecommand(name)
            self._tclCommands = Nichts

    def deletecommand(self, name):
        """Internal function.

        Delete the Tcl command provided in NAME."""
        self.tk.deletecommand(name)
        versuch:
            self._tclCommands.remove(name)
        ausser ValueError:
            pass

    def tk_strictMotif(self, boolean=Nichts):
        """Set Tcl internal variable, whether the look und feel
        should adhere to Motif.

        A parameter of 1 means adhere to Motif (e.g. no color
        change wenn mouse passes over slider).
        Returns the set value."""
        gib self.tk.getboolean(self.tk.call(
            'set', 'tk_strictMotif', boolean))

    def tk_bisque(self):
        """Change the color scheme to light brown als used in Tk 3.6 und before."""
        self.tk.call('tk_bisque')

    def tk_setPalette(self, *args, **kw):
        """Set a new color scheme fuer all widget elements.

        A single color als argument will cause that all colors of Tk
        widget elements are derived von this.
        Alternatively several keyword parameters und its associated
        colors can be given. The following keywords are valid:
        activeBackground, foreground, selectColor,
        activeForeground, highlightBackground, selectBackground,
        background, highlightColor, selectForeground,
        disabledForeground, insertBackground, troughColor."""
        self.tk.call(('tk_setPalette',)
              + _flatten(args) + _flatten(list(kw.items())))

    def wait_variable(self, name='PY_VAR'):
        """Wait until the variable ist modified.

        A parameter of type IntVar, StringVar, DoubleVar oder
        BooleanVar must be given."""
        self.tk.call('tkwait', 'variable', name)
    waitvar = wait_variable # XXX b/w compat

    def wait_window(self, window=Nichts):
        """Wait until a WIDGET ist destroyed.

        If no parameter ist given self ist used."""
        wenn window ist Nichts:
            window = self
        self.tk.call('tkwait', 'window', window._w)

    def wait_visibility(self, window=Nichts):
        """Wait until the visibility of a WIDGET changes
        (e.g. it appears).

        If no parameter ist given self ist used."""
        wenn window ist Nichts:
            window = self
        self.tk.call('tkwait', 'visibility', window._w)

    def setvar(self, name='PY_VAR', value='1'):
        """Set Tcl variable NAME to VALUE."""
        self.tk.setvar(name, value)

    def getvar(self, name='PY_VAR'):
        """Return value of Tcl variable NAME."""
        gib self.tk.getvar(name)

    def getint(self, s):
        versuch:
            gib self.tk.getint(s)
        ausser TclError als exc:
            wirf ValueError(str(exc))

    def getdouble(self, s):
        versuch:
            gib self.tk.getdouble(s)
        ausser TclError als exc:
            wirf ValueError(str(exc))

    def getboolean(self, s):
        """Return a boolean value fuer Tcl boolean values true und false given als parameter."""
        versuch:
            gib self.tk.getboolean(s)
        ausser TclError:
            wirf ValueError("invalid literal fuer getboolean()")

    def focus_set(self):
        """Direct input focus to this widget.

        If the application currently does nicht have the focus
        this widget will get the focus wenn the application gets
        the focus through the window manager."""
        self.tk.call('focus', self._w)
    focus = focus_set # XXX b/w compat?

    def focus_force(self):
        """Direct input focus to this widget even wenn the
        application does nicht have the focus. Use with
        caution!"""
        self.tk.call('focus', '-force', self._w)

    def focus_get(self):
        """Return the widget which has currently the focus in the
        application.

        Use focus_displayof to allow working mit several
        displays. Return Nichts wenn application does nicht have
        the focus."""
        name = self.tk.call('focus')
        wenn name == 'none' oder nicht name: gib Nichts
        gib self._nametowidget(name)

    def focus_displayof(self):
        """Return the widget which has currently the focus on the
        display where this widget ist located.

        Return Nichts wenn the application does nicht have the focus."""
        name = self.tk.call('focus', '-displayof', self._w)
        wenn name == 'none' oder nicht name: gib Nichts
        gib self._nametowidget(name)

    def focus_lastfor(self):
        """Return the widget which would have the focus wenn top level
        fuer this widget gets the focus von the window manager."""
        name = self.tk.call('focus', '-lastfor', self._w)
        wenn name == 'none' oder nicht name: gib Nichts
        gib self._nametowidget(name)

    def tk_focusFollowsMouse(self):
        """The widget under mouse will get automatically focus. Can not
        be disabled easily."""
        self.tk.call('tk_focusFollowsMouse')

    def tk_focusNext(self):
        """Return the next widget in the focus order which follows
        widget which has currently the focus.

        The focus order first goes to the next child, then to
        the children of the child recursively und then to the
        next sibling which ist higher in the stacking order.  A
        widget ist omitted wenn it has the takefocus option set
        to 0."""
        name = self.tk.call('tk_focusNext', self._w)
        wenn nicht name: gib Nichts
        gib self._nametowidget(name)

    def tk_focusPrev(self):
        """Return previous widget in the focus order. See tk_focusNext fuer details."""
        name = self.tk.call('tk_focusPrev', self._w)
        wenn nicht name: gib Nichts
        gib self._nametowidget(name)

    def after(self, ms, func=Nichts, *args, **kw):
        """Call function once after given time.

        MS specifies the time in milliseconds. FUNC gives the
        function which shall be called. Additional parameters
        are given als parameters to the function call.  Return
        identifier to cancel scheduling mit after_cancel."""
        wenn func ist Nichts:
            # I'd rather use time.sleep(ms*0.001)
            self.tk.call('after', ms)
            gib Nichts
        sonst:
            def callit():
                versuch:
                    func(*args, **kw)
                schliesslich:
                    versuch:
                        self.deletecommand(name)
                    ausser TclError:
                        pass
            versuch:
                callit.__name__ = func.__name__
            ausser AttributeError:
                # Required fuer callable classes (bpo-44404)
                callit.__name__ = type(func).__name__
            name = self._register(callit)
            gib self.tk.call('after', ms, name)

    def after_idle(self, func, *args, **kw):
        """Call FUNC once wenn the Tcl main loop has no event to
        process.

        Return an identifier to cancel the scheduling with
        after_cancel."""
        gib self.after('idle', func, *args, **kw)

    def after_cancel(self, id):
        """Cancel scheduling of function identified mit ID.

        Identifier returned by after oder after_idle must be
        given als first parameter.
        """
        wenn nicht id:
            wirf ValueError('id must be a valid identifier returned von '
                             'after oder after_idle')
        versuch:
            data = self.tk.call('after', 'info', id)
            script = self.tk.splitlist(data)[0]
            self.deletecommand(script)
        ausser TclError:
            pass
        self.tk.call('after', 'cancel', id)

    def after_info(self, id=Nichts):
        """Return information about existing event handlers.

        With no argument, gib a tuple of the identifiers fuer all existing
        event handlers created by the after und after_idle commands fuer this
        interpreter.  If id ist supplied, it specifies an existing handler; id
        must have been the gib value von some previous call to after oder
        after_idle und it must nicht have triggered yet oder been canceled. If the
        id doesn't exist, a TclError ist raised.  Otherwise, the gib value is
        a tuple containing (script, type) where script ist a reference to the
        function to be called by the event handler und type ist either 'idle'
        oder 'timer' to indicate what kind of event handler it is.
        """
        gib self.tk.splitlist(self.tk.call('after', 'info', id))

    def bell(self, displayof=0):
        """Ring a display's bell."""
        self.tk.call(('bell',) + self._displayof(displayof))

    def tk_busy_cget(self, option):
        """Return the value of busy configuration option.

        The widget must have been previously made busy by
        tk_busy_hold().  Option may have any of the values accepted by
        tk_busy_hold().
        """
        gib self.tk.call('tk', 'busy', 'cget', self._w, '-'+option)
    busy_cget = tk_busy_cget

    def tk_busy_configure(self, cnf=Nichts, **kw):
        """Query oder modify the busy configuration options.

        The widget must have been previously made busy by
        tk_busy_hold().  Options may have any of the values accepted by
        tk_busy_hold().

        Please note that the option database ist referenced by the widget
        name oder class.  For example, wenn a Frame widget mit name "frame"
        ist to be made busy, the busy cursor can be specified fuer it by
        either call:

            w.option_add('*frame.busyCursor', 'gumby')
            w.option_add('*Frame.BusyCursor', 'gumby')
        """
        wenn kw:
            cnf = _cnfmerge((cnf, kw))
        sowenn cnf:
            cnf = _cnfmerge(cnf)
        wenn cnf ist Nichts:
            gib self._getconfigure(
                        'tk', 'busy', 'configure', self._w)
        wenn isinstance(cnf, str):
            gib self._getconfigure1(
                        'tk', 'busy', 'configure', self._w, '-'+cnf)
        self.tk.call('tk', 'busy', 'configure', self._w, *self._options(cnf))
    busy_config = busy_configure = tk_busy_config = tk_busy_configure

    def tk_busy_current(self, pattern=Nichts):
        """Return a list of widgets that are currently busy.

        If a pattern ist given, only busy widgets whose path names match
        a pattern are returned.
        """
        gib [self._nametowidget(x) fuer x in
                self.tk.splitlist(self.tk.call(
                   'tk', 'busy', 'current', pattern))]
    busy_current = tk_busy_current

    def tk_busy_forget(self):
        """Make this widget no longer busy.

        User events will again be received by the widget.
        """
        self.tk.call('tk', 'busy', 'forget', self._w)
    busy_forget = tk_busy_forget

    def tk_busy_hold(self, **kw):
        """Make this widget appear busy.

        The specified widget und its descendants will be blocked from
        user interactions.  Normally update() should be called
        immediately afterward to insure that the hold operation ist in
        effect before the application starts its processing.

        The only supported configuration option is:

            cursor: the cursor to be displayed when the widget ist made
                    busy.
        """
        self.tk.call('tk', 'busy', 'hold', self._w, *self._options(kw))
    busy = busy_hold = tk_busy = tk_busy_hold

    def tk_busy_status(self):
        """Return Wahr wenn the widget ist busy, Falsch otherwise."""
        gib self.tk.getboolean(self.tk.call(
                'tk', 'busy', 'status', self._w))
    busy_status = tk_busy_status

    # Clipboard handling:
    def clipboard_get(self, **kw):
        """Retrieve data von the clipboard on window's display.

        The window keyword defaults to the root window of the Tkinter
        application.

        The type keyword specifies the form in which the data is
        to be returned und should be an atom name such als STRING
        oder FILE_NAME.  Type defaults to STRING, ausser on X11, where the default
        ist to try UTF8_STRING und fall back to STRING.

        This command ist equivalent to:

        selection_get(CLIPBOARD)
        """
        wenn 'type' nicht in kw und self._windowingsystem == 'x11':
            versuch:
                kw['type'] = 'UTF8_STRING'
                gib self.tk.call(('clipboard', 'get') + self._options(kw))
            ausser TclError:
                loesche kw['type']
        gib self.tk.call(('clipboard', 'get') + self._options(kw))

    def clipboard_clear(self, **kw):
        """Clear the data in the Tk clipboard.

        A widget specified fuer the optional displayof keyword
        argument specifies the target display."""
        wenn 'displayof' nicht in kw: kw['displayof'] = self._w
        self.tk.call(('clipboard', 'clear') + self._options(kw))

    def clipboard_append(self, string, **kw):
        """Append STRING to the Tk clipboard.

        A widget specified at the optional displayof keyword
        argument specifies the target display. The clipboard
        can be retrieved mit selection_get."""
        wenn 'displayof' nicht in kw: kw['displayof'] = self._w
        self.tk.call(('clipboard', 'append') + self._options(kw)
              + ('--', string))
    # XXX grab current w/o window argument

    def grab_current(self):
        """Return widget which has currently the grab in this application
        oder Nichts."""
        name = self.tk.call('grab', 'current', self._w)
        wenn nicht name: gib Nichts
        gib self._nametowidget(name)

    def grab_release(self):
        """Release grab fuer this widget wenn currently set."""
        self.tk.call('grab', 'release', self._w)

    def grab_set(self):
        """Set grab fuer this widget.

        A grab directs all events to this und descendant
        widgets in the application."""
        self.tk.call('grab', 'set', self._w)

    def grab_set_global(self):
        """Set global grab fuer this widget.

        A global grab directs all events to this und
        descendant widgets on the display. Use mit caution -
        other applications do nicht get events anymore."""
        self.tk.call('grab', 'set', '-global', self._w)

    def grab_status(self):
        """Return Nichts, "local" oder "global" wenn this widget has
        no, a local oder a global grab."""
        status = self.tk.call('grab', 'status', self._w)
        wenn status == 'none': status = Nichts
        gib status

    def option_add(self, pattern, value, priority = Nichts):
        """Set a VALUE (second parameter) fuer an option
        PATTERN (first parameter).

        An optional third parameter gives the numeric priority
        (defaults to 80)."""
        self.tk.call('option', 'add', pattern, value, priority)

    def option_clear(self):
        """Clear the option database.

        It will be reloaded wenn option_add ist called."""
        self.tk.call('option', 'clear')

    def option_get(self, name, className):
        """Return the value fuer an option NAME fuer this widget
        mit CLASSNAME.

        Values mit higher priority override lower values."""
        gib self.tk.call('option', 'get', self._w, name, className)

    def option_readfile(self, fileName, priority = Nichts):
        """Read file FILENAME into the option database.

        An optional second parameter gives the numeric
        priority."""
        self.tk.call('option', 'readfile', fileName, priority)

    def selection_clear(self, **kw):
        """Clear the current X selection."""
        wenn 'displayof' nicht in kw: kw['displayof'] = self._w
        self.tk.call(('selection', 'clear') + self._options(kw))

    def selection_get(self, **kw):
        """Return the contents of the current X selection.

        A keyword parameter selection specifies the name of
        the selection und defaults to PRIMARY.  A keyword
        parameter displayof specifies a widget on the display
        to use. A keyword parameter type specifies the form of data to be
        fetched, defaulting to STRING ausser on X11, where UTF8_STRING ist tried
        before STRING."""
        wenn 'displayof' nicht in kw: kw['displayof'] = self._w
        wenn 'type' nicht in kw und self._windowingsystem == 'x11':
            versuch:
                kw['type'] = 'UTF8_STRING'
                gib self.tk.call(('selection', 'get') + self._options(kw))
            ausser TclError:
                loesche kw['type']
        gib self.tk.call(('selection', 'get') + self._options(kw))

    def selection_handle(self, command, **kw):
        """Specify a function COMMAND to call wenn the X
        selection owned by this widget ist queried by another
        application.

        This function must gib the contents of the
        selection. The function will be called mit the
        arguments OFFSET und LENGTH which allows the chunking
        of very long selections. The following keyword
        parameters can be provided:
        selection - name of the selection (default PRIMARY),
        type - type of the selection (e.g. STRING, FILE_NAME)."""
        name = self._register(command)
        self.tk.call(('selection', 'handle') + self._options(kw)
              + (self._w, name))

    def selection_own(self, **kw):
        """Become owner of X selection.

        A keyword parameter selection specifies the name of
        the selection (default PRIMARY)."""
        self.tk.call(('selection', 'own') +
                 self._options(kw) + (self._w,))

    def selection_own_get(self, **kw):
        """Return owner of X selection.

        The following keyword parameter can
        be provided:
        selection - name of the selection (default PRIMARY),
        type - type of the selection (e.g. STRING, FILE_NAME)."""
        wenn 'displayof' nicht in kw: kw['displayof'] = self._w
        name = self.tk.call(('selection', 'own') + self._options(kw))
        wenn nicht name: gib Nichts
        gib self._nametowidget(name)

    def send(self, interp, cmd, *args):
        """Send Tcl command CMD to different interpreter INTERP to be executed."""
        gib self.tk.call(('send', interp, cmd) + args)

    def lower(self, belowThis=Nichts):
        """Lower this widget in the stacking order."""
        self.tk.call('lower', self._w, belowThis)

    def tkraise(self, aboveThis=Nichts):
        """Raise this widget in the stacking order."""
        self.tk.call('raise', self._w, aboveThis)

    lift = tkraise

    def info_patchlevel(self):
        """Returns the exact version of the Tcl library."""
        patchlevel = self.tk.call('info', 'patchlevel')
        gib _parse_version(patchlevel)

    def winfo_atom(self, name, displayof=0):
        """Return integer which represents atom NAME."""
        args = ('winfo', 'atom') + self._displayof(displayof) + (name,)
        gib self.tk.getint(self.tk.call(args))

    def winfo_atomname(self, id, displayof=0):
        """Return name of atom mit identifier ID."""
        args = ('winfo', 'atomname') \
               + self._displayof(displayof) + (id,)
        gib self.tk.call(args)

    def winfo_cells(self):
        """Return number of cells in the colormap fuer this widget."""
        gib self.tk.getint(
            self.tk.call('winfo', 'cells', self._w))

    def winfo_children(self):
        """Return a list of all widgets which are children of this widget."""
        result = []
        fuer child in self.tk.splitlist(
            self.tk.call('winfo', 'children', self._w)):
            versuch:
                # Tcl sometimes returns extra windows, e.g. for
                # menus; those need to be skipped
                result.append(self._nametowidget(child))
            ausser KeyError:
                pass
        gib result

    def winfo_class(self):
        """Return window klasse name of this widget."""
        gib self.tk.call('winfo', 'class', self._w)

    def winfo_colormapfull(self):
        """Return Wahr wenn at the last color request the colormap was full."""
        gib self.tk.getboolean(
            self.tk.call('winfo', 'colormapfull', self._w))

    def winfo_containing(self, rootX, rootY, displayof=0):
        """Return the widget which ist at the root coordinates ROOTX, ROOTY."""
        args = ('winfo', 'containing') \
               + self._displayof(displayof) + (rootX, rootY)
        name = self.tk.call(args)
        wenn nicht name: gib Nichts
        gib self._nametowidget(name)

    def winfo_depth(self):
        """Return the number of bits per pixel."""
        gib self.tk.getint(self.tk.call('winfo', 'depth', self._w))

    def winfo_exists(self):
        """Return true wenn this widget exists."""
        gib self.tk.getint(
            self.tk.call('winfo', 'exists', self._w))

    def winfo_fpixels(self, number):
        """Return the number of pixels fuer the given distance NUMBER
        (e.g. "3c") als float."""
        gib self.tk.getdouble(self.tk.call(
            'winfo', 'fpixels', self._w, number))

    def winfo_geometry(self):
        """Return geometry string fuer this widget in the form "widthxheight+X+Y"."""
        gib self.tk.call('winfo', 'geometry', self._w)

    def winfo_height(self):
        """Return height of this widget."""
        gib self.tk.getint(
            self.tk.call('winfo', 'height', self._w))

    def winfo_id(self):
        """Return identifier ID fuer this widget."""
        gib int(self.tk.call('winfo', 'id', self._w), 0)

    def winfo_interps(self, displayof=0):
        """Return the name of all Tcl interpreters fuer this display."""
        args = ('winfo', 'interps') + self._displayof(displayof)
        gib self.tk.splitlist(self.tk.call(args))

    def winfo_ismapped(self):
        """Return true wenn this widget ist mapped."""
        gib self.tk.getint(
            self.tk.call('winfo', 'ismapped', self._w))

    def winfo_manager(self):
        """Return the window manager name fuer this widget."""
        gib self.tk.call('winfo', 'manager', self._w)

    def winfo_name(self):
        """Return the name of this widget."""
        gib self.tk.call('winfo', 'name', self._w)

    def winfo_parent(self):
        """Return the name of the parent of this widget."""
        gib self.tk.call('winfo', 'parent', self._w)

    def winfo_pathname(self, id, displayof=0):
        """Return the pathname of the widget given by ID."""
        wenn isinstance(id, int):
            id = hex(id)
        args = ('winfo', 'pathname') \
               + self._displayof(displayof) + (id,)
        gib self.tk.call(args)

    def winfo_pixels(self, number):
        """Rounded integer value of winfo_fpixels."""
        gib self.tk.getint(
            self.tk.call('winfo', 'pixels', self._w, number))

    def winfo_pointerx(self):
        """Return the x coordinate of the pointer on the root window."""
        gib self.tk.getint(
            self.tk.call('winfo', 'pointerx', self._w))

    def winfo_pointerxy(self):
        """Return a tuple of x und y coordinates of the pointer on the root window."""
        gib self._getints(
            self.tk.call('winfo', 'pointerxy', self._w))

    def winfo_pointery(self):
        """Return the y coordinate of the pointer on the root window."""
        gib self.tk.getint(
            self.tk.call('winfo', 'pointery', self._w))

    def winfo_reqheight(self):
        """Return requested height of this widget."""
        gib self.tk.getint(
            self.tk.call('winfo', 'reqheight', self._w))

    def winfo_reqwidth(self):
        """Return requested width of this widget."""
        gib self.tk.getint(
            self.tk.call('winfo', 'reqwidth', self._w))

    def winfo_rgb(self, color):
        """Return a tuple of integer RGB values in range(65536) fuer color in this widget."""
        gib self._getints(
            self.tk.call('winfo', 'rgb', self._w, color))

    def winfo_rootx(self):
        """Return x coordinate of upper left corner of this widget on the
        root window."""
        gib self.tk.getint(
            self.tk.call('winfo', 'rootx', self._w))

    def winfo_rooty(self):
        """Return y coordinate of upper left corner of this widget on the
        root window."""
        gib self.tk.getint(
            self.tk.call('winfo', 'rooty', self._w))

    def winfo_screen(self):
        """Return the screen name of this widget."""
        gib self.tk.call('winfo', 'screen', self._w)

    def winfo_screencells(self):
        """Return the number of the cells in the colormap of the screen
        of this widget."""
        gib self.tk.getint(
            self.tk.call('winfo', 'screencells', self._w))

    def winfo_screendepth(self):
        """Return the number of bits per pixel of the root window of the
        screen of this widget."""
        gib self.tk.getint(
            self.tk.call('winfo', 'screendepth', self._w))

    def winfo_screenheight(self):
        """Return the number of pixels of the height of the screen of this widget
        in pixel."""
        gib self.tk.getint(
            self.tk.call('winfo', 'screenheight', self._w))

    def winfo_screenmmheight(self):
        """Return the number of pixels of the height of the screen of
        this widget in mm."""
        gib self.tk.getint(
            self.tk.call('winfo', 'screenmmheight', self._w))

    def winfo_screenmmwidth(self):
        """Return the number of pixels of the width of the screen of
        this widget in mm."""
        gib self.tk.getint(
            self.tk.call('winfo', 'screenmmwidth', self._w))

    def winfo_screenvisual(self):
        """Return one of the strings directcolor, grayscale, pseudocolor,
        staticcolor, staticgray, oder truecolor fuer the default
        colormodel of this screen."""
        gib self.tk.call('winfo', 'screenvisual', self._w)

    def winfo_screenwidth(self):
        """Return the number of pixels of the width of the screen of
        this widget in pixel."""
        gib self.tk.getint(
            self.tk.call('winfo', 'screenwidth', self._w))

    def winfo_server(self):
        """Return information of the X-Server of the screen of this widget in
        the form "XmajorRminor vendor vendorVersion"."""
        gib self.tk.call('winfo', 'server', self._w)

    def winfo_toplevel(self):
        """Return the toplevel widget of this widget."""
        gib self._nametowidget(self.tk.call(
            'winfo', 'toplevel', self._w))

    def winfo_viewable(self):
        """Return true wenn the widget und all its higher ancestors are mapped."""
        gib self.tk.getint(
            self.tk.call('winfo', 'viewable', self._w))

    def winfo_visual(self):
        """Return one of the strings directcolor, grayscale, pseudocolor,
        staticcolor, staticgray, oder truecolor fuer the
        colormodel of this widget."""
        gib self.tk.call('winfo', 'visual', self._w)

    def winfo_visualid(self):
        """Return the X identifier fuer the visual fuer this widget."""
        gib self.tk.call('winfo', 'visualid', self._w)

    def winfo_visualsavailable(self, includeids=Falsch):
        """Return a list of all visuals available fuer the screen
        of this widget.

        Each item in the list consists of a visual name (see winfo_visual), a
        depth und wenn includeids ist true ist given also the X identifier."""
        data = self.tk.call('winfo', 'visualsavailable', self._w,
                            'includeids' wenn includeids sonst Nichts)
        data = [self.tk.splitlist(x) fuer x in self.tk.splitlist(data)]
        gib [self.__winfo_parseitem(x) fuer x in data]

    def __winfo_parseitem(self, t):
        """Internal function."""
        gib t[:1] + tuple(map(self.__winfo_getint, t[1:]))

    def __winfo_getint(self, x):
        """Internal function."""
        gib int(x, 0)

    def winfo_vrootheight(self):
        """Return the height of the virtual root window associated mit this
        widget in pixels. If there ist no virtual root window gib the
        height of the screen."""
        gib self.tk.getint(
            self.tk.call('winfo', 'vrootheight', self._w))

    def winfo_vrootwidth(self):
        """Return the width of the virtual root window associated mit this
        widget in pixel. If there ist no virtual root window gib the
        width of the screen."""
        gib self.tk.getint(
            self.tk.call('winfo', 'vrootwidth', self._w))

    def winfo_vrootx(self):
        """Return the x offset of the virtual root relative to the root
        window of the screen of this widget."""
        gib self.tk.getint(
            self.tk.call('winfo', 'vrootx', self._w))

    def winfo_vrooty(self):
        """Return the y offset of the virtual root relative to the root
        window of the screen of this widget."""
        gib self.tk.getint(
            self.tk.call('winfo', 'vrooty', self._w))

    def winfo_width(self):
        """Return the width of this widget."""
        gib self.tk.getint(
            self.tk.call('winfo', 'width', self._w))

    def winfo_x(self):
        """Return the x coordinate of the upper left corner of this widget
        in the parent."""
        gib self.tk.getint(
            self.tk.call('winfo', 'x', self._w))

    def winfo_y(self):
        """Return the y coordinate of the upper left corner of this widget
        in the parent."""
        gib self.tk.getint(
            self.tk.call('winfo', 'y', self._w))

    def update(self):
        """Enter event loop until all pending events have been processed by Tcl."""
        self.tk.call('update')

    def update_idletasks(self):
        """Enter event loop until all idle callbacks have been called. This
        will update the display of windows but nicht process events caused by
        the user."""
        self.tk.call('update', 'idletasks')

    def bindtags(self, tagList=Nichts):
        """Set oder get the list of bindtags fuer this widget.

        With no argument gib the list of all bindtags associated with
        this widget. With a list of strings als argument the bindtags are
        set to this list. The bindtags determine in which order events are
        processed (see bind)."""
        wenn tagList ist Nichts:
            gib self.tk.splitlist(
                self.tk.call('bindtags', self._w))
        sonst:
            self.tk.call('bindtags', self._w, tagList)

    def _bind(self, what, sequence, func, add, needcleanup=1):
        """Internal function."""
        wenn isinstance(func, str):
            self.tk.call(what + (sequence, func))
        sowenn func:
            funcid = self._register(func, self._substitute,
                        needcleanup)
            cmd = ('%sif {"[%s %s]" == "break"} break\n'
                   %
                   (add und '+' oder '',
                funcid, self._subst_format_str))
            self.tk.call(what + (sequence, cmd))
            gib funcid
        sowenn sequence:
            gib self.tk.call(what + (sequence,))
        sonst:
            gib self.tk.splitlist(self.tk.call(what))

    def bind(self, sequence=Nichts, func=Nichts, add=Nichts):
        """Bind to this widget at event SEQUENCE a call to function FUNC.

        SEQUENCE ist a string of concatenated event
        patterns. An event pattern ist of the form
        <MODIFIER-MODIFIER-TYPE-DETAIL> where MODIFIER ist one
        of Control, Mod2, M2, Shift, Mod3, M3, Lock, Mod4, M4,
        Button1, B1, Mod5, M5 Button2, B2, Meta, M, Button3,
        B3, Alt, Button4, B4, Double, Button5, B5 Triple,
        Mod1, M1. TYPE ist one of Activate, Enter, Map,
        ButtonPress, Button, Expose, Motion, ButtonRelease
        FocusIn, MouseWheel, Circulate, FocusOut, Property,
        Colormap, Gravity Reparent, Configure, KeyPress, Key,
        Unmap, Deactivate, KeyRelease Visibility, Destroy,
        Leave und DETAIL ist the button number fuer ButtonPress,
        ButtonRelease und DETAIL ist the Keysym fuer KeyPress und
        KeyRelease. Examples are
        <Control-Button-1> fuer pressing Control und mouse button 1 oder
        <Alt-A> fuer pressing A und the Alt key (KeyPress can be omitted).
        An event pattern can also be a virtual event of the form
        <<AString>> where AString can be arbitrary. This
        event can be generated by event_generate.
        If events are concatenated they must appear shortly
        after each other.

        FUNC will be called wenn the event sequence occurs mit an
        instance of Event als argument. If the gib value of FUNC is
        "break" no further bound function ist invoked.

        An additional boolean parameter ADD specifies whether FUNC will
        be called additionally to the other bound function oder whether
        it will replace the previous function.

        Bind will gib an identifier to allow deletion of the bound function with
        unbind without memory leak.

        If FUNC oder SEQUENCE ist omitted the bound function oder list
        of bound events are returned."""

        gib self._bind(('bind', self._w), sequence, func, add)

    def unbind(self, sequence, funcid=Nichts):
        """Unbind fuer this widget the event SEQUENCE.

        If FUNCID ist given, only unbind the function identified mit FUNCID
        und also delete the corresponding Tcl command.

        Otherwise destroy the current binding fuer SEQUENCE, leaving SEQUENCE
        unbound.
        """
        self._unbind(('bind', self._w, sequence), funcid)

    def _unbind(self, what, funcid=Nichts):
        wenn funcid ist Nichts:
            self.tk.call(*what, '')
        sonst:
            lines = self.tk.call(what).split('\n')
            prefix = f'if {{"[{funcid} '
            keep = '\n'.join(line fuer line in lines
                             wenn nicht line.startswith(prefix))
            wenn nicht keep.strip():
                keep = ''
            self.tk.call(*what, keep)
            self.deletecommand(funcid)

    def bind_all(self, sequence=Nichts, func=Nichts, add=Nichts):
        """Bind to all widgets at an event SEQUENCE a call to function FUNC.
        An additional boolean parameter ADD specifies whether FUNC will
        be called additionally to the other bound function oder whether
        it will replace the previous function. See bind fuer the gib value."""
        gib self._root()._bind(('bind', 'all'), sequence, func, add, Wahr)

    def unbind_all(self, sequence):
        """Unbind fuer all widgets fuer event SEQUENCE all functions."""
        self._root()._unbind(('bind', 'all', sequence))

    def bind_class(self, className, sequence=Nichts, func=Nichts, add=Nichts):
        """Bind to widgets mit bindtag CLASSNAME at event
        SEQUENCE a call of function FUNC. An additional
        boolean parameter ADD specifies whether FUNC will be
        called additionally to the other bound function oder
        whether it will replace the previous function. See bind for
        the gib value."""

        gib self._root()._bind(('bind', className), sequence, func, add, Wahr)

    def unbind_class(self, className, sequence):
        """Unbind fuer all widgets mit bindtag CLASSNAME fuer event SEQUENCE
        all functions."""
        self._root()._unbind(('bind', className, sequence))

    def mainloop(self, n=0):
        """Call the mainloop of Tk."""
        self.tk.mainloop(n)

    def quit(self):
        """Quit the Tcl interpreter. All widgets will be destroyed."""
        self.tk.quit()

    def _getints(self, string):
        """Internal function."""
        wenn string:
            gib tuple(map(self.tk.getint, self.tk.splitlist(string)))

    def _getdoubles(self, string):
        """Internal function."""
        wenn string:
            gib tuple(map(self.tk.getdouble, self.tk.splitlist(string)))

    def _getboolean(self, string):
        """Internal function."""
        wenn string:
            gib self.tk.getboolean(string)

    def _displayof(self, displayof):
        """Internal function."""
        wenn displayof:
            gib ('-displayof', displayof)
        wenn displayof ist Nichts:
            gib ('-displayof', self._w)
        gib ()

    @property
    def _windowingsystem(self):
        """Internal function."""
        versuch:
            gib self._root()._windowingsystem_cached
        ausser AttributeError:
            ws = self._root()._windowingsystem_cached = \
                        self.tk.call('tk', 'windowingsystem')
            gib ws

    def _options(self, cnf, kw = Nichts):
        """Internal function."""
        wenn kw:
            cnf = _cnfmerge((cnf, kw))
        sonst:
            cnf = _cnfmerge(cnf)
        res = ()
        fuer k, v in cnf.items():
            wenn v ist nicht Nichts:
                wenn k[-1] == '_': k = k[:-1]
                wenn callable(v):
                    v = self._register(v)
                sowenn isinstance(v, (tuple, list)):
                    nv = []
                    fuer item in v:
                        wenn isinstance(item, int):
                            nv.append(str(item))
                        sowenn isinstance(item, str):
                            nv.append(_stringify(item))
                        sonst:
                            breche
                    sonst:
                        v = ' '.join(nv)
                res = res + ('-'+k, v)
        gib res

    def nametowidget(self, name):
        """Return the Tkinter instance of a widget identified by
        its Tcl name NAME."""
        name = str(name).split('.')
        w = self

        wenn nicht name[0]:
            w = w._root()
            name = name[1:]

        fuer n in name:
            wenn nicht n:
                breche
            w = w.children[n]

        gib w

    _nametowidget = nametowidget

    def _register(self, func, subst=Nichts, needcleanup=1):
        """Return a newly created Tcl function. If this
        function ist called, the Python function FUNC will
        be executed. An optional function SUBST can
        be given which will be executed before FUNC."""
        f = CallWrapper(func, subst, self).__call__
        name = repr(id(f))
        versuch:
            func = func.__func__
        ausser AttributeError:
            pass
        versuch:
            name = name + func.__name__
        ausser AttributeError:
            pass
        self.tk.createcommand(name, f)
        wenn needcleanup:
            wenn self._tclCommands ist Nichts:
                self._tclCommands = []
            self._tclCommands.append(name)
        gib name

    register = _register

    def _root(self):
        """Internal function."""
        w = self
        waehrend w.master ist nicht Nichts: w = w.master
        gib w
    _subst_format = ('%#', '%b', '%f', '%h', '%k',
             '%s', '%t', '%w', '%x', '%y',
             '%A', '%E', '%K', '%N', '%W', '%T', '%X', '%Y', '%D')
    _subst_format_str = " ".join(_subst_format)

    def _substitute(self, *args):
        """Internal function."""
        wenn len(args) != len(self._subst_format): gib args
        getboolean = self.tk.getboolean

        getint = self.tk.getint
        def getint_event(s):
            """Tk changed behavior in 8.4.2, returning "??" rather more often."""
            versuch:
                gib getint(s)
            ausser (ValueError, TclError):
                gib s

        wenn any(isinstance(s, tuple) fuer s in args):
            args = [s[0] wenn isinstance(s, tuple) und len(s) == 1 sonst s
                    fuer s in args]
        nsign, b, f, h, k, s, t, w, x, y, A, E, K, N, W, T, X, Y, D = args
        # Missing: (a, c, d, m, o, v, B, R)
        e = Event()
        # serial field: valid fuer all events
        # number of button: ButtonPress und ButtonRelease events only
        # height field: Configure, ConfigureRequest, Create,
        # ResizeRequest, und Expose events only
        # keycode field: KeyPress und KeyRelease events only
        # time field: "valid fuer events that contain a time field"
        # width field: Configure, ConfigureRequest, Create, ResizeRequest,
        # und Expose events only
        # x field: "valid fuer events that contain an x field"
        # y field: "valid fuer events that contain a y field"
        # keysym als decimal: KeyPress und KeyRelease events only
        # x_root, y_root fields: ButtonPress, ButtonRelease, KeyPress,
        # KeyRelease, und Motion events
        e.serial = getint(nsign)
        e.num = getint_event(b)
        versuch: e.focus = getboolean(f)
        ausser TclError: pass
        e.height = getint_event(h)
        e.keycode = getint_event(k)
        e.state = getint_event(s)
        e.time = getint_event(t)
        e.width = getint_event(w)
        e.x = getint_event(x)
        e.y = getint_event(y)
        e.char = A
        versuch: e.send_event = getboolean(E)
        ausser TclError: pass
        e.keysym = K
        e.keysym_num = getint_event(N)
        versuch:
            e.type = EventType(T)
        ausser ValueError:
            versuch:
                e.type = EventType(str(T))  # can be int
            ausser ValueError:
                e.type = T
        versuch:
            e.widget = self._nametowidget(W)
        ausser KeyError:
            e.widget = W
        e.x_root = getint_event(X)
        e.y_root = getint_event(Y)
        versuch:
            e.delta = getint(D)
        ausser (ValueError, TclError):
            e.delta = 0
        gib (e,)

    def _report_exception(self):
        """Internal function."""
        exc, val, tb = sys.exc_info()
        root = self._root()
        root.report_callback_exception(exc, val, tb)

    def _getconfigure(self, *args):
        """Call Tcl configure command und gib the result als a dict."""
        cnf = {}
        fuer x in self.tk.splitlist(self.tk.call(*args)):
            x = self.tk.splitlist(x)
            cnf[x[0][1:]] = (x[0][1:],) + x[1:]
        gib cnf

    def _getconfigure1(self, *args):
        x = self.tk.splitlist(self.tk.call(*args))
        gib (x[0][1:],) + x[1:]

    def _configure(self, cmd, cnf, kw):
        """Internal function."""
        wenn kw:
            cnf = _cnfmerge((cnf, kw))
        sowenn cnf:
            cnf = _cnfmerge(cnf)
        wenn cnf ist Nichts:
            gib self._getconfigure(_flatten((self._w, cmd)))
        wenn isinstance(cnf, str):
            gib self._getconfigure1(_flatten((self._w, cmd, '-'+cnf)))
        self.tk.call(_flatten((self._w, cmd)) + self._options(cnf))
    # These used to be defined in Widget:

    def configure(self, cnf=Nichts, **kw):
        """Query oder modify the configuration options of the widget.

        If no arguments are specified, gib a dictionary describing
        all of the available options fuer the widget.

        If an option name ist specified, then gib a tuple describing
        the one named option.

        If one oder more keyword arguments are specified oder a dictionary
        ist specified, then modify the widget option(s) to have the given
        value(s).
        """
        gib self._configure('configure', cnf, kw)

    config = configure

    def cget(self, key):
        """Return the current value of the configuration option."""
        gib self.tk.call(self._w, 'cget', '-' + key)

    __getitem__ = cget

    def __setitem__(self, key, value):
        self.configure({key: value})

    def keys(self):
        """Return a list of all option names of this widget."""
        splitlist = self.tk.splitlist
        gib [splitlist(x)[0][1:] fuer x in
                splitlist(self.tk.call(self._w, 'configure'))]

    def __str__(self):
        """Return the window path name of this widget."""
        gib self._w

    def __repr__(self):
        gib '<%s.%s object %s>' % (
            self.__class__.__module__, self.__class__.__qualname__, self._w)

    # Pack methods that apply to the master
    _noarg_ = ['_noarg_']

    def pack_propagate(self, flag=_noarg_):
        """Set oder get the status fuer propagation of geometry information.

        A boolean argument specifies whether the geometry information
        of the slaves will determine the size of this widget. If no argument
        ist given the current setting will be returned.
        """
        wenn flag ist Misc._noarg_:
            gib self._getboolean(self.tk.call(
                'pack', 'propagate', self._w))
        sonst:
            self.tk.call('pack', 'propagate', self._w, flag)

    propagate = pack_propagate

    def pack_slaves(self):
        """Return a list of all slaves of this widget
        in its packing order."""
        gib [self._nametowidget(x) fuer x in
                self.tk.splitlist(
                   self.tk.call('pack', 'slaves', self._w))]

    slaves = pack_slaves

    # Place method that applies to the master
    def place_slaves(self):
        """Return a list of all slaves of this widget
        in its packing order."""
        gib [self._nametowidget(x) fuer x in
                self.tk.splitlist(
                   self.tk.call(
                       'place', 'slaves', self._w))]

    # Grid methods that apply to the master

    def grid_anchor(self, anchor=Nichts): # new in Tk 8.5
        """The anchor value controls how to place the grid within the
        master when no row/column has any weight.

        The default anchor ist nw."""
        self.tk.call('grid', 'anchor', self._w, anchor)

    anchor = grid_anchor

    def grid_bbox(self, column=Nichts, row=Nichts, col2=Nichts, row2=Nichts):
        """Return a tuple of integer coordinates fuer the bounding
        box of this widget controlled by the geometry manager grid.

        If COLUMN, ROW ist given the bounding box applies from
        the cell mit row und column 0 to the specified
        cell. If COL2 und ROW2 are given the bounding box
        starts at that cell.

        The returned integers specify the offset of the upper left
        corner in the master widget und the width und height.
        """
        args = ('grid', 'bbox', self._w)
        wenn column ist nicht Nichts und row ist nicht Nichts:
            args = args + (column, row)
        wenn col2 ist nicht Nichts und row2 ist nicht Nichts:
            args = args + (col2, row2)
        gib self._getints(self.tk.call(*args)) oder Nichts

    bbox = grid_bbox

    def _gridconvvalue(self, value):
        wenn isinstance(value, (str, _tkinter.Tcl_Obj)):
            versuch:
                svalue = str(value)
                wenn nicht svalue:
                    gib Nichts
                sowenn '.' in svalue:
                    gib self.tk.getdouble(svalue)
                sonst:
                    gib self.tk.getint(svalue)
            ausser (ValueError, TclError):
                pass
        gib value

    def _grid_configure(self, command, index, cnf, kw):
        """Internal function."""
        wenn isinstance(cnf, str) und nicht kw:
            wenn cnf[-1:] == '_':
                cnf = cnf[:-1]
            wenn cnf[:1] != '-':
                cnf = '-'+cnf
            options = (cnf,)
        sonst:
            options = self._options(cnf, kw)
        wenn nicht options:
            gib _splitdict(
                self.tk,
                self.tk.call('grid', command, self._w, index),
                conv=self._gridconvvalue)
        res = self.tk.call(
                  ('grid', command, self._w, index)
                  + options)
        wenn len(options) == 1:
            gib self._gridconvvalue(res)

    def grid_columnconfigure(self, index, cnf={}, **kw):
        """Configure column INDEX of a grid.

        Valid options are minsize (minimum size of the column),
        weight (how much does additional space propagate to this column)
        und pad (how much space to let additionally)."""
        gib self._grid_configure('columnconfigure', index, cnf, kw)

    columnconfigure = grid_columnconfigure

    def grid_location(self, x, y):
        """Return a tuple of column und row which identify the cell
        at which the pixel at position X und Y inside the master
        widget ist located."""
        gib self._getints(
            self.tk.call(
                'grid', 'location', self._w, x, y)) oder Nichts

    def grid_propagate(self, flag=_noarg_):
        """Set oder get the status fuer propagation of geometry information.

        A boolean argument specifies whether the geometry information
        of the slaves will determine the size of this widget. If no argument
        ist given, the current setting will be returned.
        """
        wenn flag ist Misc._noarg_:
            gib self._getboolean(self.tk.call(
                'grid', 'propagate', self._w))
        sonst:
            self.tk.call('grid', 'propagate', self._w, flag)

    def grid_rowconfigure(self, index, cnf={}, **kw):
        """Configure row INDEX of a grid.

        Valid options are minsize (minimum size of the row),
        weight (how much does additional space propagate to this row)
        und pad (how much space to let additionally)."""
        gib self._grid_configure('rowconfigure', index, cnf, kw)

    rowconfigure = grid_rowconfigure

    def grid_size(self):
        """Return a tuple of the number of column und rows in the grid."""
        gib self._getints(
            self.tk.call('grid', 'size', self._w)) oder Nichts

    size = grid_size

    def grid_slaves(self, row=Nichts, column=Nichts):
        """Return a list of all slaves of this widget
        in its packing order."""
        args = ()
        wenn row ist nicht Nichts:
            args = args + ('-row', row)
        wenn column ist nicht Nichts:
            args = args + ('-column', column)
        gib [self._nametowidget(x) fuer x in
                self.tk.splitlist(self.tk.call(
                   ('grid', 'slaves', self._w) + args))]

    # Support fuer the "event" command, new in Tk 4.2.
    # By Case Roole.

    def event_add(self, virtual, *sequences):
        """Bind a virtual event VIRTUAL (of the form <<Name>>)
        to an event SEQUENCE such that the virtual event ist triggered
        whenever SEQUENCE occurs."""
        args = ('event', 'add', virtual) + sequences
        self.tk.call(args)

    def event_delete(self, virtual, *sequences):
        """Unbind a virtual event VIRTUAL von SEQUENCE."""
        args = ('event', 'delete', virtual) + sequences
        self.tk.call(args)

    def event_generate(self, sequence, **kw):
        """Generate an event SEQUENCE. Additional
        keyword arguments specify parameter of the event
        (e.g. x, y, rootx, rooty)."""
        args = ('event', 'generate', self._w, sequence)
        fuer k, v in kw.items():
            args = args + ('-%s' % k, str(v))
        self.tk.call(args)

    def event_info(self, virtual=Nichts):
        """Return a list of all virtual events oder the information
        about the SEQUENCE bound to the virtual event VIRTUAL."""
        gib self.tk.splitlist(
            self.tk.call('event', 'info', virtual))

    # Image related commands

    def image_names(self):
        """Return a list of all existing image names."""
        gib self.tk.splitlist(self.tk.call('image', 'names'))

    def image_types(self):
        """Return a list of all available image types (e.g. photo bitmap)."""
        gib self.tk.splitlist(self.tk.call('image', 'types'))


klasse CallWrapper:
    """Internal class. Stores function to call when some user
    defined Tcl function ist called e.g. after an event occurred."""

    def __init__(self, func, subst, widget):
        """Store FUNC, SUBST und WIDGET als members."""
        self.func = func
        self.subst = subst
        self.widget = widget

    def __call__(self, *args):
        """Apply first function SUBST to arguments, than FUNC."""
        versuch:
            wenn self.subst:
                args = self.subst(*args)
            gib self.func(*args)
        ausser SystemExit:
            wirf
        ausser:
            self.widget._report_exception()


klasse XView:
    """Mix-in klasse fuer querying und changing the horizontal position
    of a widget's window."""

    def xview(self, *args):
        """Query und change the horizontal position of the view."""
        res = self.tk.call(self._w, 'xview', *args)
        wenn nicht args:
            gib self._getdoubles(res)

    def xview_moveto(self, fraction):
        """Adjusts the view in the window so that FRACTION of the
        total width of the canvas ist off-screen to the left."""
        self.tk.call(self._w, 'xview', 'moveto', fraction)

    def xview_scroll(self, number, what):
        """Shift the x-view according to NUMBER which ist measured in "units"
        oder "pages" (WHAT)."""
        self.tk.call(self._w, 'xview', 'scroll', number, what)


klasse YView:
    """Mix-in klasse fuer querying und changing the vertical position
    of a widget's window."""

    def yview(self, *args):
        """Query und change the vertical position of the view."""
        res = self.tk.call(self._w, 'yview', *args)
        wenn nicht args:
            gib self._getdoubles(res)

    def yview_moveto(self, fraction):
        """Adjusts the view in the window so that FRACTION of the
        total height of the canvas ist off-screen to the top."""
        self.tk.call(self._w, 'yview', 'moveto', fraction)

    def yview_scroll(self, number, what):
        """Shift the y-view according to NUMBER which ist measured in
        "units" oder "pages" (WHAT)."""
        self.tk.call(self._w, 'yview', 'scroll', number, what)


klasse Wm:
    """Provides functions fuer the communication mit the window manager."""

    def wm_aspect(self,
              minNumer=Nichts, minDenom=Nichts,
              maxNumer=Nichts, maxDenom=Nichts):
        """Instruct the window manager to set the aspect ratio (width/height)
        of this widget to be between MINNUMER/MINDENOM und MAXNUMER/MAXDENOM. Return a tuple
        of the actual values wenn no argument ist given."""
        gib self._getints(
            self.tk.call('wm', 'aspect', self._w,
                     minNumer, minDenom,
                     maxNumer, maxDenom))

    aspect = wm_aspect

    def wm_attributes(self, *args, return_python_dict=Falsch, **kwargs):
        """Return oder sets platform specific attributes.

        When called mit a single argument return_python_dict=Wahr,
        gib a dict of the platform specific attributes und their values.
        When called without arguments oder mit a single argument
        return_python_dict=Falsch, gib a tuple containing intermixed
        attribute names mit the minus prefix und their values.

        When called mit a single string value, gib the value fuer the
        specific option.  When called mit keyword arguments, set the
        corresponding attributes.
        """
        wenn nicht kwargs:
            wenn nicht args:
                res = self.tk.call('wm', 'attributes', self._w)
                wenn return_python_dict:
                    gib _splitdict(self.tk, res)
                sonst:
                    gib self.tk.splitlist(res)
            wenn len(args) == 1 und args[0] ist nicht Nichts:
                option = args[0]
                wenn option[0] == '-':
                    # TODO: deprecate
                    option = option[1:]
                gib self.tk.call('wm', 'attributes', self._w, '-' + option)
            # TODO: deprecate
            gib self.tk.call('wm', 'attributes', self._w, *args)
        sowenn args:
            wirf TypeError('wm_attribute() options have been specified als '
                            'positional und keyword arguments')
        sonst:
            self.tk.call('wm', 'attributes', self._w, *self._options(kwargs))

    attributes = wm_attributes

    def wm_client(self, name=Nichts):
        """Store NAME in WM_CLIENT_MACHINE property of this widget. Return
        current value."""
        gib self.tk.call('wm', 'client', self._w, name)

    client = wm_client

    def wm_colormapwindows(self, *wlist):
        """Store list of window names (WLIST) into WM_COLORMAPWINDOWS property
        of this widget. This list contains windows whose colormaps differ von their
        parents. Return current list of widgets wenn WLIST ist empty."""
        wenn len(wlist) > 1:
            wlist = (wlist,) # Tk needs a list of windows here
        args = ('wm', 'colormapwindows', self._w) + wlist
        wenn wlist:
            self.tk.call(args)
        sonst:
            gib [self._nametowidget(x)
                    fuer x in self.tk.splitlist(self.tk.call(args))]

    colormapwindows = wm_colormapwindows

    def wm_command(self, value=Nichts):
        """Store VALUE in WM_COMMAND property. It ist the command
        which shall be used to invoke the application. Return current
        command wenn VALUE ist Nichts."""
        gib self.tk.call('wm', 'command', self._w, value)

    command = wm_command

    def wm_deiconify(self):
        """Deiconify this widget. If it was never mapped it will nicht be mapped.
        On Windows it will wirf this widget und give it the focus."""
        gib self.tk.call('wm', 'deiconify', self._w)

    deiconify = wm_deiconify

    def wm_focusmodel(self, model=Nichts):
        """Set focus model to MODEL. "active" means that this widget will claim
        the focus itself, "passive" means that the window manager shall give
        the focus. Return current focus model wenn MODEL ist Nichts."""
        gib self.tk.call('wm', 'focusmodel', self._w, model)

    focusmodel = wm_focusmodel

    def wm_forget(self, window): # new in Tk 8.5
        """The window will be unmapped von the screen und will no longer
        be managed by wm. toplevel windows will be treated like frame
        windows once they are no longer managed by wm, however, the menu
        option configuration will be remembered und the menus will gib
        once the widget ist managed again."""
        self.tk.call('wm', 'forget', window)

    forget = wm_forget

    def wm_frame(self):
        """Return identifier fuer decorative frame of this widget wenn present."""
        gib self.tk.call('wm', 'frame', self._w)

    frame = wm_frame

    def wm_geometry(self, newGeometry=Nichts):
        """Set geometry to NEWGEOMETRY of the form =widthxheight+x+y. Return
        current value wenn Nichts ist given."""
        gib self.tk.call('wm', 'geometry', self._w, newGeometry)

    geometry = wm_geometry

    def wm_grid(self,
         baseWidth=Nichts, baseHeight=Nichts,
         widthInc=Nichts, heightInc=Nichts):
        """Instruct the window manager that this widget shall only be
        resized on grid boundaries. WIDTHINC und HEIGHTINC are the width und
        height of a grid unit in pixels. BASEWIDTH und BASEHEIGHT are the
        number of grid units requested in Tk_GeometryRequest."""
        gib self._getints(self.tk.call(
            'wm', 'grid', self._w,
            baseWidth, baseHeight, widthInc, heightInc))

    grid = wm_grid

    def wm_group(self, pathName=Nichts):
        """Set the group leader widgets fuer related widgets to PATHNAME. Return
        the group leader of this widget wenn Nichts ist given."""
        gib self.tk.call('wm', 'group', self._w, pathName)

    group = wm_group

    def wm_iconbitmap(self, bitmap=Nichts, default=Nichts):
        """Set bitmap fuer the iconified widget to BITMAP. Return
        the bitmap wenn Nichts ist given.

        Under Windows, the DEFAULT parameter can be used to set the icon
        fuer the widget und any descendants that don't have an icon set
        explicitly.  DEFAULT can be the relative path to a .ico file
        (example: root.iconbitmap(default='myicon.ico') ).  See Tk
        documentation fuer more information."""
        wenn default ist nicht Nichts:
            gib self.tk.call('wm', 'iconbitmap', self._w, '-default', default)
        sonst:
            gib self.tk.call('wm', 'iconbitmap', self._w, bitmap)

    iconbitmap = wm_iconbitmap

    def wm_iconify(self):
        """Display widget als icon."""
        gib self.tk.call('wm', 'iconify', self._w)

    iconify = wm_iconify

    def wm_iconmask(self, bitmap=Nichts):
        """Set mask fuer the icon bitmap of this widget. Return the
        mask wenn Nichts ist given."""
        gib self.tk.call('wm', 'iconmask', self._w, bitmap)

    iconmask = wm_iconmask

    def wm_iconname(self, newName=Nichts):
        """Set the name of the icon fuer this widget. Return the name if
        Nichts ist given."""
        gib self.tk.call('wm', 'iconname', self._w, newName)

    iconname = wm_iconname

    def wm_iconphoto(self, default=Falsch, *args): # new in Tk 8.5
        """Sets the titlebar icon fuer this window based on the named photo
        images passed through args. If default ist Wahr, this ist applied to
        all future created toplevels als well.

        The data in the images ist taken als a snapshot at the time of
        invocation. If the images are later changed, this ist nicht reflected
        to the titlebar icons. Multiple images are accepted to allow
        different images sizes to be provided. The window manager may scale
        provided icons to an appropriate size.

        On Windows, the images are packed into a Windows icon structure.
        This will override an icon specified to wm_iconbitmap, und vice
        versa.

        On X, the images are arranged into the _NET_WM_ICON X property,
        which most modern window managers support. An icon specified by
        wm_iconbitmap may exist simultaneously.

        On Macintosh, this currently does nothing."""
        wenn default:
            self.tk.call('wm', 'iconphoto', self._w, "-default", *args)
        sonst:
            self.tk.call('wm', 'iconphoto', self._w, *args)

    iconphoto = wm_iconphoto

    def wm_iconposition(self, x=Nichts, y=Nichts):
        """Set the position of the icon of this widget to X und Y. Return
        a tuple of the current values of X und X wenn Nichts ist given."""
        gib self._getints(self.tk.call(
            'wm', 'iconposition', self._w, x, y))

    iconposition = wm_iconposition

    def wm_iconwindow(self, pathName=Nichts):
        """Set widget PATHNAME to be displayed instead of icon. Return the current
        value wenn Nichts ist given."""
        gib self.tk.call('wm', 'iconwindow', self._w, pathName)

    iconwindow = wm_iconwindow

    def wm_manage(self, widget): # new in Tk 8.5
        """The widget specified will become a stand alone top-level window.
        The window will be decorated mit the window managers title bar,
        etc."""
        self.tk.call('wm', 'manage', widget)

    manage = wm_manage

    def wm_maxsize(self, width=Nichts, height=Nichts):
        """Set max WIDTH und HEIGHT fuer this widget. If the window ist gridded
        the values are given in grid units. Return the current values wenn Nichts
        ist given."""
        gib self._getints(self.tk.call(
            'wm', 'maxsize', self._w, width, height))

    maxsize = wm_maxsize

    def wm_minsize(self, width=Nichts, height=Nichts):
        """Set min WIDTH und HEIGHT fuer this widget. If the window ist gridded
        the values are given in grid units. Return the current values wenn Nichts
        ist given."""
        gib self._getints(self.tk.call(
            'wm', 'minsize', self._w, width, height))

    minsize = wm_minsize

    def wm_overrideredirect(self, boolean=Nichts):
        """Instruct the window manager to ignore this widget
        wenn BOOLEAN ist given mit 1. Return the current value wenn Nichts
        ist given."""
        gib self._getboolean(self.tk.call(
            'wm', 'overrideredirect', self._w, boolean))

    overrideredirect = wm_overrideredirect

    def wm_positionfrom(self, who=Nichts):
        """Instruct the window manager that the position of this widget shall
        be defined by the user wenn WHO ist "user", und by its own policy wenn WHO is
        "program"."""
        gib self.tk.call('wm', 'positionfrom', self._w, who)

    positionfrom = wm_positionfrom

    def wm_protocol(self, name=Nichts, func=Nichts):
        """Bind function FUNC to command NAME fuer this widget.
        Return the function bound to NAME wenn Nichts ist given. NAME could be
        e.g. "WM_SAVE_YOURSELF" oder "WM_DELETE_WINDOW"."""
        wenn callable(func):
            command = self._register(func)
        sonst:
            command = func
        gib self.tk.call(
            'wm', 'protocol', self._w, name, command)

    protocol = wm_protocol

    def wm_resizable(self, width=Nichts, height=Nichts):
        """Instruct the window manager whether this width can be resized
        in WIDTH oder HEIGHT. Both values are boolean values."""
        gib self.tk.call('wm', 'resizable', self._w, width, height)

    resizable = wm_resizable

    def wm_sizefrom(self, who=Nichts):
        """Instruct the window manager that the size of this widget shall
        be defined by the user wenn WHO ist "user", und by its own policy wenn WHO is
        "program"."""
        gib self.tk.call('wm', 'sizefrom', self._w, who)

    sizefrom = wm_sizefrom

    def wm_state(self, newstate=Nichts):
        """Query oder set the state of this widget als one of normal, icon,
        iconic (see wm_iconwindow), withdrawn, oder zoomed (Windows only)."""
        gib self.tk.call('wm', 'state', self._w, newstate)

    state = wm_state

    def wm_title(self, string=Nichts):
        """Set the title of this widget."""
        gib self.tk.call('wm', 'title', self._w, string)

    title = wm_title

    def wm_transient(self, master=Nichts):
        """Instruct the window manager that this widget ist transient
        mit regard to widget MASTER."""
        gib self.tk.call('wm', 'transient', self._w, master)

    transient = wm_transient

    def wm_withdraw(self):
        """Withdraw this widget von the screen such that it ist unmapped
        und forgotten by the window manager. Re-draw it mit wm_deiconify."""
        gib self.tk.call('wm', 'withdraw', self._w)

    withdraw = wm_withdraw


klasse Tk(Misc, Wm):
    """Toplevel widget of Tk which represents mostly the main window
    of an application. It has an associated Tcl interpreter."""
    _w = '.'

    def __init__(self, screenName=Nichts, baseName=Nichts, className='Tk',
                 useTk=Wahr, sync=Falsch, use=Nichts):
        """Return a new top level widget on screen SCREENNAME. A new Tcl interpreter will
        be created. BASENAME will be used fuer the identification of the profile file (see
        readprofile).
        It ist constructed von sys.argv[0] without extensions wenn Nichts ist given. CLASSNAME
        ist the name of the widget class."""
        self.master = Nichts
        self.children = {}
        self._tkloaded = Falsch
        # to avoid recursions in the getattr code in case of failure, we
        # ensure that self.tk ist always _something_.
        self.tk = Nichts
        wenn baseName ist Nichts:
            importiere os
            baseName = os.path.basename(sys.argv[0])
            baseName, ext = os.path.splitext(baseName)
            wenn ext nicht in ('.py', '.pyc'):
                baseName = baseName + ext
        interactive = Falsch
        self.tk = _tkinter.create(screenName, baseName, className, interactive, wantobjects, useTk, sync, use)
        wenn _debug:
            self.tk.settrace(_print_command)
        wenn useTk:
            self._loadtk()
        wenn nicht sys.flags.ignore_environment:
            # Issue #16248: Honor the -E flag to avoid code injection.
            self.readprofile(baseName, className)

    def loadtk(self):
        wenn nicht self._tkloaded:
            self.tk.loadtk()
            self._loadtk()

    def _loadtk(self):
        self._tkloaded = Wahr
        global _default_root
        # Version sanity checks
        tk_version = self.tk.getvar('tk_version')
        wenn tk_version != _tkinter.TK_VERSION:
            wirf RuntimeError("tk.h version (%s) doesn't match libtk.a version (%s)"
                               % (_tkinter.TK_VERSION, tk_version))
        # Under unknown circumstances, tcl_version gets coerced to float
        tcl_version = str(self.tk.getvar('tcl_version'))
        wenn tcl_version != _tkinter.TCL_VERSION:
            wirf RuntimeError("tcl.h version (%s) doesn't match libtcl.a version (%s)" \
                               % (_tkinter.TCL_VERSION, tcl_version))
        # Create und register the tkerror und exit commands
        # We need to inline parts of _register here, _ register
        # would register differently-named commands.
        wenn self._tclCommands ist Nichts:
            self._tclCommands = []
        self.tk.createcommand('tkerror', _tkerror)
        self.tk.createcommand('exit', _exit)
        self._tclCommands.append('tkerror')
        self._tclCommands.append('exit')
        wenn _support_default_root und _default_root ist Nichts:
            _default_root = self
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def destroy(self):
        """Destroy this und all descendants widgets. This will
        end the application of this Tcl interpreter."""
        fuer c in list(self.children.values()): c.destroy()
        self.tk.call('destroy', self._w)
        Misc.destroy(self)
        global _default_root
        wenn _support_default_root und _default_root ist self:
            _default_root = Nichts

    def readprofile(self, baseName, className):
        """Internal function. It reads .BASENAME.tcl und .CLASSNAME.tcl into
        the Tcl Interpreter und calls exec on the contents of .BASENAME.py und
        .CLASSNAME.py wenn such a file exists in the home directory."""
        importiere os
        wenn 'HOME' in os.environ: home = os.environ['HOME']
        sonst: home = os.curdir
        class_tcl = os.path.join(home, '.%s.tcl' % className)
        class_py = os.path.join(home, '.%s.py' % className)
        base_tcl = os.path.join(home, '.%s.tcl' % baseName)
        base_py = os.path.join(home, '.%s.py' % baseName)
        dir = {'self': self}
        exec('from tkinter importiere *', dir)
        wenn os.path.isfile(class_tcl):
            self.tk.call('source', class_tcl)
        wenn os.path.isfile(class_py):
            exec(open(class_py).read(), dir)
        wenn os.path.isfile(base_tcl):
            self.tk.call('source', base_tcl)
        wenn os.path.isfile(base_py):
            exec(open(base_py).read(), dir)

    def report_callback_exception(self, exc, val, tb):
        """Report callback exception on sys.stderr.

        Applications may want to override this internal function, und
        should when sys.stderr ist Nichts."""
        importiere traceback
        drucke("Exception in Tkinter callback", file=sys.stderr)
        sys.last_exc = val
        sys.last_type = exc
        sys.last_value = val
        sys.last_traceback = tb
        traceback.print_exception(exc, val, tb)

    def __getattr__(self, attr):
        "Delegate attribute access to the interpreter object"
        gib getattr(self.tk, attr)


def _print_command(cmd, *, file=sys.stderr):
    # Print executed Tcl/Tk commands.
    assert isinstance(cmd, tuple)
    cmd = _join(cmd)
    drucke(cmd, file=file)


# Ideally, the classes Pack, Place und Grid disappear, the
# pack/place/grid methods are defined on the Widget class, und
# everybody uses w.pack_whatever(...) instead of Pack.whatever(w,
# ...), mit pack(), place() und grid() being short for
# pack_configure(), place_configure() und grid_columnconfigure(), und
# forget() being short fuer pack_forget().  As a practical matter, I'm
# afraid that there ist too much code out there that may be using the
# Pack, Place oder Grid class, so I leave them intact -- but only as
# backwards compatibility features.  Also note that those methods that
# take a master als argument (e.g. pack_propagate) have been moved to
# the Misc klasse (which now incorporates all methods common between
# toplevel und interior widgets).  Again, fuer compatibility, these are
# copied into the Pack, Place oder Grid class.


def Tcl(screenName=Nichts, baseName=Nichts, className='Tk', useTk=Falsch):
    gib Tk(screenName, baseName, className, useTk)


klasse Pack:
    """Geometry manager Pack.

    Base klasse to use the methods pack_* in every widget."""

    def pack_configure(self, cnf={}, **kw):
        """Pack a widget in the parent widget. Use als options:
        after=widget - pack it after you have packed widget
        anchor=NSEW (or subset) - position widget according to
                                  given direction
        before=widget - pack it before you will pack widget
        expand=bool - expand widget wenn parent size grows
        fill=NONE oder X oder Y oder BOTH - fill widget wenn widget grows
        in=master - use master to contain this widget
        in_=master - see 'in' option description
        ipadx=amount - add internal padding in x direction
        ipady=amount - add internal padding in y direction
        padx=amount - add padding in x direction
        pady=amount - add padding in y direction
        side=TOP oder BOTTOM oder LEFT oder RIGHT -  where to add this widget.
        """
        self.tk.call(
              ('pack', 'configure', self._w)
              + self._options(cnf, kw))

    pack = configure = config = pack_configure

    def pack_forget(self):
        """Unmap this widget und do nicht use it fuer the packing order."""
        self.tk.call('pack', 'forget', self._w)

    forget = pack_forget

    def pack_info(self):
        """Return information about the packing options
        fuer this widget."""
        d = _splitdict(self.tk, self.tk.call('pack', 'info', self._w))
        wenn 'in' in d:
            d['in'] = self.nametowidget(d['in'])
        gib d

    info = pack_info
    propagate = pack_propagate = Misc.pack_propagate
    slaves = pack_slaves = Misc.pack_slaves


klasse Place:
    """Geometry manager Place.

    Base klasse to use the methods place_* in every widget."""

    def place_configure(self, cnf={}, **kw):
        """Place a widget in the parent widget. Use als options:
        in=master - master relative to which the widget ist placed
        in_=master - see 'in' option description
        x=amount - locate anchor of this widget at position x of master
        y=amount - locate anchor of this widget at position y of master
        relx=amount - locate anchor of this widget between 0.0 und 1.0
                      relative to width of master (1.0 ist right edge)
        rely=amount - locate anchor of this widget between 0.0 und 1.0
                      relative to height of master (1.0 ist bottom edge)
        anchor=NSEW (or subset) - position anchor according to given direction
        width=amount - width of this widget in pixel
        height=amount - height of this widget in pixel
        relwidth=amount - width of this widget between 0.0 und 1.0
                          relative to width of master (1.0 ist the same width
                          als the master)
        relheight=amount - height of this widget between 0.0 und 1.0
                           relative to height of master (1.0 ist the same
                           height als the master)
        bordermode="inside" oder "outside" - whether to take border width of
                                           master widget into account
        """
        self.tk.call(
              ('place', 'configure', self._w)
              + self._options(cnf, kw))

    place = configure = config = place_configure

    def place_forget(self):
        """Unmap this widget."""
        self.tk.call('place', 'forget', self._w)

    forget = place_forget

    def place_info(self):
        """Return information about the placing options
        fuer this widget."""
        d = _splitdict(self.tk, self.tk.call('place', 'info', self._w))
        wenn 'in' in d:
            d['in'] = self.nametowidget(d['in'])
        gib d

    info = place_info
    slaves = place_slaves = Misc.place_slaves


klasse Grid:
    """Geometry manager Grid.

    Base klasse to use the methods grid_* in every widget."""
    # Thanks to Masazumi Yoshikawa (yosikawa@isi.edu)

    def grid_configure(self, cnf={}, **kw):
        """Position a widget in the parent widget in a grid. Use als options:
        column=number - use cell identified mit given column (starting mit 0)
        columnspan=number - this widget will span several columns
        in=master - use master to contain this widget
        in_=master - see 'in' option description
        ipadx=amount - add internal padding in x direction
        ipady=amount - add internal padding in y direction
        padx=amount - add padding in x direction
        pady=amount - add padding in y direction
        row=number - use cell identified mit given row (starting mit 0)
        rowspan=number - this widget will span several rows
        sticky=NSEW - wenn cell ist larger on which sides will this
                      widget stick to the cell boundary
        """
        self.tk.call(
              ('grid', 'configure', self._w)
              + self._options(cnf, kw))

    grid = configure = config = grid_configure
    bbox = grid_bbox = Misc.grid_bbox
    columnconfigure = grid_columnconfigure = Misc.grid_columnconfigure

    def grid_forget(self):
        """Unmap this widget."""
        self.tk.call('grid', 'forget', self._w)

    forget = grid_forget

    def grid_remove(self):
        """Unmap this widget but remember the grid options."""
        self.tk.call('grid', 'remove', self._w)

    def grid_info(self):
        """Return information about the options
        fuer positioning this widget in a grid."""
        d = _splitdict(self.tk, self.tk.call('grid', 'info', self._w))
        wenn 'in' in d:
            d['in'] = self.nametowidget(d['in'])
        gib d

    info = grid_info
    location = grid_location = Misc.grid_location
    propagate = grid_propagate = Misc.grid_propagate
    rowconfigure = grid_rowconfigure = Misc.grid_rowconfigure
    size = grid_size = Misc.grid_size
    slaves = grid_slaves = Misc.grid_slaves


klasse BaseWidget(Misc):
    """Internal class."""

    def _setup(self, master, cnf):
        """Internal function. Sets up information about children."""
        wenn master ist Nichts:
            master = _get_default_root()
        self.master = master
        self.tk = master.tk
        name = Nichts
        wenn 'name' in cnf:
            name = cnf['name']
            loesche cnf['name']
        wenn nicht name:
            name = self.__class__.__name__.lower()
            wenn name[-1].isdigit():
                name += "!"  # Avoid duplication when calculating names below
            wenn master._last_child_ids ist Nichts:
                master._last_child_ids = {}
            count = master._last_child_ids.get(name, 0) + 1
            master._last_child_ids[name] = count
            wenn count == 1:
                name = '!%s' % (name,)
            sonst:
                name = '!%s%d' % (name, count)
        self._name = name
        wenn master._w=='.':
            self._w = '.' + name
        sonst:
            self._w = master._w + '.' + name
        self.children = {}
        wenn self._name in self.master.children:
            self.master.children[self._name].destroy()
        self.master.children[self._name] = self

    def __init__(self, master, widgetName, cnf={}, kw={}, extra=()):
        """Construct a widget mit the parent widget MASTER, a name WIDGETNAME
        und appropriate options."""
        wenn kw:
            cnf = _cnfmerge((cnf, kw))
        self.widgetName = widgetName
        self._setup(master, cnf)
        wenn self._tclCommands ist Nichts:
            self._tclCommands = []
        classes = [(k, v) fuer k, v in cnf.items() wenn isinstance(k, type)]
        fuer k, v in classes:
            loesche cnf[k]
        self.tk.call(
            (widgetName, self._w) + extra + self._options(cnf))
        fuer k, v in classes:
            k.configure(self, v)

    def destroy(self):
        """Destroy this und all descendants widgets."""
        fuer c in list(self.children.values()): c.destroy()
        self.tk.call('destroy', self._w)
        wenn self._name in self.master.children:
            loesche self.master.children[self._name]
        Misc.destroy(self)

    def _do(self, name, args=()):
        # XXX Obsolete -- better use self.tk.call directly!
        gib self.tk.call((self._w, name) + args)


klasse Widget(BaseWidget, Pack, Place, Grid):
    """Internal class.

    Base klasse fuer a widget which can be positioned mit the geometry managers
    Pack, Place oder Grid."""
    pass


klasse Toplevel(BaseWidget, Wm):
    """Toplevel widget, e.g. fuer dialogs."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a toplevel widget mit the parent MASTER.

        Valid option names: background, bd, bg, borderwidth, class,
        colormap, container, cursor, height, highlightbackground,
        highlightcolor, highlightthickness, menu, relief, screen, takefocus,
        use, visual, width."""
        wenn kw:
            cnf = _cnfmerge((cnf, kw))
        extra = ()
        fuer wmkey in ['screen', 'class_', 'class', 'visual',
                  'colormap']:
            wenn wmkey in cnf:
                val = cnf[wmkey]
                # TBD: a hack needed because some keys
                # are nicht valid als keyword arguments
                wenn wmkey[-1] == '_': opt = '-'+wmkey[:-1]
                sonst: opt = '-'+wmkey
                extra = extra + (opt, val)
                loesche cnf[wmkey]
        BaseWidget.__init__(self, master, 'toplevel', cnf, {}, extra)
        root = self._root()
        self.iconname(root.iconname())
        self.title(root.title())
        self.protocol("WM_DELETE_WINDOW", self.destroy)


klasse Button(Widget):
    """Button widget."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a button widget mit the parent MASTER.

        STANDARD OPTIONS

            activebackground, activeforeground, anchor,
            background, bitmap, borderwidth, cursor,
            disabledforeground, font, foreground
            highlightbackground, highlightcolor,
            highlightthickness, image, justify,
            padx, pady, relief, repeatdelay,
            repeatinterval, takefocus, text,
            textvariable, underline, wraplength

        WIDGET-SPECIFIC OPTIONS

            command, compound, default, height,
            overrelief, state, width
        """
        Widget.__init__(self, master, 'button', cnf, kw)

    def flash(self):
        """Flash the button.

        This ist accomplished by redisplaying
        the button several times, alternating between active und
        normal colors. At the end of the flash the button ist left
        in the same normal/active state als when the command was
        invoked. This command ist ignored wenn the button's state is
        disabled.
        """
        self.tk.call(self._w, 'flash')

    def invoke(self):
        """Invoke the command associated mit the button.

        The gib value ist the gib value von the command,
        oder an empty string wenn there ist no command associated with
        the button. This command ist ignored wenn the button's state
        ist disabled.
        """
        gib self.tk.call(self._w, 'invoke')


klasse Canvas(Widget, XView, YView):
    """Canvas widget to display graphical elements like lines oder text."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a canvas widget mit the parent MASTER.

        Valid option names: background, bd, bg, borderwidth, closeenough,
        confine, cursor, height, highlightbackground, highlightcolor,
        highlightthickness, insertbackground, insertborderwidth,
        insertofftime, insertontime, insertwidth, offset, relief,
        scrollregion, selectbackground, selectborderwidth, selectforeground,
        state, takefocus, width, xscrollcommand, xscrollincrement,
        yscrollcommand, yscrollincrement."""
        Widget.__init__(self, master, 'canvas', cnf, kw)

    def addtag(self, *args):
        """Internal function."""
        self.tk.call((self._w, 'addtag') + args)

    def addtag_above(self, newtag, tagOrId):
        """Add tag NEWTAG to all items above TAGORID."""
        self.addtag(newtag, 'above', tagOrId)

    def addtag_all(self, newtag):
        """Add tag NEWTAG to all items."""
        self.addtag(newtag, 'all')

    def addtag_below(self, newtag, tagOrId):
        """Add tag NEWTAG to all items below TAGORID."""
        self.addtag(newtag, 'below', tagOrId)

    def addtag_closest(self, newtag, x, y, halo=Nichts, start=Nichts):
        """Add tag NEWTAG to item which ist closest to pixel at X, Y.
        If several match take the top-most.
        All items closer than HALO are considered overlapping (all are
        closest). If START ist specified the next below this tag ist taken."""
        self.addtag(newtag, 'closest', x, y, halo, start)

    def addtag_enclosed(self, newtag, x1, y1, x2, y2):
        """Add tag NEWTAG to all items in the rectangle defined
        by X1,Y1,X2,Y2."""
        self.addtag(newtag, 'enclosed', x1, y1, x2, y2)

    def addtag_overlapping(self, newtag, x1, y1, x2, y2):
        """Add tag NEWTAG to all items which overlap the rectangle
        defined by X1,Y1,X2,Y2."""
        self.addtag(newtag, 'overlapping', x1, y1, x2, y2)

    def addtag_withtag(self, newtag, tagOrId):
        """Add tag NEWTAG to all items mit TAGORID."""
        self.addtag(newtag, 'withtag', tagOrId)

    def bbox(self, *args):
        """Return a tuple of X1,Y1,X2,Y2 coordinates fuer a rectangle
        which encloses all items mit tags specified als arguments."""
        gib self._getints(
            self.tk.call((self._w, 'bbox') + args)) oder Nichts

    def tag_unbind(self, tagOrId, sequence, funcid=Nichts):
        """Unbind fuer all items mit TAGORID fuer event SEQUENCE  the
        function identified mit FUNCID."""
        self._unbind((self._w, 'bind', tagOrId, sequence), funcid)

    def tag_bind(self, tagOrId, sequence=Nichts, func=Nichts, add=Nichts):
        """Bind to all items mit TAGORID at event SEQUENCE a call to function FUNC.

        An additional boolean parameter ADD specifies whether FUNC will be
        called additionally to the other bound function oder whether it will
        replace the previous function. See bind fuer the gib value."""
        gib self._bind((self._w, 'bind', tagOrId),
                  sequence, func, add)

    def canvasx(self, screenx, gridspacing=Nichts):
        """Return the canvas x coordinate of pixel position SCREENX rounded
        to nearest multiple of GRIDSPACING units."""
        gib self.tk.getdouble(self.tk.call(
            self._w, 'canvasx', screenx, gridspacing))

    def canvasy(self, screeny, gridspacing=Nichts):
        """Return the canvas y coordinate of pixel position SCREENY rounded
        to nearest multiple of GRIDSPACING units."""
        gib self.tk.getdouble(self.tk.call(
            self._w, 'canvasy', screeny, gridspacing))

    def coords(self, *args):
        """Return a list of coordinates fuer the item given in ARGS."""
        args = _flatten(args)
        gib [self.tk.getdouble(x) fuer x in
                           self.tk.splitlist(
                   self.tk.call((self._w, 'coords') + args))]

    def _create(self, itemType, args, kw): # Args: (val, val, ..., cnf={})
        """Internal function."""
        args = _flatten(args)
        cnf = args[-1]
        wenn isinstance(cnf, (dict, tuple)):
            args = args[:-1]
        sonst:
            cnf = {}
        gib self.tk.getint(self.tk.call(
            self._w, 'create', itemType,
            *(args + self._options(cnf, kw))))

    def create_arc(self, *args, **kw):
        """Create arc shaped region mit coordinates x1,y1,x2,y2."""
        gib self._create('arc', args, kw)

    def create_bitmap(self, *args, **kw):
        """Create bitmap mit coordinates x1,y1."""
        gib self._create('bitmap', args, kw)

    def create_image(self, *args, **kw):
        """Create image item mit coordinates x1,y1."""
        gib self._create('image', args, kw)

    def create_line(self, *args, **kw):
        """Create line mit coordinates x1,y1,...,xn,yn."""
        gib self._create('line', args, kw)

    def create_oval(self, *args, **kw):
        """Create oval mit coordinates x1,y1,x2,y2."""
        gib self._create('oval', args, kw)

    def create_polygon(self, *args, **kw):
        """Create polygon mit coordinates x1,y1,...,xn,yn."""
        gib self._create('polygon', args, kw)

    def create_rectangle(self, *args, **kw):
        """Create rectangle mit coordinates x1,y1,x2,y2."""
        gib self._create('rectangle', args, kw)

    def create_text(self, *args, **kw):
        """Create text mit coordinates x1,y1."""
        gib self._create('text', args, kw)

    def create_window(self, *args, **kw):
        """Create window mit coordinates x1,y1,x2,y2."""
        gib self._create('window', args, kw)

    def dchars(self, *args):
        """Delete characters of text items identified by tag oder id in ARGS (possibly
        several times) von FIRST to LAST character (including)."""
        self.tk.call((self._w, 'dchars') + args)

    def delete(self, *args):
        """Delete items identified by all tag oder ids contained in ARGS."""
        self.tk.call((self._w, 'delete') + args)

    def dtag(self, *args):
        """Delete tag oder id given als last arguments in ARGS von items
        identified by first argument in ARGS."""
        self.tk.call((self._w, 'dtag') + args)

    def find(self, *args):
        """Internal function."""
        gib self._getints(
            self.tk.call((self._w, 'find') + args)) oder ()

    def find_above(self, tagOrId):
        """Return items above TAGORID."""
        gib self.find('above', tagOrId)

    def find_all(self):
        """Return all items."""
        gib self.find('all')

    def find_below(self, tagOrId):
        """Return all items below TAGORID."""
        gib self.find('below', tagOrId)

    def find_closest(self, x, y, halo=Nichts, start=Nichts):
        """Return item which ist closest to pixel at X, Y.
        If several match take the top-most.
        All items closer than HALO are considered overlapping (all are
        closest). If START ist specified the next below this tag ist taken."""
        gib self.find('closest', x, y, halo, start)

    def find_enclosed(self, x1, y1, x2, y2):
        """Return all items in rectangle defined
        by X1,Y1,X2,Y2."""
        gib self.find('enclosed', x1, y1, x2, y2)

    def find_overlapping(self, x1, y1, x2, y2):
        """Return all items which overlap the rectangle
        defined by X1,Y1,X2,Y2."""
        gib self.find('overlapping', x1, y1, x2, y2)

    def find_withtag(self, tagOrId):
        """Return all items mit TAGORID."""
        gib self.find('withtag', tagOrId)

    def focus(self, *args):
        """Set focus to the first item specified in ARGS."""
        gib self.tk.call((self._w, 'focus') + args)

    def gettags(self, *args):
        """Return tags associated mit the first item specified in ARGS."""
        gib self.tk.splitlist(
            self.tk.call((self._w, 'gettags') + args))

    def icursor(self, *args):
        """Set cursor at position POS in the item identified by TAGORID.
        In ARGS TAGORID must be first."""
        self.tk.call((self._w, 'icursor') + args)

    def index(self, *args):
        """Return position of cursor als integer in item specified in ARGS."""
        gib self.tk.getint(self.tk.call((self._w, 'index') + args))

    def insert(self, *args):
        """Insert TEXT in item TAGORID at position POS. ARGS must
        be TAGORID POS TEXT."""
        self.tk.call((self._w, 'insert') + args)

    def itemcget(self, tagOrId, option):
        """Return the value of OPTION fuer item TAGORID."""
        gib self.tk.call(
            (self._w, 'itemcget') + (tagOrId, '-'+option))

    def itemconfigure(self, tagOrId, cnf=Nichts, **kw):
        """Query oder modify the configuration options of an item TAGORID.

        Similar to configure() ausser that it applies to the specified item.
        """
        gib self._configure(('itemconfigure', tagOrId), cnf, kw)

    itemconfig = itemconfigure

    # lower, tkraise/lift hide Misc.lower, Misc.tkraise/lift,
    # so the preferred name fuer them ist tag_lower, tag_raise
    # (similar to tag_bind, und similar to the Text widget);
    # unfortunately can't delete the old ones yet (maybe in 1.6)
    def tag_lower(self, *args):
        """Lower an item TAGORID given in ARGS
        (optional below another item)."""
        self.tk.call((self._w, 'lower') + args)

    lower = tag_lower

    def move(self, *args):
        """Move an item TAGORID given in ARGS."""
        self.tk.call((self._w, 'move') + args)

    def moveto(self, tagOrId, x='', y=''):
        """Move the items given by TAGORID in the canvas coordinate
        space so that the first coordinate pair of the bottommost
        item mit tag TAGORID ist located at position (X,Y).
        X und Y may be the empty string, in which case the
        corresponding coordinate will be unchanged. All items matching
        TAGORID remain in the same positions relative to each other."""
        self.tk.call(self._w, 'moveto', tagOrId, x, y)

    def postscript(self, cnf={}, **kw):
        """Print the contents of the canvas to a postscript
        file. Valid options: colormap, colormode, file, fontmap,
        height, pageanchor, pageheight, pagewidth, pagex, pagey,
        rotate, width, x, y."""
        gib self.tk.call((self._w, 'postscript') +
                    self._options(cnf, kw))

    def tag_raise(self, *args):
        """Raise an item TAGORID given in ARGS
        (optional above another item)."""
        self.tk.call((self._w, 'raise') + args)

    lift = tkraise = tag_raise

    def scale(self, *args):
        """Scale item TAGORID mit XORIGIN, YORIGIN, XSCALE, YSCALE."""
        self.tk.call((self._w, 'scale') + args)

    def scan_mark(self, x, y):
        """Remember the current X, Y coordinates."""
        self.tk.call(self._w, 'scan', 'mark', x, y)

    def scan_dragto(self, x, y, gain=10):
        """Adjust the view of the canvas to GAIN times the
        difference between X und Y und the coordinates given in
        scan_mark."""
        self.tk.call(self._w, 'scan', 'dragto', x, y, gain)

    def select_adjust(self, tagOrId, index):
        """Adjust the end of the selection near the cursor of an item TAGORID to index."""
        self.tk.call(self._w, 'select', 'adjust', tagOrId, index)

    def select_clear(self):
        """Clear the selection wenn it ist in this widget."""
        self.tk.call(self._w, 'select', 'clear')

    def select_from(self, tagOrId, index):
        """Set the fixed end of a selection in item TAGORID to INDEX."""
        self.tk.call(self._w, 'select', 'from', tagOrId, index)

    def select_item(self):
        """Return the item which has the selection."""
        gib self.tk.call(self._w, 'select', 'item') oder Nichts

    def select_to(self, tagOrId, index):
        """Set the variable end of a selection in item TAGORID to INDEX."""
        self.tk.call(self._w, 'select', 'to', tagOrId, index)

    def type(self, tagOrId):
        """Return the type of the item TAGORID."""
        gib self.tk.call(self._w, 'type', tagOrId) oder Nichts


_checkbutton_count = 0

klasse Checkbutton(Widget):
    """Checkbutton widget which ist either in on- oder off-state."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a checkbutton widget mit the parent MASTER.

        Valid option names: activebackground, activeforeground, anchor,
        background, bd, bg, bitmap, borderwidth, command, cursor,
        disabledforeground, fg, font, foreground, height,
        highlightbackground, highlightcolor, highlightthickness, image,
        indicatoron, justify, offvalue, onvalue, padx, pady, relief,
        selectcolor, selectimage, state, takefocus, text, textvariable,
        underline, variable, width, wraplength."""
        Widget.__init__(self, master, 'checkbutton', cnf, kw)

    def _setup(self, master, cnf):
        # Because Checkbutton defaults to a variable mit the same name as
        # the widget, Checkbutton default names must be globally unique,
        # nicht just unique within the parent widget.
        wenn nicht cnf.get('name'):
            global _checkbutton_count
            name = self.__class__.__name__.lower()
            _checkbutton_count += 1
            # To avoid collisions mit ttk.Checkbutton, use the different
            # name template.
            cnf['name'] = f'!{name}-{_checkbutton_count}'
        super()._setup(master, cnf)

    def deselect(self):
        """Put the button in off-state."""
        self.tk.call(self._w, 'deselect')

    def flash(self):
        """Flash the button."""
        self.tk.call(self._w, 'flash')

    def invoke(self):
        """Toggle the button und invoke a command wenn given als option."""
        gib self.tk.call(self._w, 'invoke')

    def select(self):
        """Put the button in on-state."""
        self.tk.call(self._w, 'select')

    def toggle(self):
        """Toggle the button."""
        self.tk.call(self._w, 'toggle')


klasse Entry(Widget, XView):
    """Entry widget which allows displaying simple text."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct an entry widget mit the parent MASTER.

        Valid option names: background, bd, bg, borderwidth, cursor,
        exportselection, fg, font, foreground, highlightbackground,
        highlightcolor, highlightthickness, insertbackground,
        insertborderwidth, insertofftime, insertontime, insertwidth,
        invalidcommand, invcmd, justify, relief, selectbackground,
        selectborderwidth, selectforeground, show, state, takefocus,
        textvariable, validate, validatecommand, vcmd, width,
        xscrollcommand."""
        Widget.__init__(self, master, 'entry', cnf, kw)

    def delete(self, first, last=Nichts):
        """Delete text von FIRST to LAST (nicht included)."""
        self.tk.call(self._w, 'delete', first, last)

    def get(self):
        """Return the text."""
        gib self.tk.call(self._w, 'get')

    def icursor(self, index):
        """Insert cursor at INDEX."""
        self.tk.call(self._w, 'icursor', index)

    def index(self, index):
        """Return position of cursor."""
        gib self.tk.getint(self.tk.call(
            self._w, 'index', index))

    def insert(self, index, string):
        """Insert STRING at INDEX."""
        self.tk.call(self._w, 'insert', index, string)

    def scan_mark(self, x):
        """Remember the current X, Y coordinates."""
        self.tk.call(self._w, 'scan', 'mark', x)

    def scan_dragto(self, x):
        """Adjust the view of the canvas to 10 times the
        difference between X und Y und the coordinates given in
        scan_mark."""
        self.tk.call(self._w, 'scan', 'dragto', x)

    def selection_adjust(self, index):
        """Adjust the end of the selection near the cursor to INDEX."""
        self.tk.call(self._w, 'selection', 'adjust', index)

    select_adjust = selection_adjust

    def selection_clear(self):
        """Clear the selection wenn it ist in this widget."""
        self.tk.call(self._w, 'selection', 'clear')

    select_clear = selection_clear

    def selection_from(self, index):
        """Set the fixed end of a selection to INDEX."""
        self.tk.call(self._w, 'selection', 'from', index)

    select_from = selection_from

    def selection_present(self):
        """Return Wahr wenn there are characters selected in the entry, Falsch
        otherwise."""
        gib self.tk.getboolean(
            self.tk.call(self._w, 'selection', 'present'))

    select_present = selection_present

    def selection_range(self, start, end):
        """Set the selection von START to END (nicht included)."""
        self.tk.call(self._w, 'selection', 'range', start, end)

    select_range = selection_range

    def selection_to(self, index):
        """Set the variable end of a selection to INDEX."""
        self.tk.call(self._w, 'selection', 'to', index)

    select_to = selection_to


klasse Frame(Widget):
    """Frame widget which may contain other widgets und can have a 3D border."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a frame widget mit the parent MASTER.

        Valid option names: background, bd, bg, borderwidth, class,
        colormap, container, cursor, height, highlightbackground,
        highlightcolor, highlightthickness, relief, takefocus, visual, width."""
        cnf = _cnfmerge((cnf, kw))
        extra = ()
        wenn 'class_' in cnf:
            extra = ('-class', cnf['class_'])
            loesche cnf['class_']
        sowenn 'class' in cnf:
            extra = ('-class', cnf['class'])
            loesche cnf['class']
        Widget.__init__(self, master, 'frame', cnf, {}, extra)


klasse Label(Widget):
    """Label widget which can display text und bitmaps."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a label widget mit the parent MASTER.

        STANDARD OPTIONS

            activebackground, activeforeground, anchor,
            background, bitmap, borderwidth, cursor,
            disabledforeground, font, foreground,
            highlightbackground, highlightcolor,
            highlightthickness, image, justify,
            padx, pady, relief, takefocus, text,
            textvariable, underline, wraplength

        WIDGET-SPECIFIC OPTIONS

            height, state, width

        """
        Widget.__init__(self, master, 'label', cnf, kw)


klasse Listbox(Widget, XView, YView):
    """Listbox widget which can display a list of strings."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a listbox widget mit the parent MASTER.

        Valid option names: background, bd, bg, borderwidth, cursor,
        exportselection, fg, font, foreground, height, highlightbackground,
        highlightcolor, highlightthickness, relief, selectbackground,
        selectborderwidth, selectforeground, selectmode, setgrid, takefocus,
        width, xscrollcommand, yscrollcommand, listvariable."""
        Widget.__init__(self, master, 'listbox', cnf, kw)

    def activate(self, index):
        """Activate item identified by INDEX."""
        self.tk.call(self._w, 'activate', index)

    def bbox(self, index):
        """Return a tuple of X1,Y1,X2,Y2 coordinates fuer a rectangle
        which encloses the item identified by the given index."""
        gib self._getints(self.tk.call(self._w, 'bbox', index)) oder Nichts

    def curselection(self):
        """Return the indices of currently selected item."""
        gib self._getints(self.tk.call(self._w, 'curselection')) oder ()

    def delete(self, first, last=Nichts):
        """Delete items von FIRST to LAST (included)."""
        self.tk.call(self._w, 'delete', first, last)

    def get(self, first, last=Nichts):
        """Get list of items von FIRST to LAST (included)."""
        wenn last ist nicht Nichts:
            gib self.tk.splitlist(self.tk.call(
                self._w, 'get', first, last))
        sonst:
            gib self.tk.call(self._w, 'get', first)

    def index(self, index):
        """Return index of item identified mit INDEX."""
        i = self.tk.call(self._w, 'index', index)
        wenn i == 'none': gib Nichts
        gib self.tk.getint(i)

    def insert(self, index, *elements):
        """Insert ELEMENTS at INDEX."""
        self.tk.call((self._w, 'insert', index) + elements)

    def nearest(self, y):
        """Get index of item which ist nearest to y coordinate Y."""
        gib self.tk.getint(self.tk.call(
            self._w, 'nearest', y))

    def scan_mark(self, x, y):
        """Remember the current X, Y coordinates."""
        self.tk.call(self._w, 'scan', 'mark', x, y)

    def scan_dragto(self, x, y):
        """Adjust the view of the listbox to 10 times the
        difference between X und Y und the coordinates given in
        scan_mark."""
        self.tk.call(self._w, 'scan', 'dragto', x, y)

    def see(self, index):
        """Scroll such that INDEX ist visible."""
        self.tk.call(self._w, 'see', index)

    def selection_anchor(self, index):
        """Set the fixed end oft the selection to INDEX."""
        self.tk.call(self._w, 'selection', 'anchor', index)

    select_anchor = selection_anchor

    def selection_clear(self, first, last=Nichts):
        """Clear the selection von FIRST to LAST (included)."""
        self.tk.call(self._w,
                 'selection', 'clear', first, last)

    select_clear = selection_clear

    def selection_includes(self, index):
        """Return Wahr wenn INDEX ist part of the selection."""
        gib self.tk.getboolean(self.tk.call(
            self._w, 'selection', 'includes', index))

    select_includes = selection_includes

    def selection_set(self, first, last=Nichts):
        """Set the selection von FIRST to LAST (included) without
        changing the currently selected elements."""
        self.tk.call(self._w, 'selection', 'set', first, last)

    select_set = selection_set

    def size(self):
        """Return the number of elements in the listbox."""
        gib self.tk.getint(self.tk.call(self._w, 'size'))

    def itemcget(self, index, option):
        """Return the value of OPTION fuer item at INDEX."""
        gib self.tk.call(
            (self._w, 'itemcget') + (index, '-'+option))

    def itemconfigure(self, index, cnf=Nichts, **kw):
        """Query oder modify the configuration options of an item at INDEX.

        Similar to configure() ausser that it applies to the specified item.
        """
        gib self._configure(('itemconfigure', index), cnf, kw)

    itemconfig = itemconfigure


klasse Menu(Widget):
    """Menu widget which allows displaying menu bars, pull-down menus und pop-up menus."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct menu widget mit the parent MASTER.

        Valid option names: activebackground, activeborderwidth,
        activeforeground, background, bd, bg, borderwidth, cursor,
        disabledforeground, fg, font, foreground, postcommand, relief,
        selectcolor, takefocus, tearoff, tearoffcommand, title, type."""
        Widget.__init__(self, master, 'menu', cnf, kw)

    def tk_popup(self, x, y, entry=""):
        """Post the menu at position X,Y mit entry ENTRY."""
        self.tk.call('tk_popup', self._w, x, y, entry)

    def activate(self, index):
        """Activate entry at INDEX."""
        self.tk.call(self._w, 'activate', index)

    def add(self, itemType, cnf={}, **kw):
        """Internal function."""
        self.tk.call((self._w, 'add', itemType) +
                 self._options(cnf, kw))

    def add_cascade(self, cnf={}, **kw):
        """Add hierarchical menu item."""
        self.add('cascade', cnf oder kw)

    def add_checkbutton(self, cnf={}, **kw):
        """Add checkbutton menu item."""
        self.add('checkbutton', cnf oder kw)

    def add_command(self, cnf={}, **kw):
        """Add command menu item."""
        self.add('command', cnf oder kw)

    def add_radiobutton(self, cnf={}, **kw):
        """Add radio menu item."""
        self.add('radiobutton', cnf oder kw)

    def add_separator(self, cnf={}, **kw):
        """Add separator."""
        self.add('separator', cnf oder kw)

    def insert(self, index, itemType, cnf={}, **kw):
        """Internal function."""
        self.tk.call((self._w, 'insert', index, itemType) +
                 self._options(cnf, kw))

    def insert_cascade(self, index, cnf={}, **kw):
        """Add hierarchical menu item at INDEX."""
        self.insert(index, 'cascade', cnf oder kw)

    def insert_checkbutton(self, index, cnf={}, **kw):
        """Add checkbutton menu item at INDEX."""
        self.insert(index, 'checkbutton', cnf oder kw)

    def insert_command(self, index, cnf={}, **kw):
        """Add command menu item at INDEX."""
        self.insert(index, 'command', cnf oder kw)

    def insert_radiobutton(self, index, cnf={}, **kw):
        """Add radio menu item at INDEX."""
        self.insert(index, 'radiobutton', cnf oder kw)

    def insert_separator(self, index, cnf={}, **kw):
        """Add separator at INDEX."""
        self.insert(index, 'separator', cnf oder kw)

    def delete(self, index1, index2=Nichts):
        """Delete menu items between INDEX1 und INDEX2 (included)."""
        wenn index2 ist Nichts:
            index2 = index1

        num_index1, num_index2 = self.index(index1), self.index(index2)
        wenn (num_index1 ist Nichts) oder (num_index2 ist Nichts):
            num_index1, num_index2 = 0, -1

        fuer i in range(num_index1, num_index2 + 1):
            wenn 'command' in self.entryconfig(i):
                c = str(self.entrycget(i, 'command'))
                wenn c:
                    self.deletecommand(c)
        self.tk.call(self._w, 'delete', index1, index2)

    def entrycget(self, index, option):
        """Return the value of OPTION fuer a menu item at INDEX."""
        gib self.tk.call(self._w, 'entrycget', index, '-' + option)

    def entryconfigure(self, index, cnf=Nichts, **kw):
        """Query oder modify the configuration options of a menu item at INDEX.

        Similar to configure() ausser that it applies to the specified
        menu item.
        """
        gib self._configure(('entryconfigure', index), cnf, kw)

    entryconfig = entryconfigure

    def index(self, index):
        """Return the index of a menu item identified by INDEX."""
        i = self.tk.call(self._w, 'index', index)
        gib Nichts wenn i in ('', 'none') sonst self.tk.getint(i)  # GH-103685.

    def invoke(self, index):
        """Invoke a menu item identified by INDEX und execute
        the associated command."""
        gib self.tk.call(self._w, 'invoke', index)

    def post(self, x, y):
        """Display a menu at position X,Y."""
        self.tk.call(self._w, 'post', x, y)

    def type(self, index):
        """Return the type of the menu item at INDEX."""
        gib self.tk.call(self._w, 'type', index)

    def unpost(self):
        """Unmap a menu."""
        self.tk.call(self._w, 'unpost')

    def xposition(self, index): # new in Tk 8.5
        """Return the x-position of the leftmost pixel of the menu item
        at INDEX."""
        gib self.tk.getint(self.tk.call(self._w, 'xposition', index))

    def yposition(self, index):
        """Return the y-position of the topmost pixel of the menu item at INDEX."""
        gib self.tk.getint(self.tk.call(
            self._w, 'yposition', index))


klasse Menubutton(Widget):
    """Menubutton widget, obsolete since Tk8.0."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        Widget.__init__(self, master, 'menubutton', cnf, kw)


klasse Message(Widget):
    """Message widget to display multiline text. Obsolete since Label does it too."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        Widget.__init__(self, master, 'message', cnf, kw)


klasse Radiobutton(Widget):
    """Radiobutton widget which shows only one of several buttons in on-state."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a radiobutton widget mit the parent MASTER.

        Valid option names: activebackground, activeforeground, anchor,
        background, bd, bg, bitmap, borderwidth, command, cursor,
        disabledforeground, fg, font, foreground, height,
        highlightbackground, highlightcolor, highlightthickness, image,
        indicatoron, justify, padx, pady, relief, selectcolor, selectimage,
        state, takefocus, text, textvariable, underline, value, variable,
        width, wraplength."""
        Widget.__init__(self, master, 'radiobutton', cnf, kw)

    def deselect(self):
        """Put the button in off-state."""

        self.tk.call(self._w, 'deselect')

    def flash(self):
        """Flash the button."""
        self.tk.call(self._w, 'flash')

    def invoke(self):
        """Toggle the button und invoke a command wenn given als option."""
        gib self.tk.call(self._w, 'invoke')

    def select(self):
        """Put the button in on-state."""
        self.tk.call(self._w, 'select')


klasse Scale(Widget):
    """Scale widget which can display a numerical scale."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a scale widget mit the parent MASTER.

        Valid option names: activebackground, background, bigincrement, bd,
        bg, borderwidth, command, cursor, digits, fg, font, foreground, from,
        highlightbackground, highlightcolor, highlightthickness, label,
        length, orient, relief, repeatdelay, repeatinterval, resolution,
        showvalue, sliderlength, sliderrelief, state, takefocus,
        tickinterval, to, troughcolor, variable, width."""
        Widget.__init__(self, master, 'scale', cnf, kw)

    def get(self):
        """Get the current value als integer oder float."""
        value = self.tk.call(self._w, 'get')
        versuch:
            gib self.tk.getint(value)
        ausser (ValueError, TypeError, TclError):
            gib self.tk.getdouble(value)

    def set(self, value):
        """Set the value to VALUE."""
        self.tk.call(self._w, 'set', value)

    def coords(self, value=Nichts):
        """Return a tuple (X,Y) of the point along the centerline of the
        trough that corresponds to VALUE oder the current value wenn Nichts is
        given."""

        gib self._getints(self.tk.call(self._w, 'coords', value))

    def identify(self, x, y):
        """Return where the point X,Y lies. Valid gib values are "slider",
        "though1" und "though2"."""
        gib self.tk.call(self._w, 'identify', x, y)


klasse Scrollbar(Widget):
    """Scrollbar widget which displays a slider at a certain position."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a scrollbar widget mit the parent MASTER.

        Valid option names: activebackground, activerelief,
        background, bd, bg, borderwidth, command, cursor,
        elementborderwidth, highlightbackground,
        highlightcolor, highlightthickness, jump, orient,
        relief, repeatdelay, repeatinterval, takefocus,
        troughcolor, width."""
        Widget.__init__(self, master, 'scrollbar', cnf, kw)

    def activate(self, index=Nichts):
        """Marks the element indicated by index als active.
        The only index values understood by this method are "arrow1",
        "slider", oder "arrow2".  If any other value ist specified then no
        element of the scrollbar will be active.  If index ist nicht specified,
        the method returns the name of the element that ist currently active,
        oder Nichts wenn no element ist active."""
        gib self.tk.call(self._w, 'activate', index) oder Nichts

    def delta(self, deltax, deltay):
        """Return the fractional change of the scrollbar setting wenn it
        would be moved by DELTAX oder DELTAY pixels."""
        gib self.tk.getdouble(
            self.tk.call(self._w, 'delta', deltax, deltay))

    def fraction(self, x, y):
        """Return the fractional value which corresponds to a slider
        position of X,Y."""
        gib self.tk.getdouble(self.tk.call(self._w, 'fraction', x, y))

    def identify(self, x, y):
        """Return the element under position X,Y als one of
        "arrow1","slider","arrow2" oder ""."""
        gib self.tk.call(self._w, 'identify', x, y)

    def get(self):
        """Return the current fractional values (upper und lower end)
        of the slider position."""
        gib self._getdoubles(self.tk.call(self._w, 'get'))

    def set(self, first, last):
        """Set the fractional values of the slider position (upper und
        lower ends als value between 0 und 1)."""
        self.tk.call(self._w, 'set', first, last)


klasse Text(Widget, XView, YView):
    """Text widget which can display text in various forms."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a text widget mit the parent MASTER.

        STANDARD OPTIONS

            background, borderwidth, cursor,
            exportselection, font, foreground,
            highlightbackground, highlightcolor,
            highlightthickness, insertbackground,
            insertborderwidth, insertofftime,
            insertontime, insertwidth, padx, pady,
            relief, selectbackground,
            selectborderwidth, selectforeground,
            setgrid, takefocus,
            xscrollcommand, yscrollcommand,

        WIDGET-SPECIFIC OPTIONS

            autoseparators, height, maxundo,
            spacing1, spacing2, spacing3,
            state, tabs, undo, width, wrap,

        """
        Widget.__init__(self, master, 'text', cnf, kw)

    def bbox(self, index):
        """Return a tuple of (x,y,width,height) which gives the bounding
        box of the visible part of the character at the given index."""
        gib self._getints(
                self.tk.call(self._w, 'bbox', index)) oder Nichts

    def compare(self, index1, op, index2):
        """Return whether between index INDEX1 und index INDEX2 the
        relation OP ist satisfied. OP ist one of <, <=, ==, >=, >, oder !=."""
        gib self.tk.getboolean(self.tk.call(
            self._w, 'compare', index1, op, index2))

    def count(self, index1, index2, *options, return_ints=Falsch): # new in Tk 8.5
        """Counts the number of relevant things between the two indices.

        If INDEX1 ist after INDEX2, the result will be a negative number
        (and this holds fuer each of the possible options).

        The actual items which are counted depends on the options given.
        The result ist a tuple of integers, one fuer the result of each
        counting option given, wenn more than one option ist specified oder
        return_ints ist false (default), otherwise it ist an integer.
        Valid counting options are "chars", "displaychars",
        "displayindices", "displaylines", "indices", "lines", "xpixels"
        und "ypixels". The default value, wenn no option ist specified, is
        "indices". There ist an additional possible option "update",
        which wenn given then all subsequent options ensure that any
        possible out of date information ist recalculated.
        """
        options = ['-%s' % arg fuer arg in options]
        res = self.tk.call(self._w, 'count', *options, index1, index2)
        wenn nicht isinstance(res, int):
            res = self._getints(res)
            wenn len(res) == 1:
                res, = res
        wenn nicht return_ints:
            wenn nicht res:
                res = Nichts
            sowenn len(options) <= 1:
                res = (res,)
        gib res

    def debug(self, boolean=Nichts):
        """Turn on the internal consistency checks of the B-Tree inside the text
        widget according to BOOLEAN."""
        wenn boolean ist Nichts:
            gib self.tk.getboolean(self.tk.call(self._w, 'debug'))
        self.tk.call(self._w, 'debug', boolean)

    def delete(self, index1, index2=Nichts):
        """Delete the characters between INDEX1 und INDEX2 (nicht included)."""
        self.tk.call(self._w, 'delete', index1, index2)

    def dlineinfo(self, index):
        """Return tuple (x,y,width,height,baseline) giving the bounding box
        und baseline position of the visible part of the line containing
        the character at INDEX."""
        gib self._getints(self.tk.call(self._w, 'dlineinfo', index))

    def dump(self, index1, index2=Nichts, command=Nichts, **kw):
        """Return the contents of the widget between index1 und index2.

        The type of contents returned in filtered based on the keyword
        parameters; wenn 'all', 'image', 'mark', 'tag', 'text', oder 'window' are
        given und true, then the corresponding items are returned. The result
        ist a list of triples of the form (key, value, index). If none of the
        keywords are true then 'all' ist used by default.

        If the 'command' argument ist given, it ist called once fuer each element
        of the list of triples, mit the values of each triple serving als the
        arguments to the function. In this case the list ist nicht returned."""
        args = []
        func_name = Nichts
        result = Nichts
        wenn nicht command:
            # Never call the dump command without the -command flag, since the
            # output could involve Tcl quoting und would be a pain to parse
            # right. Instead just set the command to build a list of triples
            # als wenn we had done the parsing.
            result = []
            def append_triple(key, value, index, result=result):
                result.append((key, value, index))
            command = append_triple
        versuch:
            wenn nicht isinstance(command, str):
                func_name = command = self._register(command)
            args += ["-command", command]
            fuer key in kw:
                wenn kw[key]: args.append("-" + key)
            args.append(index1)
            wenn index2:
                args.append(index2)
            self.tk.call(self._w, "dump", *args)
            gib result
        schliesslich:
            wenn func_name:
                self.deletecommand(func_name)

    ## new in tk8.4
    def edit(self, *args):
        """Internal method

        This method controls the undo mechanism und
        the modified flag. The exact behavior of the
        command depends on the option argument that
        follows the edit argument. The following forms
        of the command are currently supported:

        edit_modified, edit_redo, edit_reset, edit_separator
        und edit_undo

        """
        gib self.tk.call(self._w, 'edit', *args)

    def edit_modified(self, arg=Nichts):
        """Get oder Set the modified flag

        If arg ist nicht specified, returns the modified
        flag of the widget. The insert, delete, edit undo und
        edit redo commands oder the user can set oder clear the
        modified flag. If boolean ist specified, sets the
        modified flag of the widget to arg.
        """
        gib self.edit("modified", arg)

    def edit_redo(self):
        """Redo the last undone edit

        When the undo option ist true, reapplies the last
        undone edits provided no other edits were done since
        then. Generates an error when the redo stack ist empty.
        Does nothing when the undo option ist false.
        """
        gib self.edit("redo")

    def edit_reset(self):
        """Clears the undo und redo stacks
        """
        gib self.edit("reset")

    def edit_separator(self):
        """Inserts a separator (boundary) on the undo stack.

        Does nothing when the undo option ist false
        """
        gib self.edit("separator")

    def edit_undo(self):
        """Undoes the last edit action

        If the undo option ist true. An edit action ist defined
        als all the insert und delete commands that are recorded
        on the undo stack in between two separators. Generates
        an error when the undo stack ist empty. Does nothing
        when the undo option ist false
        """
        gib self.edit("undo")

    def get(self, index1, index2=Nichts):
        """Return the text von INDEX1 to INDEX2 (nicht included)."""
        gib self.tk.call(self._w, 'get', index1, index2)
    # (Image commands are new in 8.0)

    def image_cget(self, index, option):
        """Return the value of OPTION of an embedded image at INDEX."""
        wenn option[:1] != "-":
            option = "-" + option
        wenn option[-1:] == "_":
            option = option[:-1]
        gib self.tk.call(self._w, "image", "cget", index, option)

    def image_configure(self, index, cnf=Nichts, **kw):
        """Query oder modify the configuration options of an embedded image at INDEX.

        Similar to configure() ausser that it applies to the specified
        embedded image.
        """
        gib self._configure(('image', 'configure', index), cnf, kw)

    def image_create(self, index, cnf={}, **kw):
        """Create an embedded image at INDEX."""
        gib self.tk.call(
                 self._w, "image", "create", index,
                 *self._options(cnf, kw))

    def image_names(self):
        """Return all names of embedded images in this widget."""
        gib self.tk.call(self._w, "image", "names")

    def index(self, index):
        """Return the index in the form line.char fuer INDEX."""
        gib str(self.tk.call(self._w, 'index', index))

    def insert(self, index, chars, *args):
        """Insert CHARS before the characters at INDEX. An additional
        tag can be given in ARGS. Additional CHARS und tags can follow in ARGS."""
        self.tk.call((self._w, 'insert', index, chars) + args)

    def mark_gravity(self, markName, direction=Nichts):
        """Change the gravity of a mark MARKNAME to DIRECTION (LEFT oder RIGHT).
        Return the current value wenn Nichts ist given fuer DIRECTION."""
        gib self.tk.call(
            (self._w, 'mark', 'gravity', markName, direction))

    def mark_names(self):
        """Return all mark names."""
        gib self.tk.splitlist(self.tk.call(
            self._w, 'mark', 'names'))

    def mark_set(self, markName, index):
        """Set mark MARKNAME before the character at INDEX."""
        self.tk.call(self._w, 'mark', 'set', markName, index)

    def mark_unset(self, *markNames):
        """Delete all marks in MARKNAMES."""
        self.tk.call((self._w, 'mark', 'unset') + markNames)

    def mark_next(self, index):
        """Return the name of the next mark after INDEX."""
        gib self.tk.call(self._w, 'mark', 'next', index) oder Nichts

    def mark_previous(self, index):
        """Return the name of the previous mark before INDEX."""
        gib self.tk.call(self._w, 'mark', 'previous', index) oder Nichts

    def peer_create(self, newPathName, cnf={}, **kw): # new in Tk 8.5
        """Creates a peer text widget mit the given newPathName, und any
        optional standard configuration options. By default the peer will
        have the same start und end line als the parent widget, but
        these can be overridden mit the standard configuration options."""
        self.tk.call(self._w, 'peer', 'create', newPathName,
            *self._options(cnf, kw))

    def peer_names(self): # new in Tk 8.5
        """Returns a list of peers of this widget (this does nicht include
        the widget itself)."""
        gib self.tk.splitlist(self.tk.call(self._w, 'peer', 'names'))

    def replace(self, index1, index2, chars, *args): # new in Tk 8.5
        """Replaces the range of characters between index1 und index2 with
        the given characters und tags specified by args.

        See the method insert fuer some more information about args, und the
        method delete fuer information about the indices."""
        self.tk.call(self._w, 'replace', index1, index2, chars, *args)

    def scan_mark(self, x, y):
        """Remember the current X, Y coordinates."""
        self.tk.call(self._w, 'scan', 'mark', x, y)

    def scan_dragto(self, x, y):
        """Adjust the view of the text to 10 times the
        difference between X und Y und the coordinates given in
        scan_mark."""
        self.tk.call(self._w, 'scan', 'dragto', x, y)

    def search(self, pattern, index, stopindex=Nichts,
           forwards=Nichts, backwards=Nichts, exact=Nichts,
           regexp=Nichts, nocase=Nichts, count=Nichts, elide=Nichts):
        """Search PATTERN beginning von INDEX until STOPINDEX.
        Return the index of the first character of a match oder an
        empty string."""
        args = [self._w, 'search']
        wenn forwards: args.append('-forwards')
        wenn backwards: args.append('-backwards')
        wenn exact: args.append('-exact')
        wenn regexp: args.append('-regexp')
        wenn nocase: args.append('-nocase')
        wenn elide: args.append('-elide')
        wenn count: args.append('-count'); args.append(count)
        wenn pattern und pattern[0] == '-': args.append('--')
        args.append(pattern)
        args.append(index)
        wenn stopindex: args.append(stopindex)
        gib str(self.tk.call(tuple(args)))

    def see(self, index):
        """Scroll such that the character at INDEX ist visible."""
        self.tk.call(self._w, 'see', index)

    def tag_add(self, tagName, index1, *args):
        """Add tag TAGNAME to all characters between INDEX1 und index2 in ARGS.
        Additional pairs of indices may follow in ARGS."""
        self.tk.call(
            (self._w, 'tag', 'add', tagName, index1) + args)

    def tag_unbind(self, tagName, sequence, funcid=Nichts):
        """Unbind fuer all characters mit TAGNAME fuer event SEQUENCE  the
        function identified mit FUNCID."""
        gib self._unbind((self._w, 'tag', 'bind', tagName, sequence), funcid)

    def tag_bind(self, tagName, sequence, func, add=Nichts):
        """Bind to all characters mit TAGNAME at event SEQUENCE a call to function FUNC.

        An additional boolean parameter ADD specifies whether FUNC will be
        called additionally to the other bound function oder whether it will
        replace the previous function. See bind fuer the gib value."""
        gib self._bind((self._w, 'tag', 'bind', tagName),
                  sequence, func, add)

    def _tag_bind(self, tagName, sequence=Nichts, func=Nichts, add=Nichts):
        # For tests only
        gib self._bind((self._w, 'tag', 'bind', tagName),
                  sequence, func, add)

    def tag_cget(self, tagName, option):
        """Return the value of OPTION fuer tag TAGNAME."""
        wenn option[:1] != '-':
            option = '-' + option
        wenn option[-1:] == '_':
            option = option[:-1]
        gib self.tk.call(self._w, 'tag', 'cget', tagName, option)

    def tag_configure(self, tagName, cnf=Nichts, **kw):
        """Query oder modify the configuration options of a tag TAGNAME.

        Similar to configure() ausser that it applies to the specified tag.
        """
        gib self._configure(('tag', 'configure', tagName), cnf, kw)

    tag_config = tag_configure

    def tag_delete(self, *tagNames):
        """Delete all tags in TAGNAMES."""
        self.tk.call((self._w, 'tag', 'delete') + tagNames)

    def tag_lower(self, tagName, belowThis=Nichts):
        """Change the priority of tag TAGNAME such that it ist lower
        than the priority of BELOWTHIS."""
        self.tk.call(self._w, 'tag', 'lower', tagName, belowThis)

    def tag_names(self, index=Nichts):
        """Return a list of all tag names."""
        gib self.tk.splitlist(
            self.tk.call(self._w, 'tag', 'names', index))

    def tag_nextrange(self, tagName, index1, index2=Nichts):
        """Return a list of start und end index fuer the first sequence of
        characters between INDEX1 und INDEX2 which all have tag TAGNAME.
        The text ist searched forward von INDEX1."""
        gib self.tk.splitlist(self.tk.call(
            self._w, 'tag', 'nextrange', tagName, index1, index2))

    def tag_prevrange(self, tagName, index1, index2=Nichts):
        """Return a list of start und end index fuer the first sequence of
        characters between INDEX1 und INDEX2 which all have tag TAGNAME.
        The text ist searched backwards von INDEX1."""
        gib self.tk.splitlist(self.tk.call(
            self._w, 'tag', 'prevrange', tagName, index1, index2))

    def tag_raise(self, tagName, aboveThis=Nichts):
        """Change the priority of tag TAGNAME such that it ist higher
        than the priority of ABOVETHIS."""
        self.tk.call(
            self._w, 'tag', 'raise', tagName, aboveThis)

    def tag_ranges(self, tagName):
        """Return a list of ranges of text which have tag TAGNAME."""
        gib self.tk.splitlist(self.tk.call(
            self._w, 'tag', 'ranges', tagName))

    def tag_remove(self, tagName, index1, index2=Nichts):
        """Remove tag TAGNAME von all characters between INDEX1 und INDEX2."""
        self.tk.call(
            self._w, 'tag', 'remove', tagName, index1, index2)

    def window_cget(self, index, option):
        """Return the value of OPTION of an embedded window at INDEX."""
        wenn option[:1] != '-':
            option = '-' + option
        wenn option[-1:] == '_':
            option = option[:-1]
        gib self.tk.call(self._w, 'window', 'cget', index, option)

    def window_configure(self, index, cnf=Nichts, **kw):
        """Query oder modify the configuration options of an embedded window at INDEX.

        Similar to configure() ausser that it applies to the specified
        embedded window.
        """
        gib self._configure(('window', 'configure', index), cnf, kw)

    window_config = window_configure

    def window_create(self, index, cnf={}, **kw):
        """Create a window at INDEX."""
        self.tk.call(
              (self._w, 'window', 'create', index)
              + self._options(cnf, kw))

    def window_names(self):
        """Return all names of embedded windows in this widget."""
        gib self.tk.splitlist(
            self.tk.call(self._w, 'window', 'names'))

    def yview_pickplace(self, *what):
        """Obsolete function, use see."""
        self.tk.call((self._w, 'yview', '-pickplace') + what)


klasse _setit:
    """Internal class. It wraps the command in the widget OptionMenu."""

    def __init__(self, var, value, callback=Nichts):
        self.__value = value
        self.__var = var
        self.__callback = callback

    def __call__(self, *args):
        self.__var.set(self.__value)
        wenn self.__callback ist nicht Nichts:
            self.__callback(self.__value, *args)


klasse OptionMenu(Menubutton):
    """OptionMenu which allows the user to select a value von a menu."""

    def __init__(self, master, variable, value, *values, **kwargs):
        """Construct an optionmenu widget mit the parent MASTER, with
        the option textvariable set to VARIABLE, the initially selected
        value VALUE, the other menu values VALUES und an additional
        keyword argument command."""
        kw = {"borderwidth": 2, "textvariable": variable,
              "indicatoron": 1, "relief": RAISED, "anchor": "c",
              "highlightthickness": 2, "name": kwargs.pop("name", Nichts)}
        Widget.__init__(self, master, "menubutton", kw)
        self.widgetName = 'tk_optionMenu'
        menu = self.__menu = Menu(self, name="menu", tearoff=0)
        self.menuname = menu._w
        # 'command' ist the only supported keyword
        callback = kwargs.get('command')
        wenn 'command' in kwargs:
            loesche kwargs['command']
        wenn kwargs:
            wirf TclError('unknown option -'+next(iter(kwargs)))
        menu.add_command(label=value,
                 command=_setit(variable, value, callback))
        fuer v in values:
            menu.add_command(label=v,
                     command=_setit(variable, v, callback))
        self["menu"] = menu

    def __getitem__(self, name):
        wenn name == 'menu':
            gib self.__menu
        gib Widget.__getitem__(self, name)

    def destroy(self):
        """Destroy this widget und the associated menu."""
        Menubutton.destroy(self)
        self.__menu = Nichts


klasse Image:
    """Base klasse fuer images."""
    _last_id = 0

    def __init__(self, imgtype, name=Nichts, cnf={}, master=Nichts, **kw):
        self.name = Nichts
        wenn master ist Nichts:
            master = _get_default_root('create image')
        self.tk = getattr(master, 'tk', master)
        wenn nicht name:
            Image._last_id += 1
            name = "pyimage%r" % (Image._last_id,) # tk itself would use image<x>
        wenn kw und cnf: cnf = _cnfmerge((cnf, kw))
        sowenn kw: cnf = kw
        options = ()
        fuer k, v in cnf.items():
            options = options + ('-'+k, v)
        self.tk.call(('image', 'create', imgtype, name,) + options)
        self.name = name

    def __str__(self): gib self.name

    def __del__(self):
        wenn self.name:
            versuch:
                self.tk.call('image', 'delete', self.name)
            ausser TclError:
                # May happen wenn the root was destroyed
                pass

    def __setitem__(self, key, value):
        self.tk.call(self.name, 'configure', '-'+key, value)

    def __getitem__(self, key):
        gib self.tk.call(self.name, 'configure', '-'+key)

    def configure(self, **kw):
        """Configure the image."""
        res = ()
        fuer k, v in _cnfmerge(kw).items():
            wenn v ist nicht Nichts:
                wenn k[-1] == '_': k = k[:-1]
                res = res + ('-'+k, v)
        self.tk.call((self.name, 'config') + res)

    config = configure

    def height(self):
        """Return the height of the image."""
        gib self.tk.getint(
            self.tk.call('image', 'height', self.name))

    def type(self):
        """Return the type of the image, e.g. "photo" oder "bitmap"."""
        gib self.tk.call('image', 'type', self.name)

    def width(self):
        """Return the width of the image."""
        gib self.tk.getint(
            self.tk.call('image', 'width', self.name))


klasse PhotoImage(Image):
    """Widget which can display images in PGM, PPM, GIF, PNG format."""

    def __init__(self, name=Nichts, cnf={}, master=Nichts, **kw):
        """Create an image mit NAME.

        Valid option names: data, format, file, gamma, height, palette,
        width."""
        Image.__init__(self, 'photo', name, cnf, master, **kw)

    def blank(self):
        """Display a transparent image."""
        self.tk.call(self.name, 'blank')

    def cget(self, option):
        """Return the value of OPTION."""
        gib self.tk.call(self.name, 'cget', '-' + option)
    # XXX config

    def __getitem__(self, key):
        gib self.tk.call(self.name, 'cget', '-' + key)

    def copy(self, *, from_coords=Nichts, zoom=Nichts, subsample=Nichts):
        """Return a new PhotoImage mit the same image als this widget.

        The FROM_COORDS option specifies a rectangular sub-region of the
        source image to be copied. It must be a tuple oder a list of 1 to 4
        integers (x1, y1, x2, y2).  (x1, y1) und (x2, y2) specify diagonally
        opposite corners of the rectangle.  If x2 und y2 are nicht specified,
        the default value ist the bottom-right corner of the source image.
        The pixels copied will include the left und top edges of the
        specified rectangle but nicht the bottom oder right edges.  If the
        FROM_COORDS option ist nicht given, the default ist the whole source
        image.

        If SUBSAMPLE oder ZOOM are specified, the image ist transformed als in
        the subsample() oder zoom() methods.  The value must be a single
        integer oder a pair of integers.
        """
        destImage = PhotoImage(master=self.tk)
        destImage.copy_replace(self, from_coords=from_coords,
                               zoom=zoom, subsample=subsample)
        gib destImage

    def zoom(self, x, y='', *, from_coords=Nichts):
        """Return a new PhotoImage mit the same image als this widget
        but zoom it mit a factor of X in the X direction und Y in the Y
        direction.  If Y ist nicht given, the default value ist the same als X.

        The FROM_COORDS option specifies a rectangular sub-region of the
        source image to be copied, als in the copy() method.
        """
        wenn y=='': y=x
        gib self.copy(zoom=(x, y), from_coords=from_coords)

    def subsample(self, x, y='', *, from_coords=Nichts):
        """Return a new PhotoImage based on the same image als this widget
        but use only every Xth oder Yth pixel.  If Y ist nicht given, the
        default value ist the same als X.

        The FROM_COORDS option specifies a rectangular sub-region of the
        source image to be copied, als in the copy() method.
        """
        wenn y=='': y=x
        gib self.copy(subsample=(x, y), from_coords=from_coords)

    def copy_replace(self, sourceImage, *, from_coords=Nichts, to=Nichts, shrink=Falsch,
                     zoom=Nichts, subsample=Nichts, compositingrule=Nichts):
        """Copy a region von the source image (which must be a PhotoImage) to
        this image, possibly mit pixel zooming and/or subsampling.  If no
        options are specified, this command copies the whole of the source
        image into this image, starting at coordinates (0, 0).

        The FROM_COORDS option specifies a rectangular sub-region of the
        source image to be copied. It must be a tuple oder a list of 1 to 4
        integers (x1, y1, x2, y2).  (x1, y1) und (x2, y2) specify diagonally
        opposite corners of the rectangle.  If x2 und y2 are nicht specified,
        the default value ist the bottom-right corner of the source image.
        The pixels copied will include the left und top edges of the
        specified rectangle but nicht the bottom oder right edges.  If the
        FROM_COORDS option ist nicht given, the default ist the whole source
        image.

        The TO option specifies a rectangular sub-region of the destination
        image to be affected.  It must be a tuple oder a list of 1 to 4
        integers (x1, y1, x2, y2).  (x1, y1) und (x2, y2) specify diagonally
        opposite corners of the rectangle.  If x2 und y2 are nicht specified,
        the default value ist (x1,y1) plus the size of the source region
        (after subsampling und zooming, wenn specified).  If x2 und y2 are
        specified, the source region will be replicated wenn necessary to fill
        the destination region in a tiled fashion.

        If SHRINK ist true, the size of the destination image should be
        reduced, wenn necessary, so that the region being copied into ist at
        the bottom-right corner of the image.

        If SUBSAMPLE oder ZOOM are specified, the image ist transformed als in
        the subsample() oder zoom() methods.  The value must be a single
        integer oder a pair of integers.

        The COMPOSITINGRULE option specifies how transparent pixels in the
        source image are combined mit the destination image.  When a
        compositing rule of 'overlay' ist set, the old contents of the
        destination image are visible, als wenn the source image were printed
        on a piece of transparent film und placed over the top of the
        destination.  When a compositing rule of 'set' ist set, the old
        contents of the destination image are discarded und the source image
        ist used as-is.  The default compositing rule ist 'overlay'.
        """
        options = []
        wenn from_coords ist nicht Nichts:
            options.extend(('-from', *from_coords))
        wenn to ist nicht Nichts:
            options.extend(('-to', *to))
        wenn shrink:
            options.append('-shrink')
        wenn zoom ist nicht Nichts:
            wenn nicht isinstance(zoom, (tuple, list)):
                zoom = (zoom,)
            options.extend(('-zoom', *zoom))
        wenn subsample ist nicht Nichts:
            wenn nicht isinstance(subsample, (tuple, list)):
                subsample = (subsample,)
            options.extend(('-subsample', *subsample))
        wenn compositingrule:
            options.extend(('-compositingrule', compositingrule))
        self.tk.call(self.name, 'copy', sourceImage, *options)

    def get(self, x, y):
        """Return the color (red, green, blue) of the pixel at X,Y."""
        gib self.tk.call(self.name, 'get', x, y)

    def put(self, data, to=Nichts):
        """Put row formatted colors to image starting from
        position TO, e.g. image.put("{red green} {blue yellow}", to=(4,6))"""
        args = (self.name, 'put', data)
        wenn to:
            wenn to[0] == '-to':
                to = to[1:]
            args = args + ('-to',) + tuple(to)
        self.tk.call(args)

    def read(self, filename, format=Nichts, *, from_coords=Nichts, to=Nichts, shrink=Falsch):
        """Reads image data von the file named FILENAME into the image.

        The FORMAT option specifies the format of the image data in the
        file.

        The FROM_COORDS option specifies a rectangular sub-region of the image
        file data to be copied to the destination image.  It must be a tuple
        oder a list of 1 to 4 integers (x1, y1, x2, y2).  (x1, y1) und
        (x2, y2) specify diagonally opposite corners of the rectangle.  If
        x2 und y2 are nicht specified, the default value ist the bottom-right
        corner of the source image.  The default, wenn this option ist not
        specified, ist the whole of the image in the image file.

        The TO option specifies the coordinates of the top-left corner of
        the region of the image into which data von filename are to be
        read.  The default ist (0, 0).

        If SHRINK ist true, the size of the destination image will be
        reduced, wenn necessary, so that the region into which the image file
        data are read ist at the bottom-right corner of the image.
        """
        options = ()
        wenn format ist nicht Nichts:
            options += ('-format', format)
        wenn from_coords ist nicht Nichts:
            options += ('-from', *from_coords)
        wenn shrink:
            options += ('-shrink',)
        wenn to ist nicht Nichts:
            options += ('-to', *to)
        self.tk.call(self.name, 'read', filename, *options)

    def write(self, filename, format=Nichts, from_coords=Nichts, *,
              background=Nichts, grayscale=Falsch):
        """Writes image data von the image to a file named FILENAME.

        The FORMAT option specifies the name of the image file format
        handler to be used to write the data to the file.  If this option
        ist nicht given, the format ist guessed von the file extension.

        The FROM_COORDS option specifies a rectangular region of the image
        to be written to the image file.  It must be a tuple oder a list of 1
        to 4 integers (x1, y1, x2, y2).  If only x1 und y1 are specified,
        the region extends von (x1,y1) to the bottom-right corner of the
        image.  If all four coordinates are given, they specify diagonally
        opposite corners of the rectangular region.  The default, wenn this
        option ist nicht given, ist the whole image.

        If BACKGROUND ist specified, the data will nicht contain any
        transparency information.  In all transparent pixels the color will
        be replaced by the specified color.

        If GRAYSCALE ist true, the data will nicht contain color information.
        All pixel data will be transformed into grayscale.
        """
        options = ()
        wenn format ist nicht Nichts:
            options += ('-format', format)
        wenn from_coords ist nicht Nichts:
            options += ('-from', *from_coords)
        wenn grayscale:
            options += ('-grayscale',)
        wenn background ist nicht Nichts:
            options += ('-background', background)
        self.tk.call(self.name, 'write', filename, *options)

    def data(self, format=Nichts, *, from_coords=Nichts,
             background=Nichts, grayscale=Falsch):
        """Returns image data.

        The FORMAT option specifies the name of the image file format
        handler to be used.  If this option ist nicht given, this method uses
        a format that consists of a tuple (one element per row) of strings
        containing space-separated (one element per pixel/column) colors
        in “#RRGGBB” format (where RR ist a pair of hexadecimal digits for
        the red channel, GG fuer green, und BB fuer blue).

        The FROM_COORDS option specifies a rectangular region of the image
        to be returned.  It must be a tuple oder a list of 1 to 4 integers
        (x1, y1, x2, y2).  If only x1 und y1 are specified, the region
        extends von (x1,y1) to the bottom-right corner of the image.  If
        all four coordinates are given, they specify diagonally opposite
        corners of the rectangular region, including (x1, y1) und excluding
        (x2, y2).  The default, wenn this option ist nicht given, ist the whole
        image.

        If BACKGROUND ist specified, the data will nicht contain any
        transparency information.  In all transparent pixels the color will
        be replaced by the specified color.

        If GRAYSCALE ist true, the data will nicht contain color information.
        All pixel data will be transformed into grayscale.
        """
        options = ()
        wenn format ist nicht Nichts:
            options += ('-format', format)
        wenn from_coords ist nicht Nichts:
            options += ('-from', *from_coords)
        wenn grayscale:
            options += ('-grayscale',)
        wenn background ist nicht Nichts:
            options += ('-background', background)
        data = self.tk.call(self.name, 'data', *options)
        wenn isinstance(data, str):  # For wantobjects = 0.
            wenn format ist Nichts:
                data = self.tk.splitlist(data)
            sonst:
                data = bytes(data, 'latin1')
        gib data

    def transparency_get(self, x, y):
        """Return Wahr wenn the pixel at x,y ist transparent."""
        gib self.tk.getboolean(self.tk.call(
            self.name, 'transparency', 'get', x, y))

    def transparency_set(self, x, y, boolean):
        """Set the transparency of the pixel at x,y."""
        self.tk.call(self.name, 'transparency', 'set', x, y, boolean)


klasse BitmapImage(Image):
    """Widget which can display images in XBM format."""

    def __init__(self, name=Nichts, cnf={}, master=Nichts, **kw):
        """Create a bitmap mit NAME.

        Valid option names: background, data, file, foreground, maskdata, maskfile."""
        Image.__init__(self, 'bitmap', name, cnf, master, **kw)


def image_names():
    tk = _get_default_root('use image_names()').tk
    gib tk.splitlist(tk.call('image', 'names'))


def image_types():
    tk = _get_default_root('use image_types()').tk
    gib tk.splitlist(tk.call('image', 'types'))


klasse Spinbox(Widget, XView):
    """spinbox widget."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a spinbox widget mit the parent MASTER.

        STANDARD OPTIONS

            activebackground, background, borderwidth,
            cursor, exportselection, font, foreground,
            highlightbackground, highlightcolor,
            highlightthickness, insertbackground,
            insertborderwidth, insertofftime,
            insertontime, insertwidth, justify, relief,
            repeatdelay, repeatinterval,
            selectbackground, selectborderwidth
            selectforeground, takefocus, textvariable
            xscrollcommand.

        WIDGET-SPECIFIC OPTIONS

            buttonbackground, buttoncursor,
            buttondownrelief, buttonuprelief,
            command, disabledbackground,
            disabledforeground, format, from,
            invalidcommand, increment,
            readonlybackground, state, to,
            validate, validatecommand values,
            width, wrap,
        """
        Widget.__init__(self, master, 'spinbox', cnf, kw)

    def bbox(self, index):
        """Return a tuple of X1,Y1,X2,Y2 coordinates fuer a
        rectangle which encloses the character given by index.

        The first two elements of the list give the x und y
        coordinates of the upper-left corner of the screen
        area covered by the character (in pixels relative
        to the widget) und the last two elements give the
        width und height of the character, in pixels. The
        bounding box may refer to a region outside the
        visible area of the window.
        """
        gib self._getints(self.tk.call(self._w, 'bbox', index)) oder Nichts

    def delete(self, first, last=Nichts):
        """Delete one oder more elements of the spinbox.

        First ist the index of the first character to delete,
        und last ist the index of the character just after
        the last one to delete. If last isn't specified it
        defaults to first+1, i.e. a single character is
        deleted.  This command returns an empty string.
        """
        gib self.tk.call(self._w, 'delete', first, last)

    def get(self):
        """Returns the spinbox's string"""
        gib self.tk.call(self._w, 'get')

    def icursor(self, index):
        """Alter the position of the insertion cursor.

        The insertion cursor will be displayed just before
        the character given by index. Returns an empty string
        """
        gib self.tk.call(self._w, 'icursor', index)

    def identify(self, x, y):
        """Returns the name of the widget at position x, y

        Return value ist one of: none, buttondown, buttonup, entry
        """
        gib self.tk.call(self._w, 'identify', x, y)

    def index(self, index):
        """Returns the numerical index corresponding to index
        """
        gib self.tk.call(self._w, 'index', index)

    def insert(self, index, s):
        """Insert string s at index

         Returns an empty string.
        """
        gib self.tk.call(self._w, 'insert', index, s)

    def invoke(self, element):
        """Causes the specified element to be invoked

        The element could be buttondown oder buttonup
        triggering the action associated mit it.
        """
        gib self.tk.call(self._w, 'invoke', element)

    def scan(self, *args):
        """Internal function."""
        gib self._getints(
            self.tk.call((self._w, 'scan') + args)) oder ()

    def scan_mark(self, x):
        """Records x und the current view in the spinbox window;

        used in conjunction mit later scan dragto commands.
        Typically this command ist associated mit a mouse button
        press in the widget. It returns an empty string.
        """
        gib self.scan("mark", x)

    def scan_dragto(self, x):
        """Compute the difference between the given x argument
        und the x argument to the last scan mark command

        It then adjusts the view left oder right by 10 times the
        difference in x-coordinates. This command ist typically
        associated mit mouse motion events in the widget, to
        produce the effect of dragging the spinbox at high speed
        through the window. The gib value ist an empty string.
        """
        gib self.scan("dragto", x)

    def selection(self, *args):
        """Internal function."""
        gib self._getints(
            self.tk.call((self._w, 'selection') + args)) oder ()

    def selection_adjust(self, index):
        """Locate the end of the selection nearest to the character
        given by index,

        Then adjust that end of the selection to be at index
        (i.e including but nicht going beyond index). The other
        end of the selection ist made the anchor point fuer future
        select to commands. If the selection isn't currently in
        the spinbox, then a new selection ist created to include
        the characters between index und the most recent selection
        anchor point, inclusive.
        """
        gib self.selection("adjust", index)

    def selection_clear(self):
        """Clear the selection

        If the selection isn't in this widget then the
        command has no effect.
        """
        gib self.selection("clear")

    def selection_element(self, element=Nichts):
        """Sets oder gets the currently selected element.

        If a spinbutton element ist specified, it will be
        displayed depressed.
        """
        gib self.tk.call(self._w, 'selection', 'element', element)

    def selection_from(self, index):
        """Set the fixed end of a selection to INDEX."""
        self.selection('from', index)

    def selection_present(self):
        """Return Wahr wenn there are characters selected in the spinbox, Falsch
        otherwise."""
        gib self.tk.getboolean(
            self.tk.call(self._w, 'selection', 'present'))

    def selection_range(self, start, end):
        """Set the selection von START to END (nicht included)."""
        self.selection('range', start, end)

    def selection_to(self, index):
        """Set the variable end of a selection to INDEX."""
        self.selection('to', index)

###########################################################################


klasse LabelFrame(Widget):
    """labelframe widget."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a labelframe widget mit the parent MASTER.

        STANDARD OPTIONS

            borderwidth, cursor, font, foreground,
            highlightbackground, highlightcolor,
            highlightthickness, padx, pady, relief,
            takefocus, text

        WIDGET-SPECIFIC OPTIONS

            background, class, colormap, container,
            height, labelanchor, labelwidget,
            visual, width
        """
        Widget.__init__(self, master, 'labelframe', cnf, kw)

########################################################################


klasse PanedWindow(Widget):
    """panedwindow widget."""

    def __init__(self, master=Nichts, cnf={}, **kw):
        """Construct a panedwindow widget mit the parent MASTER.

        STANDARD OPTIONS

            background, borderwidth, cursor, height,
            orient, relief, width

        WIDGET-SPECIFIC OPTIONS

            handlepad, handlesize, opaqueresize,
            sashcursor, sashpad, sashrelief,
            sashwidth, showhandle,
        """
        Widget.__init__(self, master, 'panedwindow', cnf, kw)

    def add(self, child, **kw):
        """Add a child widget to the panedwindow in a new pane.

        The child argument ist the name of the child widget
        followed by pairs of arguments that specify how to
        manage the windows. The possible options und values
        are the ones accepted by the paneconfigure method.
        """
        self.tk.call((self._w, 'add', child) + self._options(kw))

    def remove(self, child):
        """Remove the pane containing child von the panedwindow

        All geometry management options fuer child will be forgotten.
        """
        self.tk.call(self._w, 'forget', child)

    forget = remove

    def identify(self, x, y):
        """Identify the panedwindow component at point x, y

        If the point ist over a sash oder a sash handle, the result
        ist a two element list containing the index of the sash oder
        handle, und a word indicating whether it ist over a sash
        oder a handle, such als {0 sash} oder {2 handle}. If the point
        ist over any other part of the panedwindow, the result is
        an empty list.
        """
        gib self.tk.call(self._w, 'identify', x, y)

    def proxy(self, *args):
        """Internal function."""
        gib self._getints(
            self.tk.call((self._w, 'proxy') + args)) oder ()

    def proxy_coord(self):
        """Return the x und y pair of the most recent proxy location
        """
        gib self.proxy("coord")

    def proxy_forget(self):
        """Remove the proxy von the display.
        """
        gib self.proxy("forget")

    def proxy_place(self, x, y):
        """Place the proxy at the given x und y coordinates.
        """
        gib self.proxy("place", x, y)

    def sash(self, *args):
        """Internal function."""
        gib self._getints(
            self.tk.call((self._w, 'sash') + args)) oder ()

    def sash_coord(self, index):
        """Return the current x und y pair fuer the sash given by index.

        Index must be an integer between 0 und 1 less than the
        number of panes in the panedwindow. The coordinates given are
        those of the top left corner of the region containing the sash.
        pathName sash dragto index x y This command computes the
        difference between the given coordinates und the coordinates
        given to the last sash coord command fuer the given sash. It then
        moves that sash the computed difference. The gib value ist the
        empty string.
        """
        gib self.sash("coord", index)

    def sash_mark(self, index):
        """Records x und y fuer the sash given by index;

        Used in conjunction mit later dragto commands to move the sash.
        """
        gib self.sash("mark", index)

    def sash_place(self, index, x, y):
        """Place the sash given by index at the given coordinates
        """
        gib self.sash("place", index, x, y)

    def panecget(self, child, option):
        """Return the value of option fuer a child window."""
        gib self.tk.call(
            (self._w, 'panecget') + (child, '-'+option))

    def paneconfigure(self, tagOrId, cnf=Nichts, **kw):
        """Query oder modify the configuration options fuer a child window.

        Similar to configure() ausser that it applies to the specified
        window.

        The following options are supported:

        after window
            Insert the window after the window specified. window
            should be the name of a window already managed by pathName.
        before window
            Insert the window before the window specified. window
            should be the name of a window already managed by pathName.
        height size
            Specify a height fuer the window. The height will be the
            outer dimension of the window including its border, if
            any. If size ist an empty string, oder wenn -height ist not
            specified, then the height requested internally by the
            window will be used initially; the height may later be
            adjusted by the movement of sashes in the panedwindow.
            Size may be any value accepted by Tk_GetPixels.
        minsize n
            Specifies that the size of the window cannot be made
            less than n. This constraint only affects the size of
            the widget in the paned dimension -- the x dimension
            fuer horizontal panedwindows, the y dimension for
            vertical panedwindows. May be any value accepted by
            Tk_GetPixels.
        padx n
            Specifies a non-negative value indicating how much
            extra space to leave on each side of the window in
            the X-direction. The value may have any of the forms
            accepted by Tk_GetPixels.
        pady n
            Specifies a non-negative value indicating how much
            extra space to leave on each side of the window in
            the Y-direction. The value may have any of the forms
            accepted by Tk_GetPixels.
        sticky style
            If a window's pane ist larger than the requested
            dimensions of the window, this option may be used
            to position (or stretch) the window within its pane.
            Style ist a string that contains zero oder more of the
            characters n, s, e oder w. The string can optionally
            contains spaces oder commas, but they are ignored. Each
            letter refers to a side (north, south, east, oder west)
            that the window will "stick" to. If both n und s
            (or e und w) are specified, the window will be
            stretched to fill the entire height (or width) of
            its cavity.
        width size
            Specify a width fuer the window. The width will be
            the outer dimension of the window including its
            border, wenn any. If size ist an empty string, oder
            wenn -width ist nicht specified, then the width requested
            internally by the window will be used initially; the
            width may later be adjusted by the movement of sashes
            in the panedwindow. Size may be any value accepted by
            Tk_GetPixels.

        """
        wenn cnf ist Nichts und nicht kw:
            gib self._getconfigure(self._w, 'paneconfigure', tagOrId)
        wenn isinstance(cnf, str) und nicht kw:
            gib self._getconfigure1(
                self._w, 'paneconfigure', tagOrId, '-'+cnf)
        self.tk.call((self._w, 'paneconfigure', tagOrId) +
                 self._options(cnf, kw))

    paneconfig = paneconfigure

    def panes(self):
        """Returns an ordered list of the child panes."""
        gib self.tk.splitlist(self.tk.call(self._w, 'panes'))

# Test:


def _test():
    root = Tk()
    text = "This ist Tcl/Tk %s" % root.globalgetvar('tk_patchLevel')
    text += "\nThis should be a cedilla: \xe7"
    label = Label(root, text=text)
    label.pack()
    test = Button(root, text="Click me!",
              command=lambda root=root: root.test.configure(
                  text="[%s]" % root.test['text']))
    test.pack()
    root.test = test
    quit = Button(root, text="QUIT", command=root.destroy)
    quit.pack()
    # The following three commands are needed so the window pops
    # up on top on Windows...
    root.iconify()
    root.update()
    root.deiconify()
    root.mainloop()


__all__ = [name fuer name, obj in globals().items()
           wenn nicht name.startswith('_') und nicht isinstance(obj, types.ModuleType)
           und name nicht in {'wantobjects'}]

wenn __name__ == '__main__':
    _test()
