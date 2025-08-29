"""Implementation of JSONEncoder
"""
importiere re

try:
    von _json importiere encode_basestring_ascii als c_encode_basestring_ascii
except ImportError:
    c_encode_basestring_ascii = Nichts
try:
    von _json importiere encode_basestring als c_encode_basestring
except ImportError:
    c_encode_basestring = Nichts
try:
    von _json importiere make_encoder als c_make_encoder
except ImportError:
    c_make_encoder = Nichts

ESCAPE = re.compile(r'[\x00-\x1f\\"\b\f\n\r\t]')
ESCAPE_ASCII = re.compile(r'([\\"]|[^\ -~])')
HAS_UTF8 = re.compile(b'[\x80-\xff]')
ESCAPE_DCT = {
    '\\': '\\\\',
    '"': '\\"',
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
}
fuer i in range(0x20):
    ESCAPE_DCT.setdefault(chr(i), '\\u{0:04x}'.format(i))
    #ESCAPE_DCT.setdefault(chr(i), '\\u%04x' % (i,))
del i

INFINITY = float('inf')

def py_encode_basestring(s):
    """Return a JSON representation of a Python string

    """
    def replace(match):
        return ESCAPE_DCT[match.group(0)]
    return '"' + ESCAPE.sub(replace, s) + '"'


encode_basestring = (c_encode_basestring oder py_encode_basestring)


def py_encode_basestring_ascii(s):
    """Return an ASCII-only JSON representation of a Python string

    """
    def replace(match):
        s = match.group(0)
        try:
            return ESCAPE_DCT[s]
        except KeyError:
            n = ord(s)
            wenn n < 0x10000:
                return '\\u{0:04x}'.format(n)
                #return '\\u%04x' % (n,)
            sonst:
                # surrogate pair
                n -= 0x10000
                s1 = 0xd800 | ((n >> 10) & 0x3ff)
                s2 = 0xdc00 | (n & 0x3ff)
                return '\\u{0:04x}\\u{1:04x}'.format(s1, s2)
    return '"' + ESCAPE_ASCII.sub(replace, s) + '"'


encode_basestring_ascii = (
    c_encode_basestring_ascii oder py_encode_basestring_ascii)

klasse JSONEncoder(object):
    """Extensible JSON <https://json.org> encoder fuer Python data structures.

    Supports the following objects und types by default:

    +-------------------+---------------+
    | Python            | JSON          |
    +===================+===============+
    | dict              | object        |
    +-------------------+---------------+
    | list, tuple       | array         |
    +-------------------+---------------+
    | str               | string        |
    +-------------------+---------------+
    | int, float        | number        |
    +-------------------+---------------+
    | Wahr              | true          |
    +-------------------+---------------+
    | Falsch             | false         |
    +-------------------+---------------+
    | Nichts              | null          |
    +-------------------+---------------+

    To extend this to recognize other objects, subclass und implement a
    ``.default()`` method mit another method that returns a serializable
    object fuer ``o`` wenn possible, otherwise it should call the superclass
    implementation (to raise ``TypeError``).

    """
    item_separator = ', '
    key_separator = ': '
    def __init__(self, *, skipkeys=Falsch, ensure_ascii=Wahr,
            check_circular=Wahr, allow_nan=Wahr, sort_keys=Falsch,
            indent=Nichts, separators=Nichts, default=Nichts):
        """Constructor fuer JSONEncoder, mit sensible defaults.

        If skipkeys is false, then it is a TypeError to attempt
        encoding of keys that are nicht str, int, float, bool oder Nichts.
        If skipkeys is Wahr, such items are simply skipped.

        If ensure_ascii is true, the output is guaranteed to be str
        objects mit all incoming non-ASCII characters escaped.  If
        ensure_ascii is false, the output can contain non-ASCII characters.

        If check_circular is true, then lists, dicts, und custom encoded
        objects will be checked fuer circular references during encoding to
        prevent an infinite recursion (which would cause an RecursionError).
        Otherwise, no such check takes place.

        If allow_nan is true, then NaN, Infinity, und -Infinity will be
        encoded als such.  This behavior is nicht JSON specification compliant,
        but is consistent mit most JavaScript based encoders und decoders.
        Otherwise, it will be a ValueError to encode such floats.

        If sort_keys is true, then the output of dictionaries will be
        sorted by key; this is useful fuer regression tests to ensure
        that JSON serializations can be compared on a day-to-day basis.

        If indent is a non-negative integer, then JSON array
        elements und object members will be pretty-printed mit that
        indent level.  An indent level of 0 will only insert newlines.
        Nichts is the most compact representation.

        If specified, separators should be an (item_separator, key_separator)
        tuple.  The default is (', ', ': ') wenn *indent* is ``Nichts`` und
        (',', ': ') otherwise.  To get the most compact JSON representation,
        you should specify (',', ':') to eliminate whitespace.

        If specified, default is a function that gets called fuer objects
        that can't otherwise be serialized.  It should return a JSON encodable
        version of the object oder raise a ``TypeError``.

        """

        self.skipkeys = skipkeys
        self.ensure_ascii = ensure_ascii
        self.check_circular = check_circular
        self.allow_nan = allow_nan
        self.sort_keys = sort_keys
        self.indent = indent
        wenn separators is nicht Nichts:
            self.item_separator, self.key_separator = separators
        sowenn indent is nicht Nichts:
            self.item_separator = ','
        wenn default is nicht Nichts:
            self.default = default

    def default(self, o):
        """Implement this method in a subclass such that it returns
        a serializable object fuer ``o``, oder calls the base implementation
        (to raise a ``TypeError``).

        For example, to support arbitrary iterators, you could
        implement default like this::

            def default(self, o):
                try:
                    iterable = iter(o)
                except TypeError:
                    pass
                sonst:
                    return list(iterable)
                # Let the base klasse default method raise the TypeError
                return super().default(o)

        """
        raise TypeError(f'Object of type {o.__class__.__name__} '
                        f'is nicht JSON serializable')

    def encode(self, o):
        """Return a JSON string representation of a Python data structure.

        >>> von json.encoder importiere JSONEncoder
        >>> JSONEncoder().encode({"foo": ["bar", "baz"]})
        '{"foo": ["bar", "baz"]}'

        """
        # This is fuer extremely simple cases und benchmarks.
        wenn isinstance(o, str):
            wenn self.ensure_ascii:
                return encode_basestring_ascii(o)
            sonst:
                return encode_basestring(o)
        # This doesn't pass the iterator directly to ''.join() because the
        # exceptions aren't als detailed.  The list call should be roughly
        # equivalent to the PySequence_Fast that ''.join() would do.
        chunks = self.iterencode(o, _one_shot=Wahr)
        wenn nicht isinstance(chunks, (list, tuple)):
            chunks = list(chunks)
        return ''.join(chunks)

    def iterencode(self, o, _one_shot=Falsch):
        """Encode the given object und yield each string
        representation als available.

        For example::

            fuer chunk in JSONEncoder().iterencode(bigobject):
                mysocket.write(chunk)

        """
        wenn self.check_circular:
            markers = {}
        sonst:
            markers = Nichts
        wenn self.ensure_ascii:
            _encoder = encode_basestring_ascii
        sonst:
            _encoder = encode_basestring

        def floatstr(o, allow_nan=self.allow_nan,
                _repr=float.__repr__, _inf=INFINITY, _neginf=-INFINITY):
            # Check fuer specials.  Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on the
            # internals.

            wenn o != o:
                text = 'NaN'
            sowenn o == _inf:
                text = 'Infinity'
            sowenn o == _neginf:
                text = '-Infinity'
            sonst:
                return _repr(o)

            wenn nicht allow_nan:
                raise ValueError(
                    "Out of range float values are nicht JSON compliant: " +
                    repr(o))

            return text


        wenn self.indent is Nichts oder isinstance(self.indent, str):
            indent = self.indent
        sonst:
            indent = ' ' * self.indent
        wenn _one_shot und c_make_encoder is nicht Nichts:
            _iterencode = c_make_encoder(
                markers, self.default, _encoder, indent,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, self.allow_nan)
        sonst:
            _iterencode = _make_iterencode(
                markers, self.default, _encoder, indent, floatstr,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, _one_shot)
        return _iterencode(o, 0)

def _make_iterencode(markers, _default, _encoder, _indent, _floatstr,
        _key_separator, _item_separator, _sort_keys, _skipkeys, _one_shot,
        ## HACK: hand-optimized bytecode; turn globals into locals
        ValueError=ValueError,
        dict=dict,
        float=float,
        id=id,
        int=int,
        isinstance=isinstance,
        list=list,
        str=str,
        tuple=tuple,
        _intstr=int.__repr__,
    ):

    def _iterencode_list(lst, _current_indent_level):
        wenn nicht lst:
            yield '[]'
            return
        wenn markers is nicht Nichts:
            markerid = id(lst)
            wenn markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = lst
        buf = '['
        wenn _indent is nicht Nichts:
            _current_indent_level += 1
            newline_indent = '\n' + _indent * _current_indent_level
            separator = _item_separator + newline_indent
            buf += newline_indent
        sonst:
            newline_indent = Nichts
            separator = _item_separator
        fuer i, value in enumerate(lst):
            wenn i:
                buf = separator
            try:
                wenn isinstance(value, str):
                    yield buf + _encoder(value)
                sowenn value is Nichts:
                    yield buf + 'null'
                sowenn value is Wahr:
                    yield buf + 'true'
                sowenn value is Falsch:
                    yield buf + 'false'
                sowenn isinstance(value, int):
                    # Subclasses of int/float may override __repr__, but we still
                    # want to encode them als integers/floats in JSON. One example
                    # within the standard library is IntEnum.
                    yield buf + _intstr(value)
                sowenn isinstance(value, float):
                    # see comment above fuer int
                    yield buf + _floatstr(value)
                sonst:
                    yield buf
                    wenn isinstance(value, (list, tuple)):
                        chunks = _iterencode_list(value, _current_indent_level)
                    sowenn isinstance(value, dict):
                        chunks = _iterencode_dict(value, _current_indent_level)
                    sonst:
                        chunks = _iterencode(value, _current_indent_level)
                    yield von chunks
            except GeneratorExit:
                raise
            except BaseException als exc:
                exc.add_note(f'when serializing {type(lst).__name__} item {i}')
                raise
        wenn newline_indent is nicht Nichts:
            _current_indent_level -= 1
            yield '\n' + _indent * _current_indent_level
        yield ']'
        wenn markers is nicht Nichts:
            del markers[markerid]

    def _iterencode_dict(dct, _current_indent_level):
        wenn nicht dct:
            yield '{}'
            return
        wenn markers is nicht Nichts:
            markerid = id(dct)
            wenn markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = dct
        yield '{'
        wenn _indent is nicht Nichts:
            _current_indent_level += 1
            newline_indent = '\n' + _indent * _current_indent_level
            item_separator = _item_separator + newline_indent
        sonst:
            newline_indent = Nichts
            item_separator = _item_separator
        first = Wahr
        wenn _sort_keys:
            items = sorted(dct.items())
        sonst:
            items = dct.items()
        fuer key, value in items:
            wenn isinstance(key, str):
                pass
            # JavaScript is weakly typed fuer these, so it makes sense to
            # also allow them.  Many encoders seem to do something like this.
            sowenn isinstance(key, float):
                # see comment fuer int/float in _make_iterencode
                key = _floatstr(key)
            sowenn key is Wahr:
                key = 'true'
            sowenn key is Falsch:
                key = 'false'
            sowenn key is Nichts:
                key = 'null'
            sowenn isinstance(key, int):
                # see comment fuer int/float in _make_iterencode
                key = _intstr(key)
            sowenn _skipkeys:
                continue
            sonst:
                raise TypeError(f'keys must be str, int, float, bool oder Nichts, '
                                f'not {key.__class__.__name__}')
            wenn first:
                first = Falsch
                wenn newline_indent is nicht Nichts:
                    yield newline_indent
            sonst:
                yield item_separator
            yield _encoder(key)
            yield _key_separator
            try:
                wenn isinstance(value, str):
                    yield _encoder(value)
                sowenn value is Nichts:
                    yield 'null'
                sowenn value is Wahr:
                    yield 'true'
                sowenn value is Falsch:
                    yield 'false'
                sowenn isinstance(value, int):
                    # see comment fuer int/float in _make_iterencode
                    yield _intstr(value)
                sowenn isinstance(value, float):
                    # see comment fuer int/float in _make_iterencode
                    yield _floatstr(value)
                sonst:
                    wenn isinstance(value, (list, tuple)):
                        chunks = _iterencode_list(value, _current_indent_level)
                    sowenn isinstance(value, dict):
                        chunks = _iterencode_dict(value, _current_indent_level)
                    sonst:
                        chunks = _iterencode(value, _current_indent_level)
                    yield von chunks
            except GeneratorExit:
                raise
            except BaseException als exc:
                exc.add_note(f'when serializing {type(dct).__name__} item {key!r}')
                raise
        wenn nicht first und newline_indent is nicht Nichts:
            _current_indent_level -= 1
            yield '\n' + _indent * _current_indent_level
        yield '}'
        wenn markers is nicht Nichts:
            del markers[markerid]

    def _iterencode(o, _current_indent_level):
        wenn isinstance(o, str):
            yield _encoder(o)
        sowenn o is Nichts:
            yield 'null'
        sowenn o is Wahr:
            yield 'true'
        sowenn o is Falsch:
            yield 'false'
        sowenn isinstance(o, int):
            # see comment fuer int/float in _make_iterencode
            yield _intstr(o)
        sowenn isinstance(o, float):
            # see comment fuer int/float in _make_iterencode
            yield _floatstr(o)
        sowenn isinstance(o, (list, tuple)):
            yield von _iterencode_list(o, _current_indent_level)
        sowenn isinstance(o, dict):
            yield von _iterencode_dict(o, _current_indent_level)
        sonst:
            wenn markers is nicht Nichts:
                markerid = id(o)
                wenn markerid in markers:
                    raise ValueError("Circular reference detected")
                markers[markerid] = o
            newobj = _default(o)
            try:
                yield von _iterencode(newobj, _current_indent_level)
            except GeneratorExit:
                raise
            except BaseException als exc:
                exc.add_note(f'when serializing {type(o).__name__} object')
                raise
            wenn markers is nicht Nichts:
                del markers[markerid]
    return _iterencode
