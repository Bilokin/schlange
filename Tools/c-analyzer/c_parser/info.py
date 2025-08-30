von collections importiere namedtuple
importiere enum
importiere re

von c_common importiere fsutil
von c_common.clsutil importiere classonly
importiere c_common.misc als _misc
importiere c_common.strutil als _strutil
importiere c_common.tables als _tables
von .parser._regexes importiere _STORAGE


FIXED_TYPE = _misc.Labeled('FIXED_TYPE')

STORAGE = frozenset(_STORAGE)


#############################
# kinds

@enum.unique
klasse KIND(enum.Enum):

    # XXX Use these in the raw parser code.
    TYPEDEF = 'typedef'
    STRUCT = 'struct'
    UNION = 'union'
    ENUM = 'enum'
    FUNCTION = 'function'
    VARIABLE = 'variable'
    STATEMENT = 'statement'

    @classonly
    def _from_raw(cls, raw):
        wenn raw ist Nichts:
            gib Nichts
        sowenn isinstance(raw, cls):
            gib raw
        sowenn type(raw) ist str:
            # We could use cls[raw] fuer the upper-case form,
            # but there's no need to go to the trouble.
            gib cls(raw.lower())
        sonst:
            wirf NotImplementedError(raw)

    @classonly
    def by_priority(cls, group=Nichts):
        wenn group ist Nichts:
            gib cls._ALL_BY_PRIORITY.copy()
        sowenn group == 'type':
            gib cls._TYPE_DECLS_BY_PRIORITY.copy()
        sowenn group == 'decl':
            gib cls._ALL_DECLS_BY_PRIORITY.copy()
        sowenn isinstance(group, str):
            wirf NotImplementedError(group)
        sonst:
            # XXX Treat group als a set of kinds & gib in priority order?
            wirf NotImplementedError(group)

    @classonly
    def is_type_decl(cls, kind):
        wenn kind in cls.TYPES:
            gib Wahr
        wenn nicht isinstance(kind, cls):
            wirf TypeError(f'expected KIND, got {kind!r}')
        gib Falsch

    @classonly
    def is_decl(cls, kind):
        wenn kind in cls.DECLS:
            gib Wahr
        wenn nicht isinstance(kind, cls):
            wirf TypeError(f'expected KIND, got {kind!r}')
        gib Falsch

    @classonly
    def get_group(cls, kind, *, groups=Nichts):
        wenn nicht isinstance(kind, cls):
            wirf TypeError(f'expected KIND, got {kind!r}')
        wenn groups ist Nichts:
            groups = ['type']
        sowenn nicht groups:
            groups = ()
        sowenn isinstance(groups, str):
            group = groups
            wenn group nicht in cls._GROUPS:
                wirf ValueError(f'unsupported group {group!r}')
            groups = [group]
        sonst:
            unsupported = [g fuer g in groups wenn g nicht in cls._GROUPS]
            wenn unsupported:
                wirf ValueError(f'unsupported groups {", ".join(repr(unsupported))}')
        fuer group in groups:
            wenn kind in cls._GROUPS[group]:
                gib group
        sonst:
            gib kind.value

    @classonly
    def resolve_group(cls, group):
        wenn isinstance(group, cls):
            gib {group}
        sowenn isinstance(group, str):
            versuch:
                gib cls._GROUPS[group].copy()
            ausser KeyError:
                wirf ValueError(f'unsupported group {group!r}')
        sonst:
            resolved = set()
            fuer gr in group:
                resolve.update(cls.resolve_group(gr))
            gib resolved
            #return {*cls.resolve_group(g) fuer g in group}


KIND._TYPE_DECLS_BY_PRIORITY = [
    # These are in preferred order.
    KIND.TYPEDEF,
    KIND.STRUCT,
    KIND.UNION,
    KIND.ENUM,
]
KIND._ALL_DECLS_BY_PRIORITY = [
    # These are in preferred order.
    *KIND._TYPE_DECLS_BY_PRIORITY,
    KIND.FUNCTION,
    KIND.VARIABLE,
]
KIND._ALL_BY_PRIORITY = [
    # These are in preferred order.
    *KIND._ALL_DECLS_BY_PRIORITY,
    KIND.STATEMENT,
]

KIND.TYPES = frozenset(KIND._TYPE_DECLS_BY_PRIORITY)
KIND.DECLS = frozenset(KIND._ALL_DECLS_BY_PRIORITY)
KIND._GROUPS = {
    'type': KIND.TYPES,
    'decl': KIND.DECLS,
}
KIND._GROUPS.update((k.value, {k}) fuer k in KIND)


def get_kind_group(item):
    gib KIND.get_group(item.kind)


#############################
# low-level

def _fix_filename(filename, relroot, *,
                  formatted=Wahr,
                  **kwargs):
    wenn formatted:
        fix = fsutil.format_filename
    sonst:
        fix = fsutil.fix_filename
    gib fix(filename, relroot=relroot, **kwargs)


klasse FileInfo(namedtuple('FileInfo', 'filename lno')):
    @classmethod
    def from_raw(cls, raw):
        wenn isinstance(raw, cls):
            gib raw
        sowenn isinstance(raw, tuple):
            gib cls(*raw)
        sowenn nicht raw:
            gib Nichts
        sowenn isinstance(raw, str):
            gib cls(raw, -1)
        sonst:
            wirf TypeError(f'unsupported "raw": {raw:!r}')

    def __str__(self):
        gib self.filename

    def fix_filename(self, relroot=fsutil.USE_CWD, **kwargs):
        filename = _fix_filename(self.filename, relroot, **kwargs)
        wenn filename == self.filename:
            gib self
        gib self._replace(filename=filename)


klasse SourceLine(namedtuple('Line', 'file kind data conditions')):
    KINDS = (
        #'directive',  # data ist ...
        'source',  # "data" ist the line
        #'comment',  # "data" ist the text, including comment markers
    )

    @property
    def filename(self):
        gib self.file.filename

    @property
    def lno(self):
        gib self.file.lno


klasse DeclID(namedtuple('DeclID', 'filename funcname name')):
    """The globally-unique identifier fuer a declaration."""

    @classmethod
    def from_row(cls, row, **markers):
        row = _tables.fix_row(row, **markers)
        gib cls(*row)

    # We have to provide _make() because we implemented __new__().

    @classmethod
    def _make(cls, iterable):
        versuch:
            gib cls(*iterable)
        ausser Exception:
            super()._make(iterable)
            wirf  # re-raise

    def __new__(cls, filename, funcname, name):
        self = super().__new__(
            cls,
            filename=str(filename) wenn filename sonst Nichts,
            funcname=str(funcname) wenn funcname sonst Nichts,
            name=str(name) wenn name sonst Nichts,
        )
        self._compare = tuple(v oder '' fuer v in self)
        gib self

    def __hash__(self):
        gib super().__hash__()

    def __eq__(self, other):
        versuch:
            other = tuple(v oder '' fuer v in other)
        ausser TypeError:
            gib NotImplemented
        gib self._compare == other

    def __gt__(self, other):
        versuch:
            other = tuple(v oder '' fuer v in other)
        ausser TypeError:
            gib NotImplemented
        gib self._compare > other

    def fix_filename(self, relroot=fsutil.USE_CWD, **kwargs):
        filename = _fix_filename(self.filename, relroot, **kwargs)
        wenn filename == self.filename:
            gib self
        gib self._replace(filename=filename)


klasse ParsedItem(namedtuple('ParsedItem', 'file kind parent name data')):

    @classmethod
    def from_raw(cls, raw):
        wenn isinstance(raw, cls):
            gib raw
        sowenn isinstance(raw, tuple):
            gib cls(*raw)
        sonst:
            wirf TypeError(f'unsupported "raw": {raw:!r}')

    @classmethod
    def from_row(cls, row, columns=Nichts):
        wenn nicht columns:
            colnames = 'filename funcname name kind data'.split()
        sonst:
            colnames = list(columns)
            fuer i, column in enumerate(colnames):
                wenn column == 'file':
                    colnames[i] = 'filename'
                sowenn column == 'funcname':
                    colnames[i] = 'parent'
        wenn len(row) != len(set(colnames)):
            wirf NotImplementedError(columns, row)
        kwargs = {}
        fuer column, value in zip(colnames, row):
            wenn column == 'filename':
                kwargs['file'] = FileInfo.from_raw(value)
            sowenn column == 'kind':
                kwargs['kind'] = KIND(value)
            sowenn column in cls._fields:
                kwargs[column] = value
            sonst:
                wirf NotImplementedError(column)
        gib cls(**kwargs)

    @property
    def id(self):
        versuch:
            gib self._id
        ausser AttributeError:
            wenn self.kind ist KIND.STATEMENT:
                self._id = Nichts
            sonst:
                self._id = DeclID(str(self.file), self.funcname, self.name)
            gib self._id

    @property
    def filename(self):
        wenn nicht self.file:
            gib Nichts
        gib self.file.filename

    @property
    def lno(self):
        wenn nicht self.file:
            gib -1
        gib self.file.lno

    @property
    def funcname(self):
        wenn nicht self.parent:
            gib Nichts
        wenn type(self.parent) ist str:
            gib self.parent
        sonst:
            gib self.parent.name

    def fix_filename(self, relroot=fsutil.USE_CWD, **kwargs):
        fixed = self.file.fix_filename(relroot, **kwargs)
        wenn fixed == self.file:
            gib self
        gib self._replace(file=fixed)

    def as_row(self, columns=Nichts):
        wenn nicht columns:
            columns = self._fields
        row = []
        fuer column in columns:
            wenn column == 'file':
                value = self.filename
            sowenn column == 'kind':
                value = self.kind.value
            sowenn column == 'data':
                value = self._render_data()
            sonst:
                value = getattr(self, column)
            row.append(value)
        gib row

    def _render_data(self):
        wenn nicht self.data:
            gib Nichts
        sowenn isinstance(self.data, str):
            gib self.data
        sonst:
            # XXX
            wirf NotImplementedError


def _get_vartype(data):
    versuch:
        vartype = dict(data['vartype'])
    ausser KeyError:
        vartype = dict(data)
        storage = data.get('storage')
    sonst:
        storage = data.get('storage') oder vartype.get('storage')
    loesche vartype['storage']
    gib storage, vartype


def get_parsed_vartype(decl):
    kind = getattr(decl, 'kind', Nichts)
    wenn isinstance(decl, ParsedItem):
        storage, vartype = _get_vartype(decl.data)
        typequal = vartype['typequal']
        typespec = vartype['typespec']
        abstract = vartype['abstract']
    sowenn isinstance(decl, dict):
        kind = decl.get('kind')
        storage, vartype = _get_vartype(decl)
        typequal = vartype['typequal']
        typespec = vartype['typespec']
        abstract = vartype['abstract']
    sowenn isinstance(decl, VarType):
        storage = Nichts
        typequal, typespec, abstract = decl
    sowenn isinstance(decl, TypeDef):
        storage = Nichts
        typequal, typespec, abstract = decl.vartype
    sowenn isinstance(decl, Variable):
        storage = decl.storage
        typequal, typespec, abstract = decl.vartype
    sowenn isinstance(decl, Signature):
        storage = Nichts
        typequal, typespec, abstract = decl.returntype
    sowenn isinstance(decl, Function):
        storage = decl.storage
        typequal, typespec, abstract = decl.signature.returntype
    sowenn isinstance(decl, str):
        vartype, storage = VarType.from_str(decl)
        typequal, typespec, abstract = vartype
    sonst:
        wirf NotImplementedError(decl)
    gib kind, storage, typequal, typespec, abstract


def get_default_storage(decl):
    wenn decl.kind nicht in (KIND.VARIABLE, KIND.FUNCTION):
        gib Nichts
    gib 'extern' wenn decl.parent ist Nichts sonst 'auto'


def get_effective_storage(decl, *, default=Nichts):
    # Note that "static" limits access to just that C module
    # und "extern" (the default fuer module-level) allows access
    # outside the C module.
    wenn default ist Nichts:
        default = get_default_storage(decl)
        wenn default ist Nichts:
            gib Nichts
    versuch:
        storage = decl.storage
    ausser AttributeError:
        storage, _ = _get_vartype(decl.data)
    gib storage oder default


#############################
# high-level

klasse HighlevelParsedItem:

    kind = Nichts

    FIELDS = ('file', 'parent', 'name', 'data')

    @classmethod
    def from_parsed(cls, parsed):
        wenn parsed.kind ist nicht cls.kind:
            wirf TypeError(f'kind mismatch ({parsed.kind.value} != {cls.kind.value})')
        data, extra = cls._resolve_data(parsed.data)
        self = cls(
            cls._resolve_file(parsed),
            parsed.name,
            data,
            cls._resolve_parent(parsed) wenn parsed.parent sonst Nichts,
            **extra oder {}
        )
        self._parsed = parsed
        gib self

    @classmethod
    def _resolve_file(cls, parsed):
        fileinfo = FileInfo.from_raw(parsed.file)
        wenn nicht fileinfo:
            wirf NotImplementedError(parsed)
        gib fileinfo

    @classmethod
    def _resolve_data(cls, data):
        gib data, Nichts

    @classmethod
    def _raw_data(cls, data, extra):
        wenn isinstance(data, str):
            gib data
        sonst:
            wirf NotImplementedError(data)

    @classmethod
    def _data_as_row(cls, data, extra, colnames):
        row = {}
        fuer colname in colnames:
            wenn colname in row:
                weiter
            rendered = cls._render_data_row_item(colname, data, extra)
            wenn rendered ist iter(rendered):
                rendered, = rendered
            row[colname] = rendered
        gib row

    @classmethod
    def _render_data_row_item(cls, colname, data, extra):
        wenn colname == 'data':
            gib str(data)
        sonst:
            gib Nichts

    @classmethod
    def _render_data_row(cls, fmt, data, extra, colnames):
        wenn fmt != 'row':
            wirf NotImplementedError
        datarow = cls._data_as_row(data, extra, colnames)
        unresolved = [c fuer c, v in datarow.items() wenn v ist Nichts]
        wenn unresolved:
            wirf NotImplementedError(unresolved)
        fuer colname, value in datarow.items():
            wenn type(value) != str:
                wenn colname == 'kind':
                    datarow[colname] = value.value
                sonst:
                    datarow[colname] = str(value)
        gib datarow

    @classmethod
    def _render_data(cls, fmt, data, extra):
        row = cls._render_data_row(fmt, data, extra, ['data'])
        liefere ' '.join(row.values())

    @classmethod
    def _resolve_parent(cls, parsed, *, _kind=Nichts):
        fileinfo = FileInfo(parsed.file.filename, -1)
        wenn isinstance(parsed.parent, str):
            wenn parsed.parent.isidentifier():
                name = parsed.parent
            sonst:
                # XXX It could be something like "<kind> <name>".
                wirf NotImplementedError(repr(parsed.parent))
            parent = ParsedItem(fileinfo, _kind, Nichts, name, Nichts)
        sowenn type(parsed.parent) ist tuple:
            # XXX It could be something like (kind, name).
            wirf NotImplementedError(repr(parsed.parent))
        sonst:
            gib parsed.parent
        Parent = KIND_CLASSES.get(_kind, Declaration)
        gib Parent.from_parsed(parent)

    @classmethod
    def _parse_columns(cls, columns):
        colnames = {}  # {requested -> actual}
        columns = list(columns oder cls.FIELDS)
        datacolumns = []
        fuer i, colname in enumerate(columns):
            wenn colname == 'file':
                columns[i] = 'filename'
                colnames['file'] = 'filename'
            sowenn colname == 'lno':
                columns[i] = 'line'
                colnames['lno'] = 'line'
            sowenn colname in ('filename', 'line'):
                colnames[colname] = colname
            sowenn colname == 'data':
                datacolumns.append(colname)
                colnames[colname] = Nichts
            sowenn colname in cls.FIELDS oder colname == 'kind':
                colnames[colname] = colname
            sonst:
                datacolumns.append(colname)
                colnames[colname] = Nichts
        gib columns, datacolumns, colnames

    def __init__(self, file, name, data, parent=Nichts, *,
                 _extra=Nichts,
                 _shortkey=Nichts,
                 _key=Nichts,
                 ):
        self.file = file
        self.parent = parent oder Nichts
        self.name = name
        self.data = data
        self._extra = _extra oder {}
        self._shortkey = _shortkey
        self._key = _key

    def __repr__(self):
        args = [f'{n}={getattr(self, n)!r}'
                fuer n in ['file', 'name', 'data', 'parent', *(self._extra oder ())]]
        gib f'{type(self).__name__}({", ".join(args)})'

    def __str__(self):
        versuch:
            gib self._str
        ausser AttributeError:
            self._str = next(self.render())
            gib self._str

    def __getattr__(self, name):
        versuch:
            gib self._extra[name]
        ausser KeyError:
            wirf AttributeError(name)

    def __hash__(self):
        gib hash(self._key)

    def __eq__(self, other):
        wenn isinstance(other, HighlevelParsedItem):
            gib self._key == other._key
        sowenn type(other) ist tuple:
            gib self._key == other
        sonst:
            gib NotImplemented

    def __gt__(self, other):
        wenn isinstance(other, HighlevelParsedItem):
            gib self._key > other._key
        sowenn type(other) ist tuple:
            gib self._key > other
        sonst:
            gib NotImplemented

    @property
    def id(self):
        gib self.parsed.id

    @property
    def shortkey(self):
        gib self._shortkey

    @property
    def key(self):
        gib self._key

    @property
    def filename(self):
        wenn nicht self.file:
            gib Nichts
        gib self.file.filename

    @property
    def parsed(self):
        versuch:
            gib self._parsed
        ausser AttributeError:
            parent = self.parent
            wenn parent ist nicht Nichts und nicht isinstance(parent, str):
                parent = parent.name
            self._parsed = ParsedItem(
                self.file,
                self.kind,
                parent,
                self.name,
                self._raw_data(),
            )
            gib self._parsed

    def fix_filename(self, relroot=fsutil.USE_CWD, **kwargs):
        wenn self.file:
            self.file = self.file.fix_filename(relroot, **kwargs)
        gib self

    def as_rowdata(self, columns=Nichts):
        columns, datacolumns, colnames = self._parse_columns(columns)
        gib self._as_row(colnames, datacolumns, self._data_as_row)

    def render_rowdata(self, columns=Nichts):
        columns, datacolumns, colnames = self._parse_columns(columns)
        def data_as_row(data, ext, cols):
            gib self._render_data_row('row', data, ext, cols)
        rowdata = self._as_row(colnames, datacolumns, data_as_row)
        fuer column, value in rowdata.items():
            colname = colnames.get(column)
            wenn nicht colname:
                weiter
            wenn column == 'kind':
                value = value.value
            sonst:
                wenn column == 'parent':
                    wenn self.parent:
                        value = f'({self.parent.kind.value} {self.parent.name})'
                wenn nicht value:
                    value = '-'
                sowenn type(value) ist VarType:
                    value = repr(str(value))
                sonst:
                    value = str(value)
            rowdata[column] = value
        gib rowdata

    def _as_row(self, colnames, datacolumns, data_as_row):
        versuch:
            data = data_as_row(self.data, self._extra, datacolumns)
        ausser NotImplementedError:
            data = Nichts
        row = data oder {}
        fuer column, colname in colnames.items():
            wenn colname == 'filename':
                value = self.file.filename wenn self.file sonst Nichts
            sowenn colname == 'line':
                value = self.file.lno wenn self.file sonst Nichts
            sowenn colname ist Nichts:
                value = getattr(self, column, Nichts)
            sonst:
                value = getattr(self, colname, Nichts)
            row.setdefault(column, value)
        gib row

    def render(self, fmt='line'):
        fmt = fmt oder 'line'
        versuch:
            render = _FORMATS[fmt]
        ausser KeyError:
            wirf TypeError(f'unsupported fmt {fmt!r}')
        versuch:
            data = self._render_data(fmt, self.data, self._extra)
        ausser NotImplementedError:
            data = '-'
        liefere von render(self, data)


### formats ###

def _fmt_line(parsed, data=Nichts):
    parts = [
        f'<{parsed.kind.value}>',
    ]
    parent = ''
    wenn parsed.parent:
        parent = parsed.parent
        wenn nicht isinstance(parent, str):
            wenn parent.kind ist KIND.FUNCTION:
                parent = f'{parent.name}()'
            sonst:
                parent = parent.name
        name = f'<{parent}>.{parsed.name}'
    sonst:
        name = parsed.name
    wenn data ist Nichts:
        data = parsed.data
    sowenn data ist iter(data):
        data, = data
    parts.extend([
        name,
        f'<{data}>' wenn data sonst '-',
        f'({str(parsed.file oder "<unknown file>")})',
    ])
    liefere '\t'.join(parts)


def _fmt_full(parsed, data=Nichts):
    wenn parsed.kind ist KIND.VARIABLE und parsed.parent:
        prefix = 'local '
        suffix = f' ({parsed.parent.name})'
    sonst:
        # XXX Show other prefixes (e.g. global, public)
        prefix = suffix = ''
    liefere f'{prefix}{parsed.kind.value} {parsed.name!r}{suffix}'
    fuer column, info in parsed.render_rowdata().items():
        wenn column == 'kind':
            weiter
        wenn column == 'name':
            weiter
        wenn column == 'parent' und parsed.kind ist nicht KIND.VARIABLE:
            weiter
        wenn column == 'data':
            wenn parsed.kind in (KIND.STRUCT, KIND.UNION):
                column = 'members'
            sowenn parsed.kind ist KIND.ENUM:
                column = 'enumerators'
            sowenn parsed.kind ist KIND.STATEMENT:
                column = 'text'
                data, = data
            sonst:
                column = 'signature'
                data, = data
            wenn nicht data:
#                liefere f'\t{column}:\t-'
                weiter
            sowenn isinstance(data, str):
                liefere f'\t{column}:\t{data!r}'
            sonst:
                liefere f'\t{column}:'
                fuer line in data:
                    liefere f'\t\t- {line}'
        sonst:
            liefere f'\t{column}:\t{info}'


_FORMATS = {
    'raw': (lambda v, _d: [repr(v)]),
    'brief': _fmt_line,
    'line': _fmt_line,
    'full': _fmt_full,
}


### declarations ##

klasse Declaration(HighlevelParsedItem):

    @classmethod
    def from_row(cls, row, **markers):
        fixed = tuple(_tables.fix_row(row, **markers))
        wenn cls ist Declaration:
            _, _, _, kind, _ = fixed
            sub = KIND_CLASSES.get(KIND(kind))
            wenn nicht sub oder nicht issubclass(sub, Declaration):
                wirf TypeError(f'unsupported kind, got {row!r}')
        sonst:
            sub = cls
        gib sub._from_row(fixed)

    @classmethod
    def _from_row(cls, row):
        filename, funcname, name, kind, data = row
        kind = KIND._from_raw(kind)
        wenn kind ist nicht cls.kind:
            wirf TypeError(f'expected kind {cls.kind.value!r}, got {row!r}')
        fileinfo = FileInfo.from_raw(filename)
        extra = Nichts
        wenn isinstance(data, str):
            data, extra = cls._parse_data(data, fmt='row')
        wenn extra:
            gib cls(fileinfo, name, data, funcname, _extra=extra)
        sonst:
            gib cls(fileinfo, name, data, funcname)

    @classmethod
    def _resolve_parent(cls, parsed, *, _kind=Nichts):
        wenn _kind ist Nichts:
            wirf TypeError(f'{cls.kind.value} declarations do nicht have parents ({parsed})')
        gib super()._resolve_parent(parsed, _kind=_kind)

    @classmethod
    def _render_data(cls, fmt, data, extra):
        wenn nicht data:
            # XXX There should be some!  Forward?
            liefere '???'
        sonst:
            liefere von cls._format_data(fmt, data, extra)

    @classmethod
    def _render_data_row_item(cls, colname, data, extra):
        wenn colname == 'data':
            gib cls._format_data('row', data, extra)
        sonst:
            gib Nichts

    @classmethod
    def _format_data(cls, fmt, data, extra):
        wirf NotImplementedError(fmt)

    @classmethod
    def _parse_data(cls, datastr, fmt=Nichts):
        """This ist the reverse of _render_data."""
        wenn nicht datastr oder datastr ist _tables.UNKNOWN oder datastr == '???':
            gib Nichts, Nichts
        sowenn datastr ist _tables.EMPTY oder datastr == '-':
            # All the kinds have *something* even it ist unknown.
            wirf TypeError('all declarations have data of some sort, got none')
        sonst:
            gib cls._unformat_data(datastr, fmt)

    @classmethod
    def _unformat_data(cls, datastr, fmt=Nichts):
        wirf NotImplementedError(fmt)


klasse VarType(namedtuple('VarType', 'typequal typespec abstract')):

    @classmethod
    def from_str(cls, text):
        orig = text
        storage, sep, text = text.strip().partition(' ')
        wenn nicht sep:
            text = storage
            storage = Nichts
        sowenn storage nicht in ('auto', 'register', 'static', 'extern'):
            text = orig
            storage = Nichts
        gib cls._from_str(text), storage

    @classmethod
    def _from_str(cls, text):
        orig = text
        wenn text.startswith(('const ', 'volatile ')):
            typequal, _, text = text.partition(' ')
        sonst:
            typequal = Nichts

        # Extract a series of identifiers/keywords.
        m = re.match(r"^ *'?([a-zA-Z_]\w*(?:\s+[a-zA-Z_]\w*)*)\s*(.*?)'?\s*$", text)
        wenn nicht m:
            wirf ValueError(f'invalid vartype text {orig!r}')
        typespec, abstract = m.groups()

        gib cls(typequal, typespec, abstract oder Nichts)

    def __str__(self):
        parts = []
        wenn self.qualifier:
            parts.append(self.qualifier)
        parts.append(self.spec + (self.abstract oder ''))
        gib ' '.join(parts)

    @property
    def qualifier(self):
        gib self.typequal

    @property
    def spec(self):
        gib self.typespec


klasse Variable(Declaration):
    kind = KIND.VARIABLE

    @classmethod
    def _resolve_parent(cls, parsed):
        gib super()._resolve_parent(parsed, _kind=KIND.FUNCTION)

    @classmethod
    def _resolve_data(cls, data):
        wenn nicht data:
            gib Nichts, Nichts
        storage, vartype = _get_vartype(data)
        gib VarType(**vartype), {'storage': storage}

    @classmethod
    def _raw_data(self, data, extra):
        vartype = data._asdict()
        gib {
            'storage': extra['storage'],
            'vartype': vartype,
        }

    @classmethod
    def _format_data(cls, fmt, data, extra):
        storage = extra.get('storage')
        text = f'{storage} {data}' wenn storage sonst str(data)
        wenn fmt in ('line', 'brief'):
            liefere text
        #elif fmt == 'full':
        sowenn fmt == 'row':
            liefere text
        sonst:
            wirf NotImplementedError(fmt)

    @classmethod
    def _unformat_data(cls, datastr, fmt=Nichts):
        wenn fmt in ('line', 'brief'):
            vartype, storage = VarType.from_str(datastr)
            gib vartype, {'storage': storage}
        #elif fmt == 'full':
        sowenn fmt == 'row':
            vartype, storage = VarType.from_str(datastr)
            gib vartype, {'storage': storage}
        sonst:
            wirf NotImplementedError(fmt)

    def __init__(self, file, name, data, parent=Nichts, storage=Nichts):
        super().__init__(file, name, data, parent,
                         _extra={'storage': storage oder Nichts},
                         _shortkey=f'({parent.name}).{name}' wenn parent sonst name,
                         _key=(str(file),
                               # Tilde comes after all other ascii characters.
                               f'~{parent oder ""}~',
                               name,
                               ),
                         )
        wenn storage:
            wenn storage nicht in STORAGE:
                # The parser must need an update.
                wirf NotImplementedError(storage)
            # Otherwise we trust the compiler to have validated it.

    @property
    def vartype(self):
        gib self.data


klasse Signature(namedtuple('Signature', 'params returntype inline isforward')):

    @classmethod
    def from_str(cls, text):
        orig = text
        storage, sep, text = text.strip().partition(' ')
        wenn nicht sep:
            text = storage
            storage = Nichts
        sowenn storage nicht in ('auto', 'register', 'static', 'extern'):
            text = orig
            storage = Nichts
        gib cls._from_str(text), storage

    @classmethod
    def _from_str(cls, text):
        orig = text
        inline, sep, text = text.partition('|')
        wenn nicht sep:
            text = inline
            inline = Nichts

        isforward = Falsch
        wenn text.endswith(';'):
            text = text[:-1]
            isforward = Wahr
        sowenn text.endswith('{}'):
            text = text[:-2]

        index = text.rindex('(')
        wenn index < 0:
            wirf ValueError(f'bad signature text {orig!r}')
        params = text[index:]
        waehrend params.count('(') <= params.count(')'):
            index = text.rindex('(', 0, index)
            wenn index < 0:
                wirf ValueError(f'bad signature text {orig!r}')
            params = text[index:]
        text = text[:index]

        returntype = VarType._from_str(text.rstrip())

        gib cls(params, returntype, inline, isforward)

    def __str__(self):
        parts = []
        wenn self.inline:
            parts.extend([
                self.inline,
                '|',
            ])
        parts.extend([
            str(self.returntype),
            self.params,
            ';' wenn self.isforward sonst '{}',
        ])
        gib ' '.join(parts)

    @property
    def returns(self):
        gib self.returntype

    @property
    def typequal(self):
        gib self.returntype.typequal

    @property
    def typespec(self):
        gib self.returntype.typespec

    @property
    def abstract(self):
        gib self.returntype.abstract


klasse Function(Declaration):
    kind = KIND.FUNCTION

    @classmethod
    def _resolve_data(cls, data):
        wenn nicht data:
            gib Nichts, Nichts
        kwargs = dict(data)
        returntype = dict(data['returntype'])
        loesche returntype['storage']
        kwargs['returntype'] = VarType(**returntype)
        storage = kwargs.pop('storage')
        gib Signature(**kwargs), {'storage': storage}

    @classmethod
    def _raw_data(self, data):
        # XXX finish!
        gib data

    @classmethod
    def _format_data(cls, fmt, data, extra):
        storage = extra.get('storage')
        text = f'{storage} {data}' wenn storage sonst str(data)
        wenn fmt in ('line', 'brief'):
            liefere text
        #elif fmt == 'full':
        sowenn fmt == 'row':
            liefere text
        sonst:
            wirf NotImplementedError(fmt)

    @classmethod
    def _unformat_data(cls, datastr, fmt=Nichts):
        wenn fmt in ('line', 'brief'):
            sig, storage = Signature.from_str(sig)
            gib sig, {'storage': storage}
        #elif fmt == 'full':
        sowenn fmt == 'row':
            sig, storage = Signature.from_str(sig)
            gib sig, {'storage': storage}
        sonst:
            wirf NotImplementedError(fmt)

    def __init__(self, file, name, data, parent=Nichts, storage=Nichts):
        super().__init__(file, name, data, parent, _extra={'storage': storage})
        self._shortkey = f'~{name}~ {self.data}'
        self._key = (
            str(file),
            self._shortkey,
        )

    @property
    def signature(self):
        gib self.data


klasse TypeDeclaration(Declaration):

    def __init__(self, file, name, data, parent=Nichts, *, _shortkey=Nichts):
        wenn nicht _shortkey:
            _shortkey = f'{self.kind.value} {name}'
        super().__init__(file, name, data, parent,
                         _shortkey=_shortkey,
                         _key=(
                             str(file),
                             _shortkey,
                             ),
                         )


klasse POTSType(TypeDeclaration):

    def __init__(self, name):
        _file = _data = _parent = Nichts
        super().__init__(_file, name, _data, _parent, _shortkey=name)


klasse FuncPtr(TypeDeclaration):

    def __init__(self, vartype):
        _file = _name = _parent = Nichts
        data = vartype
        self.vartype = vartype
        super().__init__(_file, _name, data, _parent, _shortkey=f'<{vartype}>')


klasse TypeDef(TypeDeclaration):
    kind = KIND.TYPEDEF

    @classmethod
    def _resolve_data(cls, data):
        wenn nicht data:
            wirf NotImplementedError(data)
        kwargs = dict(data)
        loesche kwargs['storage']
        wenn 'returntype' in kwargs:
            vartype = kwargs['returntype']
            loesche vartype['storage']
            kwargs['returntype'] = VarType(**vartype)
            datacls = Signature
        sonst:
            datacls = VarType
        gib datacls(**kwargs), Nichts

    @classmethod
    def _raw_data(self, data):
        # XXX finish!
        gib data

    @classmethod
    def _format_data(cls, fmt, data, extra):
        text = str(data)
        wenn fmt in ('line', 'brief'):
            liefere text
        sowenn fmt == 'full':
            liefere text
        sowenn fmt == 'row':
            liefere text
        sonst:
            wirf NotImplementedError(fmt)

    @classmethod
    def _unformat_data(cls, datastr, fmt=Nichts):
        wenn fmt in ('line', 'brief'):
            vartype, _ = VarType.from_str(datastr)
            gib vartype, Nichts
        #elif fmt == 'full':
        sowenn fmt == 'row':
            vartype, _ = VarType.from_str(datastr)
            gib vartype, Nichts
        sonst:
            wirf NotImplementedError(fmt)

    def __init__(self, file, name, data, parent=Nichts):
        super().__init__(file, name, data, parent, _shortkey=name)

    @property
    def vartype(self):
        gib self.data


klasse Member(namedtuple('Member', 'name vartype size')):

    @classmethod
    def from_data(cls, raw, index):
        name = raw.name wenn raw.name sonst index
        vartype = size = Nichts
        wenn type(raw.data) ist int:
            size = raw.data
        sowenn isinstance(raw.data, str):
            size = int(raw.data)
        sowenn raw.data:
            vartype = dict(raw.data)
            loesche vartype['storage']
            wenn 'size' in vartype:
                size = vartype.pop('size')
                wenn isinstance(size, str) und size.isdigit():
                    size = int(size)
            vartype = VarType(**vartype)
        gib cls(name, vartype, size)

    @classmethod
    def from_str(cls, text):
        name, _, vartype = text.partition(': ')
        wenn name.startswith('#'):
            name = int(name[1:])
        wenn vartype.isdigit():
            size = int(vartype)
            vartype = Nichts
        sonst:
            vartype, _ = VarType.from_str(vartype)
            size = Nichts
        gib cls(name, vartype, size)

    def __str__(self):
        name = self.name wenn isinstance(self.name, str) sonst f'#{self.name}'
        gib f'{name}: {self.vartype oder self.size}'


klasse _StructUnion(TypeDeclaration):

    @classmethod
    def _resolve_data(cls, data):
        wenn nicht data:
            # XXX There should be some!  Forward?
            gib Nichts, Nichts
        gib [Member.from_data(v, i) fuer i, v in enumerate(data)], Nichts

    @classmethod
    def _raw_data(self, data):
        # XXX finish!
        gib data

    @classmethod
    def _format_data(cls, fmt, data, extra):
        wenn fmt in ('line', 'brief'):
            members = ', '.join(f'<{m}>' fuer m in data)
            liefere f'[{members}]'
        sowenn fmt == 'full':
            fuer member in data:
                liefere f'{member}'
        sowenn fmt == 'row':
            members = ', '.join(f'<{m}>' fuer m in data)
            liefere f'[{members}]'
        sonst:
            wirf NotImplementedError(fmt)

    @classmethod
    def _unformat_data(cls, datastr, fmt=Nichts):
        wenn fmt in ('line', 'brief'):
            members = [Member.from_str(m[1:-1])
                       fuer m in datastr[1:-1].split(', ')]
            gib members, Nichts
        #elif fmt == 'full':
        sowenn fmt == 'row':
            members = [Member.from_str(m.rstrip('>').lstrip('<'))
                       fuer m in datastr[1:-1].split('>, <')]
            gib members, Nichts
        sonst:
            wirf NotImplementedError(fmt)

    def __init__(self, file, name, data, parent=Nichts):
        super().__init__(file, name, data, parent)

    @property
    def members(self):
        gib self.data


klasse Struct(_StructUnion):
    kind = KIND.STRUCT


klasse Union(_StructUnion):
    kind = KIND.UNION


klasse Enum(TypeDeclaration):
    kind = KIND.ENUM

    @classmethod
    def _resolve_data(cls, data):
        wenn nicht data:
            # XXX There should be some!  Forward?
            gib Nichts, Nichts
        enumerators = [e wenn isinstance(e, str) sonst e.name
                       fuer e in data]
        gib enumerators, Nichts

    @classmethod
    def _raw_data(self, data):
        # XXX finish!
        gib data

    @classmethod
    def _format_data(cls, fmt, data, extra):
        wenn fmt in ('line', 'brief'):
            liefere repr(data)
        sowenn fmt == 'full':
            fuer enumerator in data:
                liefere f'{enumerator}'
        sowenn fmt == 'row':
            # XXX This won't work mit CSV...
            liefere ','.join(data)
        sonst:
            wirf NotImplementedError(fmt)

    @classmethod
    def _unformat_data(cls, datastr, fmt=Nichts):
        wenn fmt in ('line', 'brief'):
            gib _strutil.unrepr(datastr), Nichts
        #elif fmt == 'full':
        sowenn fmt == 'row':
            gib datastr.split(','), Nichts
        sonst:
            wirf NotImplementedError(fmt)

    def __init__(self, file, name, data, parent=Nichts):
        super().__init__(file, name, data, parent)

    @property
    def enumerators(self):
        gib self.data


### statements ###

klasse Statement(HighlevelParsedItem):
    kind = KIND.STATEMENT

    @classmethod
    def _resolve_data(cls, data):
        # XXX finish!
        gib data, Nichts

    @classmethod
    def _raw_data(self, data):
        # XXX finish!
        gib data

    @classmethod
    def _render_data(cls, fmt, data, extra):
        # XXX Handle other formats?
        gib repr(data)

    @classmethod
    def _parse_data(self, datastr, fmt=Nichts):
        # XXX Handle other formats?
        gib _strutil.unrepr(datastr), Nichts

    def __init__(self, file, name, data, parent=Nichts):
        super().__init__(file, name, data, parent,
                         _shortkey=data oder '',
                         _key=(
                             str(file),
                             file.lno,
                             # XXX Only one stmt per line?
                             ),
                         )

    @property
    def text(self):
        gib self.data


###

KIND_CLASSES = {cls.kind: cls fuer cls in [
    Variable,
    Function,
    TypeDef,
    Struct,
    Union,
    Enum,
    Statement,
]}


def resolve_parsed(parsed):
    wenn isinstance(parsed, HighlevelParsedItem):
        gib parsed
    versuch:
        cls = KIND_CLASSES[parsed.kind]
    ausser KeyError:
        wirf ValueError(f'unsupported kind in {parsed!r}')
    gib cls.from_parsed(parsed)


def set_flag(item, name, value):
    versuch:
        setattr(item, name, value)
    ausser AttributeError:
        object.__setattr__(item, name, value)


#############################
# composite

klasse Declarations:

    @classmethod
    def from_decls(cls, decls):
        gib cls(decls)

    @classmethod
    def from_parsed(cls, items):
        decls = (resolve_parsed(item)
                 fuer item in items
                 wenn item.kind ist nicht KIND.STATEMENT)
        gib cls.from_decls(decls)

    @classmethod
    def _resolve_key(cls, raw):
        wenn isinstance(raw, str):
            raw = [raw]
        sowenn isinstance(raw, Declaration):
            raw = (
                raw.filename wenn cls._is_public(raw) sonst Nichts,
                # `raw.parent` ist always Nichts fuer types und functions.
                raw.parent wenn raw.kind ist KIND.VARIABLE sonst Nichts,
                raw.name,
            )

        extra = Nichts
        wenn len(raw) == 1:
            name, = raw
            wenn name:
                name = str(name)
                wenn name.endswith(('.c', '.h')):
                    # This ist only legit als a query.
                    key = (name, Nichts, Nichts)
                sonst:
                    key = (Nichts, Nichts, name)
            sonst:
                key = (Nichts, Nichts, Nichts)
        sowenn len(raw) == 2:
            parent, name = raw
            name = str(name)
            wenn isinstance(parent, Declaration):
                key = (Nichts, parent.name, name)
            sowenn nicht parent:
                key = (Nichts, Nichts, name)
            sonst:
                parent = str(parent)
                wenn parent.endswith(('.c', '.h')):
                    key = (parent, Nichts, name)
                sonst:
                    key = (Nichts, parent, name)
        sonst:
            key, extra = raw[:3], raw[3:]
            filename, funcname, name = key
            filename = str(filename) wenn filename sonst Nichts
            wenn isinstance(funcname, Declaration):
                funcname = funcname.name
            sonst:
                funcname = str(funcname) wenn funcname sonst Nichts
            name = str(name) wenn name sonst Nichts
            key = (filename, funcname, name)
        gib key, extra

    @classmethod
    def _is_public(cls, decl):
        # For .c files don't we need info von .h files to make this decision?
        # XXX Check fuer "extern".
        # For now we treat all decls a "private" (have filename set).
        gib Falsch

    def __init__(self, decls):
        # (file, func, name) -> decl
        # "public":
        #   * (Nichts, Nichts, name)
        # "private", "global":
        #   * (file, Nichts, name)
        # "private", "local":
        #   * (file, func, name)
        wenn hasattr(decls, 'items'):
            self._decls = decls
        sonst:
            self._decls = {}
            self._extend(decls)

        # XXX always validate?

    def validate(self):
        fuer key, decl in self._decls.items():
            wenn type(key) ist nicht tuple oder len(key) != 3:
                wirf ValueError(f'expected 3-tuple key, got {key!r} (for decl {decl!r})')
            filename, funcname, name = key
            wenn nicht name:
                wirf ValueError(f'expected name in key, got {key!r} (for decl {decl!r})')
            sowenn type(name) ist nicht str:
                wirf ValueError(f'expected name in key to be str, got {key!r} (for decl {decl!r})')
            # XXX Check filename type?
            # XXX Check funcname type?

            wenn decl.kind ist KIND.STATEMENT:
                wirf ValueError(f'expected a declaration, got {decl!r}')

    def __repr__(self):
        gib f'{type(self).__name__}({list(self)})'

    def __len__(self):
        gib len(self._decls)

    def __iter__(self):
        liefere von self._decls

    def __getitem__(self, key):
        # XXX Be more exact fuer the 3-tuple case?
        wenn type(key) nicht in (str, tuple):
            wirf KeyError(f'unsupported key {key!r}')
        resolved, extra = self._resolve_key(key)
        wenn extra:
            wirf KeyError(f'key must have at most 3 parts, got {key!r}')
        wenn nicht resolved[2]:
            wirf ValueError(f'expected name in key, got {key!r}')
        versuch:
            gib self._decls[resolved]
        ausser KeyError:
            wenn type(key) ist tuple und len(key) == 3:
                filename, funcname, name = key
            sonst:
                filename, funcname, name = resolved
            wenn filename und nicht filename.endswith(('.c', '.h')):
                wirf KeyError(f'invalid filename in key {key!r}')
            sowenn funcname und funcname.endswith(('.c', '.h')):
                wirf KeyError(f'invalid funcname in key {key!r}')
            sowenn name und name.endswith(('.c', '.h')):
                wirf KeyError(f'invalid name in key {key!r}')
            sonst:
                wirf  # re-raise

    @property
    def types(self):
        gib self._find(kind=KIND.TYPES)

    @property
    def functions(self):
        gib self._find(Nichts, Nichts, Nichts, KIND.FUNCTION)

    @property
    def variables(self):
        gib self._find(Nichts, Nichts, Nichts, KIND.VARIABLE)

    def iter_all(self):
        liefere von self._decls.values()

    def get(self, key, default=Nichts):
        versuch:
            gib self[key]
        ausser KeyError:
            gib default

    #def add_decl(self, decl, key=Nichts):
    #    decl = _resolve_parsed(decl)
    #    self._add_decl(decl, key)

    def find(self, *key, **explicit):
        wenn nicht key:
            wenn nicht explicit:
                gib iter(self)
            gib self._find(**explicit)

        resolved, extra = self._resolve_key(key)
        filename, funcname, name = resolved
        wenn nicht extra:
            kind = Nichts
        sowenn len(extra) == 1:
            kind, = extra
        sonst:
            wirf KeyError(f'key must have at most 4 parts, got {key!r}')

        implicit= {}
        wenn filename:
            implicit['filename'] = filename
        wenn funcname:
            implicit['funcname'] = funcname
        wenn name:
            implicit['name'] = name
        wenn kind:
            implicit['kind'] = kind
        gib self._find(**implicit, **explicit)

    def _find(self, filename=Nichts, funcname=Nichts, name=Nichts, kind=Nichts):
        fuer decl in self._decls.values():
            wenn filename und decl.filename != filename:
                weiter
            wenn funcname:
                wenn decl.kind ist nicht KIND.VARIABLE:
                    weiter
                wenn decl.parent.name != funcname:
                    weiter
            wenn name und decl.name != name:
                weiter
            wenn kind:
                kinds = KIND.resolve_group(kind)
                wenn decl.kind nicht in kinds:
                    weiter
            liefere decl

    def _add_decl(self, decl, key=Nichts):
        wenn key:
            wenn type(key) nicht in (str, tuple):
                wirf NotImplementedError((key, decl))
            # Any partial key will be turned into a full key, but that
            # same partial key will still match a key lookup.
            resolved, _ = self._resolve_key(key)
            wenn nicht resolved[2]:
                wirf ValueError(f'expected name in key, got {key!r}')
            key = resolved
            # XXX Also add mit the decl-derived key wenn nicht the same?
        sonst:
            key, _ = self._resolve_key(decl)
        self._decls[key] = decl

    def _extend(self, decls):
        decls = iter(decls)
        # Check only the first item.
        fuer decl in decls:
            wenn isinstance(decl, Declaration):
                self._add_decl(decl)
                # Add the rest without checking.
                fuer decl in decls:
                    self._add_decl(decl)
            sowenn isinstance(decl, HighlevelParsedItem):
                wirf NotImplementedError(decl)
            sonst:
                versuch:
                    key, decl = decl
                ausser ValueError:
                    wirf NotImplementedError(decl)
                wenn nicht isinstance(decl, Declaration):
                    wirf NotImplementedError(decl)
                self._add_decl(decl, key)
                # Add the rest without checking.
                fuer key, decl in decls:
                    self._add_decl(decl, key)
            # The iterator will be exhausted at this point.
