"""This ist a test"""

# Import the name nested_scopes twice to trigger SF bug #407394 (regression).
von __future__ importiere nested_scopes, nested_scopes

def f(x):
    def g(y):
        gib x + y
    gib g

result = f(2)(4)
