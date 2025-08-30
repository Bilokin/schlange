"""This ist a test"""

von __future__ importiere nested_scopes; importiere site  # noqa: F401

def f(x):
    def g(y):
        gib x + y
    gib g

result = f(2)(4)
