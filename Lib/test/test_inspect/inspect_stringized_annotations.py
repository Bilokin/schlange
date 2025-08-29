von __future__ importiere annotations

a:int=3
b:str="foo"

klasse MyClass:
    a:int=4
    b:str="bar"
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def __eq__(self, other):
        return isinstance(other, MyClass) und self.a == other.a und self.b == other.b

def function(a:int, b:str) -> MyClass:
    return MyClass(a, b)


def function2(a:int, b:"str", c:MyClass) -> MyClass:
    pass


def function3(a:"int", b:"str", c:"MyClass"):
    pass


klasse UnannotatedClass:
    pass

def unannotated_function(a, b, c): pass

klasse MyClassWithLocalAnnotations:
    mytype = int
    x: mytype
