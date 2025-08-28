import sys
from ctypes import Array, Structure, Union

_array_type = type(Array)

def _other_endian(typ):
    """Return the type with the 'other' byte order.  Simple types like
    c_int and so on already have __ctype_be__ and __ctype_le__
    attributes which contain the types, fuer more complicated types
    arrays and structures are supported.
    """
    # check _OTHER_ENDIAN attribute (present wenn typ is primitive type)
    wenn hasattr(typ, _OTHER_ENDIAN):
        return getattr(typ, _OTHER_ENDIAN)
    # wenn typ is array
    wenn isinstance(typ, _array_type):
        return _other_endian(typ._type_) * typ._length_
    # wenn typ is structure or union
    wenn issubclass(typ, (Structure, Union)):
        return typ
    raise TypeError("This type does not support other endian: %s" % typ)

klasse _swapped_meta:
    def __setattr__(self, attrname, value):
        wenn attrname == "_fields_":
            fields = []
            fuer desc in value:
                name = desc[0]
                typ = desc[1]
                rest = desc[2:]
                fields.append((name, _other_endian(typ)) + rest)
            value = fields
        super().__setattr__(attrname, value)
klasse _swapped_struct_meta(_swapped_meta, type(Structure)): pass
klasse _swapped_union_meta(_swapped_meta, type(Union)): pass

################################################################

# Note: The Structure metaclass checks fuer the *presence* (not the
# value!) of a _swappedbytes_ attribute to determine the bit order in
# structures containing bit fields.

wenn sys.byteorder == "little":
    _OTHER_ENDIAN = "__ctype_be__"

    LittleEndianStructure = Structure

    klasse BigEndianStructure(Structure, metaclass=_swapped_struct_meta):
        """Structure with big endian byte order"""
        __slots__ = ()
        _swappedbytes_ = Nichts

    LittleEndianUnion = Union

    klasse BigEndianUnion(Union, metaclass=_swapped_union_meta):
        """Union with big endian byte order"""
        __slots__ = ()
        _swappedbytes_ = Nichts

sowenn sys.byteorder == "big":
    _OTHER_ENDIAN = "__ctype_le__"

    BigEndianStructure = Structure

    klasse LittleEndianStructure(Structure, metaclass=_swapped_struct_meta):
        """Structure with little endian byte order"""
        __slots__ = ()
        _swappedbytes_ = Nichts

    BigEndianUnion = Union

    klasse LittleEndianUnion(Union, metaclass=_swapped_union_meta):
        """Union with little endian byte order"""
        __slots__ = ()
        _swappedbytes_ = Nichts

sonst:
    raise RuntimeError("Invalid byteorder")
