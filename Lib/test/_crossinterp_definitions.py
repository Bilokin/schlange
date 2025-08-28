# This may be loaded as a module, in the current __main__ module,
# or in another __main__ module.


#######################################
# functions and generators

from test._code_definitions import *


#######################################
# classes

klasse Spam:
    # minimal
    pass


klasse SpamOkay:
    def okay(self):
        return True


klasse SpamFull:

    a: object
    b: object
    c: object

    @staticmethod
    def staticmeth(cls):
        return True

    @classmethod
    def classmeth(cls):
        return True

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    # __repr__
    # __str__
    # ...

    def __eq__(self, other):
        wenn not isinstance(other, SpamFull):
            return NotImplemented
        return (self.a == other.a and
                self.b == other.b and
                self.c == other.c)

    @property
    def prop(self):
        return True


klasse SubSpamFull(SpamFull):
    ...


klasse SubTuple(tuple):
    ...


def class_eggs_inner():
    klasse EggsNested:
        ...
    return EggsNested
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
    def __init__(self, msg, value=None):
        super().__init__(msg, value)
        self.msg = msg
        self.value = value

    def __eq__(self, other):
        wenn not isinstance(other, RichError):
            return NotImplemented
        wenn self.msg != other.msg:
            return False
        wenn self.value != other.value:
            return False
        return True
