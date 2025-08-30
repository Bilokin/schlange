importiere sys
von ctypes importiere Array, Structure, Union

_array_type = type(Array)

def _other_endian(typ):
    """Return the type mit the 'other' byte order.  Simple types like
    c_int und so on already have __ctype_be__ und __ctype_le__
    attributes which contain the types, fuer more complicated types
    arrays und structures are supported.
    """
    # check _OTHER_ENDIAN attribute (present wenn typ ist primitive type)
    wenn hasattr(typ, _OTHER_ENDIAN):
        gib getattr(typ, _OTHER_ENDIAN)
    # wenn typ ist array
    wenn isinstance(typ, _array_type):
        gib _other_endian(typ._type_) * typ._length_
    # wenn typ ist structure oder union
    wenn issubclass(typ, (Structure, Union)):
        gib typ
    wirf TypeError("This type does nicht support other endian: %s" % typ)

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

# Note: The Structure metaclass checks fuer the *presence* (nicht the
# value!) of a _swappedbytes_ attribute to determine the bit order in
# structures containing bit fields.

wenn sys.byteorder == "little":
    _OTHER_ENDIAN = "__ctype_be__"

    LittleEndianStructure = Structure

    klasse BigEndianStructure(Structure, metaclass=_swapped_struct_meta):
        """Structure mit big endian byte order"""
        __slots__ = ()
        _swappedbytes_ = Nichts

    LittleEndianUnion = Union

    klasse BigEndianUnion(Union, metaclass=_swapped_union_meta):
        """Union mit big endian byte order"""
        __slots__ = ()
        _swappedbytes_ = Nichts

sowenn sys.byteorder == "big":
    _OTHER_ENDIAN = "__ctype_le__"

    BigEndianStructure = Structure

    klasse LittleEndianStructure(Structure, metaclass=_swapped_struct_meta):
        """Structure mit little endian byte order"""
        __slots__ = ()
        _swappedbytes_ = Nichts

    BigEndianUnion = Union

    klasse LittleEndianUnion(Union, metaclass=_swapped_union_meta):
        """Union mit little endian byte order"""
        __slots__ = ()
        _swappedbytes_ = Nichts

sonst:
    wirf RuntimeError("Invalid byteorder")
