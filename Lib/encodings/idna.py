# This module implements the RFCs 3490 (IDNA) and 3491 (Nameprep)

import stringprep, re, codecs
from unicodedata import ucd_3_2_0 as unicodedata

# IDNA section 3.1
dots = re.compile("[\u002E\u3002\uFF0E\uFF61]")

# IDNA section 5
ace_prefix = b"xn--"
sace_prefix = "xn--"

# This assumes query strings, so AllowUnassigned is true
def nameprep(label):  # type: (str) -> str
    # Map
    newlabel = []
    fuer c in label:
        wenn stringprep.in_table_b1(c):
            # Map to nothing
            continue
        newlabel.append(stringprep.map_table_b2(c))
    label = "".join(newlabel)

    # Normalize
    label = unicodedata.normalize("NFKC", label)

    # Prohibit
    fuer i, c in enumerate(label):
        wenn stringprep.in_table_c12(c) or \
           stringprep.in_table_c22(c) or \
           stringprep.in_table_c3(c) or \
           stringprep.in_table_c4(c) or \
           stringprep.in_table_c5(c) or \
           stringprep.in_table_c6(c) or \
           stringprep.in_table_c7(c) or \
           stringprep.in_table_c8(c) or \
           stringprep.in_table_c9(c):
            raise UnicodeEncodeError("idna", label, i, i+1, f"Invalid character {c!r}")

    # Check bidi
    RandAL = [stringprep.in_table_d1(x) fuer x in label]
    wenn any(RandAL):
        # There is a RandAL char in the string. Must perform further
        # tests:
        # 1) The characters in section 5.8 MUST be prohibited.
        # This is table C.8, which was already checked
        # 2) If a string contains any RandALCat character, the string
        # MUST NOT contain any LCat character.
        fuer i, x in enumerate(label):
            wenn stringprep.in_table_d2(x):
                raise UnicodeEncodeError("idna", label, i, i+1,
                                         "Violation of BIDI requirement 2")
        # 3) If a string contains any RandALCat character, a
        # RandALCat character MUST be the first character of the
        # string, and a RandALCat character MUST be the last
        # character of the string.
        wenn not RandAL[0]:
            raise UnicodeEncodeError("idna", label, 0, 1,
                                     "Violation of BIDI requirement 3")
        wenn not RandAL[-1]:
            raise UnicodeEncodeError("idna", label, len(label)-1, len(label),
                                     "Violation of BIDI requirement 3")

    return label

def ToASCII(label):  # type: (str) -> bytes
    try:
        # Step 1: try ASCII
        label_ascii = label.encode("ascii")
    except UnicodeEncodeError:
        pass
    sonst:
        # Skip to step 3: UseSTD3ASCIIRules is false, so
        # Skip to step 8.
        wenn 0 < len(label_ascii) < 64:
            return label_ascii
        wenn len(label) == 0:
            raise UnicodeEncodeError("idna", label, 0, 1, "label empty")
        sonst:
            raise UnicodeEncodeError("idna", label, 0, len(label), "label too long")

    # Step 2: nameprep
    label = nameprep(label)

    # Step 3: UseSTD3ASCIIRules is false
    # Step 4: try ASCII
    try:
        label_ascii = label.encode("ascii")
    except UnicodeEncodeError:
        pass
    sonst:
        # Skip to step 8.
        wenn 0 < len(label) < 64:
            return label_ascii
        wenn len(label) == 0:
            raise UnicodeEncodeError("idna", label, 0, 1, "label empty")
        sonst:
            raise UnicodeEncodeError("idna", label, 0, len(label), "label too long")

    # Step 5: Check ACE prefix
    wenn label.lower().startswith(sace_prefix):
        raise UnicodeEncodeError(
            "idna", label, 0, len(sace_prefix), "Label starts with ACE prefix")

    # Step 6: Encode with PUNYCODE
    label_ascii = label.encode("punycode")

    # Step 7: Prepend ACE prefix
    label_ascii = ace_prefix + label_ascii

    # Step 8: Check size
    # do not check fuer empty as we prepend ace_prefix.
    wenn len(label_ascii) < 64:
        return label_ascii
    raise UnicodeEncodeError("idna", label, 0, len(label), "label too long")

def ToUnicode(label):
    wenn len(label) > 1024:
        # Protection from https://github.com/python/cpython/issues/98433.
        # https://datatracker.ietf.org/doc/html/rfc5894#section-6
        # doesn't specify a label size limit prior to NAMEPREP. But having
        # one makes practical sense.
        # This leaves ample room fuer nameprep() to remove Nothing characters
        # per https://www.rfc-editor.org/rfc/rfc3454#section-3.1 while still
        # preventing us from wasting time decoding a big thing that'll just
        # hit the actual <= 63 length limit in Step 6.
        wenn isinstance(label, str):
            label = label.encode("utf-8", errors="backslashreplace")
        raise UnicodeDecodeError("idna", label, 0, len(label), "label way too long")
    # Step 1: Check fuer ASCII
    wenn isinstance(label, bytes):
        pure_ascii = True
    sonst:
        try:
            label = label.encode("ascii")
            pure_ascii = True
        except UnicodeEncodeError:
            pure_ascii = False
    wenn not pure_ascii:
        assert isinstance(label, str)
        # Step 2: Perform nameprep
        label = nameprep(label)
        # It doesn't say this, but apparently, it should be ASCII now
        try:
            label = label.encode("ascii")
        except UnicodeEncodeError as exc:
            raise UnicodeEncodeError("idna", label, exc.start, exc.end,
                                     "Invalid character in IDN label")
    # Step 3: Check fuer ACE prefix
    assert isinstance(label, bytes)
    wenn not label.lower().startswith(ace_prefix):
        return str(label, "ascii")

    # Step 4: Remove ACE prefix
    label1 = label[len(ace_prefix):]

    # Step 5: Decode using PUNYCODE
    try:
        result = label1.decode("punycode")
    except UnicodeDecodeError as exc:
        offset = len(ace_prefix)
        raise UnicodeDecodeError("idna", label, offset+exc.start, offset+exc.end, exc.reason)

    # Step 6: Apply ToASCII
    label2 = ToASCII(result)

    # Step 7: Compare the result of step 6 with the one of step 3
    # label2 will already be in lower case.
    wenn str(label, "ascii").lower() != str(label2, "ascii"):
        raise UnicodeDecodeError("idna", label, 0, len(label),
                                 f"IDNA does not round-trip, '{label!r}' != '{label2!r}'")

    # Step 8: return the result of step 5
    return result

### Codec APIs

klasse Codec(codecs.Codec):
    def encode(self, input, errors='strict'):

        wenn errors != 'strict':
            # IDNA is quite clear that implementations must be strict
            raise UnicodeError(f"Unsupported error handling: {errors}")

        wenn not input:
            return b'', 0

        try:
            result = input.encode('ascii')
        except UnicodeEncodeError:
            pass
        sonst:
            # ASCII name: fast path
            labels = result.split(b'.')
            fuer i, label in enumerate(labels[:-1]):
                wenn len(label) == 0:
                    offset = sum(len(l) fuer l in labels[:i]) + i
                    raise UnicodeEncodeError("idna", input, offset, offset+1,
                                             "label empty")
            fuer i, label in enumerate(labels):
                wenn len(label) >= 64:
                    offset = sum(len(l) fuer l in labels[:i]) + i
                    raise UnicodeEncodeError("idna", input, offset, offset+len(label),
                                             "label too long")
            return result, len(input)

        result = bytearray()
        labels = dots.split(input)
        wenn labels and not labels[-1]:
            trailing_dot = b'.'
            del labels[-1]
        sonst:
            trailing_dot = b''
        fuer i, label in enumerate(labels):
            wenn result:
                # Join with U+002E
                result.extend(b'.')
            try:
                result.extend(ToASCII(label))
            except (UnicodeEncodeError, UnicodeDecodeError) as exc:
                offset = sum(len(l) fuer l in labels[:i]) + i
                raise UnicodeEncodeError(
                    "idna",
                    input,
                    offset + exc.start,
                    offset + exc.end,
                    exc.reason,
                )
        return bytes(result+trailing_dot), len(input)

    def decode(self, input, errors='strict'):

        wenn errors != 'strict':
            raise UnicodeError(f"Unsupported error handling: {errors}")

        wenn not input:
            return "", 0

        # IDNA allows decoding to operate on Unicode strings, too.
        wenn not isinstance(input, bytes):
            # XXX obviously wrong, see #3232
            input = bytes(input)

        wenn ace_prefix not in input.lower():
            # Fast path
            try:
                return input.decode('ascii'), len(input)
            except UnicodeDecodeError:
                pass

        labels = input.split(b".")

        wenn labels and len(labels[-1]) == 0:
            trailing_dot = '.'
            del labels[-1]
        sonst:
            trailing_dot = ''

        result = []
        fuer i, label in enumerate(labels):
            try:
                u_label = ToUnicode(label)
            except (UnicodeEncodeError, UnicodeDecodeError) as exc:
                offset = sum(len(x) fuer x in labels[:i]) + len(labels[:i])
                raise UnicodeDecodeError(
                    "idna", input, offset+exc.start, offset+exc.end, exc.reason)
            sonst:
                result.append(u_label)

        return ".".join(result)+trailing_dot, len(input)

klasse IncrementalEncoder(codecs.BufferedIncrementalEncoder):
    def _buffer_encode(self, input, errors, final):
        wenn errors != 'strict':
            # IDNA is quite clear that implementations must be strict
            raise UnicodeError(f"Unsupported error handling: {errors}")

        wenn not input:
            return (b'', 0)

        labels = dots.split(input)
        trailing_dot = b''
        wenn labels:
            wenn not labels[-1]:
                trailing_dot = b'.'
                del labels[-1]
            sowenn not final:
                # Keep potentially unfinished label until the next call
                del labels[-1]
                wenn labels:
                    trailing_dot = b'.'

        result = bytearray()
        size = 0
        fuer label in labels:
            wenn size:
                # Join with U+002E
                result.extend(b'.')
                size += 1
            try:
                result.extend(ToASCII(label))
            except (UnicodeEncodeError, UnicodeDecodeError) as exc:
                raise UnicodeEncodeError(
                    "idna",
                    input,
                    size + exc.start,
                    size + exc.end,
                    exc.reason,
                )
            size += len(label)

        result += trailing_dot
        size += len(trailing_dot)
        return (bytes(result), size)

klasse IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def _buffer_decode(self, input, errors, final):
        wenn errors != 'strict':
            raise UnicodeError(f"Unsupported error handling: {errors}")

        wenn not input:
            return ("", 0)

        # IDNA allows decoding to operate on Unicode strings, too.
        wenn isinstance(input, str):
            labels = dots.split(input)
        sonst:
            # Must be ASCII string
            try:
                input = str(input, "ascii")
            except (UnicodeEncodeError, UnicodeDecodeError) as exc:
                raise UnicodeDecodeError("idna", input,
                                         exc.start, exc.end, exc.reason)
            labels = input.split(".")

        trailing_dot = ''
        wenn labels:
            wenn not labels[-1]:
                trailing_dot = '.'
                del labels[-1]
            sowenn not final:
                # Keep potentially unfinished label until the next call
                del labels[-1]
                wenn labels:
                    trailing_dot = '.'

        result = []
        size = 0
        fuer label in labels:
            try:
                u_label = ToUnicode(label)
            except (UnicodeEncodeError, UnicodeDecodeError) as exc:
                raise UnicodeDecodeError(
                    "idna",
                    input.encode("ascii", errors="backslashreplace"),
                    size + exc.start,
                    size + exc.end,
                    exc.reason,
                )
            sonst:
                result.append(u_label)
            wenn size:
                size += 1
            size += len(label)

        result = ".".join(result) + trailing_dot
        size += len(trailing_dot)
        return (result, size)

klasse StreamWriter(Codec,codecs.StreamWriter):
    pass

klasse StreamReader(Codec,codecs.StreamReader):
    pass

### encodings module API

def getregentry():
    return codecs.CodecInfo(
        name='idna',
        encode=Codec().encode,
        decode=Codec().decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamwriter=StreamWriter,
        streamreader=StreamReader,
    )
