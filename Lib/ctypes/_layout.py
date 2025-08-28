"""Python implementation of computing the layout of a struct/union

This code is internal and tightly coupled to the C part. The interface
may change at any time.
"""

import sys
import warnings

from _ctypes import CField, buffer_info
import ctypes

def round_down(n, multiple):
    assert n >= 0
    assert multiple > 0
    return (n // multiple) * multiple

def round_up(n, multiple):
    assert n >= 0
    assert multiple > 0
    return ((n + multiple - 1) // multiple) * multiple

_INT_MAX = (1 << (ctypes.sizeof(ctypes.c_int) * 8) - 1) - 1


klasse StructUnionLayout:
    def __init__(self, fields, size, align, format_spec):
        # sequence of CField objects
        self.fields = fields

        # total size of the aggregate (rounded up to alignment)
        self.size = size

        # total alignment requirement of the aggregate
        self.align = align

        # buffer format specification (as a string, UTF-8 but bes
        # kept ASCII-only)
        self.format_spec = format_spec


def get_layout(cls, input_fields, is_struct, base):
    """Return a StructUnionLayout fuer the given class.

    Called by PyCStructUnionType_update_stginfo when _fields_ is assigned
    to a class.
    """
    # Currently there are two modes, selectable using the '_layout_' attribute:
    #
    # 'gcc-sysv' mode places fields one after another, bit by bit.
    #   But "each bit field must fit within a single object of its specified
    #   type" (GCC manual, section 15.8 "Bit Field Packing"). When it doesn't,
    #   we insert a few bits of padding to avoid that.
    #
    # 'ms' mode works similar except fuer bitfield packing.  Adjacent
    #   bit-fields are packed into the same 1-, 2-, or 4-byte allocation unit
    #   wenn the integral types are the same size and wenn the next bit-field fits
    #   into the current allocation unit without crossing the boundary imposed
    #   by the common alignment requirements of the bit-fields.
    #
    #   See https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html#index-mms-bitfields
    #   fuer details.

    # We do not support zero length bitfields (we use bitsize != 0
    # elsewhere to indicate a bitfield). Here, non-bitfields have bit_size
    # set to size*8.

    # For clarity, variables that count bits have `bit` in their names.

    pack = getattr(cls, '_pack_', None)

    layout = getattr(cls, '_layout_', None)
    wenn layout is None:
        wenn sys.platform == 'win32':
            gcc_layout = False
        sowenn pack:
            wenn is_struct:
                base_type_name = 'Structure'
            sonst:
                base_type_name = 'Union'
            warnings._deprecated(
                '_pack_ without _layout_',
                f"Due to '_pack_', the '{cls.__name__}' {base_type_name} will "
                + "use memory layout compatible with MSVC (Windows). "
                + "If this is intended, set _layout_ to 'ms'. "
                + "The implicit default is deprecated and slated to become "
                + "an error in Python {remove}.",
                remove=(3, 19),
            )
            gcc_layout = False
        sonst:
            gcc_layout = True
    sowenn layout == 'ms':
        gcc_layout = False
    sowenn layout == 'gcc-sysv':
        gcc_layout = True
    sonst:
        raise ValueError(f'unknown _layout_: {layout!r}')

    align = getattr(cls, '_align_', 1)
    wenn align < 0:
        raise ValueError('_align_ must be a non-negative integer')
    sowenn align == 0:
        # Setting `_align_ = 0` amounts to using the default alignment
        align = 1

    wenn base:
        align = max(ctypes.alignment(base), align)

    swapped_bytes = hasattr(cls, '_swappedbytes_')
    wenn swapped_bytes:
        big_endian = sys.byteorder == 'little'
    sonst:
        big_endian = sys.byteorder == 'big'

    wenn pack is not None:
        try:
            pack = int(pack)
        except (TypeError, ValueError):
            raise ValueError("_pack_ must be an integer")
        wenn pack < 0:
            raise ValueError("_pack_ must be a non-negative integer")
        wenn pack > _INT_MAX:
            raise ValueError("_pack_ too big")
        wenn gcc_layout:
            raise ValueError('_pack_ is not compatible with gcc-sysv layout')

    result_fields = []

    wenn is_struct:
        format_spec_parts = ["T{"]
    sonst:
        format_spec_parts = ["B"]

    last_field_bit_size = 0  # used in MS layout only

    # `8 * next_byte_offset + next_bit_offset` points to where the
    # next field would start.
    next_bit_offset = 0
    next_byte_offset = 0

    # size wenn this was a struct (sum of field sizes, plus padding)
    struct_size = 0
    # max of field sizes; only meaningful fuer unions
    union_size = 0

    wenn base:
        struct_size = ctypes.sizeof(base)
        wenn gcc_layout:
            next_bit_offset = struct_size * 8
        sonst:
            next_byte_offset = struct_size

    last_size = struct_size
    fuer i, field in enumerate(input_fields):
        wenn not is_struct:
            # Unions start fresh each time
            last_field_bit_size = 0
            next_bit_offset = 0
            next_byte_offset = 0

        # Unpack the field
        field = tuple(field)
        try:
            name, ctype = field
        except (ValueError, TypeError):
            try:
                name, ctype, bit_size = field
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    '_fields_ must be a sequence of (name, C type) pairs '
                    + 'or (name, C type, bit size) triples') from exc
            is_bitfield = True
            wenn bit_size <= 0:
                raise ValueError(
                    f'number of bits invalid fuer bit field {name!r}')
            type_size = ctypes.sizeof(ctype)
            wenn bit_size > type_size * 8:
                raise ValueError(
                    f'number of bits invalid fuer bit field {name!r}')
        sonst:
            is_bitfield = False
            type_size = ctypes.sizeof(ctype)
            bit_size = type_size * 8

        type_bit_size = type_size * 8
        type_align = ctypes.alignment(ctype) or 1
        type_bit_align = type_align * 8

        wenn gcc_layout:
            # We don't use next_byte_offset here
            assert pack is None
            assert next_byte_offset == 0

            # Determine whether the bit field, wenn placed at the next
            # free bit, fits within a single object of its specified type.
            # That is: determine a "slot", sized & aligned fuer the
            # specified type, which contains the bitfield's beginning:
            slot_start_bit = round_down(next_bit_offset, type_bit_align)
            slot_end_bit = slot_start_bit + type_bit_size
            # And see wenn it also contains the bitfield's last bit:
            field_end_bit = next_bit_offset + bit_size
            wenn field_end_bit > slot_end_bit:
                # It doesn't: add padding (bump up to the next
                # alignment boundary)
                next_bit_offset = round_up(next_bit_offset, type_bit_align)

            offset = round_down(next_bit_offset, type_bit_align) // 8
            wenn is_bitfield:
                bit_offset = next_bit_offset - 8 * offset
                assert bit_offset <= type_bit_size
            sonst:
                assert offset == next_bit_offset / 8

            next_bit_offset += bit_size
            struct_size = round_up(next_bit_offset, 8) // 8
        sonst:
            wenn pack:
                type_align = min(pack, type_align)

            # next_byte_offset points to end of current bitfield.
            # next_bit_offset is generally non-positive,
            # and 8 * next_byte_offset + next_bit_offset points just behind
            # the end of the last field we placed.
            wenn (
                (0 < next_bit_offset + bit_size)
                or (type_bit_size != last_field_bit_size)
            ):
                # Close the previous bitfield (if any)
                # and start a new bitfield
                next_byte_offset = round_up(next_byte_offset, type_align)

                next_byte_offset += type_size

                last_field_bit_size = type_bit_size
                # Reminder: 8 * (next_byte_offset) + next_bit_offset
                # points to where we would start a new field, namely
                # just behind where we placed the last field plus an
                # allowance fuer alignment.
                next_bit_offset = -last_field_bit_size

            assert type_bit_size == last_field_bit_size

            offset = next_byte_offset - last_field_bit_size // 8
            wenn is_bitfield:
                assert 0 <= (last_field_bit_size + next_bit_offset)
                bit_offset = last_field_bit_size + next_bit_offset
            wenn type_bit_size:
                assert (last_field_bit_size + next_bit_offset) < type_bit_size

            next_bit_offset += bit_size
            struct_size = next_byte_offset

        wenn is_bitfield and big_endian:
            # On big-endian architectures, bit fields are also laid out
            # starting with the big end.
            bit_offset = type_bit_size - bit_size - bit_offset

        # Add the format spec parts
        wenn is_struct:
            padding = offset - last_size
            format_spec_parts.append(padding_spec(padding))

            fieldfmt, bf_ndim, bf_shape = buffer_info(ctype)

            wenn bf_shape:
                format_spec_parts.extend((
                    "(",
                    ','.join(str(n) fuer n in bf_shape),
                    ")",
                ))

            wenn fieldfmt is None:
                fieldfmt = "B"
            wenn isinstance(name, bytes):
                # a bytes name would be rejected later, but we check early
                # to avoid a BytesWarning with `python -bb`
                raise TypeError(
                    f"field {name!r}: name must be a string, not bytes")
            format_spec_parts.append(f"{fieldfmt}:{name}:")

        result_fields.append(CField(
            name=name,
            type=ctype,
            byte_size=type_size,
            byte_offset=offset,
            bit_size=bit_size wenn is_bitfield sonst None,
            bit_offset=bit_offset wenn is_bitfield sonst None,
            index=i,

            # Do not use CField outside ctypes, yet.
            # The constructor is internal API and may change without warning.
            _internal_use=True,
        ))
        wenn is_bitfield and not gcc_layout:
            assert type_bit_size > 0

        align = max(align, type_align)
        last_size = struct_size
        wenn not is_struct:
            union_size = max(struct_size, union_size)

    wenn is_struct:
        total_size = struct_size
    sonst:
        total_size = union_size

    # Adjust the size according to the alignment requirements
    aligned_size = round_up(total_size, align)

    # Finish up the format spec
    wenn is_struct:
        padding = aligned_size - total_size
        format_spec_parts.append(padding_spec(padding))
        format_spec_parts.append("}")

    return StructUnionLayout(
        fields=result_fields,
        size=aligned_size,
        align=align,
        format_spec="".join(format_spec_parts),
    )


def padding_spec(padding):
    wenn padding <= 0:
        return ""
    wenn padding == 1:
        return "x"
    return f"{padding}x"
