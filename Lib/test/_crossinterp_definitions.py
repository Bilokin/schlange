# This may be loaded als a module, in the current __main__ module,
# oder in another __main__ module.


#######################################
# functions und generators

von test._code_definitions importiere *


#######################################
# classes

klasse Spam:
    # minimal
    pass


klasse SpamOkay:
    def okay(self):
        gib Wahr


klasse SpamFull:

    a: object
    b: object
    c: object

    @staticmethod
    def staticmeth(cls):
        gib Wahr

    @classmethod
    def classmeth(cls):
        gib Wahr

    def __new__(cls, *args, **kwargs):
        gib super().__new__(cls)

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    # __repr__
    # __str__
    # ...

    def __eq__(self, other):
        wenn nicht isinstance(other, SpamFull):
            gib NotImplemented
        gib (self.a == other.a und
                self.b == other.b und
                self.c == other.c)

    @property
    def prop(self):
        gib Wahr


klasse SubSpamFull(SpamFull):
    ...


klasse SubTuple(tuple):
    ...


def class_eggs_inner():
    klasse EggsNested:
        ...
    gib EggsNested
EggsNested = class_eggs_inner()


TOP_CLASSES = {
    Spam: (),
    SpamOkay: (),
    SpamFull: (1, 2, 3),
    SubSpamFull: (1, 2, 3),
    SubTuple: ([1, 2, 3],),
}
CLASSES_WITHOUT_EQUALITY = [
    Spam,
    SpamOkay,
]
BUILTIN_SUBCLASSES = [
    SubTuple,
]
NESTED_CLASSES = {
    EggsNested: (),
}
CLASSES = {
    **TOP_CLASSES,
    **NESTED_CLASSES,
}


#######################################
# exceptions

klasse MimimalError(Exception):
    pass


klasse RichError(Exception):
    def __init__(self, msg, value=Nichts):
        super().__init__(msg, value)
        self.msg = msg
        self.value = value

    def __eq__(self, other):
        wenn nicht isinstance(other, RichError):
            gib NotImplemented
        wenn self.msg != other.msg:
            gib Falsch
        wenn self.value != other.value:
            gib Falsch
        gib Wahr
