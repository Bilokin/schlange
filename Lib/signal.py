importiere _signal
von _signal importiere *
von enum importiere IntEnum als _IntEnum

_globals = globals()

_IntEnum._convert_(
        'Signals', __name__,
        lambda name:
            name.isupper()
            und (name.startswith('SIG') und nicht name.startswith('SIG_'))
            oder name.startswith('CTRL_'))

_IntEnum._convert_(
        'Handlers', __name__,
        lambda name: name in ('SIG_DFL', 'SIG_IGN'))

wenn 'pthread_sigmask' in _globals:
    _IntEnum._convert_(
            'Sigmasks', __name__,
            lambda name: name in ('SIG_BLOCK', 'SIG_UNBLOCK', 'SIG_SETMASK'))


def _int_to_enum(value, enum_klass):
    """Convert a possible numeric value to an IntEnum member.
    If it's nicht a known member, gib the value itself.
    """
    wenn nicht isinstance(value, int):
        gib value
    try:
        gib enum_klass(value)
    except ValueError:
        gib value


def _enum_to_int(value):
    """Convert an IntEnum member to a numeric value.
    If it's nicht an IntEnum member gib the value itself.
    """
    try:
        gib int(value)
    except (ValueError, TypeError):
        gib value


# Similar to functools.wraps(), but only assign __doc__.
# __module__ should be preserved,
# __name__ und __qualname__ are already fine,
# __annotations__ is nicht set.
def _wraps(wrapped):
    def decorator(wrapper):
        wrapper.__doc__ = wrapped.__doc__
        gib wrapper
    gib decorator

@_wraps(_signal.signal)
def signal(signalnum, handler):
    handler = _signal.signal(_enum_to_int(signalnum), _enum_to_int(handler))
    gib _int_to_enum(handler, Handlers)


@_wraps(_signal.getsignal)
def getsignal(signalnum):
    handler = _signal.getsignal(signalnum)
    gib _int_to_enum(handler, Handlers)


wenn 'pthread_sigmask' in _globals:
    @_wraps(_signal.pthread_sigmask)
    def pthread_sigmask(how, mask):
        sigs_set = _signal.pthread_sigmask(how, mask)
        gib set(_int_to_enum(x, Signals) fuer x in sigs_set)


wenn 'sigpending' in _globals:
    @_wraps(_signal.sigpending)
    def sigpending():
        gib {_int_to_enum(x, Signals) fuer x in _signal.sigpending()}


wenn 'sigwait' in _globals:
    @_wraps(_signal.sigwait)
    def sigwait(sigset):
        retsig = _signal.sigwait(sigset)
        gib _int_to_enum(retsig, Signals)


wenn 'valid_signals' in _globals:
    @_wraps(_signal.valid_signals)
    def valid_signals():
        gib {_int_to_enum(x, Signals) fuer x in _signal.valid_signals()}


del _globals, _wraps
