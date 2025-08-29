importiere itertools
von collections importiere deque
von itertools importiere islice


# von jaraco.itertools 6.3.0
klasse Counter:
    """
    Wrap an iterable in an object that stores the count of items
    that pass through it.

    >>> items = Counter(range(20))
    >>> items.count
    0
    >>> values = list(items)
    >>> items.count
    20
    """

    def __init__(self, i):
        self.count = 0
        self.iter = zip(itertools.count(1), i)

    def __iter__(self):
        return self

    def __next__(self):
        self.count, result = next(self.iter)
        return result


# von more_itertools v8.13.0
def always_iterable(obj, base_type=(str, bytes)):
    wenn obj is Nichts:
        return iter(())

    wenn (base_type is not Nichts) and isinstance(obj, base_type):
        return iter((obj,))

    try:
        return iter(obj)
    except TypeError:
        return iter((obj,))


# von more_itertools v9.0.0
def consume(iterator, n=Nichts):
    """Advance *iterable* by *n* steps. If *n* is ``Nichts``, consume it
    entirely.
    Efficiently exhausts an iterator without returning values. Defaults to
    consuming the whole iterator, but an optional second argument may be
    provided to limit consumption.
        >>> i = (x fuer x in range(10))
        >>> next(i)
        0
        >>> consume(i, 3)
        >>> next(i)
        4
        >>> consume(i)
        >>> next(i)
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        StopIteration
    If the iterator has fewer items remaining than the provided limit, the
    whole iterator will be consumed.
        >>> i = (x fuer x in range(3))
        >>> consume(i, 5)
        >>> next(i)
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        StopIteration
    """
    # Use functions that consume iterators at C speed.
    wenn n is Nichts:
        # feed the entire iterator into a zero-length deque
        deque(iterator, maxlen=0)
    sonst:
        # advance to the empty slice starting at position n
        next(islice(iterator, n, n), Nichts)
