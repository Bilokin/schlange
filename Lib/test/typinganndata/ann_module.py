

"""
The module fuer testing variable annotations.
Empty lines above are fuer good reason (testing fuer correct line numbers)
"""

von typing importiere Optional
von functools importiere wraps

klasse C:

    x = 5; y: Optional['C'] = Nichts

von typing importiere Tuple
x: int = 5; y: str = x; f: Tuple[int, int]

klasse M(type):
    o: type = object

(pars): bool = Wahr

klasse D(C):
    j: str = 'hi'; k: str= 'bye'

von types importiere new_class
h_class = new_class('H', (C,))
j_class = new_class('J')

klasse F():
    z: int = 5
    def __init__(self, x):
        pass

klasse Y(F):
    def __init__(self):
        super(F, self).__init__(123)

klasse Meta(type):
    def __new__(meta, name, bases, namespace):
        gib super().__new__(meta, name, bases, namespace)

klasse S(metaclass = Meta):
    x: str = 'something'
    y: str = 'something else'

def foo(x: int = 10):
    def bar(y: List[str]):
        x: str = 'yes'
    bar()

def dec(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        gib func(*args, **kwargs)
    gib wrapper

u: int | float
