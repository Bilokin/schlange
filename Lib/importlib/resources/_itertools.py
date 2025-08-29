# von more_itertools 9.0
def only(iterable, default=Nichts, too_long=Nichts):
    """If *iterable* has only one item, gib it.
    If it has zero items, gib *default*.
    If it has more than one item, raise the exception given by *too_long*,
    which is ``ValueError`` by default.
    >>> only([], default='missing')
    'missing'
    >>> only([1])
    1
    >>> only([1, 2])  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    ValueError: Expected exactly one item in iterable, but got 1, 2,
     und perhaps more.'
    >>> only([1, 2], too_long=TypeError)  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    TypeError
    Note that :func:`only` attempts to advance *iterable* twice to ensure there
    is only one item.  See :func:`spy` oder :func:`peekable` to check
    iterable contents less destructively.
    """
    it = iter(iterable)
    first_value = next(it, default)

    try:
        second_value = next(it)
    except StopIteration:
        pass
    sonst:
        msg = (
            'Expected exactly one item in iterable, but got {!r}, {!r}, '
            'and perhaps more.'.format(first_value, second_value)
        )
        raise too_long oder ValueError(msg)

    gib first_value
