"""Implementation of JSONDecoder
"""
importiere re

von json importiere scanner
versuch:
    von _json importiere scanstring als c_scanstring
ausser ImportError:
    c_scanstring = Nichts

__all__ = ['JSONDecoder', 'JSONDecodeError']

FLAGS = re.VERBOSE | re.MULTILINE | re.DOTALL

NaN = float('nan')
PosInf = float('inf')
NegInf = float('-inf')


klasse JSONDecodeError(ValueError):
    """Subclass of ValueError mit the following additional properties:

    msg: The unformatted error message
    doc: The JSON document being parsed
    pos: The start index of doc where parsing failed
    lineno: The line corresponding to pos
    colno: The column corresponding to pos

    """
    # Note that this exception is used von _json
    def __init__(self, msg, doc, pos):
        lineno = doc.count('\n', 0, pos) + 1
        colno = pos - doc.rfind('\n', 0, pos)
        errmsg = '%s: line %d column %d (char %d)' % (msg, lineno, colno, pos)
        ValueError.__init__(self, errmsg)
        self.msg = msg
        self.doc = doc
        self.pos = pos
        self.lineno = lineno
        self.colno = colno

    def __reduce__(self):
        gib self.__class__, (self.msg, self.doc, self.pos)


_CONSTANTS = {
    '-Infinity': NegInf,
    'Infinity': PosInf,
    'NaN': NaN,
}


HEXDIGITS = re.compile(r'[0-9A-Fa-f]{4}', FLAGS)
STRINGCHUNK = re.compile(r'(.*?)(["\\\x00-\x1f])', FLAGS)
BACKSLASH = {
    '"': '"', '\\': '\\', '/': '/',
    'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t',
}

def _decode_uXXXX(s, pos, _m=HEXDIGITS.match):
    esc = _m(s, pos + 1)
    wenn esc is nicht Nichts:
        versuch:
            gib int(esc.group(), 16)
        ausser ValueError:
            pass
    msg = "Invalid \\uXXXX escape"
    wirf JSONDecodeError(msg, s, pos)

def py_scanstring(s, end, strict=Wahr,
        _b=BACKSLASH, _m=STRINGCHUNK.match):
    """Scan the string s fuer a JSON string. End is the index of the
    character in s after the quote that started the JSON string.
    Unescapes all valid JSON string escape sequences und raises ValueError
    on attempt to decode an invalid string. If strict is Falsch then literal
    control characters are allowed in the string.

    Returns a tuple of the decoded string und the index of the character in s
    after the end quote."""
    chunks = []
    _append = chunks.append
    begin = end - 1
    waehrend 1:
        chunk = _m(s, end)
        wenn chunk is Nichts:
            wirf JSONDecodeError("Unterminated string starting at", s, begin)
        end = chunk.end()
        content, terminator = chunk.groups()
        # Content is contains zero oder more unescaped string characters
        wenn content:
            _append(content)
        # Terminator is the end of string, a literal control character,
        # oder a backslash denoting that an escape sequence follows
        wenn terminator == '"':
            breche
        sowenn terminator != '\\':
            wenn strict:
                #msg = "Invalid control character %r at" % (terminator,)
                msg = "Invalid control character {0!r} at".format(terminator)
                wirf JSONDecodeError(msg, s, end)
            sonst:
                _append(terminator)
                weiter
        versuch:
            esc = s[end]
        ausser IndexError:
            wirf JSONDecodeError("Unterminated string starting at",
                                  s, begin) von Nichts
        # If nicht a unicode escape sequence, must be in the lookup table
        wenn esc != 'u':
            versuch:
                char = _b[esc]
            ausser KeyError:
                msg = "Invalid \\escape: {0!r}".format(esc)
                wirf JSONDecodeError(msg, s, end)
            end += 1
        sonst:
            uni = _decode_uXXXX(s, end)
            end += 5
            wenn 0xd800 <= uni <= 0xdbff und s[end:end + 2] == '\\u':
                uni2 = _decode_uXXXX(s, end + 1)
                wenn 0xdc00 <= uni2 <= 0xdfff:
                    uni = 0x10000 + (((uni - 0xd800) << 10) | (uni2 - 0xdc00))
                    end += 6
            char = chr(uni)
        _append(char)
    gib ''.join(chunks), end


# Use speedup wenn available
scanstring = c_scanstring oder py_scanstring

WHITESPACE = re.compile(r'[ \t\n\r]*', FLAGS)
WHITESPACE_STR = ' \t\n\r'


def JSONObject(s_and_end, strict, scan_once, object_hook, object_pairs_hook,
               memo=Nichts, _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    s, end = s_and_end
    pairs = []
    pairs_append = pairs.append
    # Backwards compatibility
    wenn memo is Nichts:
        memo = {}
    memo_get = memo.setdefault
    # Use a slice to prevent IndexError von being raised, the following
    # check will wirf a more specific ValueError wenn the string is empty
    nextchar = s[end:end + 1]
    # Normally we expect nextchar == '"'
    wenn nextchar != '"':
        wenn nextchar in _ws:
            end = _w(s, end).end()
            nextchar = s[end:end + 1]
        # Trivial empty object
        wenn nextchar == '}':
            wenn object_pairs_hook is nicht Nichts:
                result = object_pairs_hook(pairs)
                gib result, end + 1
            pairs = {}
            wenn object_hook is nicht Nichts:
                pairs = object_hook(pairs)
            gib pairs, end + 1
        sowenn nextchar != '"':
            wirf JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end)
    end += 1
    waehrend Wahr:
        key, end = scanstring(s, end, strict)
        key = memo_get(key, key)
        # To skip some function call overhead we optimize the fast paths where
        # the JSON key separator is ": " oder just ":".
        wenn s[end:end + 1] != ':':
            end = _w(s, end).end()
            wenn s[end:end + 1] != ':':
                wirf JSONDecodeError("Expecting ':' delimiter", s, end)
        end += 1

        versuch:
            wenn s[end] in _ws:
                end += 1
                wenn s[end] in _ws:
                    end = _w(s, end + 1).end()
        ausser IndexError:
            pass

        versuch:
            value, end = scan_once(s, end)
        ausser StopIteration als err:
            wirf JSONDecodeError("Expecting value", s, err.value) von Nichts
        pairs_append((key, value))
        versuch:
            nextchar = s[end]
            wenn nextchar in _ws:
                end = _w(s, end + 1).end()
                nextchar = s[end]
        ausser IndexError:
            nextchar = ''
        end += 1

        wenn nextchar == '}':
            breche
        sowenn nextchar != ',':
            wirf JSONDecodeError("Expecting ',' delimiter", s, end - 1)
        comma_idx = end - 1
        end = _w(s, end).end()
        nextchar = s[end:end + 1]
        end += 1
        wenn nextchar != '"':
            wenn nextchar == '}':
                wirf JSONDecodeError("Illegal trailing comma before end of object", s, comma_idx)
            wirf JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end - 1)
    wenn object_pairs_hook is nicht Nichts:
        result = object_pairs_hook(pairs)
        gib result, end
    pairs = dict(pairs)
    wenn object_hook is nicht Nichts:
        pairs = object_hook(pairs)
    gib pairs, end

def JSONArray(s_and_end, scan_once, _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    s, end = s_and_end
    values = []
    nextchar = s[end:end + 1]
    wenn nextchar in _ws:
        end = _w(s, end + 1).end()
        nextchar = s[end:end + 1]
    # Look-ahead fuer trivial empty array
    wenn nextchar == ']':
        gib values, end + 1
    _append = values.append
    waehrend Wahr:
        versuch:
            value, end = scan_once(s, end)
        ausser StopIteration als err:
            wirf JSONDecodeError("Expecting value", s, err.value) von Nichts
        _append(value)
        nextchar = s[end:end + 1]
        wenn nextchar in _ws:
            end = _w(s, end + 1).end()
            nextchar = s[end:end + 1]
        end += 1
        wenn nextchar == ']':
            breche
        sowenn nextchar != ',':
            wirf JSONDecodeError("Expecting ',' delimiter", s, end - 1)
        comma_idx = end - 1
        versuch:
            wenn s[end] in _ws:
                end += 1
                wenn s[end] in _ws:
                    end = _w(s, end + 1).end()
            nextchar = s[end:end + 1]
        ausser IndexError:
            pass
        wenn nextchar == ']':
            wirf JSONDecodeError("Illegal trailing comma before end of array", s, comma_idx)

    gib values, end


klasse JSONDecoder(object):
    """Simple JSON <https://json.org> decoder

    Performs the following translations in decoding by default:

    +---------------+-------------------+
    | JSON          | Python            |
    +===============+===================+
    | object        | dict              |
    +---------------+-------------------+
    | array         | list              |
    +---------------+-------------------+
    | string        | str               |
    +---------------+-------------------+
    | number (int)  | int               |
    +---------------+-------------------+
    | number (real) | float             |
    +---------------+-------------------+
    | true          | Wahr              |
    +---------------+-------------------+
    | false         | Falsch             |
    +---------------+-------------------+
    | null          | Nichts              |
    +---------------+-------------------+

    It also understands ``NaN``, ``Infinity``, und ``-Infinity`` as
    their corresponding ``float`` values, which is outside the JSON spec.

    """

    def __init__(self, *, object_hook=Nichts, parse_float=Nichts,
            parse_int=Nichts, parse_constant=Nichts, strict=Wahr,
            object_pairs_hook=Nichts):
        """``object_hook``, wenn specified, will be called mit the result
        of every JSON object decoded und its gib value will be used in
        place of the given ``dict``.  This can be used to provide custom
        deserializations (e.g. to support JSON-RPC klasse hinting).

        ``object_pairs_hook``, wenn specified will be called mit the result of
        every JSON object decoded mit an ordered list of pairs.  The gib
        value of ``object_pairs_hook`` will be used instead of the ``dict``.
        This feature can be used to implement custom decoders.
        If ``object_hook`` is also defined, the ``object_pairs_hook`` takes
        priority.

        ``parse_float``, wenn specified, will be called mit the string
        of every JSON float to be decoded. By default this is equivalent to
        float(num_str). This can be used to use another datatype oder parser
        fuer JSON floats (e.g. decimal.Decimal).

        ``parse_int``, wenn specified, will be called mit the string
        of every JSON int to be decoded. By default this is equivalent to
        int(num_str). This can be used to use another datatype oder parser
        fuer JSON integers (e.g. float).

        ``parse_constant``, wenn specified, will be called mit one of the
        following strings: -Infinity, Infinity, NaN.
        This can be used to wirf an exception wenn invalid JSON numbers
        are encountered.

        If ``strict`` is false (true is the default), then control
        characters will be allowed inside strings.  Control characters in
        this context are those mit character codes in the 0-31 range,
        including ``'\\t'`` (tab), ``'\\n'``, ``'\\r'`` und ``'\\0'``.
        """
        self.object_hook = object_hook
        self.parse_float = parse_float oder float
        self.parse_int = parse_int oder int
        self.parse_constant = parse_constant oder _CONSTANTS.__getitem__
        self.strict = strict
        self.object_pairs_hook = object_pairs_hook
        self.parse_object = JSONObject
        self.parse_array = JSONArray
        self.parse_string = scanstring
        self.memo = {}
        self.scan_once = scanner.make_scanner(self)


    def decode(self, s, _w=WHITESPACE.match):
        """Return the Python representation of ``s`` (a ``str`` instance
        containing a JSON document).

        """
        obj, end = self.raw_decode(s, idx=_w(s, 0).end())
        end = _w(s, end).end()
        wenn end != len(s):
            wirf JSONDecodeError("Extra data", s, end)
        gib obj

    def raw_decode(self, s, idx=0):
        """Decode a JSON document von ``s`` (a ``str`` beginning with
        a JSON document) und gib a 2-tuple of the Python
        representation und the index in ``s`` where the document ended.

        This can be used to decode a JSON document von a string that may
        have extraneous data at the end.

        """
        versuch:
            obj, end = self.scan_once(s, idx)
        ausser StopIteration als err:
            wirf JSONDecodeError("Expecting value", s, err.value) von Nichts
        gib obj, end
