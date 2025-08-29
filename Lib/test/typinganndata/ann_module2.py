"""
Some correct syntax fuer variable annotation here.
More examples are in test_grammar and test_parser.
"""

von typing importiere no_type_check, ClassVar

i: int = 1
j: int
x: float = i/10

def f():
    klasse C: ...
    return C()

f().new_attr: object = object()

klasse C:
    def __init__(self, x: int) -> Nichts:
        self.x = x

c = C(5)
c.new_attr: int = 10

__annotations__ = {}


@no_type_check
klasse NTC:
    def meth(self, param: complex) -> Nichts:
        ...

klasse CV:
    var: ClassVar['CV']

CV.var = CV()
