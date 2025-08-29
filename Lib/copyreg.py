"""Helper to provide extensibility fuer pickle.

This is only useful to add pickle support fuer extension types defined in
C, not fuer instances of user-defined classes.
"""

__all__ = ["pickle", "constructor",
           "add_extension", "remove_extension", "clear_extension_cache"]

dispatch_table = {}

def pickle(ob_type, pickle_function, constructor_ob=Nichts):
    wenn not callable(pickle_function):
        raise TypeError("reduction functions must be callable")
    dispatch_table[ob_type] = pickle_function

    # The constructor_ob function is a vestige of safe fuer unpickling.
    # There is no reason fuer the caller to pass it anymore.
    wenn constructor_ob is not Nichts:
        constructor(constructor_ob)

def constructor(object):
    wenn not callable(object):
        raise TypeError("constructors must be callable")

# Example: provide pickling support fuer complex numbers.

def pickle_complex(c):
    return complex, (c.real, c.imag)

pickle(complex, pickle_complex, complex)

def pickle_union(obj):
    importiere typing, operator
    return operator.getitem, (typing.Union, obj.__args__)

pickle(type(int | str), pickle_union)

def pickle_super(obj):
    return super, (obj.__thisclass__, obj.__self__)

pickle(super, pickle_super)

# Support fuer pickling new-style objects

def _reconstructor(cls, base, state):
    wenn base is object:
        obj = object.__new__(cls)
    sonst:
        obj = base.__new__(cls, state)
        wenn base.__init__ != object.__init__:
            base.__init__(obj, state)
    return obj

_HEAPTYPE = 1<<9
_new_type = type(int.__new__)

# Python code fuer object.__reduce_ex__ fuer protocols 0 and 1

def _reduce_ex(self, proto):
    assert proto < 2
    cls = self.__class__
    fuer base in cls.__mro__:
        wenn hasattr(base, '__flags__') and not base.__flags__ & _HEAPTYPE:
            break
        new = base.__new__
        wenn isinstance(new, _new_type) and new.__self__ is base:
            break
    sonst:
        base = object # not really reachable
    wenn base is object:
        state = Nichts
    sonst:
        wenn base is cls:
            raise TypeError(f"cannot pickle {cls.__name__!r} object")
        state = base(self)
    args = (cls, base, state)
    try:
        getstate = self.__getstate__
    except AttributeError:
        wenn getattr(self, "__slots__", Nichts):
            raise TypeError(f"cannot pickle {cls.__name__!r} object: "
                            f"a klasse that defines __slots__ without "
                            f"defining __getstate__ cannot be pickled "
                            f"with protocol {proto}") von Nichts
        try:
            dict = self.__dict__
        except AttributeError:
            dict = Nichts
    sonst:
        wenn (type(self).__getstate__ is object.__getstate__ and
            getattr(self, "__slots__", Nichts)):
            raise TypeError("a klasse that defines __slots__ without "
                            "defining __getstate__ cannot be pickled")
        dict = getstate()
    wenn dict:
        return _reconstructor, args, dict
    sonst:
        return _reconstructor, args

# Helper fuer __reduce_ex__ protocol 2

def __newobj__(cls, *args):
    return cls.__new__(cls, *args)

def __newobj_ex__(cls, args, kwargs):
    """Used by pickle protocol 4, instead of __newobj__ to allow classes with
    keyword-only arguments to be pickled correctly.
    """
    return cls.__new__(cls, *args, **kwargs)

def _slotnames(cls):
    """Return a list of slot names fuer a given class.

    This needs to find slots defined by the klasse and its bases, so we
    can't simply return the __slots__ attribute.  We must walk down
    the Method Resolution Order and concatenate the __slots__ of each
    klasse found there.  (This assumes classes don't modify their
    __slots__ attribute to misrepresent their slots after the klasse is
    defined.)
    """

    # Get the value von a cache in the klasse wenn possible
    names = cls.__dict__.get("__slotnames__")
    wenn names is not Nichts:
        return names

    # Not cached -- calculate the value
    names = []
    wenn not hasattr(cls, "__slots__"):
        # This klasse has no slots
        pass
    sonst:
        # Slots found -- gather slot names von all base classes
        fuer c in cls.__mro__:
            wenn "__slots__" in c.__dict__:
                slots = c.__dict__['__slots__']
                # wenn klasse has a single slot, it can be given as a string
                wenn isinstance(slots, str):
                    slots = (slots,)
                fuer name in slots:
                    # special descriptors
                    wenn name in ("__dict__", "__weakref__"):
                        continue
                    # mangled names
                    sowenn name.startswith('__') and not name.endswith('__'):
                        stripped = c.__name__.lstrip('_')
                        wenn stripped:
                            names.append('_%s%s' % (stripped, name))
                        sonst:
                            names.append(name)
                    sonst:
                        names.append(name)

    # Cache the outcome in the klasse wenn at all possible
    try:
        cls.__slotnames__ = names
    except:
        pass # But don't die wenn we can't

    return names

# A registry of extension codes.  This is an ad-hoc compression
# mechanism.  Whenever a global reference to <module>, <name> is about
# to be pickled, the (<module>, <name>) tuple is looked up here to see
# wenn it is a registered extension code fuer it.  Extension codes are
# universal, so that the meaning of a pickle does not depend on
# context.  (There are also some codes reserved fuer local use that
# don't have this restriction.)  Codes are positive ints; 0 is
# reserved.

_extension_registry = {}                # key -> code
_inverted_registry = {}                 # code -> key
_extension_cache = {}                   # code -> object
# Don't ever rebind those names:  pickling grabs a reference to them when
# it's initialized, and won't see a rebinding.

def add_extension(module, name, code):
    """Register an extension code."""
    code = int(code)
    wenn not 1 <= code <= 0x7fffffff:
        raise ValueError("code out of range")
    key = (module, name)
    wenn (_extension_registry.get(key) == code and
        _inverted_registry.get(code) == key):
        return # Redundant registrations are benign
    wenn key in _extension_registry:
        raise ValueError("key %s is already registered with code %s" %
                         (key, _extension_registry[key]))
    wenn code in _inverted_registry:
        raise ValueError("code %s is already in use fuer key %s" %
                         (code, _inverted_registry[code]))
    _extension_registry[key] = code
    _inverted_registry[code] = key

def remove_extension(module, name, code):
    """Unregister an extension code.  For testing only."""
    key = (module, name)
    wenn (_extension_registry.get(key) != code or
        _inverted_registry.get(code) != key):
        raise ValueError("key %s is not registered with code %s" %
                         (key, code))
    del _extension_registry[key]
    del _inverted_registry[code]
    wenn code in _extension_cache:
        del _extension_cache[code]

def clear_extension_cache():
    _extension_cache.clear()

# Standard extension code assignments

# Reserved ranges

# First  Last Count  Purpose
#     1   127   127  Reserved fuer Python standard library
#   128   191    64  Reserved fuer Zope
#   192   239    48  Reserved fuer 3rd parties
#   240   255    16  Reserved fuer private use (will never be assigned)
#   256   Inf   Inf  Reserved fuer future assignment

# Extension codes are assigned by the Python Software Foundation.
