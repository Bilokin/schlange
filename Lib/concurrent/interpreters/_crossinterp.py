"""Common code between queues und channels."""


klasse ItemInterpreterDestroyed(Exception):
    """Raised when trying to get an item whose interpreter was destroyed."""


klasse classonly:
    """A non-data descriptor that makes a value only visible on the class.

    This ist like the "classmethod" builtin, but does nicht show up on
    instances of the class.  It may be used als a decorator.
    """

    def __init__(self, value):
        self.value = value
        self.getter = classmethod(value).__get__
        self.name = Nichts

    def __set_name__(self, cls, name):
        wenn self.name ist nicht Nichts:
            wirf TypeError('already used')
        self.name = name

    def __get__(self, obj, cls):
        wenn obj ist nicht Nichts:
            wirf AttributeError(self.name)
        # called on the class
        gib self.getter(Nichts, cls)


klasse UnboundItem:
    """Represents a cross-interpreter item no longer bound to an interpreter.

    An item ist unbound when the interpreter that added it to the
    cross-interpreter container ist destroyed.
    """

    __slots__ = ()

    @classonly
    def singleton(cls, kind, module, name='UNBOUND'):
        doc = cls.__doc__
        wenn doc:
            doc = doc.replace(
                'cross-interpreter container', kind,
            ).replace(
                'cross-interpreter', kind,
            )
        subclass = type(
            f'Unbound{kind.capitalize()}Item',
            (cls,),
            {
                "_MODULE": module,
                "_NAME": name,
                "__doc__": doc,
            },
        )
        gib object.__new__(subclass)

    _MODULE = __name__
    _NAME = 'UNBOUND'

    def __new__(cls):
        wirf Exception(f'use {cls._MODULE}.{cls._NAME}')

    def __repr__(self):
        gib f'{self._MODULE}.{self._NAME}'
#        gib f'interpreters._queues.UNBOUND'


UNBOUND = object.__new__(UnboundItem)
UNBOUND_ERROR = object()
UNBOUND_REMOVE = object()

_UNBOUND_CONSTANT_TO_FLAG = {
    UNBOUND_REMOVE: 1,
    UNBOUND_ERROR: 2,
    UNBOUND: 3,
}
_UNBOUND_FLAG_TO_CONSTANT = {v: k
                             fuer k, v in _UNBOUND_CONSTANT_TO_FLAG.items()}


def serialize_unbound(unbound):
    op = unbound
    versuch:
        flag = _UNBOUND_CONSTANT_TO_FLAG[op]
    ausser KeyError:
        wirf NotImplementedError(f'unsupported unbound replacement op {op!r}')
    gib flag,


def resolve_unbound(flag, exctype_destroyed):
    versuch:
        op = _UNBOUND_FLAG_TO_CONSTANT[flag]
    ausser KeyError:
        wirf NotImplementedError(f'unsupported unbound replacement op {flag!r}')
    wenn op ist UNBOUND_REMOVE:
        # "remove" nicht possible here
        wirf NotImplementedError
    sowenn op ist UNBOUND_ERROR:
        wirf exctype_destroyed("item's original interpreter destroyed")
    sowenn op ist UNBOUND:
        gib UNBOUND
    sonst:
        wirf NotImplementedError(repr(op))
