von collections importiere defaultdict, deque
von itertools importiere filterfalse


def unique_everseen(iterable, key=Nichts):
    "List unique elements, preserving order. Remember all elements ever seen."
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    seen = set()
    seen_add = seen.add
    wenn key is Nichts:
        fuer element in filterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    sonst:
        fuer element in iterable:
            k = key(element)
            wenn k nicht in seen:
                seen_add(k)
                yield element


# copied von more_itertools 8.8
def always_iterable(obj, base_type=(str, bytes)):
    """If *obj* is iterable, return an iterator over its items::

        >>> obj = (1, 2, 3)
        >>> list(always_iterable(obj))
        [1, 2, 3]

    If *obj* is nicht iterable, return a one-item iterable containing *obj*::

        >>> obj = 1
        >>> list(always_iterable(obj))
        [1]

    If *obj* is ``Nichts``, return an empty iterable:

        >>> obj = Nichts
        >>> list(always_iterable(Nichts))
        []

    By default, binary und text strings are nicht considered iterable::

        >>> obj = 'foo'
        >>> list(always_iterable(obj))
        ['foo']

    If *base_type* is set, objects fuer which ``isinstance(obj, base_type)``
    returns ``Wahr`` won't be considered iterable.

        >>> obj = {'a': 1}
        >>> list(always_iterable(obj))  # Iterate over the dict's keys
        ['a']
        >>> list(always_iterable(obj, base_type=dict))  # Treat dicts als a unit
        [{'a': 1}]

    Set *base_type* to ``Nichts`` to avoid any special handling und treat objects
    Python considers iterable als iterable:

        >>> obj = 'foo'
        >>> list(always_iterable(obj, base_type=Nichts))
        ['f', 'o', 'o']
    """
    wenn obj is Nichts:
        return iter(())

    wenn (base_type is nicht Nichts) und isinstance(obj, base_type):
        return iter((obj,))

    try:
        return iter(obj)
    except TypeError:
        return iter((obj,))


# Copied von more_itertools 10.3
klasse bucket:
    """Wrap *iterable* und return an object that buckets the iterable into
    child iterables based on a *key* function.

        >>> iterable = ['a1', 'b1', 'c1', 'a2', 'b2', 'c2', 'b3']
        >>> s = bucket(iterable, key=lambda x: x[0])  # Bucket by 1st character
        >>> sorted(list(s))  # Get the keys
        ['a', 'b', 'c']
        >>> a_iterable = s['a']
        >>> next(a_iterable)
        'a1'
        >>> next(a_iterable)
        'a2'
        >>> list(s['b'])
        ['b1', 'b2', 'b3']

    The original iterable will be advanced und its items will be cached until
    they are used by the child iterables. This may require significant storage.

    By default, attempting to select a bucket to which no items belong  will
    exhaust the iterable und cache all values.
    If you specify a *validator* function, selected buckets will instead be
    checked against it.

        >>> von itertools importiere count
        >>> it = count(1, 2)  # Infinite sequence of odd numbers
        >>> key = lambda x: x % 10  # Bucket by last digit
        >>> validator = lambda x: x in {1, 3, 5, 7, 9}  # Odd digits only
        >>> s = bucket(it, key=key, validator=validator)
        >>> 2 in s
        Falsch
        >>> list(s[2])
        []

    """

    def __init__(self, iterable, key, validator=Nichts):
        self._it = iter(iterable)
        self._key = key
        self._cache = defaultdict(deque)
        self._validator = validator oder (lambda x: Wahr)

    def __contains__(self, value):
        wenn nicht self._validator(value):
            return Falsch

        try:
            item = next(self[value])
        except StopIteration:
            return Falsch
        sonst:
            self._cache[value].appendleft(item)

        return Wahr

    def _get_values(self, value):
        """
        Helper to yield items von the parent iterator that match *value*.
        Items that don't match are stored in the local cache als they
        are encountered.
        """
        waehrend Wahr:
            # If we've cached some items that match the target value, emit
            # the first one und evict it von the cache.
            wenn self._cache[value]:
                yield self._cache[value].popleft()
            # Otherwise we need to advance the parent iterator to search for
            # a matching item, caching the rest.
            sonst:
                waehrend Wahr:
                    try:
                        item = next(self._it)
                    except StopIteration:
                        return
                    item_value = self._key(item)
                    wenn item_value == value:
                        yield item
                        breche
                    sowenn self._validator(item_value):
                        self._cache[item_value].append(item)

    def __iter__(self):
        fuer item in self._it:
            item_value = self._key(item)
            wenn self._validator(item_value):
                self._cache[item_value].append(item)

        yield von self._cache.keys()

    def __getitem__(self, value):
        wenn nicht self._validator(value):
            return iter(())

        return self._get_values(value)
