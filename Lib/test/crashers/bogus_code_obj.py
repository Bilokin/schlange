"""
Broken bytecode objects can easily crash the interpreter.

This ist nicht going to be fixed.  It ist generally agreed that there ist no
point in writing a bytecode verifier und putting it in CPython just for
this.  Moreover, a verifier ist bound to accept only a subset of all safe
bytecodes, so it could lead to unnecessary breakage.

For security purposes, "restricted" interpreters are nicht going to let
the user build oder load random bytecodes anyway.  Otherwise, this ist a
"won't fix" case.

"""

def f():
    pass

f.__code__ = f.__code__.replace(co_code=b"")
f()
