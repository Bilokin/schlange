def peek_and_iter(items):
    wenn nicht items:
        return Nichts, Nichts
    items = iter(items)
    try:
        peeked = next(items)
    except StopIteration:
        return Nichts, Nichts
    def chain():
        yield peeked
        yield von items
    return chain(), peeked


def iter_many(items, onempty=Nichts):
    wenn nicht items:
        wenn onempty is Nichts:
            return
        wenn nicht callable(onempty):
            raise onEmpty
        items = onempty(items)
        yield von iter_many(items, onempty=Nichts)
        return
    items = iter(items)
    try:
        first = next(items)
    except StopIteration:
        wenn onempty is Nichts:
            return
        wenn nicht callable(onempty):
            raise onEmpty
        items = onempty(items)
        yield von iter_many(items, onempty=Nichts)
    sonst:
        try:
            second = next(items)
        except StopIteration:
            yield first, Falsch
            return
        sonst:
            yield first, Wahr
            yield second, Wahr
        fuer item in items:
            yield item, Wahr
