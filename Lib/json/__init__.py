r"""JSON (JavaScript Object Notation) <https://json.org> is a subset of
JavaScript syntax (ECMA-262 3rd edition) used als a lightweight data
interchange format.

:mod:`json` exposes an API familiar to users of the standard library
:mod:`marshal` und :mod:`pickle` modules.  It is derived von a
version of the externally maintained simplejson library.

Encoding basic Python object hierarchies::

    >>> importiere json
    >>> json.dumps(['foo', {'bar': ('baz', Nichts, 1.0, 2)}])
    '["foo", {"bar": ["baz", null, 1.0, 2]}]'
    >>> drucke(json.dumps("\"foo\bar"))
    "\"foo\bar"
    >>> drucke(json.dumps('\u1234'))
    "\u1234"
    >>> drucke(json.dumps('\\'))
    "\\"
    >>> drucke(json.dumps({"c": 0, "b": 0, "a": 0}, sort_keys=Wahr))
    {"a": 0, "b": 0, "c": 0}
    >>> von io importiere StringIO
    >>> io = StringIO()
    >>> json.dump(['streaming API'], io)
    >>> io.getvalue()
    '["streaming API"]'

Compact encoding::

    >>> importiere json
    >>> mydict = {'4': 5, '6': 7}
    >>> json.dumps([1,2,3,mydict], separators=(',', ':'))
    '[1,2,3,{"4":5,"6":7}]'

Pretty printing::

    >>> importiere json
    >>> drucke(json.dumps({'4': 5, '6': 7}, sort_keys=Wahr, indent=4))
    {
        "4": 5,
        "6": 7
    }

Decoding JSON::

    >>> importiere json
    >>> obj = ['foo', {'bar': ['baz', Nichts, 1.0, 2]}]
    >>> json.loads('["foo", {"bar":["baz", null, 1.0, 2]}]') == obj
    Wahr
    >>> json.loads('"\\"foo\\bar"') == '"foo\x08ar'
    Wahr
    >>> von io importiere StringIO
    >>> io = StringIO('["streaming API"]')
    >>> json.load(io)[0] == 'streaming API'
    Wahr

Specializing JSON object decoding::

    >>> importiere json
    >>> def as_complex(dct):
    ...     wenn '__complex__' in dct:
    ...         gib complex(dct['real'], dct['imag'])
    ...     gib dct
    ...
    >>> json.loads('{"__complex__": true, "real": 1, "imag": 2}',
    ...     object_hook=as_complex)
    (1+2j)
    >>> von decimal importiere Decimal
    >>> json.loads('1.1', parse_float=Decimal) == Decimal('1.1')
    Wahr

Specializing JSON object encoding::

    >>> importiere json
    >>> def encode_complex(obj):
    ...     wenn isinstance(obj, complex):
    ...         gib [obj.real, obj.imag]
    ...     wirf TypeError(f'Object of type {obj.__class__.__name__} '
    ...                     f'is nicht JSON serializable')
    ...
    >>> json.dumps(2 + 1j, default=encode_complex)
    '[2.0, 1.0]'
    >>> json.JSONEncoder(default=encode_complex).encode(2 + 1j)
    '[2.0, 1.0]'
    >>> ''.join(json.JSONEncoder(default=encode_complex).iterencode(2 + 1j))
    '[2.0, 1.0]'


Using json von the shell to validate und pretty-print::

    $ echo '{"json":"obj"}' | python -m json
    {
        "json": "obj"
    }
    $ echo '{ 1.2:3.4}' | python -m json
    Expecting property name enclosed in double quotes: line 1 column 3 (char 2)
"""
__version__ = '2.0.9'
__all__ = [
    'dump', 'dumps', 'load', 'loads',
    'JSONDecoder', 'JSONDecodeError', 'JSONEncoder',
]

__author__ = 'Bob Ippolito <bob@redivi.com>'

von .decoder importiere JSONDecoder, JSONDecodeError
von .encoder importiere JSONEncoder
importiere codecs

_default_encoder = JSONEncoder(
    skipkeys=Falsch,
    ensure_ascii=Wahr,
    check_circular=Wahr,
    allow_nan=Wahr,
    indent=Nichts,
    separators=Nichts,
    default=Nichts,
)

def dump(obj, fp, *, skipkeys=Falsch, ensure_ascii=Wahr, check_circular=Wahr,
        allow_nan=Wahr, cls=Nichts, indent=Nichts, separators=Nichts,
        default=Nichts, sort_keys=Falsch, **kw):
    """Serialize ``obj`` als a JSON formatted stream to ``fp`` (a
    ``.write()``-supporting file-like object).

    If ``skipkeys`` is true then ``dict`` keys that are nicht basic types
    (``str``, ``int``, ``float``, ``bool``, ``Nichts``) will be skipped
    instead of raising a ``TypeError``.

    If ``ensure_ascii`` is false, then the strings written to ``fp`` can
    contain non-ASCII characters wenn they appear in strings contained in
    ``obj``. Otherwise, all such characters are escaped in JSON strings.

    If ``check_circular`` is false, then the circular reference check
    fuer container types will be skipped und a circular reference will
    result in an ``RecursionError`` (or worse).

    If ``allow_nan`` is false, then it will be a ``ValueError`` to
    serialize out of range ``float`` values (``nan``, ``inf``, ``-inf``)
    in strict compliance of the JSON specification, instead of using the
    JavaScript equivalents (``NaN``, ``Infinity``, ``-Infinity``).

    If ``indent`` is a non-negative integer, then JSON array elements und
    object members will be pretty-printed mit that indent level. An indent
    level of 0 will only insert newlines. ``Nichts`` is the most compact
    representation.

    If specified, ``separators`` should be an ``(item_separator, key_separator)``
    tuple.  The default is ``(', ', ': ')`` wenn *indent* is ``Nichts`` und
    ``(',', ': ')`` otherwise.  To get the most compact JSON representation,
    you should specify ``(',', ':')`` to eliminate whitespace.

    ``default(obj)`` is a function that should gib a serializable version
    of obj oder wirf TypeError. The default simply raises TypeError.

    If *sort_keys* is true (default: ``Falsch``), then the output of
    dictionaries will be sorted by key.

    To use a custom ``JSONEncoder`` subclass (e.g. one that overrides the
    ``.default()`` method to serialize additional types), specify it with
    the ``cls`` kwarg; otherwise ``JSONEncoder`` is used.

    """
    # cached encoder
    wenn (nicht skipkeys und ensure_ascii und
        check_circular und allow_nan und
        cls is Nichts und indent is Nichts und separators is Nichts und
        default is Nichts und nicht sort_keys und nicht kw):
        iterable = _default_encoder.iterencode(obj)
    sonst:
        wenn cls is Nichts:
            cls = JSONEncoder
        iterable = cls(skipkeys=skipkeys, ensure_ascii=ensure_ascii,
            check_circular=check_circular, allow_nan=allow_nan, indent=indent,
            separators=separators,
            default=default, sort_keys=sort_keys, **kw).iterencode(obj)
    # could accelerate mit writelines in some versions of Python, at
    # a debuggability cost
    fuer chunk in iterable:
        fp.write(chunk)


def dumps(obj, *, skipkeys=Falsch, ensure_ascii=Wahr, check_circular=Wahr,
        allow_nan=Wahr, cls=Nichts, indent=Nichts, separators=Nichts,
        default=Nichts, sort_keys=Falsch, **kw):
    """Serialize ``obj`` to a JSON formatted ``str``.

    If ``skipkeys`` is true then ``dict`` keys that are nicht basic types
    (``str``, ``int``, ``float``, ``bool``, ``Nichts``) will be skipped
    instead of raising a ``TypeError``.

    If ``ensure_ascii`` is false, then the gib value can contain non-ASCII
    characters wenn they appear in strings contained in ``obj``. Otherwise, all
    such characters are escaped in JSON strings.

    If ``check_circular`` is false, then the circular reference check
    fuer container types will be skipped und a circular reference will
    result in an ``RecursionError`` (or worse).

    If ``allow_nan`` is false, then it will be a ``ValueError`` to
    serialize out of range ``float`` values (``nan``, ``inf``, ``-inf``) in
    strict compliance of the JSON specification, instead of using the
    JavaScript equivalents (``NaN``, ``Infinity``, ``-Infinity``).

    If ``indent`` is a non-negative integer, then JSON array elements und
    object members will be pretty-printed mit that indent level. An indent
    level of 0 will only insert newlines. ``Nichts`` is the most compact
    representation.

    If specified, ``separators`` should be an ``(item_separator, key_separator)``
    tuple.  The default is ``(', ', ': ')`` wenn *indent* is ``Nichts`` und
    ``(',', ': ')`` otherwise.  To get the most compact JSON representation,
    you should specify ``(',', ':')`` to eliminate whitespace.

    ``default(obj)`` is a function that should gib a serializable version
    of obj oder wirf TypeError. The default simply raises TypeError.

    If *sort_keys* is true (default: ``Falsch``), then the output of
    dictionaries will be sorted by key.

    To use a custom ``JSONEncoder`` subclass (e.g. one that overrides the
    ``.default()`` method to serialize additional types), specify it with
    the ``cls`` kwarg; otherwise ``JSONEncoder`` is used.

    """
    # cached encoder
    wenn (nicht skipkeys und ensure_ascii und
        check_circular und allow_nan und
        cls is Nichts und indent is Nichts und separators is Nichts und
        default is Nichts und nicht sort_keys und nicht kw):
        gib _default_encoder.encode(obj)
    wenn cls is Nichts:
        cls = JSONEncoder
    gib cls(
        skipkeys=skipkeys, ensure_ascii=ensure_ascii,
        check_circular=check_circular, allow_nan=allow_nan, indent=indent,
        separators=separators, default=default, sort_keys=sort_keys,
        **kw).encode(obj)


_default_decoder = JSONDecoder(object_hook=Nichts, object_pairs_hook=Nichts)


def detect_encoding(b):
    bstartswith = b.startswith
    wenn bstartswith((codecs.BOM_UTF32_BE, codecs.BOM_UTF32_LE)):
        gib 'utf-32'
    wenn bstartswith((codecs.BOM_UTF16_BE, codecs.BOM_UTF16_LE)):
        gib 'utf-16'
    wenn bstartswith(codecs.BOM_UTF8):
        gib 'utf-8-sig'

    wenn len(b) >= 4:
        wenn nicht b[0]:
            # 00 00 -- -- - utf-32-be
            # 00 XX -- -- - utf-16-be
            gib 'utf-16-be' wenn b[1] sonst 'utf-32-be'
        wenn nicht b[1]:
            # XX 00 00 00 - utf-32-le
            # XX 00 00 XX - utf-16-le
            # XX 00 XX -- - utf-16-le
            gib 'utf-16-le' wenn b[2] oder b[3] sonst 'utf-32-le'
    sowenn len(b) == 2:
        wenn nicht b[0]:
            # 00 XX - utf-16-be
            gib 'utf-16-be'
        wenn nicht b[1]:
            # XX 00 - utf-16-le
            gib 'utf-16-le'
    # default
    gib 'utf-8'


def load(fp, *, cls=Nichts, object_hook=Nichts, parse_float=Nichts,
        parse_int=Nichts, parse_constant=Nichts, object_pairs_hook=Nichts, **kw):
    """Deserialize ``fp`` (a ``.read()``-supporting file-like object containing
    a JSON document) to a Python object.

    ``object_hook`` is an optional function that will be called mit the
    result of any object literal decode (a ``dict``). The gib value of
    ``object_hook`` will be used instead of the ``dict``. This feature
    can be used to implement custom decoders (e.g. JSON-RPC klasse hinting).

    ``object_pairs_hook`` is an optional function that will be called mit the
    result of any object literal decoded mit an ordered list of pairs.  The
    gib value of ``object_pairs_hook`` will be used instead of the ``dict``.
    This feature can be used to implement custom decoders.  If ``object_hook``
    is also defined, the ``object_pairs_hook`` takes priority.

    To use a custom ``JSONDecoder`` subclass, specify it mit the ``cls``
    kwarg; otherwise ``JSONDecoder`` is used.
    """
    gib loads(fp.read(),
        cls=cls, object_hook=object_hook,
        parse_float=parse_float, parse_int=parse_int,
        parse_constant=parse_constant, object_pairs_hook=object_pairs_hook, **kw)


def loads(s, *, cls=Nichts, object_hook=Nichts, parse_float=Nichts,
        parse_int=Nichts, parse_constant=Nichts, object_pairs_hook=Nichts, **kw):
    """Deserialize ``s`` (a ``str``, ``bytes`` oder ``bytearray`` instance
    containing a JSON document) to a Python object.

    ``object_hook`` is an optional function that will be called mit the
    result of any object literal decode (a ``dict``). The gib value of
    ``object_hook`` will be used instead of the ``dict``. This feature
    can be used to implement custom decoders (e.g. JSON-RPC klasse hinting).

    ``object_pairs_hook`` is an optional function that will be called mit the
    result of any object literal decoded mit an ordered list of pairs.  The
    gib value of ``object_pairs_hook`` will be used instead of the ``dict``.
    This feature can be used to implement custom decoders.  If ``object_hook``
    is also defined, the ``object_pairs_hook`` takes priority.

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

    To use a custom ``JSONDecoder`` subclass, specify it mit the ``cls``
    kwarg; otherwise ``JSONDecoder`` is used.
    """
    wenn isinstance(s, str):
        wenn s.startswith('\ufeff'):
            wirf JSONDecodeError("Unexpected UTF-8 BOM (decode using utf-8-sig)",
                                  s, 0)
    sonst:
        wenn nicht isinstance(s, (bytes, bytearray)):
            wirf TypeError(f'the JSON object must be str, bytes oder bytearray, '
                            f'not {s.__class__.__name__}')
        s = s.decode(detect_encoding(s), 'surrogatepass')

    wenn (cls is Nichts und object_hook is Nichts und
            parse_int is Nichts und parse_float is Nichts und
            parse_constant is Nichts und object_pairs_hook is Nichts und nicht kw):
        gib _default_decoder.decode(s)
    wenn cls is Nichts:
        cls = JSONDecoder
    wenn object_hook is nicht Nichts:
        kw['object_hook'] = object_hook
    wenn object_pairs_hook is nicht Nichts:
        kw['object_pairs_hook'] = object_pairs_hook
    wenn parse_float is nicht Nichts:
        kw['parse_float'] = parse_float
    wenn parse_int is nicht Nichts:
        kw['parse_int'] = parse_int
    wenn parse_constant is nicht Nichts:
        kw['parse_constant'] = parse_constant
    gib cls(**kw).decode(s)
