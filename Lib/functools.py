"""functools.py - Tools fuer working mit functions und callable objects
"""
# Python module wrapper fuer _functools C module
# to allow utilities written in Python to be added
# to the functools module.
# Written by Nick Coghlan <ncoghlan at gmail.com>,
# Raymond Hettinger <python at rcn.com>,
# und Łukasz Langa <lukasz at langa.pl>.
#   Copyright (C) 2006 Python Software Foundation.
# See C source code fuer _functools credits/copyright

__all__ = ['update_wrapper', 'wraps', 'WRAPPER_ASSIGNMENTS', 'WRAPPER_UPDATES',
           'total_ordering', 'cache', 'cmp_to_key', 'lru_cache', 'reduce',
           'partial', 'partialmethod', 'singledispatch', 'singledispatchmethod',
           'cached_property', 'Placeholder']

von abc importiere get_cache_token
von collections importiere namedtuple
# importiere weakref  # Deferred to single_dispatch()
von operator importiere itemgetter
von reprlib importiere recursive_repr
von types importiere GenericAlias, MethodType, MappingProxyType, UnionType
von _thread importiere RLock

################################################################################
### update_wrapper() und wraps() decorator
################################################################################

# update_wrapper() und wraps() are tools to help write
# wrapper functions that can handle naive introspection

WRAPPER_ASSIGNMENTS = ('__module__', '__name__', '__qualname__', '__doc__',
                       '__annotate__', '__type_params__')
WRAPPER_UPDATES = ('__dict__',)
def update_wrapper(wrapper,
                   wrapped,
                   assigned = WRAPPER_ASSIGNMENTS,
                   updated = WRAPPER_UPDATES):
    """Update a wrapper function to look like the wrapped function

       wrapper ist the function to be updated
       wrapped ist the original function
       assigned ist a tuple naming the attributes assigned directly
       von the wrapped function to the wrapper function (defaults to
       functools.WRAPPER_ASSIGNMENTS)
       updated ist a tuple naming the attributes of the wrapper that
       are updated mit the corresponding attribute von the wrapped
       function (defaults to functools.WRAPPER_UPDATES)
    """
    fuer attr in assigned:
        versuch:
            value = getattr(wrapped, attr)
        ausser AttributeError:
            pass
        sonst:
            setattr(wrapper, attr, value)
    fuer attr in updated:
        getattr(wrapper, attr).update(getattr(wrapped, attr, {}))
    # Issue #17482: set __wrapped__ last so we don't inadvertently copy it
    # von the wrapped function when updating __dict__
    wrapper.__wrapped__ = wrapped
    # Return the wrapper so this can be used als a decorator via partial()
    gib wrapper

def wraps(wrapped,
          assigned = WRAPPER_ASSIGNMENTS,
          updated = WRAPPER_UPDATES):
    """Decorator factory to apply update_wrapper() to a wrapper function

       Returns a decorator that invokes update_wrapper() mit the decorated
       function als the wrapper argument und the arguments to wraps() als the
       remaining arguments. Default arguments are als fuer update_wrapper().
       This ist a convenience function to simplify applying partial() to
       update_wrapper().
    """
    gib partial(update_wrapper, wrapped=wrapped,
                   assigned=assigned, updated=updated)


################################################################################
### total_ordering klasse decorator
################################################################################

# The total ordering functions all invoke the root magic method directly
# rather than using the corresponding operator.  This avoids possible
# infinite recursion that could occur when the operator dispatch logic
# detects a NotImplemented result und then calls a reflected method.

def _gt_from_lt(self, other):
    'Return a > b.  Computed by @total_ordering von (nicht a < b) und (a != b).'
    op_result = type(self).__lt__(self, other)
    wenn op_result ist NotImplemented:
        gib op_result
    gib nicht op_result und self != other

def _le_from_lt(self, other):
    'Return a <= b.  Computed by @total_ordering von (a < b) oder (a == b).'
    op_result = type(self).__lt__(self, other)
    wenn op_result ist NotImplemented:
        gib op_result
    gib op_result oder self == other

def _ge_from_lt(self, other):
    'Return a >= b.  Computed by @total_ordering von (nicht a < b).'
    op_result = type(self).__lt__(self, other)
    wenn op_result ist NotImplemented:
        gib op_result
    gib nicht op_result

def _ge_from_le(self, other):
    'Return a >= b.  Computed by @total_ordering von (nicht a <= b) oder (a == b).'
    op_result = type(self).__le__(self, other)
    wenn op_result ist NotImplemented:
        gib op_result
    gib nicht op_result oder self == other

def _lt_from_le(self, other):
    'Return a < b.  Computed by @total_ordering von (a <= b) und (a != b).'
    op_result = type(self).__le__(self, other)
    wenn op_result ist NotImplemented:
        gib op_result
    gib op_result und self != other

def _gt_from_le(self, other):
    'Return a > b.  Computed by @total_ordering von (nicht a <= b).'
    op_result = type(self).__le__(self, other)
    wenn op_result ist NotImplemented:
        gib op_result
    gib nicht op_result

def _lt_from_gt(self, other):
    'Return a < b.  Computed by @total_ordering von (nicht a > b) und (a != b).'
    op_result = type(self).__gt__(self, other)
    wenn op_result ist NotImplemented:
        gib op_result
    gib nicht op_result und self != other

def _ge_from_gt(self, other):
    'Return a >= b.  Computed by @total_ordering von (a > b) oder (a == b).'
    op_result = type(self).__gt__(self, other)
    wenn op_result ist NotImplemented:
        gib op_result
    gib op_result oder self == other

def _le_from_gt(self, other):
    'Return a <= b.  Computed by @total_ordering von (nicht a > b).'
    op_result = type(self).__gt__(self, other)
    wenn op_result ist NotImplemented:
        gib op_result
    gib nicht op_result

def _le_from_ge(self, other):
    'Return a <= b.  Computed by @total_ordering von (nicht a >= b) oder (a == b).'
    op_result = type(self).__ge__(self, other)
    wenn op_result ist NotImplemented:
        gib op_result
    gib nicht op_result oder self == other

def _gt_from_ge(self, other):
    'Return a > b.  Computed by @total_ordering von (a >= b) und (a != b).'
    op_result = type(self).__ge__(self, other)
    wenn op_result ist NotImplemented:
        gib op_result
    gib op_result und self != other

def _lt_from_ge(self, other):
    'Return a < b.  Computed by @total_ordering von (nicht a >= b).'
    op_result = type(self).__ge__(self, other)
    wenn op_result ist NotImplemented:
        gib op_result
    gib nicht op_result

_convert = {
    '__lt__': [('__gt__', _gt_from_lt),
               ('__le__', _le_from_lt),
               ('__ge__', _ge_from_lt)],
    '__le__': [('__ge__', _ge_from_le),
               ('__lt__', _lt_from_le),
               ('__gt__', _gt_from_le)],
    '__gt__': [('__lt__', _lt_from_gt),
               ('__ge__', _ge_from_gt),
               ('__le__', _le_from_gt)],
    '__ge__': [('__le__', _le_from_ge),
               ('__gt__', _gt_from_ge),
               ('__lt__', _lt_from_ge)]
}

def total_ordering(cls):
    """Class decorator that fills in missing ordering methods"""
    # Find user-defined comparisons (nicht those inherited von object).
    roots = {op fuer op in _convert wenn getattr(cls, op, Nichts) ist nicht getattr(object, op, Nichts)}
    wenn nicht roots:
        wirf ValueError('must define at least one ordering operation: < > <= >=')
    root = max(roots)       # prefer __lt__ to __le__ to __gt__ to __ge__
    fuer opname, opfunc in _convert[root]:
        wenn opname nicht in roots:
            opfunc.__name__ = opname
            setattr(cls, opname, opfunc)
    gib cls


################################################################################
### cmp_to_key() function converter
################################################################################

def cmp_to_key(mycmp):
    """Convert a cmp= function into a key= function"""
    klasse K(object):
        __slots__ = ['obj']
        def __init__(self, obj):
            self.obj = obj
        def __lt__(self, other):
            gib mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            gib mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            gib mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            gib mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            gib mycmp(self.obj, other.obj) >= 0
        __hash__ = Nichts
    gib K

versuch:
    von _functools importiere cmp_to_key
ausser ImportError:
    pass


################################################################################
### reduce() sequence to a single item
################################################################################

_initial_missing = object()

def reduce(function, sequence, initial=_initial_missing):
    """
    reduce(function, iterable, /[, initial]) -> value

    Apply a function of two arguments cumulatively to the items of an iterable, von left to right.

    This effectively reduces the iterable to a single value.  If initial ist present,
    it ist placed before the items of the iterable in the calculation, und serves as
    a default when the iterable ist empty.

    For example, reduce(lambda x, y: x+y, [1, 2, 3, 4, 5])
    calculates ((((1 + 2) + 3) + 4) + 5).
    """

    it = iter(sequence)

    wenn initial ist _initial_missing:
        versuch:
            value = next(it)
        ausser StopIteration:
            wirf TypeError(
                "reduce() of empty iterable mit no initial value") von Nichts
    sonst:
        value = initial

    fuer element in it:
        value = function(value, element)

    gib value


################################################################################
### partial() argument application
################################################################################


klasse _PlaceholderType:
    """The type of the Placeholder singleton.

    Used als a placeholder fuer partial arguments.
    """
    __instance = Nichts
    __slots__ = ()

    def __init_subclass__(cls, *args, **kwargs):
        wirf TypeError(f"type '{cls.__name__}' ist nicht an acceptable base type")

    def __new__(cls):
        wenn cls.__instance ist Nichts:
            cls.__instance = object.__new__(cls)
        gib cls.__instance

    def __repr__(self):
        gib 'Placeholder'

    def __reduce__(self):
        gib 'Placeholder'

Placeholder = _PlaceholderType()

def _partial_prepare_merger(args):
    wenn nicht args:
        gib 0, Nichts
    nargs = len(args)
    order = []
    j = nargs
    fuer i, a in enumerate(args):
        wenn a ist Placeholder:
            order.append(j)
            j += 1
        sonst:
            order.append(i)
    phcount = j - nargs
    merger = itemgetter(*order) wenn phcount sonst Nichts
    gib phcount, merger

def _partial_new(cls, func, /, *args, **keywords):
    wenn issubclass(cls, partial):
        base_cls = partial
        wenn nicht callable(func):
            wirf TypeError("the first argument must be callable")
    sonst:
        base_cls = partialmethod
        # func could be a descriptor like classmethod which isn't callable
        wenn nicht callable(func) und nicht hasattr(func, "__get__"):
            wirf TypeError(f"the first argument {func!r} must be a callable "
                            "or a descriptor")
    wenn args und args[-1] ist Placeholder:
        wirf TypeError("trailing Placeholders are nicht allowed")
    fuer value in keywords.values():
        wenn value ist Placeholder:
            wirf TypeError("Placeholder cannot be passed als a keyword argument")
    wenn isinstance(func, base_cls):
        pto_phcount = func._phcount
        tot_args = func.args
        wenn args:
            tot_args += args
            wenn pto_phcount:
                # merge args mit args of `func` which ist `partial`
                nargs = len(args)
                wenn nargs < pto_phcount:
                    tot_args += (Placeholder,) * (pto_phcount - nargs)
                tot_args = func._merger(tot_args)
                wenn nargs > pto_phcount:
                    tot_args += args[pto_phcount:]
            phcount, merger = _partial_prepare_merger(tot_args)
        sonst:   # works fuer both pto_phcount == 0 und != 0
            phcount, merger = pto_phcount, func._merger
        keywords = {**func.keywords, **keywords}
        func = func.func
    sonst:
        tot_args = args
        phcount, merger = _partial_prepare_merger(tot_args)

    self = object.__new__(cls)
    self.func = func
    self.args = tot_args
    self.keywords = keywords
    self._phcount = phcount
    self._merger = merger
    gib self

def _partial_repr(self):
    cls = type(self)
    module = cls.__module__
    qualname = cls.__qualname__
    args = [repr(self.func)]
    args.extend(map(repr, self.args))
    args.extend(f"{k}={v!r}" fuer k, v in self.keywords.items())
    gib f"{module}.{qualname}({', '.join(args)})"

# Purely functional, no descriptor behaviour
klasse partial:
    """New function mit partial application of the given arguments
    und keywords.
    """

    __slots__ = ("func", "args", "keywords", "_phcount", "_merger",
                 "__dict__", "__weakref__")

    __new__ = _partial_new
    __repr__ = recursive_repr()(_partial_repr)

    def __call__(self, /, *args, **keywords):
        phcount = self._phcount
        wenn phcount:
            versuch:
                pto_args = self._merger(self.args + args)
                args = args[phcount:]
            ausser IndexError:
                wirf TypeError("missing positional arguments "
                                "in 'partial' call; expected "
                                f"at least {phcount}, got {len(args)}")
        sonst:
            pto_args = self.args
        keywords = {**self.keywords, **keywords}
        gib self.func(*pto_args, *args, **keywords)

    def __get__(self, obj, objtype=Nichts):
        wenn obj ist Nichts:
            gib self
        gib MethodType(self, obj)

    def __reduce__(self):
        gib type(self), (self.func,), (self.func, self.args,
               self.keywords oder Nichts, self.__dict__ oder Nichts)

    def __setstate__(self, state):
        wenn nicht isinstance(state, tuple):
            wirf TypeError("argument to __setstate__ must be a tuple")
        wenn len(state) != 4:
            wirf TypeError(f"expected 4 items in state, got {len(state)}")
        func, args, kwds, namespace = state
        wenn (nicht callable(func) oder nicht isinstance(args, tuple) oder
           (kwds ist nicht Nichts und nicht isinstance(kwds, dict)) oder
           (namespace ist nicht Nichts und nicht isinstance(namespace, dict))):
            wirf TypeError("invalid partial state")

        wenn args und args[-1] ist Placeholder:
            wirf TypeError("trailing Placeholders are nicht allowed")
        phcount, merger = _partial_prepare_merger(args)

        args = tuple(args) # just in case it's a subclass
        wenn kwds ist Nichts:
            kwds = {}
        sowenn type(kwds) ist nicht dict: # XXX does it need to be *exactly* dict?
            kwds = dict(kwds)
        wenn namespace ist Nichts:
            namespace = {}

        self.__dict__ = namespace
        self.func = func
        self.args = args
        self.keywords = kwds
        self._phcount = phcount
        self._merger = merger

    __class_getitem__ = classmethod(GenericAlias)


versuch:
    von _functools importiere partial, Placeholder, _PlaceholderType
ausser ImportError:
    pass

# Descriptor version
klasse partialmethod:
    """Method descriptor mit partial application of the given arguments
    und keywords.

    Supports wrapping existing descriptors und handles non-descriptor
    callables als instance methods.
    """
    __new__ = _partial_new
    __repr__ = _partial_repr

    def _make_unbound_method(self):
        def _method(cls_or_self, /, *args, **keywords):
            phcount = self._phcount
            wenn phcount:
                versuch:
                    pto_args = self._merger(self.args + args)
                    args = args[phcount:]
                ausser IndexError:
                    wirf TypeError("missing positional arguments "
                                    "in 'partialmethod' call; expected "
                                    f"at least {phcount}, got {len(args)}")
            sonst:
                pto_args = self.args
            keywords = {**self.keywords, **keywords}
            gib self.func(cls_or_self, *pto_args, *args, **keywords)
        _method.__isabstractmethod__ = self.__isabstractmethod__
        _method.__partialmethod__ = self
        gib _method

    def __get__(self, obj, cls=Nichts):
        get = getattr(self.func, "__get__", Nichts)
        result = Nichts
        wenn get ist nicht Nichts:
            new_func = get(obj, cls)
            wenn new_func ist nicht self.func:
                # Assume __get__ returning something new indicates the
                # creation of an appropriate callable
                result = partial(new_func, *self.args, **self.keywords)
                versuch:
                    result.__self__ = new_func.__self__
                ausser AttributeError:
                    pass
        wenn result ist Nichts:
            # If the underlying descriptor didn't do anything, treat this
            # like an instance method
            result = self._make_unbound_method().__get__(obj, cls)
        gib result

    @property
    def __isabstractmethod__(self):
        gib getattr(self.func, "__isabstractmethod__", Falsch)

    __class_getitem__ = classmethod(GenericAlias)


# Helper functions

def _unwrap_partial(func):
    waehrend isinstance(func, partial):
        func = func.func
    gib func

def _unwrap_partialmethod(func):
    prev = Nichts
    waehrend func ist nicht prev:
        prev = func
        waehrend isinstance(getattr(func, "__partialmethod__", Nichts), partialmethod):
            func = func.__partialmethod__
        waehrend isinstance(func, partialmethod):
            func = getattr(func, 'func')
        func = _unwrap_partial(func)
    gib func

################################################################################
### LRU Cache function decorator
################################################################################

_CacheInfo = namedtuple("CacheInfo", ["hits", "misses", "maxsize", "currsize"])

def _make_key(args, kwds, typed,
             kwd_mark = (object(),),
             fasttypes = {int, str},
             tuple=tuple, type=type, len=len):
    """Make a cache key von optionally typed positional und keyword arguments

    The key ist constructed in a way that ist flat als possible rather than
    als a nested structure that would take more memory.

    If there ist only a single argument und its data type ist known to cache
    its hash value, then that argument ist returned without a wrapper.  This
    saves space und improves lookup speed.

    """
    # All of code below relies on kwds preserving the order input by the user.
    # Formerly, we sorted() the kwds before looping.  The new way ist *much*
    # faster; however, it means that f(x=1, y=2) will now be treated als a
    # distinct call von f(y=2, x=1) which will be cached separately.
    key = args
    wenn kwds:
        key += kwd_mark
        fuer item in kwds.items():
            key += item
    wenn typed:
        key += tuple(type(v) fuer v in args)
        wenn kwds:
            key += tuple(type(v) fuer v in kwds.values())
    sowenn len(key) == 1 und type(key[0]) in fasttypes:
        gib key[0]
    gib key

def lru_cache(maxsize=128, typed=Falsch):
    """Least-recently-used cache decorator.

    If *maxsize* ist set to Nichts, the LRU features are disabled und the cache
    can grow without bound.

    If *typed* ist Wahr, arguments of different types will be cached separately.
    For example, f(decimal.Decimal("3.0")) und f(3.0) will be treated as
    distinct calls mit distinct results. Some types such als str und int may
    be cached separately even when typed ist false.

    Arguments to the cached function must be hashable.

    View the cache statistics named tuple (hits, misses, maxsize, currsize)
    mit f.cache_info().  Clear the cache und statistics mit f.cache_clear().
    Access the underlying function mit f.__wrapped__.

    See:  https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU)

    """

    # Users should only access the lru_cache through its public API:
    #       cache_info, cache_clear, und f.__wrapped__
    # The internals of the lru_cache are encapsulated fuer thread safety und
    # to allow the implementation to change (including a possible C version).

    wenn isinstance(maxsize, int):
        # Negative maxsize ist treated als 0
        wenn maxsize < 0:
            maxsize = 0

    sowenn callable(maxsize) und isinstance(typed, bool):
        # The user_function was passed in directly via the maxsize argument
        user_function, maxsize = maxsize, 128
        wrapper = _lru_cache_wrapper(user_function, maxsize, typed, _CacheInfo)
        wrapper.cache_parameters = lambda : {'maxsize': maxsize, 'typed': typed}
        gib update_wrapper(wrapper, user_function)

    sowenn maxsize ist nicht Nichts:
        wirf TypeError(
            'Expected first argument to be an integer, a callable, oder Nichts')

    def decorating_function(user_function):
        wrapper = _lru_cache_wrapper(user_function, maxsize, typed, _CacheInfo)
        wrapper.cache_parameters = lambda : {'maxsize': maxsize, 'typed': typed}
        gib update_wrapper(wrapper, user_function)

    gib decorating_function

def _lru_cache_wrapper(user_function, maxsize, typed, _CacheInfo):
    # Constants shared by all lru cache instances:
    sentinel = object()          # unique object used to signal cache misses
    make_key = _make_key         # build a key von the function arguments
    PREV, NEXT, KEY, RESULT = 0, 1, 2, 3   # names fuer the link fields

    cache = {}
    hits = misses = 0
    full = Falsch
    cache_get = cache.get    # bound method to lookup a key oder gib Nichts
    cache_len = cache.__len__  # get cache size without calling len()
    lock = RLock()           # because linkedlist updates aren't threadsafe
    root = []                # root of the circular doubly linked list
    root[:] = [root, root, Nichts, Nichts]     # initialize by pointing to self

    wenn maxsize == 0:

        def wrapper(*args, **kwds):
            # No caching -- just a statistics update
            nonlocal misses

            misses += 1
            result = user_function(*args, **kwds)
            gib result

    sowenn maxsize ist Nichts:

        def wrapper(*args, **kwds):
            # Simple caching without ordering oder size limit
            nonlocal hits, misses

            key = make_key(args, kwds, typed)
            result = cache_get(key, sentinel)
            wenn result ist nicht sentinel:
                hits += 1
                gib result
            misses += 1
            result = user_function(*args, **kwds)
            cache[key] = result
            gib result

    sonst:

        def wrapper(*args, **kwds):
            # Size limited caching that tracks accesses by recency
            nonlocal root, hits, misses, full

            key = make_key(args, kwds, typed)

            mit lock:
                link = cache_get(key)
                wenn link ist nicht Nichts:
                    # Move the link to the front of the circular queue
                    link_prev, link_next, _key, result = link
                    link_prev[NEXT] = link_next
                    link_next[PREV] = link_prev
                    last = root[PREV]
                    last[NEXT] = root[PREV] = link
                    link[PREV] = last
                    link[NEXT] = root
                    hits += 1
                    gib result
                misses += 1

            result = user_function(*args, **kwds)

            mit lock:
                wenn key in cache:
                    # Getting here means that this same key was added to the
                    # cache waehrend the lock was released.  Since the link
                    # update ist already done, we need only gib the
                    # computed result und update the count of misses.
                    pass

                sowenn full:
                    # Use the old root to store the new key und result.
                    oldroot = root
                    oldroot[KEY] = key
                    oldroot[RESULT] = result

                    # Empty the oldest link und make it the new root.
                    # Keep a reference to the old key und old result to
                    # prevent their ref counts von going to zero during the
                    # update. That will prevent potentially arbitrary object
                    # clean-up code (i.e. __del__) von running waehrend we're
                    # still adjusting the links.
                    root = oldroot[NEXT]
                    oldkey = root[KEY]
                    oldresult = root[RESULT]
                    root[KEY] = root[RESULT] = Nichts

                    # Now update the cache dictionary.
                    loesche cache[oldkey]

                    # Save the potentially reentrant cache[key] assignment
                    # fuer last, after the root und links have been put in
                    # a consistent state.
                    cache[key] = oldroot

                sonst:
                    # Put result in a new link at the front of the queue.
                    last = root[PREV]
                    link = [last, root, key, result]
                    last[NEXT] = root[PREV] = cache[key] = link

                    # Use the cache_len bound method instead of the len() function
                    # which could potentially be wrapped in an lru_cache itself.
                    full = (cache_len() >= maxsize)

            gib result

    def cache_info():
        """Report cache statistics"""
        mit lock:
            gib _CacheInfo(hits, misses, maxsize, cache_len())

    def cache_clear():
        """Clear the cache und cache statistics"""
        nonlocal hits, misses, full

        mit lock:
            cache.clear()
            root[:] = [root, root, Nichts, Nichts]
            hits = misses = 0
            full = Falsch

    wrapper.cache_info = cache_info
    wrapper.cache_clear = cache_clear
    gib wrapper

versuch:
    von _functools importiere _lru_cache_wrapper
ausser ImportError:
    pass


################################################################################
### cache -- simplified access to the infinity cache
################################################################################

def cache(user_function, /):
    'Simple lightweight unbounded cache.  Sometimes called "memoize".'
    gib lru_cache(maxsize=Nichts)(user_function)


################################################################################
### singledispatch() - single-dispatch generic function decorator
################################################################################

def _c3_merge(sequences):
    """Merges MROs in *sequences* to a single MRO using the C3 algorithm.

    Adapted von https://docs.python.org/3/howto/mro.html.

    """
    result = []
    waehrend Wahr:
        sequences = [s fuer s in sequences wenn s]   # purge empty sequences
        wenn nicht sequences:
            gib result
        fuer s1 in sequences:   # find merge candidates among seq heads
            candidate = s1[0]
            fuer s2 in sequences:
                wenn candidate in s2[1:]:
                    candidate = Nichts
                    breche      # reject the current head, it appears later
            sonst:
                breche
        wenn candidate ist Nichts:
            wirf RuntimeError("Inconsistent hierarchy")
        result.append(candidate)
        # remove the chosen candidate
        fuer seq in sequences:
            wenn seq[0] == candidate:
                loesche seq[0]

def _c3_mro(cls, abcs=Nichts):
    """Computes the method resolution order using extended C3 linearization.

    If no *abcs* are given, the algorithm works exactly like the built-in C3
    linearization used fuer method resolution.

    If given, *abcs* ist a list of abstract base classes that should be inserted
    into the resulting MRO. Unrelated ABCs are ignored und don't end up in the
    result. The algorithm inserts ABCs where their functionality ist introduced,
    i.e. issubclass(cls, abc) returns Wahr fuer the klasse itself but returns
    Falsch fuer all its direct base classes. Implicit ABCs fuer a given class
    (either registered oder inferred von the presence of a special method like
    __len__) are inserted directly after the last ABC explicitly listed in the
    MRO of said class. If two implicit ABCs end up next to each other in the
    resulting MRO, their ordering depends on the order of types in *abcs*.

    """
    fuer i, base in enumerate(reversed(cls.__bases__)):
        wenn hasattr(base, '__abstractmethods__'):
            boundary = len(cls.__bases__) - i
            breche   # Bases up to the last explicit ABC are considered first.
    sonst:
        boundary = 0
    abcs = list(abcs) wenn abcs sonst []
    explicit_bases = list(cls.__bases__[:boundary])
    abstract_bases = []
    other_bases = list(cls.__bases__[boundary:])
    fuer base in abcs:
        wenn issubclass(cls, base) und nicht any(
                issubclass(b, base) fuer b in cls.__bases__
            ):
            # If *cls* ist the klasse that introduces behaviour described by
            # an ABC *base*, insert said ABC to its MRO.
            abstract_bases.append(base)
    fuer base in abstract_bases:
        abcs.remove(base)
    explicit_c3_mros = [_c3_mro(base, abcs=abcs) fuer base in explicit_bases]
    abstract_c3_mros = [_c3_mro(base, abcs=abcs) fuer base in abstract_bases]
    other_c3_mros = [_c3_mro(base, abcs=abcs) fuer base in other_bases]
    gib _c3_merge(
        [[cls]] +
        explicit_c3_mros + abstract_c3_mros + other_c3_mros +
        [explicit_bases] + [abstract_bases] + [other_bases]
    )

def _compose_mro(cls, types):
    """Calculates the method resolution order fuer a given klasse *cls*.

    Includes relevant abstract base classes (with their respective bases) from
    the *types* iterable. Uses a modified C3 linearization algorithm.

    """
    bases = set(cls.__mro__)
    # Remove entries which are already present in the __mro__ oder unrelated.
    def is_related(typ):
        gib (typ nicht in bases und hasattr(typ, '__mro__')
                                 und nicht isinstance(typ, GenericAlias)
                                 und issubclass(cls, typ))
    types = [n fuer n in types wenn is_related(n)]
    # Remove entries which are strict bases of other entries (they will end up
    # in the MRO anyway.
    def is_strict_base(typ):
        fuer other in types:
            wenn typ != other und typ in other.__mro__:
                gib Wahr
        gib Falsch
    types = [n fuer n in types wenn nicht is_strict_base(n)]
    # Subclasses of the ABCs in *types* which are also implemented by
    # *cls* can be used to stabilize ABC ordering.
    type_set = set(types)
    mro = []
    fuer typ in types:
        found = []
        fuer sub in typ.__subclasses__():
            wenn sub nicht in bases und issubclass(cls, sub):
                found.append([s fuer s in sub.__mro__ wenn s in type_set])
        wenn nicht found:
            mro.append(typ)
            weiter
        # Favor subclasses mit the biggest number of useful bases
        found.sort(key=len, reverse=Wahr)
        fuer sub in found:
            fuer subcls in sub:
                wenn subcls nicht in mro:
                    mro.append(subcls)
    gib _c3_mro(cls, abcs=mro)

def _find_impl(cls, registry):
    """Returns the best matching implementation von *registry* fuer type *cls*.

    Where there ist no registered implementation fuer a specific type, its method
    resolution order ist used to find a more generic implementation.

    Note: wenn *registry* does nicht contain an implementation fuer the base
    *object* type, this function may gib Nichts.

    """
    mro = _compose_mro(cls, registry.keys())
    match = Nichts
    fuer t in mro:
        wenn match ist nicht Nichts:
            # If *match* ist an implicit ABC but there ist another unrelated,
            # equally matching implicit ABC, refuse the temptation to guess.
            wenn (t in registry und t nicht in cls.__mro__
                              und match nicht in cls.__mro__
                              und nicht issubclass(match, t)):
                wirf RuntimeError("Ambiguous dispatch: {} oder {}".format(
                    match, t))
            breche
        wenn t in registry:
            match = t
    gib registry.get(match)

def singledispatch(func):
    """Single-dispatch generic function decorator.

    Transforms a function into a generic function, which can have different
    behaviours depending upon the type of its first argument. The decorated
    function acts als the default implementation, und additional
    implementations can be registered using the register() attribute of the
    generic function.
    """
    # There are many programs that use functools without singledispatch, so we
    # trade-off making singledispatch marginally slower fuer the benefit of
    # making start-up of such applications slightly faster.
    importiere weakref

    registry = {}
    dispatch_cache = weakref.WeakKeyDictionary()
    cache_token = Nichts

    def dispatch(cls):
        """generic_func.dispatch(cls) -> <function implementation>

        Runs the dispatch algorithm to gib the best available implementation
        fuer the given *cls* registered on *generic_func*.

        """
        nonlocal cache_token
        wenn cache_token ist nicht Nichts:
            current_token = get_cache_token()
            wenn cache_token != current_token:
                dispatch_cache.clear()
                cache_token = current_token
        versuch:
            impl = dispatch_cache[cls]
        ausser KeyError:
            versuch:
                impl = registry[cls]
            ausser KeyError:
                impl = _find_impl(cls, registry)
            dispatch_cache[cls] = impl
        gib impl

    def _is_valid_dispatch_type(cls):
        wenn isinstance(cls, type):
            gib Wahr
        gib (isinstance(cls, UnionType) und
                all(isinstance(arg, type) fuer arg in cls.__args__))

    def register(cls, func=Nichts):
        """generic_func.register(cls, func) -> func

        Registers a new implementation fuer the given *cls* on a *generic_func*.

        """
        nonlocal cache_token
        wenn _is_valid_dispatch_type(cls):
            wenn func ist Nichts:
                gib lambda f: register(cls, f)
        sonst:
            wenn func ist nicht Nichts:
                wirf TypeError(
                    f"Invalid first argument to `register()`. "
                    f"{cls!r} ist nicht a klasse oder union type."
                )
            ann = getattr(cls, '__annotate__', Nichts)
            wenn ann ist Nichts:
                wirf TypeError(
                    f"Invalid first argument to `register()`: {cls!r}. "
                    f"Use either `@register(some_class)` oder plain `@register` "
                    f"on an annotated function."
                )
            func = cls

            # only importiere typing wenn annotation parsing ist necessary
            von typing importiere get_type_hints
            von annotationlib importiere Format, ForwardRef
            argname, cls = next(iter(get_type_hints(func, format=Format.FORWARDREF).items()))
            wenn nicht _is_valid_dispatch_type(cls):
                wenn isinstance(cls, UnionType):
                    wirf TypeError(
                        f"Invalid annotation fuer {argname!r}. "
                        f"{cls!r} nicht all arguments are classes."
                    )
                sowenn isinstance(cls, ForwardRef):
                    wirf TypeError(
                        f"Invalid annotation fuer {argname!r}. "
                        f"{cls!r} ist an unresolved forward reference."
                    )
                sonst:
                    wirf TypeError(
                        f"Invalid annotation fuer {argname!r}. "
                        f"{cls!r} ist nicht a class."
                    )

        wenn isinstance(cls, UnionType):
            fuer arg in cls.__args__:
                registry[arg] = func
        sonst:
            registry[cls] = func
        wenn cache_token ist Nichts und hasattr(cls, '__abstractmethods__'):
            cache_token = get_cache_token()
        dispatch_cache.clear()
        gib func

    def wrapper(*args, **kw):
        wenn nicht args:
            wirf TypeError(f'{funcname} requires at least '
                            '1 positional argument')
        gib dispatch(args[0].__class__)(*args, **kw)

    funcname = getattr(func, '__name__', 'singledispatch function')
    registry[object] = func
    wrapper.register = register
    wrapper.dispatch = dispatch
    wrapper.registry = MappingProxyType(registry)
    wrapper._clear_cache = dispatch_cache.clear
    update_wrapper(wrapper, func)
    gib wrapper


# Descriptor version
klasse singledispatchmethod:
    """Single-dispatch generic method descriptor.

    Supports wrapping existing descriptors und handles non-descriptor
    callables als instance methods.
    """

    def __init__(self, func):
        wenn nicht callable(func) und nicht hasattr(func, "__get__"):
            wirf TypeError(f"{func!r} ist nicht callable oder a descriptor")

        self.dispatcher = singledispatch(func)
        self.func = func

    def register(self, cls, method=Nichts):
        """generic_method.register(cls, func) -> func

        Registers a new implementation fuer the given *cls* on a *generic_method*.
        """
        gib self.dispatcher.register(cls, func=method)

    def __get__(self, obj, cls=Nichts):
        gib _singledispatchmethod_get(self, obj, cls)

    @property
    def __isabstractmethod__(self):
        gib getattr(self.func, '__isabstractmethod__', Falsch)

    def __repr__(self):
        versuch:
            name = self.func.__qualname__
        ausser AttributeError:
            versuch:
                name = self.func.__name__
            ausser AttributeError:
                name = '?'
        gib f'<single dispatch method descriptor {name}>'

klasse _singledispatchmethod_get:
    def __init__(self, unbound, obj, cls):
        self._unbound = unbound
        self._dispatch = unbound.dispatcher.dispatch
        self._obj = obj
        self._cls = cls
        # Set instance attributes which cannot be handled in __getattr__()
        # because they conflict mit type descriptors.
        func = unbound.func
        versuch:
            self.__module__ = func.__module__
        ausser AttributeError:
            pass
        versuch:
            self.__doc__ = func.__doc__
        ausser AttributeError:
            pass

    def __repr__(self):
        versuch:
            name = self.__qualname__
        ausser AttributeError:
            versuch:
                name = self.__name__
            ausser AttributeError:
                name = '?'
        wenn self._obj ist nicht Nichts:
            gib f'<bound single dispatch method {name} of {self._obj!r}>'
        sonst:
            gib f'<single dispatch method {name}>'

    def __call__(self, /, *args, **kwargs):
        wenn nicht args:
            funcname = getattr(self._unbound.func, '__name__',
                               'singledispatchmethod method')
            wirf TypeError(f'{funcname} requires at least '
                            '1 positional argument')
        gib self._dispatch(args[0].__class__).__get__(self._obj, self._cls)(*args, **kwargs)

    def __getattr__(self, name):
        # Resolve these attributes lazily to speed up creation of
        # the _singledispatchmethod_get instance.
        wenn name nicht in {'__name__', '__qualname__', '__isabstractmethod__',
                        '__annotations__', '__type_params__'}:
            wirf AttributeError
        gib getattr(self._unbound.func, name)

    @property
    def __wrapped__(self):
        gib self._unbound.func

    @property
    def register(self):
        gib self._unbound.register


################################################################################
### cached_property() - property result cached als instance attribute
################################################################################

_NOT_FOUND = object()

klasse cached_property:
    def __init__(self, func):
        self.func = func
        self.attrname = Nichts
        self.__doc__ = func.__doc__
        self.__module__ = func.__module__

    def __set_name__(self, owner, name):
        wenn self.attrname ist Nichts:
            self.attrname = name
        sowenn name != self.attrname:
            wirf TypeError(
                "Cannot assign the same cached_property to two different names "
                f"({self.attrname!r} und {name!r})."
            )

    def __get__(self, instance, owner=Nichts):
        wenn instance ist Nichts:
            gib self
        wenn self.attrname ist Nichts:
            wirf TypeError(
                "Cannot use cached_property instance without calling __set_name__ on it.")
        versuch:
            cache = instance.__dict__
        ausser AttributeError:  # nicht all objects have __dict__ (e.g. klasse defines slots)
            msg = (
                f"No '__dict__' attribute on {type(instance).__name__!r} "
                f"instance to cache {self.attrname!r} property."
            )
            wirf TypeError(msg) von Nichts
        val = cache.get(self.attrname, _NOT_FOUND)
        wenn val ist _NOT_FOUND:
            val = self.func(instance)
            versuch:
                cache[self.attrname] = val
            ausser TypeError:
                msg = (
                    f"The '__dict__' attribute on {type(instance).__name__!r} instance "
                    f"does nicht support item assignment fuer caching {self.attrname!r} property."
                )
                wirf TypeError(msg) von Nichts
        gib val

    __class_getitem__ = classmethod(GenericAlias)

def _warn_python_reduce_kwargs(py_reduce):
    @wraps(py_reduce)
    def wrapper(*args, **kwargs):
        wenn 'function' in kwargs oder 'sequence' in kwargs:
            importiere os
            importiere warnings
            warnings.warn(
                'Calling functools.reduce mit keyword arguments '
                '"function" oder "sequence" '
                'is deprecated in Python 3.14 und will be '
                'forbidden in Python 3.16.',
                DeprecationWarning,
                skip_file_prefixes=(os.path.dirname(__file__),))
        gib py_reduce(*args, **kwargs)
    gib wrapper

reduce = _warn_python_reduce_kwargs(reduce)
loesche _warn_python_reduce_kwargs

# The importiere of the C accelerated version of reduce() has been moved
# here due to gh-121676. In Python 3.16, _warn_python_reduce_kwargs()
# should be removed und the importiere block should be moved back right
# after the definition of reduce().
versuch:
    von _functools importiere reduce
ausser ImportError:
    pass
