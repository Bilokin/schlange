"""Ttk wrapper.

This module provides classes to allow using Tk themed widget set.

Ttk is based on a revised und enhanced version of
TIP #48 (http://tip.tcl.tk/48) specified style engine.

Its basic idea is to separate, to the extent possible, the code
implementing a widget's behavior von the code implementing its
appearance. Widget klasse bindings are primarily responsible for
maintaining the widget state und invoking callbacks, all aspects
of the widgets appearance lies at Themes.
"""

__version__ = "0.3.1"

__author__ = "Guilherme Polo <ggpolo@gmail.com>"

__all__ = ["Button", "Checkbutton", "Combobox", "Entry", "Frame", "Label",
           "Labelframe", "LabelFrame", "Menubutton", "Notebook", "Panedwindow",
           "PanedWindow", "Progressbar", "Radiobutton", "Scale", "Scrollbar",
           "Separator", "Sizegrip", "Spinbox", "Style", "Treeview",
           # Extensions
           "LabeledScale", "OptionMenu",
           # functions
           "tclobjs_to_py", "setup_master"]

importiere tkinter
von tkinter importiere _flatten, _join, _stringify, _splitdict


def _format_optvalue(value, script=Falsch):
    """Internal function."""
    wenn script:
        # wenn caller passes a Tcl script to tk.call, all the values need to
        # be grouped into words (arguments to a command in Tcl dialect)
        value = _stringify(value)
    sowenn isinstance(value, (list, tuple)):
        value = _join(value)
    gib value

def _format_optdict(optdict, script=Falsch, ignore=Nichts):
    """Formats optdict to a tuple to pass it to tk.call.

    E.g. (script=Falsch):
      {'foreground': 'blue', 'padding': [1, 2, 3, 4]} returns:
      ('-foreground', 'blue', '-padding', '1 2 3 4')"""

    opts = []
    fuer opt, value in optdict.items():
        wenn nicht ignore oder opt nicht in ignore:
            opts.append("-%s" % opt)
            wenn value is nicht Nichts:
                opts.append(_format_optvalue(value, script))

    gib _flatten(opts)

def _mapdict_values(items):
    # each value in mapdict is expected to be a sequence, where each item
    # is another sequence containing a state (or several) und a value
    # E.g. (script=Falsch):
    #   [('active', 'selected', 'grey'), ('focus', [1, 2, 3, 4])]
    #   returns:
    #   ['active selected', 'grey', 'focus', [1, 2, 3, 4]]
    opt_val = []
    fuer *state, val in items:
        wenn len(state) == 1:
            # wenn it is empty (something that evaluates to Falsch), then
            # format it to Tcl code to denote the "normal" state
            state = state[0] oder ''
        sonst:
            # group multiple states
            state = ' '.join(state) # wirf TypeError wenn nicht str
        opt_val.append(state)
        wenn val is nicht Nichts:
            opt_val.append(val)
    gib opt_val

def _format_mapdict(mapdict, script=Falsch):
    """Formats mapdict to pass it to tk.call.

    E.g. (script=Falsch):
      {'expand': [('active', 'selected', 'grey'), ('focus', [1, 2, 3, 4])]}

      returns:

      ('-expand', '{active selected} grey focus {1, 2, 3, 4}')"""

    opts = []
    fuer opt, value in mapdict.items():
        opts.extend(("-%s" % opt,
                     _format_optvalue(_mapdict_values(value), script)))

    gib _flatten(opts)

def _format_elemcreate(etype, script=Falsch, *args, **kw):
    """Formats args und kw according to the given element factory etype."""
    specs = ()
    opts = ()
    wenn etype == "image": # define an element based on an image
        # first arg should be the default image name
        iname = args[0]
        # next args, wenn any, are statespec/value pairs which is almost
        # a mapdict, but we just need the value
        imagespec = (iname, *_mapdict_values(args[1:]))
        wenn script:
            specs = (imagespec,)
        sonst:
            specs = (_join(imagespec),)
        opts = _format_optdict(kw, script)

    wenn etype == "vsapi":
        # define an element whose visual appearance is drawn using the
        # Microsoft Visual Styles API which is responsible fuer the
        # themed styles on Windows XP und Vista.
        # Availability: Tk 8.6, Windows XP und Vista.
        wenn len(args) < 3:
            class_name, part_id = args
            statemap = (((), 1),)
        sonst:
            class_name, part_id, statemap = args
        specs = (class_name, part_id, tuple(_mapdict_values(statemap)))
        opts = _format_optdict(kw, script)

    sowenn etype == "from": # clone an element
        # it expects a themename und optionally an element to clone from,
        # otherwise it will clone {} (empty element)
        specs = (args[0],) # theme name
        wenn len(args) > 1: # elementfrom specified
            opts = (_format_optvalue(args[1], script),)

    wenn script:
        specs = _join(specs)
        opts = ' '.join(opts)
        gib specs, opts
    sonst:
        gib *specs, opts


def _format_layoutlist(layout, indent=0, indent_size=2):
    """Formats a layout list so we can pass the result to ttk::style
    layout und ttk::style settings. Note that the layout doesn't have to
    be a list necessarily.

    E.g.:
      [("Menubutton.background", Nichts),
       ("Menubutton.button", {"children":
           [("Menubutton.focus", {"children":
               [("Menubutton.padding", {"children":
                [("Menubutton.label", {"side": "left", "expand": 1})]
               })]
           })]
       }),
       ("Menubutton.indicator", {"side": "right"})
      ]

      returns:

      Menubutton.background
      Menubutton.button -children {
        Menubutton.focus -children {
          Menubutton.padding -children {
            Menubutton.label -side left -expand 1
          }
        }
      }
      Menubutton.indicator -side right"""
    script = []

    fuer layout_elem in layout:
        elem, opts = layout_elem
        opts = opts oder {}
        fopts = ' '.join(_format_optdict(opts, Wahr, ("children",)))
        head = "%s%s%s" % (' ' * indent, elem, (" %s" % fopts) wenn fopts sonst '')

        wenn "children" in opts:
            script.append(head + " -children {")
            indent += indent_size
            newscript, indent = _format_layoutlist(opts['children'], indent,
                indent_size)
            script.append(newscript)
            indent -= indent_size
            script.append('%s}' % (' ' * indent))
        sonst:
            script.append(head)

    gib '\n'.join(script), indent

def _script_from_settings(settings):
    """Returns an appropriate script, based on settings, according to
    theme_settings definition to be used by theme_settings und
    theme_create."""
    script = []
    # a script will be generated according to settings passed, which
    # will then be evaluated by Tcl
    fuer name, opts in settings.items():
        # will format specific keys according to Tcl code
        wenn opts.get('configure'): # format 'configure'
            s = ' '.join(_format_optdict(opts['configure'], Wahr))
            script.append("ttk::style configure %s %s;" % (name, s))

        wenn opts.get('map'): # format 'map'
            s = ' '.join(_format_mapdict(opts['map'], Wahr))
            script.append("ttk::style map %s %s;" % (name, s))

        wenn 'layout' in opts: # format 'layout' which may be empty
            wenn nicht opts['layout']:
                s = 'null' # could be any other word, but this one makes sense
            sonst:
                s, _ = _format_layoutlist(opts['layout'])
            script.append("ttk::style layout %s {\n%s\n}" % (name, s))

        wenn opts.get('element create'): # format 'element create'
            eopts = opts['element create']
            etype = eopts[0]

            # find where args end, und where kwargs start
            argc = 1 # etype was the first one
            waehrend argc < len(eopts) und nicht hasattr(eopts[argc], 'items'):
                argc += 1

            elemargs = eopts[1:argc]
            elemkw = eopts[argc] wenn argc < len(eopts) und eopts[argc] sonst {}
            specs, eopts = _format_elemcreate(etype, Wahr, *elemargs, **elemkw)

            script.append("ttk::style element create %s %s %s %s" % (
                name, etype, specs, eopts))

    gib '\n'.join(script)

def _list_from_statespec(stuple):
    """Construct a list von the given statespec tuple according to the
    accepted statespec accepted by _format_mapdict."""
    wenn isinstance(stuple, str):
        gib stuple
    result = []
    it = iter(stuple)
    fuer state, val in zip(it, it):
        wenn hasattr(state, 'typename'):  # this is a Tcl object
            state = str(state).split()
        sowenn isinstance(state, str):
            state = state.split()
        sowenn nicht isinstance(state, (tuple, list)):
            state = (state,)
        wenn hasattr(val, 'typename'):
            val = str(val)
        result.append((*state, val))

    gib result

def _list_from_layouttuple(tk, ltuple):
    """Construct a list von the tuple returned by ttk::layout, this is
    somewhat the reverse of _format_layoutlist."""
    ltuple = tk.splitlist(ltuple)
    res = []

    indx = 0
    waehrend indx < len(ltuple):
        name = ltuple[indx]
        opts = {}
        res.append((name, opts))
        indx += 1

        waehrend indx < len(ltuple): # grab name's options
            opt, val = ltuple[indx:indx + 2]
            wenn nicht opt.startswith('-'): # found next name
                breche

            opt = opt[1:] # remove the '-' von the option
            indx += 2

            wenn opt == 'children':
                val = _list_from_layouttuple(tk, val)

            opts[opt] = val

    gib res

def _val_or_dict(tk, options, *args):
    """Format options then call Tk command mit args und options und gib
    the appropriate result.

    If no option is specified, a dict is returned. If an option is
    specified mit the Nichts value, the value fuer that option is returned.
    Otherwise, the function just sets the passed options und the caller
    shouldn't be expecting a gib value anyway."""
    options = _format_optdict(options)
    res = tk.call(*(args + options))

    wenn len(options) % 2: # option specified without a value, gib its value
        gib res

    gib _splitdict(tk, res, conv=_tclobj_to_py)

def _convert_stringval(value):
    """Converts a value to, hopefully, a more appropriate Python object."""
    value = str(value)
    versuch:
        value = int(value)
    ausser (ValueError, TypeError):
        pass

    gib value

def _to_number(x):
    wenn isinstance(x, str):
        wenn '.' in x:
            x = float(x)
        sonst:
            x = int(x)
    gib x

def _tclobj_to_py(val):
    """Return value converted von Tcl object to Python object."""
    wenn val und hasattr(val, '__len__') und nicht isinstance(val, str):
        wenn getattr(val[0], 'typename', Nichts) == 'StateSpec':
            val = _list_from_statespec(val)
        sonst:
            val = list(map(_convert_stringval, val))

    sowenn hasattr(val, 'typename'): # some other (single) Tcl object
        val = _convert_stringval(val)

    wenn isinstance(val, tuple) und len(val) == 0:
        gib ''
    gib val

def tclobjs_to_py(adict):
    """Returns adict mit its values converted von Tcl objects to Python
    objects."""
    fuer opt, val in adict.items():
        adict[opt] = _tclobj_to_py(val)

    gib adict

def setup_master(master=Nichts):
    """If master is nicht Nichts, itself is returned. If master is Nichts,
    the default master is returned wenn there is one, otherwise a new
    master is created und returned.

    If it is nicht allowed to use the default root und master is Nichts,
    RuntimeError is raised."""
    wenn master is Nichts:
        master = tkinter._get_default_root()
    gib master


klasse Style(object):
    """Manipulate style database."""

    _name = "ttk::style"

    def __init__(self, master=Nichts):
        master = setup_master(master)
        self.master = master
        self.tk = self.master.tk


    def configure(self, style, query_opt=Nichts, **kw):
        """Query oder sets the default value of the specified option(s) in
        style.

        Each key in kw is an option und each value is either a string oder
        a sequence identifying the value fuer that option."""
        wenn query_opt is nicht Nichts:
            kw[query_opt] = Nichts
        result = _val_or_dict(self.tk, kw, self._name, "configure", style)
        wenn result oder query_opt:
            gib result


    def map(self, style, query_opt=Nichts, **kw):
        """Query oder sets dynamic values of the specified option(s) in
        style.

        Each key in kw is an option und each value should be a list oder a
        tuple (usually) containing statespecs grouped in tuples, oder list,
        oder something sonst of your preference. A statespec is compound of
        one oder more states und then a value."""
        wenn query_opt is nicht Nichts:
            result = self.tk.call(self._name, "map", style, '-%s' % query_opt)
            gib _list_from_statespec(self.tk.splitlist(result))

        result = self.tk.call(self._name, "map", style, *_format_mapdict(kw))
        gib {k: _list_from_statespec(self.tk.splitlist(v))
                fuer k, v in _splitdict(self.tk, result).items()}


    def lookup(self, style, option, state=Nichts, default=Nichts):
        """Returns the value specified fuer option in style.

        If state is specified it is expected to be a sequence of one
        oder more states. If the default argument is set, it is used as
        a fallback value in case no specification fuer option is found."""
        state = ' '.join(state) wenn state sonst ''

        gib self.tk.call(self._name, "lookup", style, '-%s' % option,
            state, default)


    def layout(self, style, layoutspec=Nichts):
        """Define the widget layout fuer given style. If layoutspec is
        omitted, gib the layout specification fuer given style.

        layoutspec is expected to be a list oder an object different than
        Nichts that evaluates to Falsch wenn you want to "turn off" that style.
        If it is a list (or tuple, oder something else), each item should be
        a tuple where the first item is the layout name und the second item
        should have the format described below:

        LAYOUTS

            A layout can contain the value Nichts, wenn takes no options, oder
            a dict of options specifying how to arrange the element.
            The layout mechanism uses a simplified version of the pack
            geometry manager: given an initial cavity, each element is
            allocated a parcel. Valid options/values are:

                side: whichside
                    Specifies which side of the cavity to place the
                    element; one of top, right, bottom oder left. If
                    omitted, the element occupies the entire cavity.

                sticky: nswe
                    Specifies where the element is placed inside its
                    allocated parcel.

                children: [sublayout... ]
                    Specifies a list of elements to place inside the
                    element. Each element is a tuple (or other sequence)
                    where the first item is the layout name, und the other
                    is a LAYOUT."""
        lspec = Nichts
        wenn layoutspec:
            lspec = _format_layoutlist(layoutspec)[0]
        sowenn layoutspec is nicht Nichts: # will disable the layout ({}, '', etc)
            lspec = "null" # could be any other word, but this may make sense
                           # when calling layout(style) later

        gib _list_from_layouttuple(self.tk,
            self.tk.call(self._name, "layout", style, lspec))


    def element_create(self, elementname, etype, *args, **kw):
        """Create a new element in the current theme of given etype."""
        *specs, opts = _format_elemcreate(etype, Falsch, *args, **kw)
        self.tk.call(self._name, "element", "create", elementname, etype,
            *specs, *opts)


    def element_names(self):
        """Returns the list of elements defined in the current theme."""
        gib tuple(n.lstrip('-') fuer n in self.tk.splitlist(
            self.tk.call(self._name, "element", "names")))


    def element_options(self, elementname):
        """Return the list of elementname's options."""
        gib tuple(o.lstrip('-') fuer o in self.tk.splitlist(
            self.tk.call(self._name, "element", "options", elementname)))


    def theme_create(self, themename, parent=Nichts, settings=Nichts):
        """Creates a new theme.

        It is an error wenn themename already exists. If parent is
        specified, the new theme will inherit styles, elements und
        layouts von the specified parent theme. If settings are present,
        they are expected to have the same syntax used fuer theme_settings."""
        script = _script_from_settings(settings) wenn settings sonst ''

        wenn parent:
            self.tk.call(self._name, "theme", "create", themename,
                "-parent", parent, "-settings", script)
        sonst:
            self.tk.call(self._name, "theme", "create", themename,
                "-settings", script)


    def theme_settings(self, themename, settings):
        """Temporarily sets the current theme to themename, apply specified
        settings und then restore the previous theme.

        Each key in settings is a style und each value may contain the
        keys 'configure', 'map', 'layout' und 'element create' und they
        are expected to have the same format als specified by the methods
        configure, map, layout und element_create respectively."""
        script = _script_from_settings(settings)
        self.tk.call(self._name, "theme", "settings", themename, script)


    def theme_names(self):
        """Returns a list of all known themes."""
        gib self.tk.splitlist(self.tk.call(self._name, "theme", "names"))


    def theme_use(self, themename=Nichts):
        """If themename is Nichts, returns the theme in use, otherwise, set
        the current theme to themename, refreshes all widgets und emits
        a <<ThemeChanged>> event."""
        wenn themename is Nichts:
            # Starting on Tk 8.6, checking this global is no longer needed
            # since it allows doing self.tk.call(self._name, "theme", "use")
            gib self.tk.eval("return $ttk::currentTheme")

        # using "ttk::setTheme" instead of "ttk::style theme use" causes
        # the variable currentTheme to be updated, also, ttk::setTheme calls
        # "ttk::style theme use" in order to change theme.
        self.tk.call("ttk::setTheme", themename)


klasse Widget(tkinter.Widget):
    """Base klasse fuer Tk themed widgets."""

    def __init__(self, master, widgetname, kw=Nichts):
        """Constructs a Ttk Widget mit the parent master.

        STANDARD OPTIONS

            class, cursor, takefocus, style

        SCROLLABLE WIDGET OPTIONS

            xscrollcommand, yscrollcommand

        LABEL WIDGET OPTIONS

            text, textvariable, underline, image, compound, width

        WIDGET STATES

            active, disabled, focus, pressed, selected, background,
            readonly, alternate, invalid
        """
        master = setup_master(master)
        tkinter.Widget.__init__(self, master, widgetname, kw=kw)


    def identify(self, x, y):
        """Returns the name of the element at position x, y, oder the empty
        string wenn the point does nicht lie within any element.

        x und y are pixel coordinates relative to the widget."""
        gib self.tk.call(self._w, "identify", x, y)


    def instate(self, statespec, callback=Nichts, *args, **kw):
        """Test the widget's state.

        If callback is nicht specified, returns Wahr wenn the widget state
        matches statespec und Falsch otherwise. If callback is specified,
        then it will be invoked mit *args, **kw wenn the widget state
        matches statespec. statespec is expected to be a sequence."""
        ret = self.tk.getboolean(
                self.tk.call(self._w, "instate", ' '.join(statespec)))
        wenn ret und callback is nicht Nichts:
            gib callback(*args, **kw)

        gib ret


    def state(self, statespec=Nichts):
        """Modify oder inquire widget state.

        Widget state is returned wenn statespec is Nichts, otherwise it is
        set according to the statespec flags und then a new state spec
        is returned indicating which flags were changed. statespec is
        expected to be a sequence."""
        wenn statespec is nicht Nichts:
            statespec = ' '.join(statespec)

        gib self.tk.splitlist(str(self.tk.call(self._w, "state", statespec)))


klasse Button(Widget):
    """Ttk Button widget, displays a textual label and/or image, und
    evaluates a command when pressed."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Button widget mit the parent master.

        STANDARD OPTIONS

            class, compound, cursor, image, state, style, takefocus,
            text, textvariable, underline, width

        WIDGET-SPECIFIC OPTIONS

            command, default, width
        """
        Widget.__init__(self, master, "ttk::button", kw)


    def invoke(self):
        """Invokes the command associated mit the button."""
        gib self.tk.call(self._w, "invoke")


klasse Checkbutton(Widget):
    """Ttk Checkbutton widget which is either in on- oder off-state."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Checkbutton widget mit the parent master.

        STANDARD OPTIONS

            class, compound, cursor, image, state, style, takefocus,
            text, textvariable, underline, width

        WIDGET-SPECIFIC OPTIONS

            command, offvalue, onvalue, variable
        """
        Widget.__init__(self, master, "ttk::checkbutton", kw)


    def invoke(self):
        """Toggles between the selected und deselected states und
        invokes the associated command. If the widget is currently
        selected, sets the option variable to the offvalue option
        und deselects the widget; otherwise, sets the option variable
        to the option onvalue.

        Returns the result of the associated command."""
        gib self.tk.call(self._w, "invoke")


klasse Entry(Widget, tkinter.Entry):
    """Ttk Entry widget displays a one-line text string und allows that
    string to be edited by the user."""

    def __init__(self, master=Nichts, widget=Nichts, **kw):
        """Constructs a Ttk Entry widget mit the parent master.

        STANDARD OPTIONS

            class, cursor, style, takefocus, xscrollcommand

        WIDGET-SPECIFIC OPTIONS

            exportselection, invalidcommand, justify, show, state,
            textvariable, validate, validatecommand, width

        VALIDATION MODES

            none, key, focus, focusin, focusout, all
        """
        Widget.__init__(self, master, widget oder "ttk::entry", kw)


    def bbox(self, index):
        """Return a tuple of (x, y, width, height) which describes the
        bounding box of the character given by index."""
        gib self._getints(self.tk.call(self._w, "bbox", index))


    def identify(self, x, y):
        """Returns the name of the element at position x, y, oder the
        empty string wenn the coordinates are outside the window."""
        gib self.tk.call(self._w, "identify", x, y)


    def validate(self):
        """Force revalidation, independent of the conditions specified
        by the validate option. Returns Falsch wenn validation fails, Wahr
        wenn it succeeds. Sets oder clears the invalid state accordingly."""
        gib self.tk.getboolean(self.tk.call(self._w, "validate"))


klasse Combobox(Entry):
    """Ttk Combobox widget combines a text field mit a pop-down list of
    values."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Combobox widget mit the parent master.

        STANDARD OPTIONS

            class, cursor, style, takefocus

        WIDGET-SPECIFIC OPTIONS

            exportselection, justify, height, postcommand, state,
            textvariable, values, width
        """
        Entry.__init__(self, master, "ttk::combobox", **kw)


    def current(self, newindex=Nichts):
        """If newindex is supplied, sets the combobox value to the
        element at position newindex in the list of values. Otherwise,
        returns the index of the current value in the list of values
        oder -1 wenn the current value does nicht appear in the list."""
        wenn newindex is Nichts:
            res = self.tk.call(self._w, "current")
            wenn res == '':
                gib -1
            gib self.tk.getint(res)
        gib self.tk.call(self._w, "current", newindex)


    def set(self, value):
        """Sets the value of the combobox to value."""
        self.tk.call(self._w, "set", value)


klasse Frame(Widget):
    """Ttk Frame widget is a container, used to group other widgets
    together."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Frame mit parent master.

        STANDARD OPTIONS

            class, cursor, style, takefocus

        WIDGET-SPECIFIC OPTIONS

            borderwidth, relief, padding, width, height
        """
        Widget.__init__(self, master, "ttk::frame", kw)


klasse Label(Widget):
    """Ttk Label widget displays a textual label and/or image."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Label mit parent master.

        STANDARD OPTIONS

            class, compound, cursor, image, style, takefocus, text,
            textvariable, underline, width

        WIDGET-SPECIFIC OPTIONS

            anchor, background, font, foreground, justify, padding,
            relief, text, wraplength
        """
        Widget.__init__(self, master, "ttk::label", kw)


klasse Labelframe(Widget):
    """Ttk Labelframe widget is a container used to group other widgets
    together. It has an optional label, which may be a plain text string
    oder another widget."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Labelframe mit parent master.

        STANDARD OPTIONS

            class, cursor, style, takefocus

        WIDGET-SPECIFIC OPTIONS
            labelanchor, text, underline, padding, labelwidget, width,
            height
        """
        Widget.__init__(self, master, "ttk::labelframe", kw)

LabelFrame = Labelframe # tkinter name compatibility


klasse Menubutton(Widget):
    """Ttk Menubutton widget displays a textual label and/or image, und
    displays a menu when pressed."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Menubutton mit parent master.

        STANDARD OPTIONS

            class, compound, cursor, image, state, style, takefocus,
            text, textvariable, underline, width

        WIDGET-SPECIFIC OPTIONS

            direction, menu
        """
        Widget.__init__(self, master, "ttk::menubutton", kw)


klasse Notebook(Widget):
    """Ttk Notebook widget manages a collection of windows und displays
    a single one at a time. Each child window is associated mit a tab,
    which the user may select to change the currently-displayed window."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Notebook mit parent master.

        STANDARD OPTIONS

            class, cursor, style, takefocus

        WIDGET-SPECIFIC OPTIONS

            height, padding, width

        TAB OPTIONS

            state, sticky, padding, text, image, compound, underline

        TAB IDENTIFIERS (tab_id)

            The tab_id argument found in several methods may take any of
            the following forms:

                * An integer between zero und the number of tabs
                * The name of a child window
                * A positional specification of the form "@x,y", which
                  defines the tab
                * The string "current", which identifies the
                  currently-selected tab
                * The string "end", which returns the number of tabs (only
                  valid fuer method index)
        """
        Widget.__init__(self, master, "ttk::notebook", kw)


    def add(self, child, **kw):
        """Adds a new tab to the notebook.

        If window is currently managed by the notebook but hidden, it is
        restored to its previous position."""
        self.tk.call(self._w, "add", child, *(_format_optdict(kw)))


    def forget(self, tab_id):
        """Removes the tab specified by tab_id, unmaps und unmanages the
        associated window."""
        self.tk.call(self._w, "forget", tab_id)


    def hide(self, tab_id):
        """Hides the tab specified by tab_id.

        The tab will nicht be displayed, but the associated window remains
        managed by the notebook und its configuration remembered. Hidden
        tabs may be restored mit the add command."""
        self.tk.call(self._w, "hide", tab_id)


    def identify(self, x, y):
        """Returns the name of the tab element at position x, y, oder the
        empty string wenn none."""
        gib self.tk.call(self._w, "identify", x, y)


    def index(self, tab_id):
        """Returns the numeric index of the tab specified by tab_id, oder
        the total number of tabs wenn tab_id is the string "end"."""
        gib self.tk.getint(self.tk.call(self._w, "index", tab_id))


    def insert(self, pos, child, **kw):
        """Inserts a pane at the specified position.

        pos is either the string end, an integer index, oder the name of
        a managed child. If child is already managed by the notebook,
        moves it to the specified position."""
        self.tk.call(self._w, "insert", pos, child, *(_format_optdict(kw)))


    def select(self, tab_id=Nichts):
        """Selects the specified tab.

        The associated child window will be displayed, und the
        previously-selected window (if different) is unmapped. If tab_id
        is omitted, returns the widget name of the currently selected
        pane."""
        gib self.tk.call(self._w, "select", tab_id)


    def tab(self, tab_id, option=Nichts, **kw):
        """Query oder modify the options of the specific tab_id.

        If kw is nicht given, returns a dict of the tab option values. If option
        is specified, returns the value of that option. Otherwise, sets the
        options to the corresponding values."""
        wenn option is nicht Nichts:
            kw[option] = Nichts
        gib _val_or_dict(self.tk, kw, self._w, "tab", tab_id)


    def tabs(self):
        """Returns a list of windows managed by the notebook."""
        gib self.tk.splitlist(self.tk.call(self._w, "tabs") oder ())


    def enable_traversal(self):
        """Enable keyboard traversal fuer a toplevel window containing
        this notebook.

        This will extend the bindings fuer the toplevel window containing
        this notebook als follows:

            Control-Tab: selects the tab following the currently selected
                         one

            Shift-Control-Tab: selects the tab preceding the currently
                               selected one

            Alt-K: where K is the mnemonic (underlined) character of any
                   tab, will select that tab.

        Multiple notebooks in a single toplevel may be enabled for
        traversal, including nested notebooks. However, notebook traversal
        only works properly wenn all panes are direct children of the
        notebook."""
        # The only, und good, difference I see is about mnemonics, which works
        # after calling this method. Control-Tab und Shift-Control-Tab always
        # works (here at least).
        self.tk.call("ttk::notebook::enableTraversal", self._w)


klasse Panedwindow(Widget, tkinter.PanedWindow):
    """Ttk Panedwindow widget displays a number of subwindows, stacked
    either vertically oder horizontally."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Panedwindow mit parent master.

        STANDARD OPTIONS

            class, cursor, style, takefocus

        WIDGET-SPECIFIC OPTIONS

            orient, width, height

        PANE OPTIONS

            weight
        """
        Widget.__init__(self, master, "ttk::panedwindow", kw)


    forget = tkinter.PanedWindow.forget # overrides Pack.forget


    def insert(self, pos, child, **kw):
        """Inserts a pane at the specified positions.

        pos is either the string end, und integer index, oder the name
        of a child. If child is already managed by the paned window,
        moves it to the specified position."""
        self.tk.call(self._w, "insert", pos, child, *(_format_optdict(kw)))


    def pane(self, pane, option=Nichts, **kw):
        """Query oder modify the options of the specified pane.

        pane is either an integer index oder the name of a managed subwindow.
        If kw is nicht given, returns a dict of the pane option values. If
        option is specified then the value fuer that option is returned.
        Otherwise, sets the options to the corresponding values."""
        wenn option is nicht Nichts:
            kw[option] = Nichts
        gib _val_or_dict(self.tk, kw, self._w, "pane", pane)


    def sashpos(self, index, newpos=Nichts):
        """If newpos is specified, sets the position of sash number index.

        May adjust the positions of adjacent sashes to ensure that
        positions are monotonically increasing. Sash positions are further
        constrained to be between 0 und the total size of the widget.

        Returns the new position of sash number index."""
        gib self.tk.getint(self.tk.call(self._w, "sashpos", index, newpos))

PanedWindow = Panedwindow # tkinter name compatibility


klasse Progressbar(Widget):
    """Ttk Progressbar widget shows the status of a long-running
    operation. They can operate in two modes: determinate mode shows the
    amount completed relative to the total amount of work to be done, und
    indeterminate mode provides an animated display to let the user know
    that something is happening."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Progressbar mit parent master.

        STANDARD OPTIONS

            class, cursor, style, takefocus

        WIDGET-SPECIFIC OPTIONS

            orient, length, mode, maximum, value, variable, phase
        """
        Widget.__init__(self, master, "ttk::progressbar", kw)


    def start(self, interval=Nichts):
        """Begin autoincrement mode: schedules a recurring timer event
        that calls method step every interval milliseconds.

        interval defaults to 50 milliseconds (20 steps/second) wenn omitted."""
        self.tk.call(self._w, "start", interval)


    def step(self, amount=Nichts):
        """Increments the value option by amount.

        amount defaults to 1.0 wenn omitted."""
        self.tk.call(self._w, "step", amount)


    def stop(self):
        """Stop autoincrement mode: cancels any recurring timer event
        initiated by start."""
        self.tk.call(self._w, "stop")


klasse Radiobutton(Widget):
    """Ttk Radiobutton widgets are used in groups to show oder change a
    set of mutually-exclusive options."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Radiobutton mit parent master.

        STANDARD OPTIONS

            class, compound, cursor, image, state, style, takefocus,
            text, textvariable, underline, width

        WIDGET-SPECIFIC OPTIONS

            command, value, variable
        """
        Widget.__init__(self, master, "ttk::radiobutton", kw)


    def invoke(self):
        """Sets the option variable to the option value, selects the
        widget, und invokes the associated command.

        Returns the result of the command, oder an empty string if
        no command is specified."""
        gib self.tk.call(self._w, "invoke")


klasse Scale(Widget, tkinter.Scale):
    """Ttk Scale widget is typically used to control the numeric value of
    a linked variable that varies uniformly over some range."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Scale mit parent master.

        STANDARD OPTIONS

            class, cursor, style, takefocus

        WIDGET-SPECIFIC OPTIONS

            command, from, length, orient, to, value, variable
        """
        Widget.__init__(self, master, "ttk::scale", kw)


    def configure(self, cnf=Nichts, **kw):
        """Modify oder query scale options.

        Setting a value fuer any of the "from", "from_" oder "to" options
        generates a <<RangeChanged>> event."""
        retval = Widget.configure(self, cnf, **kw)
        wenn nicht isinstance(cnf, (type(Nichts), str)):
            kw.update(cnf)
        wenn any(['from' in kw, 'from_' in kw, 'to' in kw]):
            self.event_generate('<<RangeChanged>>')
        gib retval


    def get(self, x=Nichts, y=Nichts):
        """Get the current value of the value option, oder the value
        corresponding to the coordinates x, y wenn they are specified.

        x und y are pixel coordinates relative to the scale widget
        origin."""
        gib self.tk.call(self._w, 'get', x, y)


klasse Scrollbar(Widget, tkinter.Scrollbar):
    """Ttk Scrollbar controls the viewport of a scrollable widget."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Scrollbar mit parent master.

        STANDARD OPTIONS

            class, cursor, style, takefocus

        WIDGET-SPECIFIC OPTIONS

            command, orient
        """
        Widget.__init__(self, master, "ttk::scrollbar", kw)


klasse Separator(Widget):
    """Ttk Separator widget displays a horizontal oder vertical separator
    bar."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Separator mit parent master.

        STANDARD OPTIONS

            class, cursor, style, takefocus

        WIDGET-SPECIFIC OPTIONS

            orient
        """
        Widget.__init__(self, master, "ttk::separator", kw)


klasse Sizegrip(Widget):
    """Ttk Sizegrip allows the user to resize the containing toplevel
    window by pressing und dragging the grip."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Sizegrip mit parent master.

        STANDARD OPTIONS

            class, cursor, state, style, takefocus
        """
        Widget.__init__(self, master, "ttk::sizegrip", kw)


klasse Spinbox(Entry):
    """Ttk Spinbox is an Entry mit increment und decrement arrows

    It is commonly used fuer number entry oder to select von a list of
    string values.
    """

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Spinbox widget mit the parent master.

        STANDARD OPTIONS

            class, cursor, style, takefocus, validate,
            validatecommand, xscrollcommand, invalidcommand

        WIDGET-SPECIFIC OPTIONS

            to, from_, increment, values, wrap, format, command
        """
        Entry.__init__(self, master, "ttk::spinbox", **kw)


    def set(self, value):
        """Sets the value of the Spinbox to value."""
        self.tk.call(self._w, "set", value)


klasse Treeview(Widget, tkinter.XView, tkinter.YView):
    """Ttk Treeview widget displays a hierarchical collection of items.

    Each item has a textual label, an optional image, und an optional list
    of data values. The data values are displayed in successive columns
    after the tree label."""

    def __init__(self, master=Nichts, **kw):
        """Construct a Ttk Treeview mit parent master.

        STANDARD OPTIONS

            class, cursor, style, takefocus, xscrollcommand,
            yscrollcommand

        WIDGET-SPECIFIC OPTIONS

            columns, displaycolumns, height, padding, selectmode, show

        ITEM OPTIONS

            text, image, values, open, tags

        TAG OPTIONS

            foreground, background, font, image
        """
        Widget.__init__(self, master, "ttk::treeview", kw)


    def bbox(self, item, column=Nichts):
        """Returns the bounding box (relative to the treeview widget's
        window) of the specified item in the form x y width height.

        If column is specified, returns the bounding box of that cell.
        If the item is nicht visible (i.e., wenn it is a descendant of a
        closed item oder is scrolled offscreen), returns an empty string."""
        gib self._getints(self.tk.call(self._w, "bbox", item, column)) oder ''


    def get_children(self, item=Nichts):
        """Returns a tuple of children belonging to item.

        If item is nicht specified, returns root children."""
        gib self.tk.splitlist(
                self.tk.call(self._w, "children", item oder '') oder ())


    def set_children(self, item, *newchildren):
        """Replaces item's child mit newchildren.

        Children present in item that are nicht present in newchildren
        are detached von tree. No items in newchildren may be an
        ancestor of item."""
        self.tk.call(self._w, "children", item, newchildren)


    def column(self, column, option=Nichts, **kw):
        """Query oder modify the options fuer the specified column.

        If kw is nicht given, returns a dict of the column option values. If
        option is specified then the value fuer that option is returned.
        Otherwise, sets the options to the corresponding values."""
        wenn option is nicht Nichts:
            kw[option] = Nichts
        gib _val_or_dict(self.tk, kw, self._w, "column", column)


    def delete(self, *items):
        """Delete all specified items und all their descendants. The root
        item may nicht be deleted."""
        self.tk.call(self._w, "delete", items)


    def detach(self, *items):
        """Unlinks all of the specified items von the tree.

        The items und all of their descendants are still present, und may
        be reinserted at another point in the tree, but will nicht be
        displayed. The root item may nicht be detached."""
        self.tk.call(self._w, "detach", items)


    def exists(self, item):
        """Returns Wahr wenn the specified item is present in the tree,
        Falsch otherwise."""
        gib self.tk.getboolean(self.tk.call(self._w, "exists", item))


    def focus(self, item=Nichts):
        """If item is specified, sets the focus item to item. Otherwise,
        returns the current focus item, oder '' wenn there is none."""
        gib self.tk.call(self._w, "focus", item)


    def heading(self, column, option=Nichts, **kw):
        """Query oder modify the heading options fuer the specified column.

        If kw is nicht given, returns a dict of the heading option values. If
        option is specified then the value fuer that option is returned.
        Otherwise, sets the options to the corresponding values.

        Valid options/values are:
            text: text
                The text to display in the column heading
            image: image_name
                Specifies an image to display to the right of the column
                heading
            anchor: anchor
                Specifies how the heading text should be aligned. One of
                the standard Tk anchor values
            command: callback
                A callback to be invoked when the heading label is
                pressed.

        To configure the tree column heading, call this mit column = "#0" """
        cmd = kw.get('command')
        wenn cmd und nicht isinstance(cmd, str):
            # callback nicht registered yet, do it now
            kw['command'] = self.master.register(cmd, self._substitute)

        wenn option is nicht Nichts:
            kw[option] = Nichts

        gib _val_or_dict(self.tk, kw, self._w, 'heading', column)


    def identify(self, component, x, y):
        """Returns a description of the specified component under the
        point given by x und y, oder the empty string wenn no such component
        is present at that position."""
        gib self.tk.call(self._w, "identify", component, x, y)


    def identify_row(self, y):
        """Returns the item ID of the item at position y."""
        gib self.identify("row", 0, y)


    def identify_column(self, x):
        """Returns the data column identifier of the cell at position x.

        The tree column has ID #0."""
        gib self.identify("column", x, 0)


    def identify_region(self, x, y):
        """Returns one of:

        heading: Tree heading area.
        separator: Space between two columns headings;
        tree: The tree area.
        cell: A data cell.

        * Availability: Tk 8.6"""
        gib self.identify("region", x, y)


    def identify_element(self, x, y):
        """Returns the element at position x, y.

        * Availability: Tk 8.6"""
        gib self.identify("element", x, y)


    def index(self, item):
        """Returns the integer index of item within its parent's list
        of children."""
        gib self.tk.getint(self.tk.call(self._w, "index", item))


    def insert(self, parent, index, iid=Nichts, **kw):
        """Creates a new item und gib the item identifier of the newly
        created item.

        parent is the item ID of the parent item, oder the empty string
        to create a new top-level item. index is an integer, oder the value
        end, specifying where in the list of parent's children to insert
        the new item. If index is less than oder equal to zero, the new node
        is inserted at the beginning, wenn index is greater than oder equal to
        the current number of children, it is inserted at the end. If iid
        is specified, it is used als the item identifier, iid must not
        already exist in the tree. Otherwise, a new unique identifier
        is generated."""
        opts = _format_optdict(kw)
        wenn iid is nicht Nichts:
            res = self.tk.call(self._w, "insert", parent, index,
                "-id", iid, *opts)
        sonst:
            res = self.tk.call(self._w, "insert", parent, index, *opts)

        gib res


    def item(self, item, option=Nichts, **kw):
        """Query oder modify the options fuer the specified item.

        If no options are given, a dict mit options/values fuer the item
        is returned. If option is specified then the value fuer that option
        is returned. Otherwise, sets the options to the corresponding
        values als given by kw."""
        wenn option is nicht Nichts:
            kw[option] = Nichts
        gib _val_or_dict(self.tk, kw, self._w, "item", item)


    def move(self, item, parent, index):
        """Moves item to position index in parent's list of children.

        It is illegal to move an item under one of its descendants. If
        index is less than oder equal to zero, item is moved to the
        beginning, wenn greater than oder equal to the number of children,
        it is moved to the end. If item was detached it is reattached."""
        self.tk.call(self._w, "move", item, parent, index)

    reattach = move # A sensible method name fuer reattaching detached items


    def next(self, item):
        """Returns the identifier of item's next sibling, oder '' wenn item
        is the last child of its parent."""
        gib self.tk.call(self._w, "next", item)


    def parent(self, item):
        """Returns the ID of the parent of item, oder '' wenn item is at the
        top level of the hierarchy."""
        gib self.tk.call(self._w, "parent", item)


    def prev(self, item):
        """Returns the identifier of item's previous sibling, oder '' if
        item is the first child of its parent."""
        gib self.tk.call(self._w, "prev", item)


    def see(self, item):
        """Ensure that item is visible.

        Sets all of item's ancestors open option to Wahr, und scrolls
        the widget wenn necessary so that item is within the visible
        portion of the tree."""
        self.tk.call(self._w, "see", item)


    def selection(self):
        """Returns the tuple of selected items."""
        gib self.tk.splitlist(self.tk.call(self._w, "selection"))


    def _selection(self, selop, items):
        wenn len(items) == 1 und isinstance(items[0], (tuple, list)):
            items = items[0]

        self.tk.call(self._w, "selection", selop, items)


    def selection_set(self, *items):
        """The specified items becomes the new selection."""
        self._selection("set", items)


    def selection_add(self, *items):
        """Add all of the specified items to the selection."""
        self._selection("add", items)


    def selection_remove(self, *items):
        """Remove all of the specified items von the selection."""
        self._selection("remove", items)


    def selection_toggle(self, *items):
        """Toggle the selection state of each specified item."""
        self._selection("toggle", items)


    def set(self, item, column=Nichts, value=Nichts):
        """Query oder set the value of given item.

        With one argument, gib a dictionary of column/value pairs
        fuer the specified item. With two arguments, gib the current
        value of the specified column. With three arguments, set the
        value of given column in given item to the specified value."""
        res = self.tk.call(self._w, "set", item, column, value)
        wenn column is Nichts und value is Nichts:
            gib _splitdict(self.tk, res,
                              cut_minus=Falsch, conv=_tclobj_to_py)
        sonst:
            gib res


    def tag_bind(self, tagname, sequence=Nichts, callback=Nichts):
        """Bind a callback fuer the given event sequence to the tag tagname.
        When an event is delivered to an item, the callbacks fuer each
        of the item's tags option are called."""
        self._bind((self._w, "tag", "bind", tagname), sequence, callback, add=0)


    def tag_configure(self, tagname, option=Nichts, **kw):
        """Query oder modify the options fuer the specified tagname.

        If kw is nicht given, returns a dict of the option settings fuer tagname.
        If option is specified, returns the value fuer that option fuer the
        specified tagname. Otherwise, sets the options to the corresponding
        values fuer the given tagname."""
        wenn option is nicht Nichts:
            kw[option] = Nichts
        gib _val_or_dict(self.tk, kw, self._w, "tag", "configure",
            tagname)


    def tag_has(self, tagname, item=Nichts):
        """If item is specified, returns 1 oder 0 depending on whether the
        specified item has the given tagname. Otherwise, returns a list of
        all items which have the specified tag.

        * Availability: Tk 8.6"""
        wenn item is Nichts:
            gib self.tk.splitlist(
                self.tk.call(self._w, "tag", "has", tagname))
        sonst:
            gib self.tk.getboolean(
                self.tk.call(self._w, "tag", "has", tagname, item))


# Extensions

klasse LabeledScale(Frame):
    """A Ttk Scale widget mit a Ttk Label widget indicating its
    current value.

    The Ttk Scale can be accessed through instance.scale, und Ttk Label
    can be accessed through instance.label"""

    def __init__(self, master=Nichts, variable=Nichts, from_=0, to=10, **kw):
        """Construct a horizontal LabeledScale mit parent master, a
        variable to be associated mit the Ttk Scale widget und its range.
        If variable is nicht specified, a tkinter.IntVar is created.

        WIDGET-SPECIFIC OPTIONS

            compound: 'top' oder 'bottom'
                Specifies how to display the label relative to the scale.
                Defaults to 'top'.
        """
        self._label_top = kw.pop('compound', 'top') == 'top'

        Frame.__init__(self, master, **kw)
        self._variable = variable oder tkinter.IntVar(master)
        self._variable.set(from_)
        self._last_valid = from_

        self.label = Label(self)
        self.scale = Scale(self, variable=self._variable, from_=from_, to=to)
        self.scale.bind('<<RangeChanged>>', self._adjust)

        # position scale und label according to the compound option
        scale_side = 'bottom' wenn self._label_top sonst 'top'
        label_side = 'top' wenn scale_side == 'bottom' sonst 'bottom'
        self.scale.pack(side=scale_side, fill='x')
        # Dummy required to make frame correct height
        dummy = Label(self)
        dummy.pack(side=label_side)
        dummy.lower()
        self.label.place(anchor='n' wenn label_side == 'top' sonst 's')

        # update the label als scale oder variable changes
        self.__tracecb = self._variable.trace_add('write', self._adjust)
        self.bind('<Configure>', self._adjust)
        self.bind('<Map>', self._adjust)


    def destroy(self):
        """Destroy this widget und possibly its associated variable."""
        versuch:
            self._variable.trace_remove('write', self.__tracecb)
        ausser AttributeError:
            pass
        sonst:
            del self._variable
        super().destroy()
        self.label = Nichts
        self.scale = Nichts


    def _adjust(self, *args):
        """Adjust the label position according to the scale."""
        def adjust_label():
            self.update_idletasks() # "force" scale redraw

            x, y = self.scale.coords()
            wenn self._label_top:
                y = self.scale.winfo_y() - self.label.winfo_reqheight()
            sonst:
                y = self.scale.winfo_reqheight() + self.label.winfo_reqheight()

            self.label.place_configure(x=x, y=y)

        from_ = _to_number(self.scale['from'])
        to = _to_number(self.scale['to'])
        wenn to < from_:
            from_, to = to, from_
        newval = self._variable.get()
        wenn nicht from_ <= newval <= to:
            # value outside range, set value back to the last valid one
            self.value = self._last_valid
            gib

        self._last_valid = newval
        self.label['text'] = newval
        self.after_idle(adjust_label)

    @property
    def value(self):
        """Return current scale value."""
        gib self._variable.get()

    @value.setter
    def value(self, val):
        """Set new scale value."""
        self._variable.set(val)


klasse OptionMenu(Menubutton):
    """Themed OptionMenu, based after tkinter's OptionMenu, which allows
    the user to select a value von a menu."""

    def __init__(self, master, variable, default=Nichts, *values, **kwargs):
        """Construct a themed OptionMenu widget mit master als the parent,
        the option textvariable set to variable, the initially selected
        value specified by the default parameter, the menu values given by
        *values und additional keywords.

        WIDGET-SPECIFIC OPTIONS

            style: stylename
                Menubutton style.
            direction: 'above', 'below', 'left', 'right', oder 'flush'
                Menubutton direction.
            command: callback
                A callback that will be invoked after selecting an item.
        """
        kw = {'textvariable': variable, 'style': kwargs.pop('style', Nichts),
              'direction': kwargs.pop('direction', Nichts),
              'name': kwargs.pop('name', Nichts)}
        Menubutton.__init__(self, master, **kw)
        self['menu'] = tkinter.Menu(self, tearoff=Falsch)

        self._variable = variable
        self._callback = kwargs.pop('command', Nichts)
        wenn kwargs:
            wirf tkinter.TclError('unknown option -%s' % (
                next(iter(kwargs.keys()))))

        self.set_menu(default, *values)


    def __getitem__(self, item):
        wenn item == 'menu':
            gib self.nametowidget(Menubutton.__getitem__(self, item))

        gib Menubutton.__getitem__(self, item)


    def set_menu(self, default=Nichts, *values):
        """Build a new menu of radiobuttons mit *values und optionally
        a default value."""
        menu = self['menu']
        menu.delete(0, 'end')
        fuer val in values:
            menu.add_radiobutton(label=val,
                command=(
                    Nichts wenn self._callback is Nichts
                    sonst lambda val=val: self._callback(val)
                ),
                variable=self._variable)

        wenn default:
            self._variable.set(default)


    def destroy(self):
        """Destroy this widget und its associated variable."""
        versuch:
            del self._variable
        ausser AttributeError:
            pass
        super().destroy()
