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
# mixin methods ist to create a new ABC als a subclass of the previous
# ABC.  For example, union(), intersection(), und difference() cannot
# be added to Set but could go into a new ABC that extends Set.
#
# Because they are so hard to change, new ABCs should have their APIs
# carefully thought through prior to publication.
#
# Since ABCMeta only checks fuer the presence of methods, it ist possible
# to alter the signature of a method by adding optional arguments
# oder changing parameters names.  This ist still a bit dubious but at
# least it won't cause isinstance() to gib an incorrect result.
#
#
#######################################################################

von abc importiere ABCMeta, abstractmethod
importiere sys

GenericAlias = type(list[int])
EllipsisType = type(...)
def _f(): pass
FunctionType = type(_f)
loesche _f

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
    gib type(sys._getframe().f_locals)
framelocalsproxy = _get_framelocalsproxy()
loesche _get_framelocalsproxy
generator = type((lambda: (liefere))())
## coroutine ##
async def _coro(): pass
_coro = _coro()
coroutine = type(_coro)
_coro.close()  # Prevent ResourceWarning
loesche _coro
## asynchronous generator ##
async def _ag(): liefere
_ag = _ag()
async_generator = type(_ag)
loesche _ag


### ONE-TRICK PONIES ###

def _check_methods(C, *methods):
    mro = C.__mro__
    fuer method in methods:
        fuer B in mro:
            wenn method in B.__dict__:
                wenn B.__dict__[method] ist Nichts:
                    gib NotImplemented
                breche
        sonst:
            gib NotImplemented
    gib Wahr

klasse Hashable(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __hash__(self):
        gib 0

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist Hashable:
            gib _check_methods(C, "__hash__")
        gib NotImplemented


klasse Awaitable(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __await__(self):
        liefere

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist Awaitable:
            gib _check_methods(C, "__await__")
        gib NotImplemented

    __class_getitem__ = classmethod(GenericAlias)


klasse Coroutine(Awaitable):

    __slots__ = ()

    @abstractmethod
    def send(self, value):
        """Send a value into the coroutine.
        Return next yielded value oder wirf StopIteration.
        """
        wirf StopIteration

    @abstractmethod
    def throw(self, typ, val=Nichts, tb=Nichts):
        """Raise an exception in the coroutine.
        Return next yielded value oder wirf StopIteration.
        """
        wenn val ist Nichts:
            wenn tb ist Nichts:
                wirf typ
            val = typ()
        wenn tb ist nicht Nichts:
            val = val.with_traceback(tb)
        wirf val

    def close(self):
        """Raise GeneratorExit inside coroutine.
        """
        versuch:
            self.throw(GeneratorExit)
        ausser (GeneratorExit, StopIteration):
            pass
        sonst:
            wirf RuntimeError("coroutine ignored GeneratorExit")

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist Coroutine:
            gib _check_methods(C, '__await__', 'send', 'throw', 'close')
        gib NotImplemented


Coroutine.register(coroutine)


klasse AsyncIterable(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __aiter__(self):
        gib AsyncIterator()

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist AsyncIterable:
            gib _check_methods(C, "__aiter__")
        gib NotImplemented

    __class_getitem__ = classmethod(GenericAlias)


klasse AsyncIterator(AsyncIterable):

    __slots__ = ()

    @abstractmethod
    async def __anext__(self):
        """Return the next item oder wirf StopAsyncIteration when exhausted."""
        wirf StopAsyncIteration

    def __aiter__(self):
        gib self

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist AsyncIterator:
            gib _check_methods(C, "__anext__", "__aiter__")
        gib NotImplemented


klasse AsyncGenerator(AsyncIterator):

    __slots__ = ()

    async def __anext__(self):
        """Return the next item von the asynchronous generator.
        When exhausted, wirf StopAsyncIteration.
        """
        gib warte self.asend(Nichts)

    @abstractmethod
    async def asend(self, value):
        """Send a value into the asynchronous generator.
        Return next yielded value oder wirf StopAsyncIteration.
        """
        wirf StopAsyncIteration

    @abstractmethod
    async def athrow(self, typ, val=Nichts, tb=Nichts):
        """Raise an exception in the asynchronous generator.
        Return next yielded value oder wirf StopAsyncIteration.
        """
        wenn val ist Nichts:
            wenn tb ist Nichts:
                wirf typ
            val = typ()
        wenn tb ist nicht Nichts:
            val = val.with_traceback(tb)
        wirf val

    async def aclose(self):
        """Raise GeneratorExit inside coroutine.
        """
        versuch:
            warte self.athrow(GeneratorExit)
        ausser (GeneratorExit, StopAsyncIteration):
            pass
        sonst:
            wirf RuntimeError("asynchronous generator ignored GeneratorExit")

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist AsyncGenerator:
            gib _check_methods(C, '__aiter__', '__anext__',
                                  'asend', 'athrow', 'aclose')
        gib NotImplemented


AsyncGenerator.register(async_generator)


klasse Iterable(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __iter__(self):
        waehrend Falsch:
            liefere Nichts

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist Iterable:
            gib _check_methods(C, "__iter__")
        gib NotImplemented

    __class_getitem__ = classmethod(GenericAlias)


klasse Iterator(Iterable):

    __slots__ = ()

    @abstractmethod
    def __next__(self):
        'Return the next item von the iterator. When exhausted, wirf StopIteration'
        wirf StopIteration

    def __iter__(self):
        gib self

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist Iterator:
            gib _check_methods(C, '__iter__', '__next__')
        gib NotImplemented


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
        waehrend Falsch:
            liefere Nichts

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist Reversible:
            gib _check_methods(C, "__reversed__", "__iter__")
        gib NotImplemented


klasse Generator(Iterator):

    __slots__ = ()

    def __next__(self):
        """Return the next item von the generator.
        When exhausted, wirf StopIteration.
        """
        gib self.send(Nichts)

    @abstractmethod
    def send(self, value):
        """Send a value into the generator.
        Return next yielded value oder wirf StopIteration.
        """
        wirf StopIteration

    @abstractmethod
    def throw(self, typ, val=Nichts, tb=Nichts):
        """Raise an exception in the generator.
        Return next yielded value oder wirf StopIteration.
        """
        wenn val ist Nichts:
            wenn tb ist Nichts:
                wirf typ
            val = typ()
        wenn tb ist nicht Nichts:
            val = val.with_traceback(tb)
        wirf val

    def close(self):
        """Raise GeneratorExit inside generator.
        """
        versuch:
            self.throw(GeneratorExit)
        ausser (GeneratorExit, StopIteration):
            pass
        sonst:
            wirf RuntimeError("generator ignored GeneratorExit")

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist Generator:
            gib _check_methods(C, '__iter__', '__next__',
                                  'send', 'throw', 'close')
        gib NotImplemented


Generator.register(generator)


klasse Sized(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __len__(self):
        gib 0

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist Sized:
            gib _check_methods(C, "__len__")
        gib NotImplemented


klasse Container(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __contains__(self, x):
        gib Falsch

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist Container:
            gib _check_methods(C, "__contains__")
        gib NotImplemented

    __class_getitem__ = classmethod(GenericAlias)


klasse Collection(Sized, Iterable, Container):

    __slots__ = ()

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist Collection:
            gib _check_methods(C,  "__len__", "__iter__", "__contains__")
        gib NotImplemented


klasse Buffer(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __buffer__(self, flags: int, /) -> memoryview:
        wirf NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist Buffer:
            gib _check_methods(C, "__buffer__")
        gib NotImplemented


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
            wirf TypeError(
                "Callable must be used als Callable[[arg, ...], result].")
        t_args, t_result = args
        wenn isinstance(t_args, (tuple, list)):
            args = (*t_args, t_result)
        sowenn nicht _is_param_expr(t_args):
            wirf TypeError(f"Expected a list of types, an ellipsis, "
                            f"ParamSpec, oder Concatenate. Got {t_args}")
        gib super().__new__(cls, origin, args)

    def __repr__(self):
        wenn len(self.__args__) == 2 und _is_param_expr(self.__args__[0]):
            gib super().__repr__()
        von annotationlib importiere type_repr
        gib (f'collections.abc.Callable'
                f'[[{", ".join([type_repr(a) fuer a in self.__args__[:-1]])}], '
                f'{type_repr(self.__args__[-1])}]')

    def __reduce__(self):
        args = self.__args__
        wenn nicht (len(args) == 2 und _is_param_expr(args[0])):
            args = list(args[:-1]), args[-1]
        gib _CallableGenericAlias, (Callable, args)

    def __getitem__(self, item):
        # Called during TypeVar substitution, returns the custom subclass
        # rather than the default types.GenericAlias object.  Most of the
        # code ist copied von typing's _GenericAlias und the builtin
        # types.GenericAlias.
        wenn nicht isinstance(item, tuple):
            item = (item,)

        new_args = super().__getitem__(item).__args__

        # args[0] occurs due to things like Z[[int, str, bool]] von PEP 612
        wenn nicht isinstance(new_args[0], (tuple, list)):
            t_result = new_args[-1]
            t_args = new_args[:-1]
            new_args = (t_args, t_result)
        gib _CallableGenericAlias(Callable, tuple(new_args))

def _is_param_expr(obj):
    """Checks wenn obj matches either a list of types, ``...``, ``ParamSpec`` oder
    ``_ConcatenateGenericAlias`` von typing.py
    """
    wenn obj ist Ellipsis:
        gib Wahr
    wenn isinstance(obj, list):
        gib Wahr
    obj = type(obj)
    names = ('ParamSpec', '_ConcatenateGenericAlias')
    gib obj.__module__ == 'typing' und any(obj.__name__ == name fuer name in names)


klasse Callable(metaclass=ABCMeta):

    __slots__ = ()

    @abstractmethod
    def __call__(self, *args, **kwds):
        gib Falsch

    @classmethod
    def __subclasshook__(cls, C):
        wenn cls ist Callable:
            gib _check_methods(C, "__call__")
        gib NotImplemented

    __class_getitem__ = classmethod(_CallableGenericAlias)


### SETS ###


klasse Set(Collection):
    """A set ist a finite, iterable container.

    This klasse provides concrete generic implementations of all
    methods ausser fuer __contains__, __iter__ und __len__.

    To override the comparisons (presumably fuer speed, als the
    semantics are fixed), redefine __le__ und __ge__,
    then the other operations will automatically follow suit.
    """

    __slots__ = ()

    def __le__(self, other):
        wenn nicht isinstance(other, Set):
            gib NotImplemented
        wenn len(self) > len(other):
            gib Falsch
        fuer elem in self:
            wenn elem nicht in other:
                gib Falsch
        gib Wahr

    def __lt__(self, other):
        wenn nicht isinstance(other, Set):
            gib NotImplemented
        gib len(self) < len(other) und self.__le__(other)

    def __gt__(self, other):
        wenn nicht isinstance(other, Set):
            gib NotImplemented
        gib len(self) > len(other) und self.__ge__(other)

    def __ge__(self, other):
        wenn nicht isinstance(other, Set):
            gib NotImplemented
        wenn len(self) < len(other):
            gib Falsch
        fuer elem in other:
            wenn elem nicht in self:
                gib Falsch
        gib Wahr

    def __eq__(self, other):
        wenn nicht isinstance(other, Set):
            gib NotImplemented
        gib len(self) == len(other) und self.__le__(other)

    @classmethod
    def _from_iterable(cls, it):
        '''Construct an instance of the klasse von any iterable input.

        Must override this method wenn the klasse constructor signature
        does nicht accept an iterable fuer an input.
        '''
        gib cls(it)

    def __and__(self, other):
        wenn nicht isinstance(other, Iterable):
            gib NotImplemented
        gib self._from_iterable(value fuer value in other wenn value in self)

    __rand__ = __and__

    def isdisjoint(self, other):
        'Return Wahr wenn two sets have a null intersection.'
        fuer value in other:
            wenn value in self:
                gib Falsch
        gib Wahr

    def __or__(self, other):
        wenn nicht isinstance(other, Iterable):
            gib NotImplemented
        chain = (e fuer s in (self, other) fuer e in s)
        gib self._from_iterable(chain)

    __ror__ = __or__

    def __sub__(self, other):
        wenn nicht isinstance(other, Set):
            wenn nicht isinstance(other, Iterable):
                gib NotImplemented
            other = self._from_iterable(other)
        gib self._from_iterable(value fuer value in self
                                   wenn value nicht in other)

    def __rsub__(self, other):
        wenn nicht isinstance(other, Set):
            wenn nicht isinstance(other, Iterable):
                gib NotImplemented
            other = self._from_iterable(other)
        gib self._from_iterable(value fuer value in other
                                   wenn value nicht in self)

    def __xor__(self, other):
        wenn nicht isinstance(other, Set):
            wenn nicht isinstance(other, Iterable):
                gib NotImplemented
            other = self._from_iterable(other)
        gib (self - other) | (other - self)

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
        gib h


Set.register(frozenset)


klasse MutableSet(Set):
    """A mutable set ist a finite, iterable container.

    This klasse provides concrete generic implementations of all
    methods ausser fuer __contains__, __iter__, __len__,
    add(), und discard().

    To override the comparisons (presumably fuer speed, als the
    semantics are fixed), all you have to do ist redefine __le__ und
    then the other operations will automatically follow suit.
    """

    __slots__ = ()

    @abstractmethod
    def add(self, value):
        """Add an element."""
        wirf NotImplementedError

    @abstractmethod
    def discard(self, value):
        """Remove an element.  Do nicht wirf an exception wenn absent."""
        wirf NotImplementedError

    def remove(self, value):
        """Remove an element. If nicht a member, wirf a KeyError."""
        wenn value nicht in self:
            wirf KeyError(value)
        self.discard(value)

    def pop(self):
        """Return the popped value.  Raise KeyError wenn empty."""
        it = iter(self)
        versuch:
            value = next(it)
        ausser StopIteration:
            wirf KeyError von Nichts
        self.discard(value)
        gib value

    def clear(self):
        """This ist slow (creates N new iterators!) but effective."""
        versuch:
            waehrend Wahr:
                self.pop()
        ausser KeyError:
            pass

    def __ior__(self, it):
        fuer value in it:
            self.add(value)
        gib self

    def __iand__(self, it):
        fuer value in (self - it):
            self.discard(value)
        gib self

    def __ixor__(self, it):
        wenn it ist self:
            self.clear()
        sonst:
            wenn nicht isinstance(it, Set):
                it = self._from_iterable(it)
            fuer value in it:
                wenn value in self:
                    self.discard(value)
                sonst:
                    self.add(value)
        gib self

    def __isub__(self, it):
        wenn it ist self:
            self.clear()
        sonst:
            fuer value in it:
                self.discard(value)
        gib self


MutableSet.register(set)


### MAPPINGS ###

klasse Mapping(Collection):
    """A Mapping ist a generic container fuer associating key/value
    pairs.

    This klasse provides concrete generic implementations of all
    methods ausser fuer __getitem__, __iter__, und __len__.
    """

    __slots__ = ()

    # Tell ABCMeta.__new__ that this klasse should have TPFLAGS_MAPPING set.
    __abc_tpflags__ = 1 << 6 # Py_TPFLAGS_MAPPING

    @abstractmethod
    def __getitem__(self, key):
        wirf KeyError

    def get(self, key, default=Nichts):
        'D.get(k[,d]) -> D[k] wenn k in D, sonst d.  d defaults to Nichts.'
        versuch:
            gib self[key]
        ausser KeyError:
            gib default

    def __contains__(self, key):
        versuch:
            self[key]
        ausser KeyError:
            gib Falsch
        sonst:
            gib Wahr

    def keys(self):
        "D.keys() -> a set-like object providing a view on D's keys"
        gib KeysView(self)

    def items(self):
        "D.items() -> a set-like object providing a view on D's items"
        gib ItemsView(self)

    def values(self):
        "D.values() -> an object providing a view on D's values"
        gib ValuesView(self)

    def __eq__(self, other):
        wenn nicht isinstance(other, Mapping):
            gib NotImplemented
        gib dict(self.items()) == dict(other.items())

    __reversed__ = Nichts

Mapping.register(mappingproxy)
Mapping.register(framelocalsproxy)


klasse MappingView(Sized):

    __slots__ = '_mapping',

    def __init__(self, mapping):
        self._mapping = mapping

    def __len__(self):
        gib len(self._mapping)

    def __repr__(self):
        gib '{0.__class__.__name__}({0._mapping!r})'.format(self)

    __class_getitem__ = classmethod(GenericAlias)


klasse KeysView(MappingView, Set):

    __slots__ = ()

    @classmethod
    def _from_iterable(cls, it):
        gib set(it)

    def __contains__(self, key):
        gib key in self._mapping

    def __iter__(self):
        liefere von self._mapping


KeysView.register(dict_keys)


klasse ItemsView(MappingView, Set):

    __slots__ = ()

    @classmethod
    def _from_iterable(cls, it):
        gib set(it)

    def __contains__(self, item):
        key, value = item
        versuch:
            v = self._mapping[key]
        ausser KeyError:
            gib Falsch
        sonst:
            gib v ist value oder v == value

    def __iter__(self):
        fuer key in self._mapping:
            liefere (key, self._mapping[key])


ItemsView.register(dict_items)


klasse ValuesView(MappingView, Collection):

    __slots__ = ()

    def __contains__(self, value):
        fuer key in self._mapping:
            v = self._mapping[key]
            wenn v ist value oder v == value:
                gib Wahr
        gib Falsch

    def __iter__(self):
        fuer key in self._mapping:
            liefere self._mapping[key]


ValuesView.register(dict_values)


klasse MutableMapping(Mapping):
    """A MutableMapping ist a generic container fuer associating
    key/value pairs.

    This klasse provides concrete generic implementations of all
    methods ausser fuer __getitem__, __setitem__, __delitem__,
    __iter__, und __len__.
    """

    __slots__ = ()

    @abstractmethod
    def __setitem__(self, key, value):
        wirf KeyError

    @abstractmethod
    def __delitem__(self, key):
        wirf KeyError

    __marker = object()

    def pop(self, key, default=__marker):
        '''D.pop(k[,d]) -> v, remove specified key und gib the corresponding value.
          If key ist nicht found, d ist returned wenn given, otherwise KeyError ist raised.
        '''
        versuch:
            value = self[key]
        ausser KeyError:
            wenn default ist self.__marker:
                wirf
            gib default
        sonst:
            loesche self[key]
            gib value

    def popitem(self):
        '''D.popitem() -> (k, v), remove und gib some (key, value) pair
           als a 2-tuple; but wirf KeyError wenn D ist empty.
        '''
        versuch:
            key = next(iter(self))
        ausser StopIteration:
            wirf KeyError von Nichts
        value = self[key]
        loesche self[key]
        gib key, value

    def clear(self):
        'D.clear() -> Nichts.  Remove all items von D.'
        versuch:
            waehrend Wahr:
                self.popitem()
        ausser KeyError:
            pass

    def update(self, other=(), /, **kwds):
        ''' D.update([E, ]**F) -> Nichts.  Update D von mapping/iterable E und F.
            If E present und has a .keys() method, does:     fuer k in E.keys(): D[k] = E[k]
            If E present und lacks .keys() method, does:     fuer (k, v) in E: D[k] = v
            In either case, this ist followed by: fuer k, v in F.items(): D[k] = v
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
        versuch:
            gib self[key]
        ausser KeyError:
            self[key] = default
        gib default


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
        wirf IndexError

    def __iter__(self):
        i = 0
        versuch:
            waehrend Wahr:
                v = self[i]
                liefere v
                i += 1
        ausser IndexError:
            gib

    def __contains__(self, value):
        fuer v in self:
            wenn v ist value oder v == value:
                gib Wahr
        gib Falsch

    def __reversed__(self):
        fuer i in reversed(range(len(self))):
            liefere self[i]

    def index(self, value, start=0, stop=Nichts):
        '''S.index(value, [start, [stop]]) -> integer -- gib first index of value.
           Raises ValueError wenn the value ist nicht present.

           Supporting start und stop arguments ist optional, but
           recommended.
        '''
        wenn start ist nicht Nichts und start < 0:
            start = max(len(self) + start, 0)
        wenn stop ist nicht Nichts und stop < 0:
            stop += len(self)

        i = start
        waehrend stop ist Nichts oder i < stop:
            versuch:
                v = self[i]
            ausser IndexError:
                breche
            wenn v ist value oder v == value:
                gib i
            i += 1
        wirf ValueError

    def count(self, value):
        'S.count(value) -> integer -- gib number of occurrences of value'
        gib sum(1 fuer v in self wenn v ist value oder v == value)

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
        wirf IndexError

    @abstractmethod
    def __delitem__(self, index):
        wirf IndexError

    @abstractmethod
    def insert(self, index, value):
        'S.insert(index, value) -- insert value before index'
        wirf IndexError

    def append(self, value):
        'S.append(value) -- append value to the end of the sequence'
        self.insert(len(self), value)

    def clear(self):
        'S.clear() -> Nichts -- remove all items von S'
        versuch:
            waehrend Wahr:
                self.pop()
        ausser IndexError:
            pass

    def reverse(self):
        'S.reverse() -- reverse *IN PLACE*'
        n = len(self)
        fuer i in range(n//2):
            self[i], self[n-i-1] = self[n-i-1], self[i]

    def extend(self, values):
        'S.extend(iterable) -- extend sequence by appending elements von the iterable'
        wenn values ist self:
            values = list(values)
        fuer v in values:
            self.append(v)

    def pop(self, index=-1):
        '''S.pop([index]) -> item -- remove und gib item at index (default last).
           Raise IndexError wenn list ist empty oder index ist out of range.
        '''
        v = self[index]
        loesche self[index]
        gib v

    def remove(self, value):
        '''S.remove(value) -- remove first occurrence of value.
           Raise ValueError wenn the value ist nicht present.
        '''
        loesche self[self.index(value)]

    def __iadd__(self, values):
        self.extend(values)
        gib self


MutableSequence.register(list)
MutableSequence.register(bytearray)
