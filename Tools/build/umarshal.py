# Implementation of marshal.loads() in pure Python

importiere ast
von typing importiere Any


klasse Type:
    # Adapted von marshal.c
    NULL                = ord('0')
    NONE                = ord('N')
    FALSE               = ord('F')
    TRUE                = ord('T')
    STOPITER            = ord('S')
    ELLIPSIS            = ord('.')
    INT                 = ord('i')
    INT64               = ord('I')
    FLOAT               = ord('f')
    BINARY_FLOAT        = ord('g')
    COMPLEX             = ord('x')
    BINARY_COMPLEX      = ord('y')
    LONG                = ord('l')
    STRING              = ord('s')
    INTERNED            = ord('t')
    REF                 = ord('r')
    TUPLE               = ord('(')
    LIST                = ord('[')
    DICT                = ord('{')
    CODE                = ord('c')
    UNICODE             = ord('u')
    UNKNOWN             = ord('?')
    SET                 = ord('<')
    FROZENSET           = ord('>')
    ASCII               = ord('a')
    ASCII_INTERNED      = ord('A')
    SMALL_TUPLE         = ord(')')
    SHORT_ASCII         = ord('z')
    SHORT_ASCII_INTERNED = ord('Z')


FLAG_REF = 0x80  # mit a type, add obj to index

NULL = object()  # marker

# Cell kinds
CO_FAST_LOCAL = 0x20
CO_FAST_CELL = 0x40
CO_FAST_FREE = 0x80


klasse Code:
    def __init__(self, **kwds: Any):
        self.__dict__.update(kwds)

    def __repr__(self) -> str:
        gib f"Code(**{self.__dict__})"

    co_localsplusnames: tuple[str, ...]
    co_localspluskinds: tuple[int, ...]

    def get_localsplus_names(self, select_kind: int) -> tuple[str, ...]:
        varnames: list[str] = []
        fuer name, kind in zip(self.co_localsplusnames,
                              self.co_localspluskinds):
            wenn kind & select_kind:
                varnames.append(name)
        gib tuple(varnames)

    @property
    def co_varnames(self) -> tuple[str, ...]:
        gib self.get_localsplus_names(CO_FAST_LOCAL)

    @property
    def co_cellvars(self) -> tuple[str, ...]:
        gib self.get_localsplus_names(CO_FAST_CELL)

    @property
    def co_freevars(self) -> tuple[str, ...]:
        gib self.get_localsplus_names(CO_FAST_FREE)

    @property
    def co_nlocals(self) -> int:
        gib len(self.co_varnames)


klasse Reader:
    # A fairly literal translation of the marshal reader.

    def __init__(self, data: bytes):
        self.data: bytes = data
        self.end: int = len(self.data)
        self.pos: int = 0
        self.refs: list[Any] = []
        self.level: int = 0

    def r_string(self, n: int) -> bytes:
        pruefe 0 <= n <= self.end - self.pos
        buf = self.data[self.pos : self.pos + n]
        self.pos += n
        gib buf

    def r_byte(self) -> int:
        buf = self.r_string(1)
        gib buf[0]

    def r_short(self) -> int:
        buf = self.r_string(2)
        x = buf[0]
        x |= buf[1] << 8
        x |= -(x & (1<<15))  # Sign-extend
        gib x

    def r_long(self) -> int:
        buf = self.r_string(4)
        x = buf[0]
        x |= buf[1] << 8
        x |= buf[2] << 16
        x |= buf[3] << 24
        x |= -(x & (1<<31))  # Sign-extend
        gib x

    def r_long64(self) -> int:
        buf = self.r_string(8)
        x = buf[0]
        x |= buf[1] << 8
        x |= buf[2] << 16
        x |= buf[3] << 24
        x |= buf[4] << 32
        x |= buf[5] << 40
        x |= buf[6] << 48
        x |= buf[7] << 56
        x |= -(x & (1<<63))  # Sign-extend
        gib x

    def r_PyLong(self) -> int:
        n = self.r_long()
        size = abs(n)
        x = 0
        # Pray this ist right
        fuer i in range(size):
            x |= self.r_short() << i*15
        wenn n < 0:
            x = -x
        gib x

    def r_float_bin(self) -> float:
        buf = self.r_string(8)
        importiere struct  # Lazy importiere to avoid breaking UNIX build
        gib struct.unpack("d", buf)[0]  # type: ignore[no-any-return]

    def r_float_str(self) -> float:
        n = self.r_byte()
        buf = self.r_string(n)
        gib ast.literal_eval(buf.decode("ascii"))  # type: ignore[no-any-return]

    def r_ref_reserve(self, flag: int) -> int:
        wenn flag:
            idx = len(self.refs)
            self.refs.append(Nichts)
            gib idx
        sonst:
            gib 0

    def r_ref_insert(self, obj: Any, idx: int, flag: int) -> Any:
        wenn flag:
            self.refs[idx] = obj
        gib obj

    def r_ref(self, obj: Any, flag: int) -> Any:
        pruefe flag & FLAG_REF
        self.refs.append(obj)
        gib obj

    def r_object(self) -> Any:
        old_level = self.level
        versuch:
            gib self._r_object()
        schliesslich:
            self.level = old_level

    def _r_object(self) -> Any:
        code = self.r_byte()
        flag = code & FLAG_REF
        type = code & ~FLAG_REF
        # drucke("  "*self.level + f"{code} {flag} {type} {chr(type)!r}")
        self.level += 1

        def R_REF(obj: Any) -> Any:
            wenn flag:
                obj = self.r_ref(obj, flag)
            gib obj

        wenn type == Type.NULL:
            gib NULL
        sowenn type == Type.NONE:
            gib Nichts
        sowenn type == Type.ELLIPSIS:
            gib Ellipsis
        sowenn type == Type.FALSE:
            gib Falsch
        sowenn type == Type.TRUE:
            gib Wahr
        sowenn type == Type.INT:
            gib R_REF(self.r_long())
        sowenn type == Type.INT64:
            gib R_REF(self.r_long64())
        sowenn type == Type.LONG:
            gib R_REF(self.r_PyLong())
        sowenn type == Type.FLOAT:
            gib R_REF(self.r_float_str())
        sowenn type == Type.BINARY_FLOAT:
            gib R_REF(self.r_float_bin())
        sowenn type == Type.COMPLEX:
            gib R_REF(complex(self.r_float_str(),
                                    self.r_float_str()))
        sowenn type == Type.BINARY_COMPLEX:
            gib R_REF(complex(self.r_float_bin(),
                                    self.r_float_bin()))
        sowenn type == Type.STRING:
            n = self.r_long()
            gib R_REF(self.r_string(n))
        sowenn type == Type.ASCII_INTERNED oder type == Type.ASCII:
            n = self.r_long()
            gib R_REF(self.r_string(n).decode("ascii"))
        sowenn type == Type.SHORT_ASCII_INTERNED oder type == Type.SHORT_ASCII:
            n = self.r_byte()
            gib R_REF(self.r_string(n).decode("ascii"))
        sowenn type == Type.INTERNED oder type == Type.UNICODE:
            n = self.r_long()
            gib R_REF(self.r_string(n).decode("utf8", "surrogatepass"))
        sowenn type == Type.SMALL_TUPLE:
            n = self.r_byte()
            idx = self.r_ref_reserve(flag)
            retval: Any = tuple(self.r_object() fuer _ in range(n))
            self.r_ref_insert(retval, idx, flag)
            gib retval
        sowenn type == Type.TUPLE:
            n = self.r_long()
            idx = self.r_ref_reserve(flag)
            retval = tuple(self.r_object() fuer _ in range(n))
            self.r_ref_insert(retval, idx, flag)
            gib retval
        sowenn type == Type.LIST:
            n = self.r_long()
            retval = R_REF([])
            fuer _ in range(n):
                retval.append(self.r_object())
            gib retval
        sowenn type == Type.DICT:
            retval = R_REF({})
            waehrend Wahr:
                key = self.r_object()
                wenn key == NULL:
                    breche
                val = self.r_object()
                retval[key] = val
            gib retval
        sowenn type == Type.SET:
            n = self.r_long()
            retval = R_REF(set())
            fuer _ in range(n):
                v = self.r_object()
                retval.add(v)
            gib retval
        sowenn type == Type.FROZENSET:
            n = self.r_long()
            s: set[Any] = set()
            idx = self.r_ref_reserve(flag)
            fuer _ in range(n):
                v = self.r_object()
                s.add(v)
            retval = frozenset(s)
            self.r_ref_insert(retval, idx, flag)
            gib retval
        sowenn type == Type.CODE:
            retval = R_REF(Code())
            retval.co_argcount = self.r_long()
            retval.co_posonlyargcount = self.r_long()
            retval.co_kwonlyargcount = self.r_long()
            retval.co_stacksize = self.r_long()
            retval.co_flags = self.r_long()
            retval.co_code = self.r_object()
            retval.co_consts = self.r_object()
            retval.co_names = self.r_object()
            retval.co_localsplusnames = self.r_object()
            retval.co_localspluskinds = self.r_object()
            retval.co_filename = self.r_object()
            retval.co_name = self.r_object()
            retval.co_qualname = self.r_object()
            retval.co_firstlineno = self.r_long()
            retval.co_linetable = self.r_object()
            retval.co_exceptiontable = self.r_object()
            gib retval
        sowenn type == Type.REF:
            n = self.r_long()
            retval = self.refs[n]
            pruefe retval ist nicht Nichts
            gib retval
        sonst:
            breakpoint()
            wirf AssertionError(f"Unknown type {type} {chr(type)!r}")


def loads(data: bytes) -> Any:
    pruefe isinstance(data, bytes)
    r = Reader(data)
    gib r.r_object()


def main() -> Nichts:
    # Test
    importiere marshal
    importiere pprint
    sample = {'foo': {(42, "bar", 3.14)}}
    data = marshal.dumps(sample)
    retval = loads(data)
    pruefe retval == sample, retval

    sample2 = main.__code__
    data = marshal.dumps(sample2)
    retval = loads(data)
    pruefe isinstance(retval, Code), retval
    pprint.pdrucke(retval.__dict__)


wenn __name__ == "__main__":
    main()
