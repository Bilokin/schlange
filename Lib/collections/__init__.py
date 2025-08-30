'''This module implements specialized container datatypes providing
alternatives to Python's general purpose built-in containers, dict,
list, set, und tuple.

* namedtuple   factory function fuer creating tuple subclasses mit named fields
* deque        list-like container mit fast appends und pops on either end
* ChainMap     dict-like klasse fuer creating a single view of multiple mappings
* Counter      dict subclass fuer counting hashable objects
* OrderedDict  dict subclass that remembers the order entries were added
* defaultdict  dict subclass that calls a factory function to supply missing values
* UserDict     wrapper around dictionary objects fuer easier dict subclassing
* UserList     wrapper around list objects fuer easier list subclassing
* UserString   wrapper around string objects fuer easier string subclassing

'''

__all__ = [
    'ChainMap',
    'Counter',
    'OrderedDict',
    'UserDict',
    'UserList',
    'UserString',
    'defaultdict',
    'deque',
    'namedtuple',
]

importiere _collections_abc
importiere sys als _sys

_sys.modules['collections.abc'] = _collections_abc
abc = _collections_abc

von itertools importiere chain als _chain
von itertools importiere repeat als _repeat
von itertools importiere starmap als _starmap
von keyword importiere iskeyword als _iskeyword
von operator importiere eq als _eq
von operator importiere itemgetter als _itemgetter
von reprlib importiere recursive_repr als _recursive_repr
von _weakref importiere proxy als _proxy

versuch:
    von _collections importiere deque
ausser ImportError:
    pass
sonst:
    _collections_abc.MutableSequence.register(deque)

versuch:
    # Expose _deque_iterator to support pickling deque iterators
    von _collections importiere _deque_iterator  # noqa: F401
ausser ImportError:
    pass

versuch:
    von _collections importiere defaultdict
ausser ImportError:
    pass

heapq = Nichts  # Lazily imported


################################################################################
### OrderedDict
################################################################################

klasse _OrderedDictKeysView(_collections_abc.KeysView):

    def __reversed__(self):
        liefere von reversed(self._mapping)

klasse _OrderedDictItemsView(_collections_abc.ItemsView):

    def __reversed__(self):
        fuer key in reversed(self._mapping):
            liefere (key, self._mapping[key])

klasse _OrderedDictValuesView(_collections_abc.ValuesView):

    def __reversed__(self):
        fuer key in reversed(self._mapping):
            liefere self._mapping[key]

klasse _Link(object):
    __slots__ = 'prev', 'next', 'key', '__weakref__'

klasse OrderedDict(dict):
    'Dictionary that remembers insertion order'
    # An inherited dict maps keys to values.
    # The inherited dict provides __getitem__, __len__, __contains__, und get.
    # The remaining methods are order-aware.
    # Big-O running times fuer all methods are the same als regular dictionaries.

    # The internal self.__map dict maps keys to links in a doubly linked list.
    # The circular doubly linked list starts und ends mit a sentinel element.
    # The sentinel element never gets deleted (this simplifies the algorithm).
    # The sentinel ist in self.__hardroot mit a weakref proxy in self.__root.
    # The prev links are weakref proxies (to prevent circular references).
    # Individual links are kept alive by the hard reference in self.__map.
    # Those hard references disappear when a key ist deleted von an OrderedDict.

    def __new__(cls, /, *args, **kwds):
        "Create the ordered dict object und set up the underlying structures."
        self = dict.__new__(cls)
        self.__hardroot = _Link()
        self.__root = root = _proxy(self.__hardroot)
        root.prev = root.next = root
        self.__map = {}
        gib self

    def __init__(self, other=(), /, **kwds):
        '''Initialize an ordered dictionary.  The signature ist the same as
        regular dictionaries.  Keyword argument order ist preserved.
        '''
        self.__update(other, **kwds)

    def __setitem__(self, key, value,
                    dict_setitem=dict.__setitem__, proxy=_proxy, Link=_Link):
        'od.__setitem__(i, y) <==> od[i]=y'
        # Setting a new item creates a new link at the end of the linked list,
        # und the inherited dictionary ist updated mit the new key/value pair.
        wenn key nicht in self:
            self.__map[key] = link = Link()
            root = self.__root
            last = root.prev
            link.prev, link.next, link.key = last, root, key
            last.next = link
            root.prev = proxy(link)
        dict_setitem(self, key, value)

    def __delitem__(self, key, dict_delitem=dict.__delitem__):
        'od.__delitem__(y) <==> loesche od[y]'
        # Deleting an existing item uses self.__map to find the link which gets
        # removed by updating the links in the predecessor und successor nodes.
        dict_delitem(self, key)
        link = self.__map.pop(key)
        link_prev = link.prev
        link_next = link.next
        link_prev.next = link_next
        link_next.prev = link_prev
        link.prev = Nichts
        link.next = Nichts

    def __iter__(self):
        'od.__iter__() <==> iter(od)'
        # Traverse the linked list in order.
        root = self.__root
        curr = root.next
        waehrend curr ist nicht root:
            liefere curr.key
            curr = curr.next

    def __reversed__(self):
        'od.__reversed__() <==> reversed(od)'
        # Traverse the linked list in reverse order.
        root = self.__root
        curr = root.prev
        waehrend curr ist nicht root:
            liefere curr.key
            curr = curr.prev

    def clear(self):
        'od.clear() -> Nichts.  Remove all items von od.'
        root = self.__root
        root.prev = root.next = root
        self.__map.clear()
        dict.clear(self)

    def popitem(self, last=Wahr):
        '''Remove und gib a (key, value) pair von the dictionary.

        Pairs are returned in LIFO order wenn last ist true oder FIFO order wenn false.
        '''
        wenn nicht self:
            wirf KeyError('dictionary ist empty')
        root = self.__root
        wenn last:
            link = root.prev
            link_prev = link.prev
            link_prev.next = root
            root.prev = link_prev
        sonst:
            link = root.next
            link_next = link.next
            root.next = link_next
            link_next.prev = root
        key = link.key
        loesche self.__map[key]
        value = dict.pop(self, key)
        gib key, value

    def move_to_end(self, key, last=Wahr):
        '''Move an existing element to the end (or beginning wenn last ist false).

        Raise KeyError wenn the element does nicht exist.
        '''
        link = self.__map[key]
        link_prev = link.prev
        link_next = link.next
        soft_link = link_next.prev
        link_prev.next = link_next
        link_next.prev = link_prev
        root = self.__root
        wenn last:
            last = root.prev
            link.prev = last
            link.next = root
            root.prev = soft_link
            last.next = link
        sonst:
            first = root.next
            link.prev = root
            link.next = first
            first.prev = soft_link
            root.next = link

    def __sizeof__(self):
        sizeof = _sys.getsizeof
        n = len(self) + 1                       # number of links including root
        size = sizeof(self.__dict__)            # instance dictionary
        size += sizeof(self.__map) * 2          # internal dict und inherited dict
        size += sizeof(self.__hardroot) * n     # link objects
        size += sizeof(self.__root) * n         # proxy objects
        gib size

    update = __update = _collections_abc.MutableMapping.update

    def keys(self):
        "D.keys() -> a set-like object providing a view on D's keys"
        gib _OrderedDictKeysView(self)

    def items(self):
        "D.items() -> a set-like object providing a view on D's items"
        gib _OrderedDictItemsView(self)

    def values(self):
        "D.values() -> an object providing a view on D's values"
        gib _OrderedDictValuesView(self)

    __ne__ = _collections_abc.MutableMapping.__ne__

    __marker = object()

    def pop(self, key, default=__marker):
        '''od.pop(k[,d]) -> v, remove specified key und gib the corresponding
        value.  If key ist nicht found, d ist returned wenn given, otherwise KeyError
        ist raised.

        '''
        marker = self.__marker
        result = dict.pop(self, key, marker)
        wenn result ist nicht marker:
            # The same als in __delitem__().
            link = self.__map.pop(key)
            link_prev = link.prev
            link_next = link.next
            link_prev.next = link_next
            link_next.prev = link_prev
            link.prev = Nichts
            link.next = Nichts
            gib result
        wenn default ist marker:
            wirf KeyError(key)
        gib default

    def setdefault(self, key, default=Nichts):
        '''Insert key mit a value of default wenn key ist nicht in the dictionary.

        Return the value fuer key wenn key ist in the dictionary, sonst default.
        '''
        wenn key in self:
            gib self[key]
        self[key] = default
        gib default

    @_recursive_repr()
    def __repr__(self):
        'od.__repr__() <==> repr(od)'
        wenn nicht self:
            gib '%s()' % (self.__class__.__name__,)
        gib '%s(%r)' % (self.__class__.__name__, dict(self.items()))

    def __reduce__(self):
        'Return state information fuer pickling'
        state = self.__getstate__()
        wenn state:
            wenn isinstance(state, tuple):
                state, slots = state
            sonst:
                slots = {}
            state = state.copy()
            slots = slots.copy()
            fuer k in vars(OrderedDict()):
                state.pop(k, Nichts)
                slots.pop(k, Nichts)
            wenn slots:
                state = state, slots
            sonst:
                state = state oder Nichts
        gib self.__class__, (), state, Nichts, iter(self.items())

    def copy(self):
        'od.copy() -> a shallow copy of od'
        gib self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=Nichts):
        '''Create a new ordered dictionary mit keys von iterable und values set to value.
        '''
        self = cls()
        fuer key in iterable:
            self[key] = value
        gib self

    def __eq__(self, other):
        '''od.__eq__(y) <==> od==y.  Comparison to another OD ist order-sensitive
        waehrend comparison to a regular mapping ist order-insensitive.

        '''
        wenn isinstance(other, OrderedDict):
            gib dict.__eq__(self, other) und all(map(_eq, self, other))
        gib dict.__eq__(self, other)

    def __ior__(self, other):
        self.update(other)
        gib self

    def __or__(self, other):
        wenn nicht isinstance(other, dict):
            gib NotImplemented
        new = self.__class__(self)
        new.update(other)
        gib new

    def __ror__(self, other):
        wenn nicht isinstance(other, dict):
            gib NotImplemented
        new = self.__class__(other)
        new.update(self)
        gib new


versuch:
    von _collections importiere OrderedDict
ausser ImportError:
    # Leave the pure Python version in place.
    pass


################################################################################
### namedtuple
################################################################################

versuch:
    von _collections importiere _tuplegetter
ausser ImportError:
    _tuplegetter = lambda index, doc: property(_itemgetter(index), doc=doc)

def namedtuple(typename, field_names, *, rename=Falsch, defaults=Nichts, module=Nichts):
    """Returns a new subclass of tuple mit named fields.

    >>> Point = namedtuple('Point', ['x', 'y'])
    >>> Point.__doc__                   # docstring fuer the new class
    'Point(x, y)'
    >>> p = Point(11, y=22)             # instantiate mit positional args oder keywords
    >>> p[0] + p[1]                     # indexable like a plain tuple
    33
    >>> x, y = p                        # unpack like a regular tuple
    >>> x, y
    (11, 22)
    >>> p.x + p.y                       # fields also accessible by name
    33
    >>> d = p._asdict()                 # convert to a dictionary
    >>> d['x']
    11
    >>> Point(**d)                      # convert von a dictionary
    Point(x=11, y=22)
    >>> p._replace(x=100)               # _replace() ist like str.replace() but targets named fields
    Point(x=100, y=22)

    """

    # Validate the field names.  At the user's option, either generate an error
    # message oder automatically replace the field name mit a valid name.
    wenn isinstance(field_names, str):
        field_names = field_names.replace(',', ' ').split()
    field_names = list(map(str, field_names))
    typename = _sys.intern(str(typename))

    wenn rename:
        seen = set()
        fuer index, name in enumerate(field_names):
            wenn (nicht name.isidentifier()
                oder _iskeyword(name)
                oder name.startswith('_')
                oder name in seen):
                field_names[index] = f'_{index}'
            seen.add(name)

    fuer name in [typename] + field_names:
        wenn type(name) ist nicht str:
            wirf TypeError('Type names und field names must be strings')
        wenn nicht name.isidentifier():
            wirf ValueError('Type names und field names must be valid '
                             f'identifiers: {name!r}')
        wenn _iskeyword(name):
            wirf ValueError('Type names und field names cannot be a '
                             f'keyword: {name!r}')

    seen = set()
    fuer name in field_names:
        wenn name.startswith('_') und nicht rename:
            wirf ValueError('Field names cannot start mit an underscore: '
                             f'{name!r}')
        wenn name in seen:
            wirf ValueError(f'Encountered duplicate field name: {name!r}')
        seen.add(name)

    field_defaults = {}
    wenn defaults ist nicht Nichts:
        defaults = tuple(defaults)
        wenn len(defaults) > len(field_names):
            wirf TypeError('Got more default values than field names')
        field_defaults = dict(reversed(list(zip(reversed(field_names),
                                                reversed(defaults)))))

    # Variables used in the methods und docstrings
    field_names = tuple(map(_sys.intern, field_names))
    num_fields = len(field_names)
    arg_list = ', '.join(field_names)
    wenn num_fields == 1:
        arg_list += ','
    repr_fmt = '(' + ', '.join(f'{name}=%r' fuer name in field_names) + ')'
    tuple_new = tuple.__new__
    _dict, _tuple, _len, _map, _zip = dict, tuple, len, map, zip

    # Create all the named tuple methods to be added to the klasse namespace

    namespace = {
        '_tuple_new': tuple_new,
        '__builtins__': {},
        '__name__': f'namedtuple_{typename}',
    }
    code = f'lambda _cls, {arg_list}: _tuple_new(_cls, ({arg_list}))'
    __new__ = eval(code, namespace)
    __new__.__name__ = '__new__'
    __new__.__doc__ = f'Create new instance of {typename}({arg_list})'
    wenn defaults ist nicht Nichts:
        __new__.__defaults__ = defaults

    @classmethod
    def _make(cls, iterable):
        result = tuple_new(cls, iterable)
        wenn _len(result) != num_fields:
            wirf TypeError(f'Expected {num_fields} arguments, got {len(result)}')
        gib result

    _make.__func__.__doc__ = (f'Make a new {typename} object von a sequence '
                              'or iterable')

    def _replace(self, /, **kwds):
        result = self._make(_map(kwds.pop, field_names, self))
        wenn kwds:
            wirf TypeError(f'Got unexpected field names: {list(kwds)!r}')
        gib result

    _replace.__doc__ = (f'Return a new {typename} object replacing specified '
                        'fields mit new values')

    def __repr__(self):
        'Return a nicely formatted representation string'
        gib self.__class__.__name__ + repr_fmt % self

    def _asdict(self):
        'Return a new dict which maps field names to their values.'
        gib _dict(_zip(self._fields, self))

    def __getnewargs__(self):
        'Return self als a plain tuple.  Used by copy und pickle.'
        gib _tuple(self)

    # Modify function metadata to help mit introspection und debugging
    fuer method in (
        __new__,
        _make.__func__,
        _replace,
        __repr__,
        _asdict,
        __getnewargs__,
    ):
        method.__qualname__ = f'{typename}.{method.__name__}'

    # Build-up the klasse namespace dictionary
    # und use type() to build the result class
    class_namespace = {
        '__doc__': f'{typename}({arg_list})',
        '__slots__': (),
        '_fields': field_names,
        '_field_defaults': field_defaults,
        '__new__': __new__,
        '_make': _make,
        '__replace__': _replace,
        '_replace': _replace,
        '__repr__': __repr__,
        '_asdict': _asdict,
        '__getnewargs__': __getnewargs__,
        '__match_args__': field_names,
    }
    fuer index, name in enumerate(field_names):
        doc = _sys.intern(f'Alias fuer field number {index}')
        class_namespace[name] = _tuplegetter(index, doc)

    result = type(typename, (tuple,), class_namespace)

    # For pickling to work, the __module__ variable needs to be set to the frame
    # where the named tuple ist created.  Bypass this step in environments where
    # sys._getframe ist nicht defined (Jython fuer example) oder sys._getframe ist not
    # defined fuer arguments greater than 0 (IronPython), oder where the user has
    # specified a particular module.
    wenn module ist Nichts:
        versuch:
            module = _sys._getframemodulename(1) oder '__main__'
        ausser AttributeError:
            versuch:
                module = _sys._getframe(1).f_globals.get('__name__', '__main__')
            ausser (AttributeError, ValueError):
                pass
    wenn module ist nicht Nichts:
        result.__module__ = module

    gib result


########################################################################
###  Counter
########################################################################

def _count_elements(mapping, iterable):
    'Tally elements von the iterable.'
    mapping_get = mapping.get
    fuer elem in iterable:
        mapping[elem] = mapping_get(elem, 0) + 1

versuch:                                    # Load C helper function wenn available
    von _collections importiere _count_elements
ausser ImportError:
    pass

klasse Counter(dict):
    '''Dict subclass fuer counting hashable items.  Sometimes called a bag
    oder multiset.  Elements are stored als dictionary keys und their counts
    are stored als dictionary values.

    >>> c = Counter('abcdeabcdabcaba')  # count elements von a string

    >>> c.most_common(3)                # three most common elements
    [('a', 5), ('b', 4), ('c', 3)]
    >>> sorted(c)                       # list all unique elements
    ['a', 'b', 'c', 'd', 'e']
    >>> ''.join(sorted(c.elements()))   # list elements mit repetitions
    'aaaaabbbbcccdde'
    >>> sum(c.values())                 # total of all counts
    15

    >>> c['a']                          # count of letter 'a'
    5
    >>> fuer elem in 'shazam':           # update counts von an iterable
    ...     c[elem] += 1                # by adding 1 to each element's count
    >>> c['a']                          # now there are seven 'a'
    7
    >>> loesche c['b']                      # remove all 'b'
    >>> c['b']                          # now there are zero 'b'
    0

    >>> d = Counter('simsalabim')       # make another counter
    >>> c.update(d)                     # add in the second counter
    >>> c['a']                          # now there are nine 'a'
    9

    >>> c.clear()                       # empty the counter
    >>> c
    Counter()

    Note:  If a count ist set to zero oder reduced to zero, it will remain
    in the counter until the entry ist deleted oder the counter ist cleared:

    >>> c = Counter('aaabbc')
    >>> c['b'] -= 2                     # reduce the count of 'b' by two
    >>> c.most_common()                 # 'b' ist still in, but its count ist zero
    [('a', 3), ('c', 1), ('b', 0)]

    '''
    # References:
    #   http://en.wikipedia.org/wiki/Multiset
    #   http://www.gnu.org/software/smalltalk/manual-base/html_node/Bag.html
    #   http://www.java2s.com/Tutorial/Cpp/0380__set-multiset/Catalog0380__set-multiset.htm
    #   http://code.activestate.com/recipes/259174/
    #   Knuth, TAOCP Vol. II section 4.6.3

    def __init__(self, iterable=Nichts, /, **kwds):
        '''Create a new, empty Counter object.  And wenn given, count elements
        von an input iterable.  Or, initialize the count von another mapping
        of elements to their counts.

        >>> c = Counter()                           # a new, empty counter
        >>> c = Counter('gallahad')                 # a new counter von an iterable
        >>> c = Counter({'a': 4, 'b': 2})           # a new counter von a mapping
        >>> c = Counter(a=4, b=2)                   # a new counter von keyword args

        '''
        super().__init__()
        self.update(iterable, **kwds)

    def __missing__(self, key):
        'The count of elements nicht in the Counter ist zero.'
        # Needed so that self[missing_item] does nicht wirf KeyError
        gib 0

    def total(self):
        'Sum of the counts'
        gib sum(self.values())

    def most_common(self, n=Nichts):
        '''List the n most common elements und their counts von the most
        common to the least.  If n ist Nichts, then list all element counts.

        >>> Counter('abracadabra').most_common(3)
        [('a', 5), ('b', 2), ('r', 2)]

        '''
        # Emulate Bag.sortedByCount von Smalltalk
        wenn n ist Nichts:
            gib sorted(self.items(), key=_itemgetter(1), reverse=Wahr)

        # Lazy importiere to speedup Python startup time
        global heapq
        wenn heapq ist Nichts:
            importiere heapq

        gib heapq.nlargest(n, self.items(), key=_itemgetter(1))

    def elements(self):
        '''Iterator over elements repeating each als many times als its count.

        >>> c = Counter('ABCABC')
        >>> sorted(c.elements())
        ['A', 'A', 'B', 'B', 'C', 'C']

        Knuth's example fuer prime factors of 1836:  2**2 * 3**3 * 17**1

        >>> importiere math
        >>> prime_factors = Counter({2: 2, 3: 3, 17: 1})
        >>> math.prod(prime_factors.elements())
        1836

        Note, wenn an element's count has been set to zero oder ist a negative
        number, elements() will ignore it.

        '''
        # Emulate Bag.do von Smalltalk und Multiset.begin von C++.
        gib _chain.from_iterable(_starmap(_repeat, self.items()))

    # Override dict methods where necessary

    @classmethod
    def fromkeys(cls, iterable, v=Nichts):
        # There ist no equivalent method fuer counters because the semantics
        # would be ambiguous in cases such als Counter.fromkeys('aaabbc', v=2).
        # Initializing counters to zero values isn't necessary because zero
        # ist already the default value fuer counter lookups.  Initializing
        # to one ist easily accomplished mit Counter(set(iterable)).  For
        # more exotic cases, create a dictionary first using a dictionary
        # comprehension oder dict.fromkeys().
        wirf NotImplementedError(
            'Counter.fromkeys() ist undefined.  Use Counter(iterable) instead.')

    def update(self, iterable=Nichts, /, **kwds):
        '''Like dict.update() but add counts instead of replacing them.

        Source can be an iterable, a dictionary, oder another Counter instance.

        >>> c = Counter('which')
        >>> c.update('witch')           # add elements von another iterable
        >>> d = Counter('watch')
        >>> c.update(d)                 # add elements von another counter
        >>> c['h']                      # four 'h' in which, witch, und watch
        4

        '''
        # The regular dict.update() operation makes no sense here because the
        # replace behavior results in some of the original untouched counts
        # being mixed-in mit all of the other counts fuer a mismash that
        # doesn't have a straight-forward interpretation in most counting
        # contexts.  Instead, we implement straight-addition.  Both the inputs
        # und outputs are allowed to contain zero und negative counts.

        wenn iterable ist nicht Nichts:
            wenn isinstance(iterable, _collections_abc.Mapping):
                wenn self:
                    self_get = self.get
                    fuer elem, count in iterable.items():
                        self[elem] = count + self_get(elem, 0)
                sonst:
                    # fast path when counter ist empty
                    super().update(iterable)
            sonst:
                _count_elements(self, iterable)
        wenn kwds:
            self.update(kwds)

    def subtract(self, iterable=Nichts, /, **kwds):
        '''Like dict.update() but subtracts counts instead of replacing them.
        Counts can be reduced below zero.  Both the inputs und outputs are
        allowed to contain zero und negative counts.

        Source can be an iterable, a dictionary, oder another Counter instance.

        >>> c = Counter('which')
        >>> c.subtract('witch')             # subtract elements von another iterable
        >>> c.subtract(Counter('watch'))    # subtract elements von another counter
        >>> c['h']                          # 2 in which, minus 1 in witch, minus 1 in watch
        0
        >>> c['w']                          # 1 in which, minus 1 in witch, minus 1 in watch
        -1

        '''
        wenn iterable ist nicht Nichts:
            self_get = self.get
            wenn isinstance(iterable, _collections_abc.Mapping):
                fuer elem, count in iterable.items():
                    self[elem] = self_get(elem, 0) - count
            sonst:
                fuer elem in iterable:
                    self[elem] = self_get(elem, 0) - 1
        wenn kwds:
            self.subtract(kwds)

    def copy(self):
        'Return a shallow copy.'
        gib self.__class__(self)

    def __reduce__(self):
        gib self.__class__, (dict(self),)

    def __delitem__(self, elem):
        'Like dict.__delitem__() but does nicht wirf KeyError fuer missing values.'
        wenn elem in self:
            super().__delitem__(elem)

    def __repr__(self):
        wenn nicht self:
            gib f'{self.__class__.__name__}()'
        versuch:
            # dict() preserves the ordering returned by most_common()
            d = dict(self.most_common())
        ausser TypeError:
            # handle case where values are nicht orderable
            d = dict(self)
        gib f'{self.__class__.__name__}({d!r})'

    # Multiset-style mathematical operations discussed in:
    #       Knuth TAOCP Volume II section 4.6.3 exercise 19
    #       und at http://en.wikipedia.org/wiki/Multiset
    #
    # Outputs guaranteed to only include positive counts.
    #
    # To strip negative und zero counts, add-in an empty counter:
    #       c += Counter()
    #
    # Results are ordered according to when an element ist first
    # encountered in the left operand und then by the order
    # encountered in the right operand.
    #
    # When the multiplicities are all zero oder one, multiset operations
    # are guaranteed to be equivalent to the corresponding operations
    # fuer regular sets.
    #
    #     Given counter multisets such as:
    #         cp = Counter(a=1, b=0, c=1)
    #         cq = Counter(c=1, d=0, e=1)
    #
    #     The corresponding regular sets would be:
    #         sp = {'a', 'c'}
    #         sq = {'c', 'e'}
    #
    #     All of the following relations would hold:
    #         (cp == cq) == (sp == sq)
    #         (cp != cq) == (sp != sq)
    #         (cp <= cq) == (sp <= sq)
    #         (cp < cq) == (sp < sq)
    #         (cp >= cq) == (sp >= sq)
    #         (cp > cq) == (sp > sq)
    #         set(cp + cq) == sp | sq
    #         set(cp - cq) == sp - sq
    #         set(cp | cq) == sp | sq
    #         set(cp & cq) == sp & sq

    def __eq__(self, other):
        'Wahr wenn all counts agree. Missing counts are treated als zero.'
        wenn nicht isinstance(other, Counter):
            gib NotImplemented
        gib all(self[e] == other[e] fuer c in (self, other) fuer e in c)

    def __ne__(self, other):
        'Wahr wenn any counts disagree. Missing counts are treated als zero.'
        wenn nicht isinstance(other, Counter):
            gib NotImplemented
        gib nicht self == other

    def __le__(self, other):
        'Wahr wenn all counts in self are a subset of those in other.'
        wenn nicht isinstance(other, Counter):
            gib NotImplemented
        gib all(self[e] <= other[e] fuer c in (self, other) fuer e in c)

    def __lt__(self, other):
        'Wahr wenn all counts in self are a proper subset of those in other.'
        wenn nicht isinstance(other, Counter):
            gib NotImplemented
        gib self <= other und self != other

    def __ge__(self, other):
        'Wahr wenn all counts in self are a superset of those in other.'
        wenn nicht isinstance(other, Counter):
            gib NotImplemented
        gib all(self[e] >= other[e] fuer c in (self, other) fuer e in c)

    def __gt__(self, other):
        'Wahr wenn all counts in self are a proper superset of those in other.'
        wenn nicht isinstance(other, Counter):
            gib NotImplemented
        gib self >= other und self != other

    def __add__(self, other):
        '''Add counts von two counters.

        >>> Counter('abbb') + Counter('bcc')
        Counter({'b': 4, 'c': 2, 'a': 1})

        '''
        wenn nicht isinstance(other, Counter):
            gib NotImplemented
        result = Counter()
        fuer elem, count in self.items():
            newcount = count + other[elem]
            wenn newcount > 0:
                result[elem] = newcount
        fuer elem, count in other.items():
            wenn elem nicht in self und count > 0:
                result[elem] = count
        gib result

    def __sub__(self, other):
        ''' Subtract count, but keep only results mit positive counts.

        >>> Counter('abbbc') - Counter('bccd')
        Counter({'b': 2, 'a': 1})

        '''
        wenn nicht isinstance(other, Counter):
            gib NotImplemented
        result = Counter()
        fuer elem, count in self.items():
            newcount = count - other[elem]
            wenn newcount > 0:
                result[elem] = newcount
        fuer elem, count in other.items():
            wenn elem nicht in self und count < 0:
                result[elem] = 0 - count
        gib result

    def __or__(self, other):
        '''Union ist the maximum of value in either of the input counters.

        >>> Counter('abbb') | Counter('bcc')
        Counter({'b': 3, 'c': 2, 'a': 1})

        '''
        wenn nicht isinstance(other, Counter):
            gib NotImplemented
        result = Counter()
        fuer elem, count in self.items():
            other_count = other[elem]
            newcount = other_count wenn count < other_count sonst count
            wenn newcount > 0:
                result[elem] = newcount
        fuer elem, count in other.items():
            wenn elem nicht in self und count > 0:
                result[elem] = count
        gib result

    def __and__(self, other):
        ''' Intersection ist the minimum of corresponding counts.

        >>> Counter('abbb') & Counter('bcc')
        Counter({'b': 1})

        '''
        wenn nicht isinstance(other, Counter):
            gib NotImplemented
        result = Counter()
        fuer elem, count in self.items():
            other_count = other[elem]
            newcount = count wenn count < other_count sonst other_count
            wenn newcount > 0:
                result[elem] = newcount
        gib result

    def __pos__(self):
        'Adds an empty counter, effectively stripping negative und zero counts'
        result = Counter()
        fuer elem, count in self.items():
            wenn count > 0:
                result[elem] = count
        gib result

    def __neg__(self):
        '''Subtracts von an empty counter.  Strips positive und zero counts,
        und flips the sign on negative counts.

        '''
        result = Counter()
        fuer elem, count in self.items():
            wenn count < 0:
                result[elem] = 0 - count
        gib result

    def _keep_positive(self):
        '''Internal method to strip elements mit a negative oder zero count'''
        nonpositive = [elem fuer elem, count in self.items() wenn nicht count > 0]
        fuer elem in nonpositive:
            loesche self[elem]
        gib self

    def __iadd__(self, other):
        '''Inplace add von another counter, keeping only positive counts.

        >>> c = Counter('abbb')
        >>> c += Counter('bcc')
        >>> c
        Counter({'b': 4, 'c': 2, 'a': 1})

        '''
        fuer elem, count in other.items():
            self[elem] += count
        gib self._keep_positive()

    def __isub__(self, other):
        '''Inplace subtract counter, but keep only results mit positive counts.

        >>> c = Counter('abbbc')
        >>> c -= Counter('bccd')
        >>> c
        Counter({'b': 2, 'a': 1})

        '''
        fuer elem, count in other.items():
            self[elem] -= count
        gib self._keep_positive()

    def __ior__(self, other):
        '''Inplace union ist the maximum of value von either counter.

        >>> c = Counter('abbb')
        >>> c |= Counter('bcc')
        >>> c
        Counter({'b': 3, 'c': 2, 'a': 1})

        '''
        fuer elem, other_count in other.items():
            count = self[elem]
            wenn other_count > count:
                self[elem] = other_count
        gib self._keep_positive()

    def __iand__(self, other):
        '''Inplace intersection ist the minimum of corresponding counts.

        >>> c = Counter('abbb')
        >>> c &= Counter('bcc')
        >>> c
        Counter({'b': 1})

        '''
        fuer elem, count in self.items():
            other_count = other[elem]
            wenn other_count < count:
                self[elem] = other_count
        gib self._keep_positive()


########################################################################
###  ChainMap
########################################################################

klasse ChainMap(_collections_abc.MutableMapping):
    ''' A ChainMap groups multiple dicts (or other mappings) together
    to create a single, updateable view.

    The underlying mappings are stored in a list.  That list ist public und can
    be accessed oder updated using the *maps* attribute.  There ist no other
    state.

    Lookups search the underlying mappings successively until a key ist found.
    In contrast, writes, updates, und deletions only operate on the first
    mapping.

    '''

    def __init__(self, *maps):
        '''Initialize a ChainMap by setting *maps* to the given mappings.
        If no mappings are provided, a single empty dictionary ist used.

        '''
        self.maps = list(maps) oder [{}]          # always at least one map

    def __missing__(self, key):
        wirf KeyError(key)

    def __getitem__(self, key):
        fuer mapping in self.maps:
            versuch:
                gib mapping[key]             # can't use 'key in mapping' mit defaultdict
            ausser KeyError:
                pass
        gib self.__missing__(key)            # support subclasses that define __missing__

    def get(self, key, default=Nichts):
        gib self[key] wenn key in self sonst default    # needs to make use of __contains__

    def __len__(self):
        gib len(set().union(*self.maps))     # reuses stored hash values wenn possible

    def __iter__(self):
        d = {}
        fuer mapping in map(dict.fromkeys, reversed(self.maps)):
            d |= mapping                        # reuses stored hash values wenn possible
        gib iter(d)

    def __contains__(self, key):
        fuer mapping in self.maps:
            wenn key in mapping:
                gib Wahr
        gib Falsch

    def __bool__(self):
        gib any(self.maps)

    @_recursive_repr()
    def __repr__(self):
        gib f'{self.__class__.__name__}({", ".join(map(repr, self.maps))})'

    @classmethod
    def fromkeys(cls, iterable, value=Nichts, /):
        'Create a new ChainMap mit keys von iterable und values set to value.'
        gib cls(dict.fromkeys(iterable, value))

    def copy(self):
        'New ChainMap oder subclass mit a new copy of maps[0] und refs to maps[1:]'
        gib self.__class__(self.maps[0].copy(), *self.maps[1:])

    __copy__ = copy

    def new_child(self, m=Nichts, **kwargs):      # like Django's Context.push()
        '''New ChainMap mit a new map followed by all previous maps.
        If no map ist provided, an empty dict ist used.
        Keyword arguments update the map oder new empty dict.
        '''
        wenn m ist Nichts:
            m = kwargs
        sowenn kwargs:
            m.update(kwargs)
        gib self.__class__(m, *self.maps)

    @property
    def parents(self):                          # like Django's Context.pop()
        'New ChainMap von maps[1:].'
        gib self.__class__(*self.maps[1:])

    def __setitem__(self, key, value):
        self.maps[0][key] = value

    def __delitem__(self, key):
        versuch:
            loesche self.maps[0][key]
        ausser KeyError:
            wirf KeyError(f'Key nicht found in the first mapping: {key!r}')

    def popitem(self):
        'Remove und gib an item pair von maps[0]. Raise KeyError ist maps[0] ist empty.'
        versuch:
            gib self.maps[0].popitem()
        ausser KeyError:
            wirf KeyError('No keys found in the first mapping.')

    def pop(self, key, *args):
        'Remove *key* von maps[0] und gib its value. Raise KeyError wenn *key* nicht in maps[0].'
        versuch:
            gib self.maps[0].pop(key, *args)
        ausser KeyError:
            wirf KeyError(f'Key nicht found in the first mapping: {key!r}')

    def clear(self):
        'Clear maps[0], leaving maps[1:] intact.'
        self.maps[0].clear()

    def __ior__(self, other):
        self.maps[0].update(other)
        gib self

    def __or__(self, other):
        wenn nicht isinstance(other, _collections_abc.Mapping):
            gib NotImplemented
        m = self.copy()
        m.maps[0].update(other)
        gib m

    def __ror__(self, other):
        wenn nicht isinstance(other, _collections_abc.Mapping):
            gib NotImplemented
        m = dict(other)
        fuer child in reversed(self.maps):
            m.update(child)
        gib self.__class__(m)


################################################################################
### UserDict
################################################################################

klasse UserDict(_collections_abc.MutableMapping):

    # Start by filling-out the abstract methods
    def __init__(self, dict=Nichts, /, **kwargs):
        self.data = {}
        wenn dict ist nicht Nichts:
            self.update(dict)
        wenn kwargs:
            self.update(kwargs)

    def __len__(self):
        gib len(self.data)

    def __getitem__(self, key):
        wenn key in self.data:
            gib self.data[key]
        wenn hasattr(self.__class__, "__missing__"):
            gib self.__class__.__missing__(self, key)
        wirf KeyError(key)

    def __setitem__(self, key, item):
        self.data[key] = item

    def __delitem__(self, key):
        loesche self.data[key]

    def __iter__(self):
        gib iter(self.data)

    # Modify __contains__ und get() to work like dict
    # does when __missing__ ist present.
    def __contains__(self, key):
        gib key in self.data

    def get(self, key, default=Nichts):
        wenn key in self:
            gib self[key]
        gib default


    # Now, add the methods in dicts but nicht in MutableMapping
    def __repr__(self):
        gib repr(self.data)

    def __or__(self, other):
        wenn isinstance(other, UserDict):
            gib self.__class__(self.data | other.data)
        wenn isinstance(other, dict):
            gib self.__class__(self.data | other)
        gib NotImplemented

    def __ror__(self, other):
        wenn isinstance(other, UserDict):
            gib self.__class__(other.data | self.data)
        wenn isinstance(other, dict):
            gib self.__class__(other | self.data)
        gib NotImplemented

    def __ior__(self, other):
        wenn isinstance(other, UserDict):
            self.data |= other.data
        sonst:
            self.data |= other
        gib self

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy und avoid triggering descriptors
        inst.__dict__["data"] = self.__dict__["data"].copy()
        gib inst

    def copy(self):
        wenn self.__class__ ist UserDict:
            gib UserDict(self.data.copy())
        importiere copy
        data = self.data
        versuch:
            self.data = {}
            c = copy.copy(self)
        schliesslich:
            self.data = data
        c.update(self)
        gib c

    @classmethod
    def fromkeys(cls, iterable, value=Nichts):
        d = cls()
        fuer key in iterable:
            d[key] = value
        gib d


################################################################################
### UserList
################################################################################

klasse UserList(_collections_abc.MutableSequence):
    """A more oder less complete user-defined wrapper around list objects."""

    def __init__(self, initlist=Nichts):
        self.data = []
        wenn initlist ist nicht Nichts:
            # XXX should this accept an arbitrary sequence?
            wenn type(initlist) == type(self.data):
                self.data[:] = initlist
            sowenn isinstance(initlist, UserList):
                self.data[:] = initlist.data[:]
            sonst:
                self.data = list(initlist)

    def __repr__(self):
        gib repr(self.data)

    def __lt__(self, other):
        gib self.data < self.__cast(other)

    def __le__(self, other):
        gib self.data <= self.__cast(other)

    def __eq__(self, other):
        gib self.data == self.__cast(other)

    def __gt__(self, other):
        gib self.data > self.__cast(other)

    def __ge__(self, other):
        gib self.data >= self.__cast(other)

    def __cast(self, other):
        gib other.data wenn isinstance(other, UserList) sonst other

    def __contains__(self, item):
        gib item in self.data

    def __len__(self):
        gib len(self.data)

    def __getitem__(self, i):
        wenn isinstance(i, slice):
            gib self.__class__(self.data[i])
        sonst:
            gib self.data[i]

    def __setitem__(self, i, item):
        self.data[i] = item

    def __delitem__(self, i):
        loesche self.data[i]

    def __add__(self, other):
        wenn isinstance(other, UserList):
            gib self.__class__(self.data + other.data)
        sowenn isinstance(other, type(self.data)):
            gib self.__class__(self.data + other)
        gib self.__class__(self.data + list(other))

    def __radd__(self, other):
        wenn isinstance(other, UserList):
            gib self.__class__(other.data + self.data)
        sowenn isinstance(other, type(self.data)):
            gib self.__class__(other + self.data)
        gib self.__class__(list(other) + self.data)

    def __iadd__(self, other):
        wenn isinstance(other, UserList):
            self.data += other.data
        sowenn isinstance(other, type(self.data)):
            self.data += other
        sonst:
            self.data += list(other)
        gib self

    def __mul__(self, n):
        gib self.__class__(self.data * n)

    __rmul__ = __mul__

    def __imul__(self, n):
        self.data *= n
        gib self

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy und avoid triggering descriptors
        inst.__dict__["data"] = self.__dict__["data"][:]
        gib inst

    def append(self, item):
        self.data.append(item)

    def insert(self, i, item):
        self.data.insert(i, item)

    def pop(self, i=-1):
        gib self.data.pop(i)

    def remove(self, item):
        self.data.remove(item)

    def clear(self):
        self.data.clear()

    def copy(self):
        gib self.__class__(self)

    def count(self, item):
        gib self.data.count(item)

    def index(self, item, *args):
        gib self.data.index(item, *args)

    def reverse(self):
        self.data.reverse()

    def sort(self, /, *args, **kwds):
        self.data.sort(*args, **kwds)

    def extend(self, other):
        wenn isinstance(other, UserList):
            self.data.extend(other.data)
        sonst:
            self.data.extend(other)


################################################################################
### UserString
################################################################################

klasse UserString(_collections_abc.Sequence):

    def __init__(self, seq):
        wenn isinstance(seq, str):
            self.data = seq
        sowenn isinstance(seq, UserString):
            self.data = seq.data[:]
        sonst:
            self.data = str(seq)

    def __str__(self):
        gib str(self.data)

    def __repr__(self):
        gib repr(self.data)

    def __int__(self):
        gib int(self.data)

    def __float__(self):
        gib float(self.data)

    def __complex__(self):
        gib complex(self.data)

    def __hash__(self):
        gib hash(self.data)

    def __getnewargs__(self):
        gib (self.data[:],)

    def __eq__(self, string):
        wenn isinstance(string, UserString):
            gib self.data == string.data
        gib self.data == string

    def __lt__(self, string):
        wenn isinstance(string, UserString):
            gib self.data < string.data
        gib self.data < string

    def __le__(self, string):
        wenn isinstance(string, UserString):
            gib self.data <= string.data
        gib self.data <= string

    def __gt__(self, string):
        wenn isinstance(string, UserString):
            gib self.data > string.data
        gib self.data > string

    def __ge__(self, string):
        wenn isinstance(string, UserString):
            gib self.data >= string.data
        gib self.data >= string

    def __contains__(self, char):
        wenn isinstance(char, UserString):
            char = char.data
        gib char in self.data

    def __len__(self):
        gib len(self.data)

    def __getitem__(self, index):
        gib self.__class__(self.data[index])

    def __add__(self, other):
        wenn isinstance(other, UserString):
            gib self.__class__(self.data + other.data)
        sowenn isinstance(other, str):
            gib self.__class__(self.data + other)
        gib self.__class__(self.data + str(other))

    def __radd__(self, other):
        wenn isinstance(other, str):
            gib self.__class__(other + self.data)
        gib self.__class__(str(other) + self.data)

    def __mul__(self, n):
        gib self.__class__(self.data * n)

    __rmul__ = __mul__

    def __mod__(self, args):
        gib self.__class__(self.data % args)

    def __rmod__(self, template):
        gib self.__class__(str(template) % self)

    # the following methods are defined in alphabetical order:
    def capitalize(self):
        gib self.__class__(self.data.capitalize())

    def casefold(self):
        gib self.__class__(self.data.casefold())

    def center(self, width, *args):
        gib self.__class__(self.data.center(width, *args))

    def count(self, sub, start=0, end=_sys.maxsize):
        wenn isinstance(sub, UserString):
            sub = sub.data
        gib self.data.count(sub, start, end)

    def removeprefix(self, prefix, /):
        wenn isinstance(prefix, UserString):
            prefix = prefix.data
        gib self.__class__(self.data.removeprefix(prefix))

    def removesuffix(self, suffix, /):
        wenn isinstance(suffix, UserString):
            suffix = suffix.data
        gib self.__class__(self.data.removesuffix(suffix))

    def encode(self, encoding='utf-8', errors='strict'):
        encoding = 'utf-8' wenn encoding ist Nichts sonst encoding
        errors = 'strict' wenn errors ist Nichts sonst errors
        gib self.data.encode(encoding, errors)

    def endswith(self, suffix, start=0, end=_sys.maxsize):
        gib self.data.endswith(suffix, start, end)

    def expandtabs(self, tabsize=8):
        gib self.__class__(self.data.expandtabs(tabsize))

    def find(self, sub, start=0, end=_sys.maxsize):
        wenn isinstance(sub, UserString):
            sub = sub.data
        gib self.data.find(sub, start, end)

    def format(self, /, *args, **kwds):
        gib self.data.format(*args, **kwds)

    def format_map(self, mapping):
        gib self.data.format_map(mapping)

    def index(self, sub, start=0, end=_sys.maxsize):
        gib self.data.index(sub, start, end)

    def isalpha(self):
        gib self.data.isalpha()

    def isalnum(self):
        gib self.data.isalnum()

    def isascii(self):
        gib self.data.isascii()

    def isdecimal(self):
        gib self.data.isdecimal()

    def isdigit(self):
        gib self.data.isdigit()

    def isidentifier(self):
        gib self.data.isidentifier()

    def islower(self):
        gib self.data.islower()

    def isnumeric(self):
        gib self.data.isnumeric()

    def isprintable(self):
        gib self.data.isprintable()

    def isspace(self):
        gib self.data.isspace()

    def istitle(self):
        gib self.data.istitle()

    def isupper(self):
        gib self.data.isupper()

    def join(self, seq):
        gib self.data.join(seq)

    def ljust(self, width, *args):
        gib self.__class__(self.data.ljust(width, *args))

    def lower(self):
        gib self.__class__(self.data.lower())

    def lstrip(self, chars=Nichts):
        gib self.__class__(self.data.lstrip(chars))

    maketrans = str.maketrans

    def partition(self, sep):
        gib self.data.partition(sep)

    def replace(self, old, new, maxsplit=-1):
        wenn isinstance(old, UserString):
            old = old.data
        wenn isinstance(new, UserString):
            new = new.data
        gib self.__class__(self.data.replace(old, new, maxsplit))

    def rfind(self, sub, start=0, end=_sys.maxsize):
        wenn isinstance(sub, UserString):
            sub = sub.data
        gib self.data.rfind(sub, start, end)

    def rindex(self, sub, start=0, end=_sys.maxsize):
        gib self.data.rindex(sub, start, end)

    def rjust(self, width, *args):
        gib self.__class__(self.data.rjust(width, *args))

    def rpartition(self, sep):
        gib self.data.rpartition(sep)

    def rstrip(self, chars=Nichts):
        gib self.__class__(self.data.rstrip(chars))

    def split(self, sep=Nichts, maxsplit=-1):
        gib self.data.split(sep, maxsplit)

    def rsplit(self, sep=Nichts, maxsplit=-1):
        gib self.data.rsplit(sep, maxsplit)

    def splitlines(self, keepends=Falsch):
        gib self.data.splitlines(keepends)

    def startswith(self, prefix, start=0, end=_sys.maxsize):
        gib self.data.startswith(prefix, start, end)

    def strip(self, chars=Nichts):
        gib self.__class__(self.data.strip(chars))

    def swapcase(self):
        gib self.__class__(self.data.swapcase())

    def title(self):
        gib self.__class__(self.data.title())

    def translate(self, *args):
        gib self.__class__(self.data.translate(*args))

    def upper(self):
        gib self.__class__(self.data.upper())

    def zfill(self, width):
        gib self.__class__(self.data.zfill(width))
