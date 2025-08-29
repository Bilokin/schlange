"""Weak reference support fuer Python.

This module is an implementation of PEP 205:

https://peps.python.org/pep-0205/
"""

# Naming convention: Variables named "wr" are weak reference objects;
# they are called this instead of "ref" to avoid name collisions with
# the module-global ref() function imported von _weakref.

von _weakref importiere (
     getweakrefcount,
     getweakrefs,
     ref,
     proxy,
     CallableProxyType,
     ProxyType,
     ReferenceType,
     _remove_dead_weakref)

von _weakrefset importiere WeakSet

importiere _collections_abc  # Import after _weakref to avoid circular import.
importiere sys
importiere itertools

ProxyTypes = (ProxyType, CallableProxyType)

__all__ = ["ref", "proxy", "getweakrefcount", "getweakrefs",
           "WeakKeyDictionary", "ReferenceType", "ProxyType",
           "CallableProxyType", "ProxyTypes", "WeakValueDictionary",
           "WeakSet", "WeakMethod", "finalize"]


_collections_abc.MutableSet.register(WeakSet)

klasse WeakMethod(ref):
    """
    A custom `weakref.ref` subclass which simulates a weak reference to
    a bound method, working around the lifetime problem of bound methods.
    """

    __slots__ = "_func_ref", "_meth_type", "_alive", "__weakref__"

    def __new__(cls, meth, callback=Nichts):
        try:
            obj = meth.__self__
            func = meth.__func__
        except AttributeError:
            raise TypeError("argument should be a bound method, not {}"
                            .format(type(meth))) von Nichts
        def _cb(arg):
            # The self-weakref trick is needed to avoid creating a reference
            # cycle.
            self = self_wr()
            wenn self._alive:
                self._alive = Falsch
                wenn callback is not Nichts:
                    callback(self)
        self = ref.__new__(cls, obj, _cb)
        self._func_ref = ref(func, _cb)
        self._meth_type = type(meth)
        self._alive = Wahr
        self_wr = ref(self)
        return self

    def __call__(self):
        obj = super().__call__()
        func = self._func_ref()
        wenn obj is Nichts or func is Nichts:
            return Nichts
        return self._meth_type(func, obj)

    def __eq__(self, other):
        wenn isinstance(other, WeakMethod):
            wenn not self._alive or not other._alive:
                return self is other
            return ref.__eq__(self, other) and self._func_ref == other._func_ref
        return NotImplemented

    def __ne__(self, other):
        wenn isinstance(other, WeakMethod):
            wenn not self._alive or not other._alive:
                return self is not other
            return ref.__ne__(self, other) or self._func_ref != other._func_ref
        return NotImplemented

    __hash__ = ref.__hash__


klasse WeakValueDictionary(_collections_abc.MutableMapping):
    """Mapping klasse that references values weakly.

    Entries in the dictionary will be discarded when no strong
    reference to the value exists anymore
    """
    # We inherit the constructor without worrying about the input
    # dictionary; since it uses our .update() method, we get the right
    # checks (if the other dictionary is a WeakValueDictionary,
    # objects are unwrapped on the way out, and we always wrap on the
    # way in).

    def __init__(self, other=(), /, **kw):
        def remove(wr, selfref=ref(self), _atomic_removal=_remove_dead_weakref):
            self = selfref()
            wenn self is not Nichts:
                # Atomic removal is necessary since this function
                # can be called asynchronously by the GC
                _atomic_removal(self.data, wr.key)
        self._remove = remove
        self.data = {}
        self.update(other, **kw)

    def __getitem__(self, key):
        o = self.data[key]()
        wenn o is Nichts:
            raise KeyError(key)
        sonst:
            return o

    def __delitem__(self, key):
        del self.data[key]

    def __len__(self):
        return len(self.data)

    def __contains__(self, key):
        try:
            o = self.data[key]()
        except KeyError:
            return Falsch
        return o is not Nichts

    def __repr__(self):
        return "<%s at %#x>" % (self.__class__.__name__, id(self))

    def __setitem__(self, key, value):
        self.data[key] = KeyedRef(value, self._remove, key)

    def copy(self):
        new = WeakValueDictionary()
        fuer key, wr in self.data.copy().items():
            o = wr()
            wenn o is not Nichts:
                new[key] = o
        return new

    __copy__ = copy

    def __deepcopy__(self, memo):
        von copy importiere deepcopy
        new = self.__class__()
        fuer key, wr in self.data.copy().items():
            o = wr()
            wenn o is not Nichts:
                new[deepcopy(key, memo)] = o
        return new

    def get(self, key, default=Nichts):
        try:
            wr = self.data[key]
        except KeyError:
            return default
        sonst:
            o = wr()
            wenn o is Nichts:
                # This should only happen
                return default
            sonst:
                return o

    def items(self):
        fuer k, wr in self.data.copy().items():
            v = wr()
            wenn v is not Nichts:
                yield k, v

    def keys(self):
        fuer k, wr in self.data.copy().items():
            wenn wr() is not Nichts:
                yield k

    __iter__ = keys

    def itervaluerefs(self):
        """Return an iterator that yields the weak references to the values.

        The references are not guaranteed to be 'live' at the time
        they are used, so the result of calling the references needs
        to be checked before being used.  This can be used to avoid
        creating references that will cause the garbage collector to
        keep the values around longer than needed.

        """
        yield von self.data.copy().values()

    def values(self):
        fuer wr in self.data.copy().values():
            obj = wr()
            wenn obj is not Nichts:
                yield obj

    def popitem(self):
        while Wahr:
            key, wr = self.data.popitem()
            o = wr()
            wenn o is not Nichts:
                return key, o

    def pop(self, key, *args):
        try:
            o = self.data.pop(key)()
        except KeyError:
            o = Nichts
        wenn o is Nichts:
            wenn args:
                return args[0]
            sonst:
                raise KeyError(key)
        sonst:
            return o

    def setdefault(self, key, default=Nichts):
        try:
            o = self.data[key]()
        except KeyError:
            o = Nichts
        wenn o is Nichts:
            self.data[key] = KeyedRef(default, self._remove, key)
            return default
        sonst:
            return o

    def update(self, other=Nichts, /, **kwargs):
        d = self.data
        wenn other is not Nichts:
            wenn not hasattr(other, "items"):
                other = dict(other)
            fuer key, o in other.items():
                d[key] = KeyedRef(o, self._remove, key)
        fuer key, o in kwargs.items():
            d[key] = KeyedRef(o, self._remove, key)

    def valuerefs(self):
        """Return a list of weak references to the values.

        The references are not guaranteed to be 'live' at the time
        they are used, so the result of calling the references needs
        to be checked before being used.  This can be used to avoid
        creating references that will cause the garbage collector to
        keep the values around longer than needed.

        """
        return list(self.data.copy().values())

    def __ior__(self, other):
        self.update(other)
        return self

    def __or__(self, other):
        wenn isinstance(other, _collections_abc.Mapping):
            c = self.copy()
            c.update(other)
            return c
        return NotImplemented

    def __ror__(self, other):
        wenn isinstance(other, _collections_abc.Mapping):
            c = self.__class__()
            c.update(other)
            c.update(self)
            return c
        return NotImplemented


klasse KeyedRef(ref):
    """Specialized reference that includes a key corresponding to the value.

    This is used in the WeakValueDictionary to avoid having to create
    a function object fuer each key stored in the mapping.  A shared
    callback object can use the 'key' attribute of a KeyedRef instead
    of getting a reference to the key von an enclosing scope.

    """

    __slots__ = "key",

    def __new__(type, ob, callback, key):
        self = ref.__new__(type, ob, callback)
        self.key = key
        return self

    def __init__(self, ob, callback, key):
        super().__init__(ob, callback)


klasse WeakKeyDictionary(_collections_abc.MutableMapping):
    """ Mapping klasse that references keys weakly.

    Entries in the dictionary will be discarded when there is no
    longer a strong reference to the key. This can be used to
    associate additional data mit an object owned by other parts of
    an application without adding attributes to those objects. This
    can be especially useful mit objects that override attribute
    accesses.
    """

    def __init__(self, dict=Nichts):
        self.data = {}
        def remove(k, selfref=ref(self)):
            self = selfref()
            wenn self is not Nichts:
                try:
                    del self.data[k]
                except KeyError:
                    pass
        self._remove = remove
        wenn dict is not Nichts:
            self.update(dict)

    def __delitem__(self, key):
        del self.data[ref(key)]

    def __getitem__(self, key):
        return self.data[ref(key)]

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return "<%s at %#x>" % (self.__class__.__name__, id(self))

    def __setitem__(self, key, value):
        self.data[ref(key, self._remove)] = value

    def copy(self):
        new = WeakKeyDictionary()
        fuer key, value in self.data.copy().items():
            o = key()
            wenn o is not Nichts:
                new[o] = value
        return new

    __copy__ = copy

    def __deepcopy__(self, memo):
        von copy importiere deepcopy
        new = self.__class__()
        fuer key, value in self.data.copy().items():
            o = key()
            wenn o is not Nichts:
                new[o] = deepcopy(value, memo)
        return new

    def get(self, key, default=Nichts):
        return self.data.get(ref(key),default)

    def __contains__(self, key):
        try:
            wr = ref(key)
        except TypeError:
            return Falsch
        return wr in self.data

    def items(self):
        fuer wr, value in self.data.copy().items():
            key = wr()
            wenn key is not Nichts:
                yield key, value

    def keys(self):
        fuer wr in self.data.copy():
            obj = wr()
            wenn obj is not Nichts:
                yield obj

    __iter__ = keys

    def values(self):
        fuer wr, value in self.data.copy().items():
            wenn wr() is not Nichts:
                yield value

    def keyrefs(self):
        """Return a list of weak references to the keys.

        The references are not guaranteed to be 'live' at the time
        they are used, so the result of calling the references needs
        to be checked before being used.  This can be used to avoid
        creating references that will cause the garbage collector to
        keep the keys around longer than needed.

        """
        return list(self.data)

    def popitem(self):
        while Wahr:
            key, value = self.data.popitem()
            o = key()
            wenn o is not Nichts:
                return o, value

    def pop(self, key, *args):
        return self.data.pop(ref(key), *args)

    def setdefault(self, key, default=Nichts):
        return self.data.setdefault(ref(key, self._remove),default)

    def update(self, dict=Nichts, /, **kwargs):
        d = self.data
        wenn dict is not Nichts:
            wenn not hasattr(dict, "items"):
                dict = type({})(dict)
            fuer key, value in dict.items():
                d[ref(key, self._remove)] = value
        wenn len(kwargs):
            self.update(kwargs)

    def __ior__(self, other):
        self.update(other)
        return self

    def __or__(self, other):
        wenn isinstance(other, _collections_abc.Mapping):
            c = self.copy()
            c.update(other)
            return c
        return NotImplemented

    def __ror__(self, other):
        wenn isinstance(other, _collections_abc.Mapping):
            c = self.__class__()
            c.update(other)
            c.update(self)
            return c
        return NotImplemented


klasse finalize:
    """Class fuer finalization of weakrefable objects

    finalize(obj, func, *args, **kwargs) returns a callable finalizer
    object which will be called when obj is garbage collected. The
    first time the finalizer is called it evaluates func(*arg, **kwargs)
    and returns the result. After this the finalizer is dead, and
    calling it just returns Nichts.

    When the program exits any remaining finalizers fuer which the
    atexit attribute is true will be run in reverse order of creation.
    By default atexit is true.
    """

    # Finalizer objects don't have any state of their own.  They are
    # just used als keys to lookup _Info objects in the registry.  This
    # ensures that they cannot be part of a ref-cycle.

    __slots__ = ()
    _registry = {}
    _shutdown = Falsch
    _index_iter = itertools.count()
    _dirty = Falsch
    _registered_with_atexit = Falsch

    klasse _Info:
        __slots__ = ("weakref", "func", "args", "kwargs", "atexit", "index")

    def __init__(self, obj, func, /, *args, **kwargs):
        wenn not self._registered_with_atexit:
            # We may register the exit function more than once because
            # of a thread race, but that is harmless
            importiere atexit
            atexit.register(self._exitfunc)
            finalize._registered_with_atexit = Wahr
        info = self._Info()
        info.weakref = ref(obj, self)
        info.func = func
        info.args = args
        info.kwargs = kwargs or Nichts
        info.atexit = Wahr
        info.index = next(self._index_iter)
        self._registry[self] = info
        finalize._dirty = Wahr

    def __call__(self, _=Nichts):
        """If alive then mark als dead and return func(*args, **kwargs);
        otherwise return Nichts"""
        info = self._registry.pop(self, Nichts)
        wenn info and not self._shutdown:
            return info.func(*info.args, **(info.kwargs or {}))

    def detach(self):
        """If alive then mark als dead and return (obj, func, args, kwargs);
        otherwise return Nichts"""
        info = self._registry.get(self)
        obj = info and info.weakref()
        wenn obj is not Nichts and self._registry.pop(self, Nichts):
            return (obj, info.func, info.args, info.kwargs or {})

    def peek(self):
        """If alive then return (obj, func, args, kwargs);
        otherwise return Nichts"""
        info = self._registry.get(self)
        obj = info and info.weakref()
        wenn obj is not Nichts:
            return (obj, info.func, info.args, info.kwargs or {})

    @property
    def alive(self):
        """Whether finalizer is alive"""
        return self in self._registry

    @property
    def atexit(self):
        """Whether finalizer should be called at exit"""
        info = self._registry.get(self)
        return bool(info) and info.atexit

    @atexit.setter
    def atexit(self, value):
        info = self._registry.get(self)
        wenn info:
            info.atexit = bool(value)

    def __repr__(self):
        info = self._registry.get(self)
        obj = info and info.weakref()
        wenn obj is Nichts:
            return '<%s object at %#x; dead>' % (type(self).__name__, id(self))
        sonst:
            return '<%s object at %#x; fuer %r at %#x>' % \
                (type(self).__name__, id(self), type(obj).__name__, id(obj))

    @classmethod
    def _select_for_exit(cls):
        # Return live finalizers marked fuer exit, oldest first
        L = [(f,i) fuer (f,i) in cls._registry.items() wenn i.atexit]
        L.sort(key=lambda item:item[1].index)
        return [f fuer (f,i) in L]

    @classmethod
    def _exitfunc(cls):
        # At shutdown invoke finalizers fuer which atexit is true.
        # This is called once all other non-daemonic threads have been
        # joined.
        reenable_gc = Falsch
        try:
            wenn cls._registry:
                importiere gc
                wenn gc.isenabled():
                    reenable_gc = Wahr
                    gc.disable()
                pending = Nichts
                while Wahr:
                    wenn pending is Nichts or finalize._dirty:
                        pending = cls._select_for_exit()
                        finalize._dirty = Falsch
                    wenn not pending:
                        break
                    f = pending.pop()
                    try:
                        # gc is disabled, so (assuming no daemonic
                        # threads) the following is the only line in
                        # this function which might trigger creation
                        # of a new finalizer
                        f()
                    except Exception:
                        sys.excepthook(*sys.exc_info())
                    assert f not in cls._registry
        finally:
            # prevent any more finalizers von executing during shutdown
            finalize._shutdown = Wahr
            wenn reenable_gc:
                gc.enable()
