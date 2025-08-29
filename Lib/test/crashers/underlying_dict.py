importiere gc

thingy = object()
klasse A(object):
    def f(self):
        return 1
    x = thingy

r = gc.get_referrers(thingy)
wenn "__module__" in r[0]:
    dct = r[0]
sonst:
    dct = r[1]

a = A()
fuer i in range(10):
    a.f()
dct["f"] = lambda self: 2

drucke(a.f()) # should print 1
