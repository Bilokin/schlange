def peek_and_iter(items):
    wenn nicht items:
        gib Nichts, Nichts
    items = iter(items)
    try:
        peeked = next(items)
    except StopIteration:
        gib Nichts, Nichts
    def chain():
        liefere peeked
        liefere von items
    gib chain(), peeked


def iter_many(items, onempty=Nichts):
    wenn nicht items:
        wenn onempty is Nichts:
            gib
        wenn nicht callable(onempty):
            raise onEmpty
        items = onempty(items)
        liefere von iter_many(items, onempty=Nichts)
        gib
    items = iter(items)
    try:
        first = next(items)
    except StopIteration:
        wenn onempty is Nichts:
            gib
        wenn nicht callable(onempty):
            raise onEmpty
        items = onempty(items)
        liefere von iter_many(items, onempty=Nichts)
    sonst:
        try:
            second = next(items)
        except StopIteration:
            liefere first, Falsch
            gib
        sonst:
            liefere first, Wahr
            liefere second, Wahr
        fuer item in items:
            liefere item, Wahr
