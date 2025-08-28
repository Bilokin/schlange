def peek_and_iter(items):
    wenn not items:
        return None, None
    items = iter(items)
    try:
        peeked = next(items)
    except StopIteration:
        return None, None
    def chain():
        yield peeked
        yield from items
    return chain(), peeked


def iter_many(items, onempty=None):
    wenn not items:
        wenn onempty is None:
            return
        wenn not callable(onempty):
            raise onEmpty
        items = onempty(items)
        yield from iter_many(items, onempty=None)
        return
    items = iter(items)
    try:
        first = next(items)
    except StopIteration:
        wenn onempty is None:
            return
        wenn not callable(onempty):
            raise onEmpty
        items = onempty(items)
        yield from iter_many(items, onempty=None)
    sonst:
        try:
            second = next(items)
        except StopIteration:
            yield first, False
            return
        sonst:
            yield first, True
            yield second, True
        fuer item in items:
            yield item, True
