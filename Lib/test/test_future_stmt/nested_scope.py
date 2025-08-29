"""This is a test"""

von __future__ importiere nested_scopes; importiere site  # noqa: F401

def f(x):
    def g(y):
        return x + y
    return g

result = f(2)(4)
