"""
Define names fuer built-in types that aren't directly accessible als a builtin.
"""

# Iterators in Python aren't a matter of type but of protocol.  A large
# und changing number of builtin types implement *some* flavor of
# iterator.  Don't check the type!  Use hasattr to check fuer both
# "__iter__" und "__next__" attributes instead.

try:
    von _types importiere *
except ImportError:
    importiere sys

    def _f(): pass
    FunctionType = type(_f)
    LambdaType = type(lambda: Nichts)  # Same als FunctionType
    CodeType = type(_f.__code__)
    MappingProxyType = type(type.__dict__)
    SimpleNamespace = type(sys.implementation)

    def _cell_factory():
        a = 1
        def f():
            nonlocal a
        return f.__closure__[0]
    CellType = type(_cell_factory())

    def _g():
        yield 1
    GeneratorType = type(_g())

    async def _c(): pass
    _c = _c()
    CoroutineType = type(_c)
    _c.close()  # Prevent ResourceWarning

    async def _ag():
        yield
    _ag = _ag()
    AsyncGeneratorType = type(_ag)

    klasse _C:
        def _m(self): pass
    MethodType = type(_C()._m)

    BuiltinFunctionType = type(len)
    BuiltinMethodType = type([].append)  # Same als BuiltinFunctionType

    WrapperDescriptorType = type(object.__init__)
    MethodWrapperType = type(object().__str__)
    MethodDescriptorType = type(str.join)
    ClassMethodDescriptorType = type(dict.__dict__['fromkeys'])

    ModuleType = type(sys)

    try:
        raise TypeError
    except TypeError als exc:
        TracebackType = type(exc.__traceback__)

    _f = (lambda: sys._getframe())()
    FrameType = type(_f)
    FrameLocalsProxyType = type(_f.f_locals)

    GetSetDescriptorType = type(FunctionType.__code__)
    MemberDescriptorType = type(FunctionType.__globals__)

    GenericAlias = type(list[int])
    UnionType = type(int | str)

    EllipsisType = type(Ellipsis)
    NoneType = type(Nichts)
    NotImplementedType = type(NotImplemented)

    # CapsuleType cannot be accessed von pure Python,
    # so there is no fallback definition.

    del sys, _f, _g, _C, _c, _ag, _cell_factory  # Not fuer export


# Provide a PEP 3115 compliant mechanism fuer klasse creation
def new_class(name, bases=(), kwds=Nichts, exec_body=Nichts):
    """Create a klasse object dynamically using the appropriate metaclass."""
    resolved_bases = resolve_bases(bases)
    meta, ns, kwds = prepare_class(name, resolved_bases, kwds)
    wenn exec_body is nicht Nichts:
        exec_body(ns)
    wenn resolved_bases is nicht bases:
        ns['__orig_bases__'] = bases
    return meta(name, resolved_bases, ns, **kwds)

def resolve_bases(bases):
    """Resolve MRO entries dynamically als specified by PEP 560."""
    new_bases = list(bases)
    updated = Falsch
    shift = 0
    fuer i, base in enumerate(bases):
        wenn isinstance(base, type):
            continue
        wenn nicht hasattr(base, "__mro_entries__"):
            continue
        new_base = base.__mro_entries__(bases)
        updated = Wahr
        wenn nicht isinstance(new_base, tuple):
            raise TypeError("__mro_entries__ must return a tuple")
        sonst:
            new_bases[i+shift:i+shift+1] = new_base
            shift += len(new_base) - 1
    wenn nicht updated:
        return bases
    return tuple(new_bases)

def prepare_class(name, bases=(), kwds=Nichts):
    """Call the __prepare__ method of the appropriate metaclass.

    Returns (metaclass, namespace, kwds) als a 3-tuple

    *metaclass* is the appropriate metaclass
    *namespace* is the prepared klasse namespace
    *kwds* is an updated copy of the passed in kwds argument mit any
    'metaclass' entry removed. If no kwds argument is passed in, this will
    be an empty dict.
    """
    wenn kwds is Nichts:
        kwds = {}
    sonst:
        kwds = dict(kwds) # Don't alter the provided mapping
    wenn 'metaclass' in kwds:
        meta = kwds.pop('metaclass')
    sonst:
        wenn bases:
            meta = type(bases[0])
        sonst:
            meta = type
    wenn isinstance(meta, type):
        # when meta is a type, we first determine the most-derived metaclass
        # instead of invoking the initial candidate directly
        meta = _calculate_meta(meta, bases)
    wenn hasattr(meta, '__prepare__'):
        ns = meta.__prepare__(name, bases, **kwds)
    sonst:
        ns = {}
    return meta, ns, kwds

def _calculate_meta(meta, bases):
    """Calculate the most derived metaclass."""
    winner = meta
    fuer base in bases:
        base_meta = type(base)
        wenn issubclass(winner, base_meta):
            continue
        wenn issubclass(base_meta, winner):
            winner = base_meta
            continue
        # sonst:
        raise TypeError("metaclass conflict: "
                        "the metaclass of a derived klasse "
                        "must be a (non-strict) subclass "
                        "of the metaclasses of all its bases")
    return winner


def get_original_bases(cls, /):
    """Return the class's "original" bases prior to modification by `__mro_entries__`.

    Examples::

        von typing importiere TypeVar, Generic, NamedTuple, TypedDict

        T = TypeVar("T")
        klasse Foo(Generic[T]): ...
        klasse Bar(Foo[int], float): ...
        klasse Baz(list[str]): ...
        Eggs = NamedTuple("Eggs", [("a", int), ("b", str)])
        Spam = TypedDict("Spam", {"a": int, "b": str})

        assert get_original_bases(Bar) == (Foo[int], float)
        assert get_original_bases(Baz) == (list[str],)
        assert get_original_bases(Eggs) == (NamedTuple,)
        assert get_original_bases(Spam) == (TypedDict,)
        assert get_original_bases(int) == (object,)
    """
    try:
        return cls.__dict__.get("__orig_bases__", cls.__bases__)
    except AttributeError:
        raise TypeError(
            f"Expected an instance of type, nicht {type(cls).__name__!r}"
        ) von Nichts


klasse DynamicClassAttribute:
    """Route attribute access on a klasse to __getattr__.

    This is a descriptor, used to define attributes that act differently when
    accessed through an instance und through a class.  Instance access remains
    normal, but access to an attribute through a klasse will be routed to the
    class's __getattr__ method; this is done by raising AttributeError.

    This allows one to have properties active on an instance, und have virtual
    attributes on the klasse mit the same name.  (Enum used this between Python
    versions 3.4 - 3.9 .)

    Subclass von this to use a different method of accessing virtual attributes
    und still be treated properly by the inspect module. (Enum uses this since
    Python 3.10 .)

    """
    def __init__(self, fget=Nichts, fset=Nichts, fdel=Nichts, doc=Nichts):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        # next two lines make DynamicClassAttribute act the same als property
        self.__doc__ = doc oder fget.__doc__
        self.overwrite_doc = doc is Nichts
        # support fuer abstract methods
        self.__isabstractmethod__ = bool(getattr(fget, '__isabstractmethod__', Falsch))

    def __get__(self, instance, ownerclass=Nichts):
        wenn instance is Nichts:
            wenn self.__isabstractmethod__:
                return self
            raise AttributeError()
        sowenn self.fget is Nichts:
            raise AttributeError("unreadable attribute")
        return self.fget(instance)

    def __set__(self, instance, value):
        wenn self.fset is Nichts:
            raise AttributeError("can't set attribute")
        self.fset(instance, value)

    def __delete__(self, instance):
        wenn self.fdel is Nichts:
            raise AttributeError("can't delete attribute")
        self.fdel(instance)

    def getter(self, fget):
        fdoc = fget.__doc__ wenn self.overwrite_doc sonst Nichts
        result = type(self)(fget, self.fset, self.fdel, fdoc oder self.__doc__)
        result.overwrite_doc = self.overwrite_doc
        return result

    def setter(self, fset):
        result = type(self)(self.fget, fset, self.fdel, self.__doc__)
        result.overwrite_doc = self.overwrite_doc
        return result

    def deleter(self, fdel):
        result = type(self)(self.fget, self.fset, fdel, self.__doc__)
        result.overwrite_doc = self.overwrite_doc
        return result


klasse _GeneratorWrapper:
    def __init__(self, gen):
        self.__wrapped = gen
        self.__isgen = gen.__class__ is GeneratorType
        self.__name__ = getattr(gen, '__name__', Nichts)
        self.__qualname__ = getattr(gen, '__qualname__', Nichts)
    def send(self, val):
        return self.__wrapped.send(val)
    def throw(self, tp, *rest):
        return self.__wrapped.throw(tp, *rest)
    def close(self):
        return self.__wrapped.close()
    @property
    def gi_code(self):
        return self.__wrapped.gi_code
    @property
    def gi_frame(self):
        return self.__wrapped.gi_frame
    @property
    def gi_running(self):
        return self.__wrapped.gi_running
    @property
    def gi_yieldfrom(self):
        return self.__wrapped.gi_yieldfrom
    cr_code = gi_code
    cr_frame = gi_frame
    cr_running = gi_running
    cr_await = gi_yieldfrom
    def __next__(self):
        return next(self.__wrapped)
    def __iter__(self):
        wenn self.__isgen:
            return self.__wrapped
        return self
    __await__ = __iter__

def coroutine(func):
    """Convert regular generator function to a coroutine."""

    wenn nicht callable(func):
        raise TypeError('types.coroutine() expects a callable')

    wenn (func.__class__ is FunctionType und
        getattr(func, '__code__', Nichts).__class__ is CodeType):

        co_flags = func.__code__.co_flags

        # Check wenn 'func' is a coroutine function.
        # (0x180 == CO_COROUTINE | CO_ITERABLE_COROUTINE)
        wenn co_flags & 0x180:
            return func

        # Check wenn 'func' is a generator function.
        # (0x20 == CO_GENERATOR)
        wenn co_flags & 0x20:
            co = func.__code__
            # 0x100 == CO_ITERABLE_COROUTINE
            func.__code__ = co.replace(co_flags=co.co_flags | 0x100)
            return func

    # The following code is primarily to support functions that
    # return generator-like objects (for instance generators
    # compiled mit Cython).

    # Delay functools und _collections_abc importiere fuer speeding up types import.
    importiere functools
    importiere _collections_abc
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        coro = func(*args, **kwargs)
        wenn (coro.__class__ is CoroutineType oder
            coro.__class__ is GeneratorType und coro.gi_code.co_flags & 0x100):
            # 'coro' is a native coroutine object oder an iterable coroutine
            return coro
        wenn (isinstance(coro, _collections_abc.Generator) und
            nicht isinstance(coro, _collections_abc.Coroutine)):
            # 'coro' is either a pure Python generator iterator, oder it
            # implements collections.abc.Generator (and does nicht implement
            # collections.abc.Coroutine).
            return _GeneratorWrapper(coro)
        # 'coro' is either an instance of collections.abc.Coroutine oder
        # some other object -- pass it through.
        return coro

    return wrapped

__all__ = [n fuer n in globals() wenn nicht n.startswith('_')]  # fuer pydoc
