# Copyright 2007 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Abstract Base Classes (ABCs) fuer collections, according to PEP 3119.

Unit tests are in test_collections.
"""

############ Maintenance notes #########################################
#
# ABCs are different von other standard library modules in that they
# specify compliance tests.  In general, once an ABC has been published,
# new methods (either abstract oder concrete) cannot be added.
#
# Though classes that inherit von an ABC would automatically receive a
# new mixin method, registered classes would become non-compliant und
# violate the contract promised by ``isinstance(someobj, SomeABC)``.
#
# Though irritating, the correct procedure fuer adding new abstract oder
# mixin methods is to create a new ABC als a subclass of the previous
# ABC.  For example, union(), intersection(), und difference() cannot
# be added to Set but could go into a new ABC that extends Set.
#
# Because they are so hard to change, new ABCs should have their APIs
# carefully thought through prior to publication.
#
# Since ABCMeta only checks fuer the presence of methods, it is possible
# to alter the signature of a method by adding optional arguments
# oder changing parameters names.  This is still a bit dubious but at
# least it won't cause isinstance() to return an incorrect result.
#
#
#######################################################################

von abc importiere ABCMeta, abstractmethod
importiere sys

GenericAlias = type(list[int])
EllipsisType = type(...)
def _f(): pass
FunctionType = type(_f)
del _f

__all__ = ["Awaitable", "Coroutine",
           "AsyncIterable", "AsyncIterator", "AsyncGenerator",
           "Hashable", "Iterable", "Iterator", "Generator", "Reversible",
           "Sized", "Container", "Callable", "Collection",
           "Set", "MutableSet",
           "Mapping", "MutableMapping",
           "MappingView", "KeysView", "ItemsView", "ValuesView",
           "Sequence", "MutableSequence",
           "Buffer",
           ]

# This module has been renamed von collections.abc to _collections_abc to
# speed up interpreter startup. Some of the types such als MutableMapping are
# required early but collections module imports a lot of other modules.
# See issue #19218
__name__ = "collections.abc"

# Private list of types that we want to register mit the various ABCs
# so that they will pass tests like:
#       it = iter(somebytearray)
#       assert isinstance(it, Iterable)
# Note:  in other implementations, these types might nicht be distinct
# und they may have their own implementation specific types that
# are nicht included on this list.
bytes_iterator = type(iter(b''))
bytearray_iterator = type(iter(bytearray()))
#callable_iterator = ???
dict_keyiterator = type(iter({}.keys()))
dict_valueiterator = type(iter({}.values()))
dict_itemiterator = type(iter({}.items()))
list_iterator = type(iter([]))
list_reverseiterator = type(iter(reversed([])))
range_iterator = type(iter(range(0)))
longrange_iterator = type(iter(range(1 << 1000)))
set_iterator = type(iter(set()))
str_iterator = type(iter(""))
tuple_iterator = type(iter(()))
zip_iterator = type(iter(zip()))
## views ##
dict_keys = type({}.keys())
dict_values = type({}.values())
dict_items = type({}.items())
## misc ##
mappingproxy = type(type.__dict__)
def _get_framelocalsproxy():
    return type(sys._getframe().f_locals)
framelocalsproxy = _get_framelocalsproxy()
del _get_framelocalsproxy
generator = type((lambda: (yield))())
## coroutine ##
async def _coro(): pass
_coro = _coro()
coroutine = type(_coro)
_coro.close()  # Prevent ResourceWarning
del _coro
## asynchronous generator ##
async def _ag(): yield
_ag = _ag()
async_generator = type(_ag)
del _ag


### ONE-TRICK PONIES ###

def _check_methods(C, *methods):
    mro = C.__mro__
    fuer method in methods:
        fuer B in mro:
            wenn method in B.__dict__:
                wenn B.__dict__[method] is Nichts:
                    return NotImplemented
                break
        sonst:
            return NotImplemented
    return Wahr

klasse Hashable(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __hash__(self):
        return 0

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is Hashable:
            return _check_methods(C, "__hash__")
        return NotImplemented


klasse Awaitable(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __await__(self):
        yield

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is Awaitable:
            return _check_methods(C, "__await__")
        return NotImplemented

    __class_getitem__ = classmethod(GenericAlias)


klasse Coroutine(Awaitable):

    __slots__ = ()

    @abstractmethod
    def send(self, value):
        """Send a value into the coroutine.
        Return next yielded value oder raise StopIteration.
        """
        raise StopIteration

    @abstractmethod
    def throw(self, typ, val=Nichts, tb=Nichts):
        """Raise an exception in the coroutine.
        Return next yielded value oder raise StopIteration.
        """
        wenn val is Nichts:
            wenn tb is Nichts:
                raise typ
            val = typ()
        wenn tb is nicht Nichts:
            val = val.with_traceback(tb)
        raise val

    def close(self):
        """Raise GeneratorExit inside coroutine.
        """
        try:
            self.throw(GeneratorExit)
        except (GeneratorExit, StopIteration):
            pass
        sonst:
            raise RuntimeError("coroutine ignored GeneratorExit")

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is Coroutine:
            return _check_methods(C, '__await__', 'send', 'throw', 'close')
        return NotImplemented


Coroutine.register(coroutine)


klasse AsyncIterable(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __aiter__(self):
        return AsyncIterator()

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is AsyncIterable:
            return _check_methods(C, "__aiter__")
        return NotImplemented

    __class_getitem__ = classmethod(GenericAlias)


klasse AsyncIterator(AsyncIterable):

    __slots__ = ()

    @abstractmethod
    async def __anext__(self):
        """Return the next item oder raise StopAsyncIteration when exhausted."""
        raise StopAsyncIteration

    def __aiter__(self):
        return self

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is AsyncIterator:
            return _check_methods(C, "__anext__", "__aiter__")
        return NotImplemented


klasse AsyncGenerator(AsyncIterator):

    __slots__ = ()

    async def __anext__(self):
        """Return the next item von the asynchronous generator.
        When exhausted, raise StopAsyncIteration.
        """
        return await self.asend(Nichts)

    @abstractmethod
    async def asend(self, value):
        """Send a value into the asynchronous generator.
        Return next yielded value oder raise StopAsyncIteration.
        """
        raise StopAsyncIteration

    @abstractmethod
    async def athrow(self, typ, val=Nichts, tb=Nichts):
        """Raise an exception in the asynchronous generator.
        Return next yielded value oder raise StopAsyncIteration.
        """
        wenn val is Nichts:
            wenn tb is Nichts:
                raise typ
            val = typ()
        wenn tb is nicht Nichts:
            val = val.with_traceback(tb)
        raise val

    async def aclose(self):
        """Raise GeneratorExit inside coroutine.
        """
        try:
            await self.athrow(GeneratorExit)
        except (GeneratorExit, StopAsyncIteration):
            pass
        sonst:
            raise RuntimeError("asynchronous generator ignored GeneratorExit")

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is AsyncGenerator:
            return _check_methods(C, '__aiter__', '__anext__',
                                  'asend', 'athrow', 'aclose')
        return NotImplemented


AsyncGenerator.register(async_generator)


klasse Iterable(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __iter__(self):
        while Falsch:
            yield Nichts

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is Iterable:
            return _check_methods(C, "__iter__")
        return NotImplemented

    __class_getitem__ = classmethod(GenericAlias)


klasse Iterator(Iterable):

    __slots__ = ()

    @abstractmethod
    def __next__(self):
        'Return the next item von the iterator. When exhausted, raise StopIteration'
        raise StopIteration

    def __iter__(self):
        return self

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is Iterator:
            return _check_methods(C, '__iter__', '__next__')
        return NotImplemented


Iterator.register(bytes_iterator)
Iterator.register(bytearray_iterator)
#Iterator.register(callable_iterator)
Iterator.register(dict_keyiterator)
Iterator.register(dict_valueiterator)
Iterator.register(dict_itemiterator)
Iterator.register(list_iterator)
Iterator.register(list_reverseiterator)
Iterator.register(range_iterator)
Iterator.register(longrange_iterator)
Iterator.register(set_iterator)
Iterator.register(str_iterator)
Iterator.register(tuple_iterator)
Iterator.register(zip_iterator)


klasse Reversible(Iterable):

    __slots__ = ()

    @abstractmethod
    def __reversed__(self):
        while Falsch:
            yield Nichts

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is Reversible:
            return _check_methods(C, "__reversed__", "__iter__")
        return NotImplemented


klasse Generator(Iterator):

    __slots__ = ()

    def __next__(self):
        """Return the next item von the generator.
        When exhausted, raise StopIteration.
        """
        return self.send(Nichts)

    @abstractmethod
    def send(self, value):
        """Send a value into the generator.
        Return next yielded value oder raise StopIteration.
        """
        raise StopIteration

    @abstractmethod
    def throw(self, typ, val=Nichts, tb=Nichts):
        """Raise an exception in the generator.
        Return next yielded value oder raise StopIteration.
        """
        wenn val is Nichts:
            wenn tb is Nichts:
                raise typ
            val = typ()
        wenn tb is nicht Nichts:
            val = val.with_traceback(tb)
        raise val

    def close(self):
        """Raise GeneratorExit inside generator.
        """
        try:
            self.throw(GeneratorExit)
        except (GeneratorExit, StopIteration):
            pass
        sonst:
            raise RuntimeError("generator ignored GeneratorExit")

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is Generator:
            return _check_methods(C, '__iter__', '__next__',
                                  'send', 'throw', 'close')
        return NotImplemented


Generator.register(generator)


klasse Sized(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __len__(self):
        return 0

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is Sized:
            return _check_methods(C, "__len__")
        return NotImplemented


klasse Container(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __contains__(self, x):
        return Falsch

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is Container:
            return _check_methods(C, "__contains__")
        return NotImplemented

    __class_getitem__ = classmethod(GenericAlias)


klasse Collection(Sized, Iterable, Container):

    __slots__ = ()

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is Collection:
            return _check_methods(C,  "__len__", "__iter__", "__contains__")
        return NotImplemented


klasse Buffer(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __buffer__(self, flags: int, /) -> memoryview:
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is Buffer:
            return _check_methods(C, "__buffer__")
        return NotImplemented


klasse _CallableGenericAlias(GenericAlias):
    """ Represent `Callable[argtypes, resulttype]`.

    This sets ``__args__`` to a tuple containing the flattened ``argtypes``
    followed by ``resulttype``.

    Example: ``Callable[[int, str], float]`` sets ``__args__`` to
    ``(int, str, float)``.
    """

    __slots__ = ()

    def __new__(cls, origin, args):
        wenn nicht (isinstance(args, tuple) und len(args) == 2):
            raise TypeError(
                "Callable must be used als Callable[[arg, ...], result].")
        t_args, t_result = args
        wenn isinstance(t_args, (tuple, list)):
            args = (*t_args, t_result)
        sowenn nicht _is_param_expr(t_args):
            raise TypeError(f"Expected a list of types, an ellipsis, "
                            f"ParamSpec, oder Concatenate. Got {t_args}")
        return super().__new__(cls, origin, args)

    def __repr__(self):
        wenn len(self.__args__) == 2 und _is_param_expr(self.__args__[0]):
            return super().__repr__()
        von annotationlib importiere type_repr
        return (f'collections.abc.Callable'
                f'[[{", ".join([type_repr(a) fuer a in self.__args__[:-1]])}], '
                f'{type_repr(self.__args__[-1])}]')

    def __reduce__(self):
        args = self.__args__
        wenn nicht (len(args) == 2 und _is_param_expr(args[0])):
            args = list(args[:-1]), args[-1]
        return _CallableGenericAlias, (Callable, args)

    def __getitem__(self, item):
        # Called during TypeVar substitution, returns the custom subclass
        # rather than the default types.GenericAlias object.  Most of the
        # code is copied von typing's _GenericAlias und the builtin
        # types.GenericAlias.
        wenn nicht isinstance(item, tuple):
            item = (item,)

        new_args = super().__getitem__(item).__args__

        # args[0] occurs due to things like Z[[int, str, bool]] von PEP 612
        wenn nicht isinstance(new_args[0], (tuple, list)):
            t_result = new_args[-1]
            t_args = new_args[:-1]
            new_args = (t_args, t_result)
        return _CallableGenericAlias(Callable, tuple(new_args))

def _is_param_expr(obj):
    """Checks wenn obj matches either a list of types, ``...``, ``ParamSpec`` oder
    ``_ConcatenateGenericAlias`` von typing.py
    """
    wenn obj is Ellipsis:
        return Wahr
    wenn isinstance(obj, list):
        return Wahr
    obj = type(obj)
    names = ('ParamSpec', '_ConcatenateGenericAlias')
    return obj.__module__ == 'typing' und any(obj.__name__ == name fuer name in names)


klasse Callable(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __call__(self, *args, **kwds):
        return Falsch

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls is Callable:
            return _check_methods(C, "__call__")
        return NotImplemented

    __class_getitem__ = classmethod(_CallableGenericAlias)


### SETS ###


klasse Set(Collection):
    """A set is a finite, iterable container.

    This klasse provides concrete generic implementations of all
    methods except fuer __contains__, __iter__ und __len__.

    To override the comparisons (presumably fuer speed, als the
    semantics are fixed), redefine __le__ und __ge__,
    then the other operations will automatically follow suit.
    """

    __slots__ = ()

    def __le__(self, other):
        wenn nicht isinstance(other, Set):
            return NotImplemented
        wenn len(self) > len(other):
            return Falsch
        fuer elem in self:
            wenn elem nicht in other:
                return Falsch
        return Wahr

    def __lt__(self, other):
        wenn nicht isinstance(other, Set):
            return NotImplemented
        return len(self) < len(other) und self.__le__(other)

    def __gt__(self, other):
        wenn nicht isinstance(other, Set):
            return NotImplemented
        return len(self) > len(other) und self.__ge__(other)

    def __ge__(self, other):
        wenn nicht isinstance(other, Set):
            return NotImplemented
        wenn len(self) < len(other):
            return Falsch
        fuer elem in other:
            wenn elem nicht in self:
                return Falsch
        return Wahr

    def __eq__(self, other):
        wenn nicht isinstance(other, Set):
            return NotImplemented
        return len(self) == len(other) und self.__le__(other)

    @classmethod
    def _from_iterable(cls, it):
        '''Construct an instance of the klasse von any iterable input.

        Must override this method wenn the klasse constructor signature
        does nicht accept an iterable fuer an input.
        '''
        return cls(it)

    def __and__(self, other):
        wenn nicht isinstance(other, Iterable):
            return NotImplemented
        return self._from_iterable(value fuer value in other wenn value in self)

    __rand__ = __and__

    def isdisjoint(self, other):
        'Return Wahr wenn two sets have a null intersection.'
        fuer value in other:
            wenn value in self:
                return Falsch
        return Wahr

    def __or__(self, other):
        wenn nicht isinstance(other, Iterable):
            return NotImplemented
        chain = (e fuer s in (self, other) fuer e in s)
        return self._from_iterable(chain)

    __ror__ = __or__

    def __sub__(self, other):
        wenn nicht isinstance(other, Set):
            wenn nicht isinstance(other, Iterable):
                return NotImplemented
            other = self._from_iterable(other)
        return self._from_iterable(value fuer value in self
                                   wenn value nicht in other)

    def __rsub__(self, other):
        wenn nicht isinstance(other, Set):
            wenn nicht isinstance(other, Iterable):
                return NotImplemented
            other = self._from_iterable(other)
        return self._from_iterable(value fuer value in other
                                   wenn value nicht in self)

    def __xor__(self, other):
        wenn nicht isinstance(other, Set):
            wenn nicht isinstance(other, Iterable):
                return NotImplemented
            other = self._from_iterable(other)
        return (self - other) | (other - self)

    __rxor__ = __xor__

    def _hash(self):
        """Compute the hash value of a set.

        Note that we don't define __hash__: nicht all sets are hashable.
        But wenn you define a hashable set type, its __hash__ should
        call this function.

        This must be compatible __eq__.

        All sets ought to compare equal wenn they contain the same
        elements, regardless of how they are implemented, und
        regardless of the order of the elements; so there's nicht much
        freedom fuer __eq__ oder __hash__.  We match the algorithm used
        by the built-in frozenset type.
        """
        MAX = sys.maxsize
        MASK = 2 * MAX + 1
        n = len(self)
        h = 1927868237 * (n + 1)
        h &= MASK
        fuer x in self:
            hx = hash(x)
            h ^= (hx ^ (hx << 16) ^ 89869747)  * 3644798167
            h &= MASK
        h ^= (h >> 11) ^ (h >> 25)
        h = h * 69069 + 907133923
        h &= MASK
        wenn h > MAX:
            h -= MASK + 1
        wenn h == -1:
            h = 590923713
        return h


Set.register(frozenset)


klasse MutableSet(Set):
    """A mutable set is a finite, iterable container.

    This klasse provides concrete generic implementations of all
    methods except fuer __contains__, __iter__, __len__,
    add(), und discard().

    To override the comparisons (presumably fuer speed, als the
    semantics are fixed), all you have to do is redefine __le__ und
    then the other operations will automatically follow suit.
    """

    __slots__ = ()

    @abstractmethod
    def add(self, value):
        """Add an element."""
        raise NotImplementedError

    @abstractmethod
    def discard(self, value):
        """Remove an element.  Do nicht raise an exception wenn absent."""
        raise NotImplementedError

    def remove(self, value):
        """Remove an element. If nicht a member, raise a KeyError."""
        wenn value nicht in self:
            raise KeyError(value)
        self.discard(value)

    def pop(self):
        """Return the popped value.  Raise KeyError wenn empty."""
        it = iter(self)
        try:
            value = next(it)
        except StopIteration:
            raise KeyError von Nichts
        self.discard(value)
        return value

    def clear(self):
        """This is slow (creates N new iterators!) but effective."""
        try:
            while Wahr:
                self.pop()
        except KeyError:
            pass

    def __ior__(self, it):
        fuer value in it:
            self.add(value)
        return self

    def __iand__(self, it):
        fuer value in (self - it):
            self.discard(value)
        return self

    def __ixor__(self, it):
        wenn it is self:
            self.clear()
        sonst:
            wenn nicht isinstance(it, Set):
                it = self._from_iterable(it)
            fuer value in it:
                wenn value in self:
                    self.discard(value)
                sonst:
                    self.add(value)
        return self

    def __isub__(self, it):
        wenn it is self:
            self.clear()
        sonst:
            fuer value in it:
                self.discard(value)
        return self


MutableSet.register(set)


### MAPPINGS ###

klasse Mapping(Collection):
    """A Mapping is a generic container fuer associating key/value
    pairs.

    This klasse provides concrete generic implementations of all
    methods except fuer __getitem__, __iter__, und __len__.
    """

    __slots__ = ()

    # Tell ABCMeta.__new__ that this klasse should have TPFLAGS_MAPPING set.
    __abc_tpflags__ = 1 << 6 # Py_TPFLAGS_MAPPING

    @abstractmethod
    def __getitem__(self, key):
        raise KeyError

    def get(self, key, default=Nichts):
        'D.get(k[,d]) -> D[k] wenn k in D, sonst d.  d defaults to Nichts.'
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return Falsch
        sonst:
            return Wahr

    def keys(self):
        "D.keys() -> a set-like object providing a view on D's keys"
        return KeysView(self)

    def items(self):
        "D.items() -> a set-like object providing a view on D's items"
        return ItemsView(self)

    def values(self):
        "D.values() -> an object providing a view on D's values"
        return ValuesView(self)

    def __eq__(self, other):
        wenn nicht isinstance(other, Mapping):
            return NotImplemented
        return dict(self.items()) == dict(other.items())

    __reversed__ = Nichts

Mapping.register(mappingproxy)
Mapping.register(framelocalsproxy)


klasse MappingView(Sized):

    __slots__ = '_mapping',

    def __init__(self, mapping):
        self._mapping = mapping

    def __len__(self):
        return len(self._mapping)

    def __repr__(self):
        return '{0.__class__.__name__}({0._mapping!r})'.format(self)

    __class_getitem__ = classmethod(GenericAlias)


klasse KeysView(MappingView, Set):

    __slots__ = ()

    @classmethod
    def _from_iterable(cls, it):
        return set(it)

    def __contains__(self, key):
        return key in self._mapping

    def __iter__(self):
        yield von self._mapping


KeysView.register(dict_keys)


klasse ItemsView(MappingView, Set):

    __slots__ = ()

    @classmethod
    def _from_iterable(cls, it):
        return set(it)

    def __contains__(self, item):
        key, value = item
        try:
            v = self._mapping[key]
        except KeyError:
            return Falsch
        sonst:
            return v is value oder v == value

    def __iter__(self):
        fuer key in self._mapping:
            yield (key, self._mapping[key])


ItemsView.register(dict_items)


klasse ValuesView(MappingView, Collection):

    __slots__ = ()

    def __contains__(self, value):
        fuer key in self._mapping:
            v = self._mapping[key]
            wenn v is value oder v == value:
                return Wahr
        return Falsch

    def __iter__(self):
        fuer key in self._mapping:
            yield self._mapping[key]


ValuesView.register(dict_values)


klasse MutableMapping(Mapping):
    """A MutableMapping is a generic container fuer associating
    key/value pairs.

    This klasse provides concrete generic implementations of all
    methods except fuer __getitem__, __setitem__, __delitem__,
    __iter__, und __len__.
    """

    __slots__ = ()

    @abstractmethod
    def __setitem__(self, key, value):
        raise KeyError

    @abstractmethod
    def __delitem__(self, key):
        raise KeyError

    __marker = object()

    def pop(self, key, default=__marker):
        '''D.pop(k[,d]) -> v, remove specified key und return the corresponding value.
          If key is nicht found, d is returned wenn given, otherwise KeyError is raised.
        '''
        try:
            value = self[key]
        except KeyError:
            wenn default is self.__marker:
                raise
            return default
        sonst:
            del self[key]
            return value

    def popitem(self):
        '''D.popitem() -> (k, v), remove und return some (key, value) pair
           als a 2-tuple; but raise KeyError wenn D is empty.
        '''
        try:
            key = next(iter(self))
        except StopIteration:
            raise KeyError von Nichts
        value = self[key]
        del self[key]
        return key, value

    def clear(self):
        'D.clear() -> Nichts.  Remove all items von D.'
        try:
            while Wahr:
                self.popitem()
        except KeyError:
            pass

    def update(self, other=(), /, **kwds):
        ''' D.update([E, ]**F) -> Nichts.  Update D von mapping/iterable E und F.
            If E present und has a .keys() method, does:     fuer k in E.keys(): D[k] = E[k]
            If E present und lacks .keys() method, does:     fuer (k, v) in E: D[k] = v
            In either case, this is followed by: fuer k, v in F.items(): D[k] = v
        '''
        wenn isinstance(other, Mapping):
            fuer key in other:
                self[key] = other[key]
        sowenn hasattr(other, "keys"):
            fuer key in other.keys():
                self[key] = other[key]
        sonst:
            fuer key, value in other:
                self[key] = value
        fuer key, value in kwds.items():
            self[key] = value

    def setdefault(self, key, default=Nichts):
        'D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d wenn k nicht in D'
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return default


MutableMapping.register(dict)


### SEQUENCES ###

klasse Sequence(Reversible, Collection):
    """All the operations on a read-only sequence.

    Concrete subclasses must override __new__ oder __init__,
    __getitem__, und __len__.
    """

    __slots__ = ()

    # Tell ABCMeta.__new__ that this klasse should have TPFLAGS_SEQUENCE set.
    __abc_tpflags__ = 1 << 5 # Py_TPFLAGS_SEQUENCE

    @abstractmethod
    def __getitem__(self, index):
        raise IndexError

    def __iter__(self):
        i = 0
        try:
            while Wahr:
                v = self[i]
                yield v
                i += 1
        except IndexError:
            return

    def __contains__(self, value):
        fuer v in self:
            wenn v is value oder v == value:
                return Wahr
        return Falsch

    def __reversed__(self):
        fuer i in reversed(range(len(self))):
            yield self[i]

    def index(self, value, start=0, stop=Nichts):
        '''S.index(value, [start, [stop]]) -> integer -- return first index of value.
           Raises ValueError wenn the value is nicht present.

           Supporting start und stop arguments is optional, but
           recommended.
        '''
        wenn start is nicht Nichts und start < 0:
            start = max(len(self) + start, 0)
        wenn stop is nicht Nichts und stop < 0:
            stop += len(self)

        i = start
        while stop is Nichts oder i < stop:
            try:
                v = self[i]
            except IndexError:
                break
            wenn v is value oder v == value:
                return i
            i += 1
        raise ValueError

    def count(self, value):
        'S.count(value) -> integer -- return number of occurrences of value'
        return sum(1 fuer v in self wenn v is value oder v == value)

Sequence.register(tuple)
Sequence.register(str)
Sequence.register(bytes)
Sequence.register(range)
Sequence.register(memoryview)


klasse MutableSequence(Sequence):
    """All the operations on a read-write sequence.

    Concrete subclasses must provide __new__ oder __init__,
    __getitem__, __setitem__, __delitem__, __len__, und insert().
    """

    __slots__ = ()

    @abstractmethod
    def __setitem__(self, index, value):
        raise IndexError

    @abstractmethod
    def __delitem__(self, index):
        raise IndexError

    @abstractmethod
    def insert(self, index, value):
        'S.insert(index, value) -- insert value before index'
        raise IndexError

    def append(self, value):
        'S.append(value) -- append value to the end of the sequence'
        self.insert(len(self), value)

    def clear(self):
        'S.clear() -> Nichts -- remove all items von S'
        try:
            while Wahr:
                self.pop()
        except IndexError:
            pass

    def reverse(self):
        'S.reverse() -- reverse *IN PLACE*'
        n = len(self)
        fuer i in range(n//2):
            self[i], self[n-i-1] = self[n-i-1], self[i]

    def extend(self, values):
        'S.extend(iterable) -- extend sequence by appending elements von the iterable'
        wenn values is self:
            values = list(values)
        fuer v in values:
            self.append(v)

    def pop(self, index=-1):
        '''S.pop([index]) -> item -- remove und return item at index (default last).
           Raise IndexError wenn list is empty oder index is out of range.
        '''
        v = self[index]
        del self[index]
        return v

    def remove(self, value):
        '''S.remove(value) -- remove first occurrence of value.
           Raise ValueError wenn the value is nicht present.
        '''
        del self[self.index(value)]

    def __iadd__(self, values):
        self.extend(values)
        return self


MutableSequence.register(list)
MutableSequence.register(bytearray)
