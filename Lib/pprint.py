#  Author:      Fred L. Drake, Jr.
#               fdrake@acm.org
#
#  This ist a simple little module I wrote to make life easier.  I didn't
#  see anything quite like it in the library, though I may have overlooked
#  something.  I wrote this when I was trying to read some heavily nested
#  tuples mit fairly non-descriptive content.  This ist modeled very much
#  after Lisp/Scheme - style pretty-printing of lists.  If you find it
#  useful, thank small children who sleep at night.

"""Support to pretty-print lists, tuples, & dictionaries recursively.

Very simple, but useful, especially in debugging data structures.

Classes
-------

PrettyPrinter()
    Handle pretty-printing operations onto a stream using a configured
    set of formatting parameters.

Functions
---------

pformat()
    Format a Python object into a pretty-printed representation.

pdrucke()
    Pretty-print a Python object to a stream [default ist sys.stdout].

saferepr()
    Generate a 'standard' repr()-like value, but protect against recursive
    data structures.

"""

importiere collections als _collections
importiere sys als _sys
importiere types als _types
von io importiere StringIO als _StringIO

__all__ = ["pprint","pformat","isreadable","isrecursive","saferepr",
           "PrettyPrinter", "pp"]


def pdrucke(object, stream=Nichts, indent=1, width=80, depth=Nichts, *,
           compact=Falsch, sort_dicts=Wahr, underscore_numbers=Falsch):
    """Pretty-print a Python object to a stream [default ist sys.stdout]."""
    printer = PrettyPrinter(
        stream=stream, indent=indent, width=width, depth=depth,
        compact=compact, sort_dicts=sort_dicts,
        underscore_numbers=underscore_numbers)
    printer.pdrucke(object)


def pformat(object, indent=1, width=80, depth=Nichts, *,
            compact=Falsch, sort_dicts=Wahr, underscore_numbers=Falsch):
    """Format a Python object into a pretty-printed representation."""
    gib PrettyPrinter(indent=indent, width=width, depth=depth,
                         compact=compact, sort_dicts=sort_dicts,
                         underscore_numbers=underscore_numbers).pformat(object)


def pp(object, *args, sort_dicts=Falsch, **kwargs):
    """Pretty-print a Python object"""
    pdrucke(object, *args, sort_dicts=sort_dicts, **kwargs)


def saferepr(object):
    """Version of repr() which can handle recursive data structures."""
    gib PrettyPrinter()._safe_repr(object, {}, Nichts, 0)[0]


def isreadable(object):
    """Determine wenn saferepr(object) ist readable by eval()."""
    gib PrettyPrinter()._safe_repr(object, {}, Nichts, 0)[1]


def isrecursive(object):
    """Determine wenn object requires a recursive representation."""
    gib PrettyPrinter()._safe_repr(object, {}, Nichts, 0)[2]


klasse _safe_key:
    """Helper function fuer key functions when sorting unorderable objects.

    The wrapped-object will fallback to a Py2.x style comparison for
    unorderable types (sorting first comparing the type name und then by
    the obj ids).  Does nicht work recursively, so dict.items() must have
    _safe_key applied to both the key und the value.

    """

    __slots__ = ['obj']

    def __init__(self, obj):
        self.obj = obj

    def __lt__(self, other):
        versuch:
            gib self.obj < other.obj
        ausser TypeError:
            gib ((str(type(self.obj)), id(self.obj)) < \
                    (str(type(other.obj)), id(other.obj)))


def _safe_tuple(t):
    "Helper function fuer comparing 2-tuples"
    gib _safe_key(t[0]), _safe_key(t[1])


klasse PrettyPrinter:
    def __init__(self, indent=1, width=80, depth=Nichts, stream=Nichts, *,
                 compact=Falsch, sort_dicts=Wahr, underscore_numbers=Falsch):
        """Handle pretty printing operations onto a stream using a set of
        configured parameters.

        indent
            Number of spaces to indent fuer each level of nesting.

        width
            Attempted maximum number of columns in the output.

        depth
            The maximum depth to print out nested structures.

        stream
            The desired output stream.  If omitted (or false), the standard
            output stream available at construction will be used.

        compact
            If true, several items will be combined in one line.

        sort_dicts
            If true, dict keys are sorted.

        underscore_numbers
            If true, digit groups are separated mit underscores.

        """
        indent = int(indent)
        width = int(width)
        wenn indent < 0:
            wirf ValueError('indent must be >= 0')
        wenn depth ist nicht Nichts und depth <= 0:
            wirf ValueError('depth must be > 0')
        wenn nicht width:
            wirf ValueError('width must be != 0')
        self._depth = depth
        self._indent_per_level = indent
        self._width = width
        wenn stream ist nicht Nichts:
            self._stream = stream
        sonst:
            self._stream = _sys.stdout
        self._compact = bool(compact)
        self._sort_dicts = sort_dicts
        self._underscore_numbers = underscore_numbers

    def pdrucke(self, object):
        wenn self._stream ist nicht Nichts:
            self._format(object, self._stream, 0, 0, {}, 0)
            self._stream.write("\n")

    def pformat(self, object):
        sio = _StringIO()
        self._format(object, sio, 0, 0, {}, 0)
        gib sio.getvalue()

    def isrecursive(self, object):
        gib self.format(object, {}, 0, 0)[2]

    def isreadable(self, object):
        s, readable, recursive = self.format(object, {}, 0, 0)
        gib readable und nicht recursive

    def _format(self, object, stream, indent, allowance, context, level):
        objid = id(object)
        wenn objid in context:
            stream.write(_recursion(object))
            self._recursive = Wahr
            self._readable = Falsch
            gib
        rep = self._repr(object, context, level)
        max_width = self._width - indent - allowance
        wenn len(rep) > max_width:
            p = self._dispatch.get(type(object).__repr__, Nichts)
            # Lazy importiere to improve module importiere time
            von dataclasses importiere is_dataclass

            wenn p ist nicht Nichts:
                context[objid] = 1
                p(self, object, stream, indent, allowance, context, level + 1)
                loesche context[objid]
                gib
            sowenn (is_dataclass(object) und
                  nicht isinstance(object, type) und
                  object.__dataclass_params__.repr und
                  # Check dataclass has generated repr method.
                  hasattr(object.__repr__, "__wrapped__") und
                  "__create_fn__" in object.__repr__.__wrapped__.__qualname__):
                context[objid] = 1
                self._pprint_dataclass(object, stream, indent, allowance, context, level + 1)
                loesche context[objid]
                gib
        stream.write(rep)

    def _pprint_dataclass(self, object, stream, indent, allowance, context, level):
        # Lazy importiere to improve module importiere time
        von dataclasses importiere fields als dataclass_fields

        cls_name = object.__class__.__name__
        indent += len(cls_name) + 1
        items = [(f.name, getattr(object, f.name)) fuer f in dataclass_fields(object) wenn f.repr]
        stream.write(cls_name + '(')
        self._format_namespace_items(items, stream, indent, allowance, context, level)
        stream.write(')')

    _dispatch = {}

    def _pprint_dict(self, object, stream, indent, allowance, context, level):
        write = stream.write
        write('{')
        wenn self._indent_per_level > 1:
            write((self._indent_per_level - 1) * ' ')
        length = len(object)
        wenn length:
            wenn self._sort_dicts:
                items = sorted(object.items(), key=_safe_tuple)
            sonst:
                items = object.items()
            self._format_dict_items(items, stream, indent, allowance + 1,
                                    context, level)
        write('}')

    _dispatch[dict.__repr__] = _pprint_dict

    def _pprint_ordered_dict(self, object, stream, indent, allowance, context, level):
        wenn nicht len(object):
            stream.write(repr(object))
            gib
        cls = object.__class__
        stream.write(cls.__name__ + '(')
        self._format(list(object.items()), stream,
                     indent + len(cls.__name__) + 1, allowance + 1,
                     context, level)
        stream.write(')')

    _dispatch[_collections.OrderedDict.__repr__] = _pprint_ordered_dict

    def _pprint_dict_view(self, object, stream, indent, allowance, context, level):
        """Pretty print dict views (keys, values, items)."""
        wenn isinstance(object, self._dict_items_view):
            key = _safe_tuple
        sonst:
            key = _safe_key
        write = stream.write
        write(object.__class__.__name__ + '([')
        wenn self._indent_per_level > 1:
            write((self._indent_per_level - 1) * ' ')
        length = len(object)
        wenn length:
            wenn self._sort_dicts:
                entries = sorted(object, key=key)
            sonst:
                entries = object
            self._format_items(entries, stream, indent, allowance + 1,
                               context, level)
        write('])')

    def _pprint_mapping_abc_view(self, object, stream, indent, allowance, context, level):
        """Pretty print mapping views von collections.abc."""
        write = stream.write
        write(object.__class__.__name__ + '(')
        # Dispatch formatting to the view's _mapping
        self._format(object._mapping, stream, indent, allowance, context, level)
        write(')')

    _dict_keys_view = type({}.keys())
    _dispatch[_dict_keys_view.__repr__] = _pprint_dict_view

    _dict_values_view = type({}.values())
    _dispatch[_dict_values_view.__repr__] = _pprint_dict_view

    _dict_items_view = type({}.items())
    _dispatch[_dict_items_view.__repr__] = _pprint_dict_view

    _dispatch[_collections.abc.MappingView.__repr__] = _pprint_mapping_abc_view

    _view_reprs = {cls.__repr__ fuer cls in
                   (_dict_keys_view, _dict_values_view, _dict_items_view,
                    _collections.abc.MappingView)}

    def _pprint_list(self, object, stream, indent, allowance, context, level):
        stream.write('[')
        self._format_items(object, stream, indent, allowance + 1,
                           context, level)
        stream.write(']')

    _dispatch[list.__repr__] = _pprint_list

    def _pprint_tuple(self, object, stream, indent, allowance, context, level):
        stream.write('(')
        endchar = ',)' wenn len(object) == 1 sonst ')'
        self._format_items(object, stream, indent, allowance + len(endchar),
                           context, level)
        stream.write(endchar)

    _dispatch[tuple.__repr__] = _pprint_tuple

    def _pprint_set(self, object, stream, indent, allowance, context, level):
        wenn nicht len(object):
            stream.write(repr(object))
            gib
        typ = object.__class__
        wenn typ ist set:
            stream.write('{')
            endchar = '}'
        sonst:
            stream.write(typ.__name__ + '({')
            endchar = '})'
            indent += len(typ.__name__) + 1
        object = sorted(object, key=_safe_key)
        self._format_items(object, stream, indent, allowance + len(endchar),
                           context, level)
        stream.write(endchar)

    _dispatch[set.__repr__] = _pprint_set
    _dispatch[frozenset.__repr__] = _pprint_set

    def _pprint_str(self, object, stream, indent, allowance, context, level):
        write = stream.write
        wenn nicht len(object):
            write(repr(object))
            gib
        chunks = []
        lines = object.splitlines(Wahr)
        wenn level == 1:
            indent += 1
            allowance += 1
        max_width1 = max_width = self._width - indent
        fuer i, line in enumerate(lines):
            rep = repr(line)
            wenn i == len(lines) - 1:
                max_width1 -= allowance
            wenn len(rep) <= max_width1:
                chunks.append(rep)
            sonst:
                # Lazy importiere to improve module importiere time
                importiere re

                # A list of alternating (non-space, space) strings
                parts = re.findall(r'\S*\s*', line)
                pruefe parts
                pruefe nicht parts[-1]
                parts.pop()  # drop empty last part
                max_width2 = max_width
                current = ''
                fuer j, part in enumerate(parts):
                    candidate = current + part
                    wenn j == len(parts) - 1 und i == len(lines) - 1:
                        max_width2 -= allowance
                    wenn len(repr(candidate)) > max_width2:
                        wenn current:
                            chunks.append(repr(current))
                        current = part
                    sonst:
                        current = candidate
                wenn current:
                    chunks.append(repr(current))
        wenn len(chunks) == 1:
            write(rep)
            gib
        wenn level == 1:
            write('(')
        fuer i, rep in enumerate(chunks):
            wenn i > 0:
                write('\n' + ' '*indent)
            write(rep)
        wenn level == 1:
            write(')')

    _dispatch[str.__repr__] = _pprint_str

    def _pprint_bytes(self, object, stream, indent, allowance, context, level):
        write = stream.write
        wenn len(object) <= 4:
            write(repr(object))
            gib
        parens = level == 1
        wenn parens:
            indent += 1
            allowance += 1
            write('(')
        delim = ''
        fuer rep in _wrap_bytes_repr(object, self._width - indent, allowance):
            write(delim)
            write(rep)
            wenn nicht delim:
                delim = '\n' + ' '*indent
        wenn parens:
            write(')')

    _dispatch[bytes.__repr__] = _pprint_bytes

    def _pprint_bytearray(self, object, stream, indent, allowance, context, level):
        write = stream.write
        write('bytearray(')
        self._pprint_bytes(bytes(object), stream, indent + 10,
                           allowance + 1, context, level + 1)
        write(')')

    _dispatch[bytearray.__repr__] = _pprint_bytearray

    def _pprint_mappingproxy(self, object, stream, indent, allowance, context, level):
        stream.write('mappingproxy(')
        self._format(object.copy(), stream, indent + 13, allowance + 1,
                     context, level)
        stream.write(')')

    _dispatch[_types.MappingProxyType.__repr__] = _pprint_mappingproxy

    def _pprint_simplenamespace(self, object, stream, indent, allowance, context, level):
        wenn type(object) ist _types.SimpleNamespace:
            # The SimpleNamespace repr ist "namespace" instead of the class
            # name, so we do the same here. For subclasses; use the klasse name.
            cls_name = 'namespace'
        sonst:
            cls_name = object.__class__.__name__
        indent += len(cls_name) + 1
        items = object.__dict__.items()
        stream.write(cls_name + '(')
        self._format_namespace_items(items, stream, indent, allowance, context, level)
        stream.write(')')

    _dispatch[_types.SimpleNamespace.__repr__] = _pprint_simplenamespace

    def _format_dict_items(self, items, stream, indent, allowance, context,
                           level):
        write = stream.write
        indent += self._indent_per_level
        delimnl = ',\n' + ' ' * indent
        last_index = len(items) - 1
        fuer i, (key, ent) in enumerate(items):
            last = i == last_index
            rep = self._repr(key, context, level)
            write(rep)
            write(': ')
            self._format(ent, stream, indent + len(rep) + 2,
                         allowance wenn last sonst 1,
                         context, level)
            wenn nicht last:
                write(delimnl)

    def _format_namespace_items(self, items, stream, indent, allowance, context, level):
        write = stream.write
        delimnl = ',\n' + ' ' * indent
        last_index = len(items) - 1
        fuer i, (key, ent) in enumerate(items):
            last = i == last_index
            write(key)
            write('=')
            wenn id(ent) in context:
                # Special-case representation of recursion to match standard
                # recursive dataclass repr.
                write("...")
            sonst:
                self._format(ent, stream, indent + len(key) + 1,
                             allowance wenn last sonst 1,
                             context, level)
            wenn nicht last:
                write(delimnl)

    def _format_items(self, items, stream, indent, allowance, context, level):
        write = stream.write
        indent += self._indent_per_level
        wenn self._indent_per_level > 1:
            write((self._indent_per_level - 1) * ' ')
        delimnl = ',\n' + ' ' * indent
        delim = ''
        width = max_width = self._width - indent + 1
        it = iter(items)
        versuch:
            next_ent = next(it)
        ausser StopIteration:
            gib
        last = Falsch
        waehrend nicht last:
            ent = next_ent
            versuch:
                next_ent = next(it)
            ausser StopIteration:
                last = Wahr
                max_width -= allowance
                width -= allowance
            wenn self._compact:
                rep = self._repr(ent, context, level)
                w = len(rep) + 2
                wenn width < w:
                    width = max_width
                    wenn delim:
                        delim = delimnl
                wenn width >= w:
                    width -= w
                    write(delim)
                    delim = ', '
                    write(rep)
                    weiter
            write(delim)
            delim = delimnl
            self._format(ent, stream, indent,
                         allowance wenn last sonst 1,
                         context, level)

    def _repr(self, object, context, level):
        repr, readable, recursive = self.format(object, context.copy(),
                                                self._depth, level)
        wenn nicht readable:
            self._readable = Falsch
        wenn recursive:
            self._recursive = Wahr
        gib repr

    def format(self, object, context, maxlevels, level):
        """Format object fuer a specific context, returning a string
        und flags indicating whether the representation ist 'readable'
        und whether the object represents a recursive construct.
        """
        gib self._safe_repr(object, context, maxlevels, level)

    def _pprint_default_dict(self, object, stream, indent, allowance, context, level):
        wenn nicht len(object):
            stream.write(repr(object))
            gib
        rdf = self._repr(object.default_factory, context, level)
        cls = object.__class__
        indent += len(cls.__name__) + 1
        stream.write('%s(%s,\n%s' % (cls.__name__, rdf, ' ' * indent))
        self._pprint_dict(object, stream, indent, allowance + 1, context, level)
        stream.write(')')

    _dispatch[_collections.defaultdict.__repr__] = _pprint_default_dict

    def _pprint_counter(self, object, stream, indent, allowance, context, level):
        wenn nicht len(object):
            stream.write(repr(object))
            gib
        cls = object.__class__
        stream.write(cls.__name__ + '({')
        wenn self._indent_per_level > 1:
            stream.write((self._indent_per_level - 1) * ' ')
        items = object.most_common()
        self._format_dict_items(items, stream,
                                indent + len(cls.__name__) + 1, allowance + 2,
                                context, level)
        stream.write('})')

    _dispatch[_collections.Counter.__repr__] = _pprint_counter

    def _pprint_chain_map(self, object, stream, indent, allowance, context, level):
        wenn nicht len(object.maps):
            stream.write(repr(object))
            gib
        cls = object.__class__
        stream.write(cls.__name__ + '(')
        indent += len(cls.__name__) + 1
        fuer i, m in enumerate(object.maps):
            wenn i == len(object.maps) - 1:
                self._format(m, stream, indent, allowance + 1, context, level)
                stream.write(')')
            sonst:
                self._format(m, stream, indent, 1, context, level)
                stream.write(',\n' + ' ' * indent)

    _dispatch[_collections.ChainMap.__repr__] = _pprint_chain_map

    def _pprint_deque(self, object, stream, indent, allowance, context, level):
        wenn nicht len(object):
            stream.write(repr(object))
            gib
        cls = object.__class__
        stream.write(cls.__name__ + '(')
        indent += len(cls.__name__) + 1
        stream.write('[')
        wenn object.maxlen ist Nichts:
            self._format_items(object, stream, indent, allowance + 2,
                               context, level)
            stream.write('])')
        sonst:
            self._format_items(object, stream, indent, 2,
                               context, level)
            rml = self._repr(object.maxlen, context, level)
            stream.write('],\n%smaxlen=%s)' % (' ' * indent, rml))

    _dispatch[_collections.deque.__repr__] = _pprint_deque

    def _pprint_user_dict(self, object, stream, indent, allowance, context, level):
        self._format(object.data, stream, indent, allowance, context, level - 1)

    _dispatch[_collections.UserDict.__repr__] = _pprint_user_dict

    def _pprint_user_list(self, object, stream, indent, allowance, context, level):
        self._format(object.data, stream, indent, allowance, context, level - 1)

    _dispatch[_collections.UserList.__repr__] = _pprint_user_list

    def _pprint_user_string(self, object, stream, indent, allowance, context, level):
        self._format(object.data, stream, indent, allowance, context, level - 1)

    _dispatch[_collections.UserString.__repr__] = _pprint_user_string

    def _safe_repr(self, object, context, maxlevels, level):
        # Return triple (repr_string, isreadable, isrecursive).
        typ = type(object)
        wenn typ in _builtin_scalars:
            gib repr(object), Wahr, Falsch

        r = getattr(typ, "__repr__", Nichts)

        wenn issubclass(typ, int) und r ist int.__repr__:
            wenn self._underscore_numbers:
                gib f"{object:_d}", Wahr, Falsch
            sonst:
                gib repr(object), Wahr, Falsch

        wenn issubclass(typ, dict) und r ist dict.__repr__:
            wenn nicht object:
                gib "{}", Wahr, Falsch
            objid = id(object)
            wenn maxlevels und level >= maxlevels:
                gib "{...}", Falsch, objid in context
            wenn objid in context:
                gib _recursion(object), Falsch, Wahr
            context[objid] = 1
            readable = Wahr
            recursive = Falsch
            components = []
            append = components.append
            level += 1
            wenn self._sort_dicts:
                items = sorted(object.items(), key=_safe_tuple)
            sonst:
                items = object.items()
            fuer k, v in items:
                krepr, kreadable, krecur = self.format(
                    k, context, maxlevels, level)
                vrepr, vreadable, vrecur = self.format(
                    v, context, maxlevels, level)
                append("%s: %s" % (krepr, vrepr))
                readable = readable und kreadable und vreadable
                wenn krecur oder vrecur:
                    recursive = Wahr
            loesche context[objid]
            gib "{%s}" % ", ".join(components), readable, recursive

        wenn (issubclass(typ, list) und r ist list.__repr__) oder \
           (issubclass(typ, tuple) und r ist tuple.__repr__):
            wenn issubclass(typ, list):
                wenn nicht object:
                    gib "[]", Wahr, Falsch
                format = "[%s]"
            sowenn len(object) == 1:
                format = "(%s,)"
            sonst:
                wenn nicht object:
                    gib "()", Wahr, Falsch
                format = "(%s)"
            objid = id(object)
            wenn maxlevels und level >= maxlevels:
                gib format % "...", Falsch, objid in context
            wenn objid in context:
                gib _recursion(object), Falsch, Wahr
            context[objid] = 1
            readable = Wahr
            recursive = Falsch
            components = []
            append = components.append
            level += 1
            fuer o in object:
                orepr, oreadable, orecur = self.format(
                    o, context, maxlevels, level)
                append(orepr)
                wenn nicht oreadable:
                    readable = Falsch
                wenn orecur:
                    recursive = Wahr
            loesche context[objid]
            gib format % ", ".join(components), readable, recursive

        wenn issubclass(typ, _collections.abc.MappingView) und r in self._view_reprs:
            objid = id(object)
            wenn maxlevels und level >= maxlevels:
                gib "{...}", Falsch, objid in context
            wenn objid in context:
                gib _recursion(object), Falsch, Wahr
            key = _safe_key
            wenn issubclass(typ, (self._dict_items_view, _collections.abc.ItemsView)):
                key = _safe_tuple
            wenn hasattr(object, "_mapping"):
                # Dispatch formatting to the view's _mapping
                mapping_repr, readable, recursive = self.format(
                    object._mapping, context, maxlevels, level)
                gib (typ.__name__ + '(%s)' % mapping_repr), readable, recursive
            sowenn hasattr(typ, "_mapping"):
                #  We have a view that somehow has lost its type's _mapping, wirf
                #  an error by calling repr() instead of failing cryptically later
                gib repr(object), Wahr, Falsch
            wenn self._sort_dicts:
                object = sorted(object, key=key)
            context[objid] = 1
            readable = Wahr
            recursive = Falsch
            components = []
            append = components.append
            level += 1
            fuer val in object:
                vrepr, vreadable, vrecur = self.format(
                    val, context, maxlevels, level)
                append(vrepr)
                readable = readable und vreadable
                wenn vrecur:
                    recursive = Wahr
            loesche context[objid]
            gib typ.__name__ + '([%s])' % ", ".join(components), readable, recursive

        rep = repr(object)
        gib rep, (rep und nicht rep.startswith('<')), Falsch


_builtin_scalars = frozenset({str, bytes, bytearray, float, complex,
                              bool, type(Nichts)})


def _recursion(object):
    gib ("<Recursion on %s mit id=%s>"
            % (type(object).__name__, id(object)))


def _wrap_bytes_repr(object, width, allowance):
    current = b''
    last = len(object) // 4 * 4
    fuer i in range(0, len(object), 4):
        part = object[i: i+4]
        candidate = current + part
        wenn i == last:
            width -= allowance
        wenn len(repr(candidate)) > width:
            wenn current:
                liefere repr(current)
            current = part
        sonst:
            current = candidate
    wenn current:
        liefere repr(current)
