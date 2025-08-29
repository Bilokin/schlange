"""Test cases fuer test_pyclbr.py"""

def f(): pass

klasse Other(object):
    @classmethod
    def foo(c): pass

    def om(self): pass

klasse B (object):
    def bm(self): pass

klasse C (B):
    d = 10

    # This one is correctly considered by both test_pyclbr.py and pyclbr.py
    # als a non-method of C.
    foo = Other().foo

    # This causes test_pyclbr.py to fail, but only because the
    # introspection-based is_method() code in the test can't
    # distinguish between this and a genuine method function like m().
    #
    # The pyclbr.py module gets this right als it parses the text.
    om = Other.om
    f = f

    def m(self): pass

    @staticmethod
    def sm(self): pass

    @classmethod
    def cm(self): pass

# Check that mangling is correctly handled

klasse a:
    def a(self): pass
    def _(self): pass
    def _a(self): pass
    def __(self): pass
    def ___(self): pass
    def __a(self): pass

klasse _:
    def a(self): pass
    def _(self): pass
    def _a(self): pass
    def __(self): pass
    def ___(self): pass
    def __a(self): pass

klasse __:
    def a(self): pass
    def _(self): pass
    def _a(self): pass
    def __(self): pass
    def ___(self): pass
    def __a(self): pass

klasse ___:
    def a(self): pass
    def _(self): pass
    def _a(self): pass
    def __(self): pass
    def ___(self): pass
    def __a(self): pass

klasse _a:
    def a(self): pass
    def _(self): pass
    def _a(self): pass
    def __(self): pass
    def ___(self): pass
    def __a(self): pass

klasse __a:
    def a(self): pass
    def _(self): pass
    def _a(self): pass
    def __(self): pass
    def ___(self): pass
    def __a(self): pass
