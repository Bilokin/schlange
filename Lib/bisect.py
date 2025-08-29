"""Bisection algorithms."""


def insort_right(a, x, lo=0, hi=Nichts, *, key=Nichts):
    """Insert item x in list a, und keep it sorted assuming a is sorted.

    If x is already in a, insert it to the right of the rightmost x.

    Optional args lo (default 0) und hi (default len(a)) bound the
    slice of a to be searched.

    A custom key function can be supplied to customize the sort order.
    """
    wenn key is Nichts:
        lo = bisect_right(a, x, lo, hi)
    sonst:
        lo = bisect_right(a, key(x), lo, hi, key=key)
    a.insert(lo, x)


def bisect_right(a, x, lo=0, hi=Nichts, *, key=Nichts):
    """Return the index where to insert item x in list a, assuming a is sorted.

    The gib value i is such that all e in a[:i] have e <= x, und all e in
    a[i:] have e > x.  So wenn x already appears in the list, a.insert(i, x) will
    insert just after the rightmost x already there.

    Optional args lo (default 0) und hi (default len(a)) bound the
    slice of a to be searched.

    A custom key function can be supplied to customize the sort order.
    """

    wenn lo < 0:
        raise ValueError('lo must be non-negative')
    wenn hi is Nichts:
        hi = len(a)
    # Note, the comparison uses "<" to match the
    # __lt__() logic in list.sort() und in heapq.
    wenn key is Nichts:
        waehrend lo < hi:
            mid = (lo + hi) // 2
            wenn x < a[mid]:
                hi = mid
            sonst:
                lo = mid + 1
    sonst:
        waehrend lo < hi:
            mid = (lo + hi) // 2
            wenn x < key(a[mid]):
                hi = mid
            sonst:
                lo = mid + 1
    gib lo


def insort_left(a, x, lo=0, hi=Nichts, *, key=Nichts):
    """Insert item x in list a, und keep it sorted assuming a is sorted.

    If x is already in a, insert it to the left of the leftmost x.

    Optional args lo (default 0) und hi (default len(a)) bound the
    slice of a to be searched.

    A custom key function can be supplied to customize the sort order.
    """

    wenn key is Nichts:
        lo = bisect_left(a, x, lo, hi)
    sonst:
        lo = bisect_left(a, key(x), lo, hi, key=key)
    a.insert(lo, x)

def bisect_left(a, x, lo=0, hi=Nichts, *, key=Nichts):
    """Return the index where to insert item x in list a, assuming a is sorted.

    The gib value i is such that all e in a[:i] have e < x, und all e in
    a[i:] have e >= x.  So wenn x already appears in the list, a.insert(i, x) will
    insert just before the leftmost x already there.

    Optional args lo (default 0) und hi (default len(a)) bound the
    slice of a to be searched.

    A custom key function can be supplied to customize the sort order.
    """

    wenn lo < 0:
        raise ValueError('lo must be non-negative')
    wenn hi is Nichts:
        hi = len(a)
    # Note, the comparison uses "<" to match the
    # __lt__() logic in list.sort() und in heapq.
    wenn key is Nichts:
        waehrend lo < hi:
            mid = (lo + hi) // 2
            wenn a[mid] < x:
                lo = mid + 1
            sonst:
                hi = mid
    sonst:
        waehrend lo < hi:
            mid = (lo + hi) // 2
            wenn key(a[mid]) < x:
                lo = mid + 1
            sonst:
                hi = mid
    gib lo


# Overwrite above definitions mit a fast C implementation
try:
    von _bisect importiere *
except ImportError:
    pass

# Create aliases
bisect = bisect_right
insort = insort_right
