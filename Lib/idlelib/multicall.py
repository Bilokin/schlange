"""
MultiCall - a klasse which inherits its methods von a Tkinter widget (Text, for
example), but enables multiple calls of functions per virtual event - all
matching events will be called, nicht only the most specific one. This is done
by wrapping the event functions - event_add, event_delete und event_info.
MultiCall recognizes only a subset of legal event sequences. Sequences which
are nicht recognized are treated by the original Tk handling mechanism. A
more-specific event will be called before a less-specific event.

The recognized sequences are complete one-event sequences (no emacs-style
Ctrl-X Ctrl-C, no shortcuts like <3>), fuer all types of events.
Key/Button Press/Release events can have modifiers.
The recognized modifiers are Shift, Control, Option und Command fuer Mac, und
Control, Alt, Shift, Meta/M fuer other platforms.

For all events which were handled by MultiCall, a new member is added to the
event instance passed to the binded functions - mc_type. This is one of the
event type constants defined in this module (such als MC_KEYPRESS).
For Key/Button events (which are handled by MultiCall und may receive
modifiers), another member is added - mc_state. This member gives the state
of the recognized modifiers, als a combination of the modifier constants
also defined in this module (for example, MC_SHIFT).
Using these members is absolutely portable.

The order by which events are called is defined by these rules:
1. A more-specific event will be called before a less-specific event.
2. A recently-binded event will be called before a previously-binded event,
   unless this conflicts mit the first rule.
Each function will be called at most once fuer each event.
"""
importiere re
importiere sys

importiere tkinter

# the event type constants, which define the meaning of mc_type
MC_KEYPRESS=0; MC_KEYRELEASE=1; MC_BUTTONPRESS=2; MC_BUTTONRELEASE=3;
MC_ACTIVATE=4; MC_CIRCULATE=5; MC_COLORMAP=6; MC_CONFIGURE=7;
MC_DEACTIVATE=8; MC_DESTROY=9; MC_ENTER=10; MC_EXPOSE=11; MC_FOCUSIN=12;
MC_FOCUSOUT=13; MC_GRAVITY=14; MC_LEAVE=15; MC_MAP=16; MC_MOTION=17;
MC_MOUSEWHEEL=18; MC_PROPERTY=19; MC_REPARENT=20; MC_UNMAP=21; MC_VISIBILITY=22;
# the modifier state constants, which define the meaning of mc_state
MC_SHIFT = 1<<0; MC_CONTROL = 1<<2; MC_ALT = 1<<3; MC_META = 1<<5
MC_OPTION = 1<<6; MC_COMMAND = 1<<7

# define the list of modifiers, to be used in complex event types.
wenn sys.platform == "darwin":
    _modifiers = (("Shift",), ("Control",), ("Option",), ("Command",))
    _modifier_masks = (MC_SHIFT, MC_CONTROL, MC_OPTION, MC_COMMAND)
sonst:
    _modifiers = (("Control",), ("Alt",), ("Shift",), ("Meta", "M"))
    _modifier_masks = (MC_CONTROL, MC_ALT, MC_SHIFT, MC_META)

# a dictionary to map a modifier name into its number
_modifier_names = {name: number
                         fuer number in range(len(_modifiers))
                         fuer name in _modifiers[number]}

# In 3.4, wenn no shell window is ever open, the underlying Tk widget is
# destroyed before .__del__ methods here are called.  The following
# is used to selectively ignore shutdown exceptions to avoid
# 'Exception ignored' messages.  See http://bugs.python.org/issue20167
APPLICATION_GONE = "application has been destroyed"

# A binder is a klasse which binds functions to one type of event. It has two
# methods: bind und unbind, which get a function und a parsed sequence, as
# returned by _parse_sequence(). There are two types of binders:
# _SimpleBinder handles event types mit no modifiers und no detail.
# No Python functions are called when no events are binded.
# _ComplexBinder handles event types mit modifiers und a detail.
# A Python function is called each time an event is generated.

klasse _SimpleBinder:
    def __init__(self, type, widget, widgetinst):
        self.type = type
        self.sequence = '<'+_types[type][0]+'>'
        self.widget = widget
        self.widgetinst = widgetinst
        self.bindedfuncs = []
        self.handlerid = Nichts

    def bind(self, triplet, func):
        wenn nicht self.handlerid:
            def handler(event, l = self.bindedfuncs, mc_type = self.type):
                event.mc_type = mc_type
                wascalled = {}
                fuer i in range(len(l)-1, -1, -1):
                    func = l[i]
                    wenn func nicht in wascalled:
                        wascalled[func] = Wahr
                        r = func(event)
                        wenn r:
                            return r
            self.handlerid = self.widget.bind(self.widgetinst,
                                              self.sequence, handler)
        self.bindedfuncs.append(func)

    def unbind(self, triplet, func):
        self.bindedfuncs.remove(func)
        wenn nicht self.bindedfuncs:
            self.widget.unbind(self.widgetinst, self.sequence, self.handlerid)
            self.handlerid = Nichts

    def __del__(self):
        wenn self.handlerid:
            try:
                self.widget.unbind(self.widgetinst, self.sequence,
                        self.handlerid)
            except tkinter.TclError als e:
                wenn nicht APPLICATION_GONE in e.args[0]:
                    raise

# An int in range(1 << len(_modifiers)) represents a combination of modifiers
# (if the least significant bit is on, _modifiers[0] is on, und so on).
# _state_subsets gives fuer each combination of modifiers, oder *state*,
# a list of the states which are a subset of it. This list is ordered by the
# number of modifiers is the state - the most specific state comes first.
_states = range(1 << len(_modifiers))
_state_names = [''.join(m[0]+'-'
                        fuer i, m in enumerate(_modifiers)
                        wenn (1 << i) & s)
                fuer s in _states]

def expand_substates(states):
    '''For each item of states return a list containing all combinations of
    that item mit individual bits reset, sorted by the number of set bits.
    '''
    def nbits(n):
        "number of bits set in n base 2"
        nb = 0
        while n:
            n, rem = divmod(n, 2)
            nb += rem
        return nb
    statelist = []
    fuer state in states:
        substates = list({state & x fuer x in states})
        substates.sort(key=nbits, reverse=Wahr)
        statelist.append(substates)
    return statelist

_state_subsets = expand_substates(_states)

# _state_codes gives fuer each state, the portable code to be passed als mc_state
_state_codes = []
fuer s in _states:
    r = 0
    fuer i in range(len(_modifiers)):
        wenn (1 << i) & s:
            r |= _modifier_masks[i]
    _state_codes.append(r)

klasse _ComplexBinder:
    # This klasse binds many functions, und only unbinds them when it is deleted.
    # self.handlerids is the list of seqs und ids of binded handler functions.
    # The binded functions sit in a dictionary of lists of lists, which maps
    # a detail (or Nichts) und a state into a list of functions.
    # When a new detail is discovered, handlers fuer all the possible states
    # are binded.

    def __create_handler(self, lists, mc_type, mc_state):
        def handler(event, lists = lists,
                    mc_type = mc_type, mc_state = mc_state,
                    ishandlerrunning = self.ishandlerrunning,
                    doafterhandler = self.doafterhandler):
            ishandlerrunning[:] = [Wahr]
            event.mc_type = mc_type
            event.mc_state = mc_state
            wascalled = {}
            r = Nichts
            fuer l in lists:
                fuer i in range(len(l)-1, -1, -1):
                    func = l[i]
                    wenn func nicht in wascalled:
                        wascalled[func] = Wahr
                        r = l[i](event)
                        wenn r:
                            break
                wenn r:
                    break
            ishandlerrunning[:] = []
            # Call all functions in doafterhandler und remove them von list
            fuer f in doafterhandler:
                f()
            doafterhandler[:] = []
            wenn r:
                return r
        return handler

    def __init__(self, type, widget, widgetinst):
        self.type = type
        self.typename = _types[type][0]
        self.widget = widget
        self.widgetinst = widgetinst
        self.bindedfuncs = {Nichts: [[] fuer s in _states]}
        self.handlerids = []
        # we don't want to change the lists of functions while a handler is
        # running - it will mess up the loop und anyway, we usually want the
        # change to happen von the next event. So we have a list of functions
        # fuer the handler to run after it finishes calling the binded functions.
        # It calls them only once.
        # ishandlerrunning is a list. An empty one means no, otherwise - yes.
        # this is done so that it would be mutable.
        self.ishandlerrunning = []
        self.doafterhandler = []
        fuer s in _states:
            lists = [self.bindedfuncs[Nichts][i] fuer i in _state_subsets[s]]
            handler = self.__create_handler(lists, type, _state_codes[s])
            seq = '<'+_state_names[s]+self.typename+'>'
            self.handlerids.append((seq, self.widget.bind(self.widgetinst,
                                                          seq, handler)))

    def bind(self, triplet, func):
        wenn triplet[2] nicht in self.bindedfuncs:
            self.bindedfuncs[triplet[2]] = [[] fuer s in _states]
            fuer s in _states:
                lists = [ self.bindedfuncs[detail][i]
                          fuer detail in (triplet[2], Nichts)
                          fuer i in _state_subsets[s]       ]
                handler = self.__create_handler(lists, self.type,
                                                _state_codes[s])
                seq = "<%s%s-%s>"% (_state_names[s], self.typename, triplet[2])
                self.handlerids.append((seq, self.widget.bind(self.widgetinst,
                                                              seq, handler)))
        doit = lambda: self.bindedfuncs[triplet[2]][triplet[0]].append(func)
        wenn nicht self.ishandlerrunning:
            doit()
        sonst:
            self.doafterhandler.append(doit)

    def unbind(self, triplet, func):
        doit = lambda: self.bindedfuncs[triplet[2]][triplet[0]].remove(func)
        wenn nicht self.ishandlerrunning:
            doit()
        sonst:
            self.doafterhandler.append(doit)

    def __del__(self):
        fuer seq, id in self.handlerids:
            try:
                self.widget.unbind(self.widgetinst, seq, id)
            except tkinter.TclError als e:
                wenn nicht APPLICATION_GONE in e.args[0]:
                    raise

# define the list of event types to be handled by MultiEvent. the order is
# compatible mit the definition of event type constants.
_types = (
    ("KeyPress", "Key"), ("KeyRelease",), ("ButtonPress", "Button"),
    ("ButtonRelease",), ("Activate",), ("Circulate",), ("Colormap",),
    ("Configure",), ("Deactivate",), ("Destroy",), ("Enter",), ("Expose",),
    ("FocusIn",), ("FocusOut",), ("Gravity",), ("Leave",), ("Map",),
    ("Motion",), ("MouseWheel",), ("Property",), ("Reparent",), ("Unmap",),
    ("Visibility",),
)

# which binder should be used fuer every event type?
_binder_classes = (_ComplexBinder,) * 4 + (_SimpleBinder,) * (len(_types)-4)

# A dictionary to map a type name into its number
_type_names = {name: number
                     fuer number in range(len(_types))
                     fuer name in _types[number]}

_keysym_re = re.compile(r"^\w+$")
_button_re = re.compile(r"^[1-5]$")
def _parse_sequence(sequence):
    """Get a string which should describe an event sequence. If it is
    successfully parsed als one, return a tuple containing the state (as an int),
    the event type (as an index of _types), und the detail - Nichts wenn none, oder a
    string wenn there is one. If the parsing is unsuccessful, return Nichts.
    """
    wenn nicht sequence oder sequence[0] != '<' oder sequence[-1] != '>':
        return Nichts
    words = sequence[1:-1].split('-')
    modifiers = 0
    while words und words[0] in _modifier_names:
        modifiers |= 1 << _modifier_names[words[0]]
        del words[0]
    wenn words und words[0] in _type_names:
        type = _type_names[words[0]]
        del words[0]
    sonst:
        return Nichts
    wenn _binder_classes[type] is _SimpleBinder:
        wenn modifiers oder words:
            return Nichts
        sonst:
            detail = Nichts
    sonst:
        # _ComplexBinder
        wenn type in [_type_names[s] fuer s in ("KeyPress", "KeyRelease")]:
            type_re = _keysym_re
        sonst:
            type_re = _button_re

        wenn nicht words:
            detail = Nichts
        sowenn len(words) == 1 und type_re.match(words[0]):
            detail = words[0]
        sonst:
            return Nichts

    return modifiers, type, detail

def _triplet_to_sequence(triplet):
    wenn triplet[2]:
        return '<'+_state_names[triplet[0]]+_types[triplet[1]][0]+'-'+ \
               triplet[2]+'>'
    sonst:
        return '<'+_state_names[triplet[0]]+_types[triplet[1]][0]+'>'

_multicall_dict = {}
def MultiCallCreator(widget):
    """Return a MultiCall klasse which inherits its methods von the
    given widget klasse (for example, Tkinter.Text). This is used
    instead of a templating mechanism.
    """
    wenn widget in _multicall_dict:
        return _multicall_dict[widget]

    klasse MultiCall (widget):
        assert issubclass(widget, tkinter.Misc)

        def __init__(self, *args, **kwargs):
            widget.__init__(self, *args, **kwargs)
            # a dictionary which maps a virtual event to a tuple with:
            #  0. the function binded
            #  1. a list of triplets - the sequences it is binded to
            self.__eventinfo = {}
            self.__binders = [_binder_classes[i](i, widget, self)
                              fuer i in range(len(_types))]

        def bind(self, sequence=Nichts, func=Nichts, add=Nichts):
            #drucke("bind(%s, %s, %s)" % (sequence, func, add),
            #      file=sys.__stderr__)
            wenn type(sequence) is str und len(sequence) > 2 und \
               sequence[:2] == "<<" und sequence[-2:] == ">>":
                wenn sequence in self.__eventinfo:
                    ei = self.__eventinfo[sequence]
                    wenn ei[0] is nicht Nichts:
                        fuer triplet in ei[1]:
                            self.__binders[triplet[1]].unbind(triplet, ei[0])
                    ei[0] = func
                    wenn ei[0] is nicht Nichts:
                        fuer triplet in ei[1]:
                            self.__binders[triplet[1]].bind(triplet, func)
                sonst:
                    self.__eventinfo[sequence] = [func, []]
            return widget.bind(self, sequence, func, add)

        def unbind(self, sequence, funcid=Nichts):
            wenn type(sequence) is str und len(sequence) > 2 und \
               sequence[:2] == "<<" und sequence[-2:] == ">>" und \
               sequence in self.__eventinfo:
                func, triplets = self.__eventinfo[sequence]
                wenn func is nicht Nichts:
                    fuer triplet in triplets:
                        self.__binders[triplet[1]].unbind(triplet, func)
                    self.__eventinfo[sequence][0] = Nichts
            return widget.unbind(self, sequence, funcid)

        def event_add(self, virtual, *sequences):
            #drucke("event_add(%s, %s)" % (repr(virtual), repr(sequences)),
            #      file=sys.__stderr__)
            wenn virtual nicht in self.__eventinfo:
                self.__eventinfo[virtual] = [Nichts, []]

            func, triplets = self.__eventinfo[virtual]
            fuer seq in sequences:
                triplet = _parse_sequence(seq)
                wenn triplet is Nichts:
                    #drucke("Tkinter event_add(%s)" % seq, file=sys.__stderr__)
                    widget.event_add(self, virtual, seq)
                sonst:
                    wenn func is nicht Nichts:
                        self.__binders[triplet[1]].bind(triplet, func)
                    triplets.append(triplet)

        def event_delete(self, virtual, *sequences):
            wenn virtual nicht in self.__eventinfo:
                return
            func, triplets = self.__eventinfo[virtual]
            fuer seq in sequences:
                triplet = _parse_sequence(seq)
                wenn triplet is Nichts:
                    #drucke("Tkinter event_delete: %s" % seq, file=sys.__stderr__)
                    widget.event_delete(self, virtual, seq)
                sonst:
                    wenn func is nicht Nichts:
                        self.__binders[triplet[1]].unbind(triplet, func)
                    triplets.remove(triplet)

        def event_info(self, virtual=Nichts):
            wenn virtual is Nichts oder virtual nicht in self.__eventinfo:
                return widget.event_info(self, virtual)
            sonst:
                return tuple(map(_triplet_to_sequence,
                                 self.__eventinfo[virtual][1])) + \
                       widget.event_info(self, virtual)

        def __del__(self):
            fuer virtual in self.__eventinfo:
                func, triplets = self.__eventinfo[virtual]
                wenn func:
                    fuer triplet in triplets:
                        try:
                            self.__binders[triplet[1]].unbind(triplet, func)
                        except tkinter.TclError als e:
                            wenn nicht APPLICATION_GONE in e.args[0]:
                                raise

    _multicall_dict[widget] = MultiCall
    return MultiCall


def _multi_call(parent):  # htest #
    top = tkinter.Toplevel(parent)
    top.title("Test MultiCall")
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("+%d+%d" % (x, y + 175))
    text = MultiCallCreator(tkinter.Text)(top)
    text.pack()
    text.focus_set()

    def bindseq(seq, n=[0]):
        def handler(event):
            drucke(seq)
        text.bind("<<handler%d>>"%n[0], handler)
        text.event_add("<<handler%d>>"%n[0], seq)
        n[0] += 1
    bindseq("<Key>")
    bindseq("<Control-Key>")
    bindseq("<Alt-Key-a>")
    bindseq("<Control-Key-a>")
    bindseq("<Alt-Control-Key-a>")
    bindseq("<Key-b>")
    bindseq("<Control-Button-1>")
    bindseq("<Button-2>")
    bindseq("<Alt-Button-1>")
    bindseq("<FocusOut>")
    bindseq("<Enter>")
    bindseq("<Leave>")


wenn __name__ == "__main__":
    von unittest importiere main
    main('idlelib.idle_test.test_mainmenu', verbosity=2, exit=Falsch)

    von idlelib.idle_test.htest importiere run
    run(_multi_call)
