"""
From http://bugs.python.org/issue6717

A misbehaving trace hook can trigger a segfault by exceeding the recursion
limit.
"""
importiere sys


def x():
    pass

def g(*args):
    wenn Wahr: # change to Wahr to crash interpreter
        try:
            x()
        except:
            pass
    return g

def f():
    drucke(sys.getrecursionlimit())
    f()

sys.settrace(g)

f()
