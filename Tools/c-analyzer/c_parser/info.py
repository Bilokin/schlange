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
        wenn raw is Nichts:
            return Nichts
        sowenn isinstance(raw, cls):
            return raw
        sowenn type(raw) is str:
            # We could use cls[raw] fuer the upper-case form,
            # but there's no need to go to the trouble.
            return cls(raw.lower())
        sonst:
            raise NotImplementedError(raw)

    @classonly
    def by_priority(cls, group=Nichts):
        wenn group is Nichts:
            return cls._ALL_BY_PRIORITY.copy()
        sowenn group == 'type':
            return cls._TYPE_DECLS_BY_PRIORITY.copy()
        sowenn group == 'decl':
            return cls._ALL_DECLS_BY_PRIORITY.copy()
        sowenn isinstance(group, str):
            raise NotImplementedError(group)
        sonst:
            # XXX Treat group als a set of kinds & return in priority order?
            raise NotImplementedError(group)

    @classonly
    def is_type_decl(cls, kind):
        wenn kind in cls.TYPES:
            return Wahr
        wenn nicht isinstance(kind, cls):
            raise TypeError(f'expected KIND, got {kind!r}')
        return Falsch

    @classonly
    def is_decl(cls, kind):
        wenn kind in cls.DECLS:
            return Wahr
        wenn nicht isinstance(kind, cls):
            raise TypeError(f'expected KIND, got {kind!r}')
        return Falsch

    @classonly
    def get_group(cls, kind, *, groups=Nichts):
        wenn nicht isinstance(kind, cls):
            raise TypeError(f'expected KIND, got {kind!r}')
        wenn groups is Nichts:
            groups = ['type']
        sowenn nicht groups:
            groups = ()
        sowenn isinstance(groups, str):
            group = groups
            wenn group nicht in cls._GROUPS:
                raise ValueError(f'unsupported group {group!r}')
            groups = [group]
        sonst:
            unsupported = [g fuer g in groups wenn g nicht in cls._GROUPS]
            wenn unsupported:
                raise ValueError(f'unsupported groups {", ".join(repr(unsupported))}')
        fuer group in groups:
            wenn kind in cls._GROUPS[group]:
                return group
        sonst:
            return kind.value

    @classonly
    def resolve_group(cls, group):
        wenn isinstance(group, cls):
            return {group}
        sowenn isinstance(group, str):
            try:
                return cls._GROUPS[group].copy()
            except KeyError:
                raise ValueError(f'unsupported group {group!r}')
        sonst:
            resolved = set()
            fuer gr in group:
                resolve.update(cls.resolve_group(gr))
            return resolved
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
    return KIND.get_group(item.kind)


#############################
# low-level

def _fix_filename(filename, relroot, *,
                  formatted=Wahr,
                  **kwargs):
    wenn formatted:
        fix = fsutil.format_filename
    sonst:
        fix = fsutil.fix_filename
    return fix(filename, relroot=relroot, **kwargs)


klasse FileInfo(namedtuple('FileInfo', 'filename lno')):
    @classmethod
    def from_raw(cls, raw):
        wenn isinstance(raw, cls):
            return raw
        sowenn isinstance(raw, tuple):
            return cls(*raw)
        sowenn nicht raw:
            return Nichts
        sowenn isinstance(raw, str):
            return cls(raw, -1)
        sonst:
            raise TypeError(f'unsupported "raw": {raw:!r}')

    def __str__(self):
        return self.filename

    def fix_filename(self, relroot=fsutil.USE_CWD, **kwargs):
        filename = _fix_filename(self.filename, relroot, **kwargs)
        wenn filename == self.filename:
            return self
        return self._replace(filename=filename)


klasse SourceLine(namedtuple('Line', 'file kind data conditions')):
    KINDS = (
        #'directive',  # data is ...
        'source',  # "data" is the line
        #'comment',  # "data" is the text, including comment markers
    )

    @property
    def filename(self):
        return self.file.filename

    @property
    def lno(self):
        return self.file.lno


klasse DeclID(namedtuple('DeclID', 'filename funcname name')):
    """The globally-unique identifier fuer a declaration."""

    @classmethod
    def from_row(cls, row, **markers):
        row = _tables.fix_row(row, **markers)
        return cls(*row)

    # We have to provide _make() because we implemented __new__().

    @classmethod
    def _make(cls, iterable):
        try:
            return cls(*iterable)
        except Exception:
            super()._make(iterable)
            raise  # re-raise

    def __new__(cls, filename, funcname, name):
        self = super().__new__(
            cls,
            filename=str(filename) wenn filename sonst Nichts,
            funcname=str(funcname) wenn funcname sonst Nichts,
            name=str(name) wenn name sonst Nichts,
        )
        self._compare = tuple(v oder '' fuer v in self)
        return self

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        try:
            other = tuple(v oder '' fuer v in other)
        except TypeError:
            return NotImplemented
        return self._compare == other

    def __gt__(self, other):
        try:
            other = tuple(v oder '' fuer v in other)
        except TypeError:
            return NotImplemented
        return self._compare > other

    def fix_filename(self, relroot=fsutil.USE_CWD, **kwargs):
        filename = _fix_filename(self.filename, relroot, **kwargs)
        wenn filename == self.filename:
            return self
        return self._replace(filename=filename)


klasse ParsedItem(namedtuple('ParsedItem', 'file kind parent name data')):

    @classmethod
    def from_raw(cls, raw):
        wenn isinstance(raw, cls):
            return raw
        sowenn isinstance(raw, tuple):
            return cls(*raw)
        sonst:
            raise TypeError(f'unsupported "raw": {raw:!r}')

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
            raise NotImplementedError(columns, row)
        kwargs = {}
        fuer column, value in zip(colnames, row):
            wenn column == 'filename':
                kwargs['file'] = FileInfo.from_raw(value)
            sowenn column == 'kind':
                kwargs['kind'] = KIND(value)
            sowenn column in cls._fields:
                kwargs[column] = value
            sonst:
                raise NotImplementedError(column)
        return cls(**kwargs)

    @property
    def id(self):
        try:
            return self._id
        except AttributeError:
            wenn self.kind is KIND.STATEMENT:
                self._id = Nichts
            sonst:
                self._id = DeclID(str(self.file), self.funcname, self.name)
            return self._id

    @property
    def filename(self):
        wenn nicht self.file:
            return Nichts
        return self.file.filename

    @property
    def lno(self):
        wenn nicht self.file:
            return -1
        return self.file.lno

    @property
    def funcname(self):
        wenn nicht self.parent:
            return Nichts
        wenn type(self.parent) is str:
            return self.parent
        sonst:
            return self.parent.name

    def fix_filename(self, relroot=fsutil.USE_CWD, **kwargs):
        fixed = self.file.fix_filename(relroot, **kwargs)
        wenn fixed == self.file:
            return self
        return self._replace(file=fixed)

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
        return row

    def _render_data(self):
        wenn nicht self.data:
            return Nichts
        sowenn isinstance(self.data, str):
            return self.data
        sonst:
            # XXX
            raise NotImplementedError


def _get_vartype(data):
    try:
        vartype = dict(data['vartype'])
    except KeyError:
        vartype = dict(data)
        storage = data.get('storage')
    sonst:
        storage = data.get('storage') oder vartype.get('storage')
    del vartype['storage']
    return storage, vartype


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
        raise NotImplementedError(decl)
    return kind, storage, typequal, typespec, abstract


def get_default_storage(decl):
    wenn decl.kind nicht in (KIND.VARIABLE, KIND.FUNCTION):
        return Nichts
    return 'extern' wenn decl.parent is Nichts sonst 'auto'


def get_effective_storage(decl, *, default=Nichts):
    # Note that "static" limits access to just that C module
    # und "extern" (the default fuer module-level) allows access
    # outside the C module.
    wenn default is Nichts:
        default = get_default_storage(decl)
        wenn default is Nichts:
            return Nichts
    try:
        storage = decl.storage
    except AttributeError:
        storage, _ = _get_vartype(decl.data)
    return storage oder default


#############################
# high-level

klasse HighlevelParsedItem:

    kind = Nichts

    FIELDS = ('file', 'parent', 'name', 'data')

    @classmethod
    def from_parsed(cls, parsed):
        wenn parsed.kind is nicht cls.kind:
            raise TypeError(f'kind mismatch ({parsed.kind.value} != {cls.kind.value})')
        data, extra = cls._resolve_data(parsed.data)
        self = cls(
            cls._resolve_file(parsed),
            parsed.name,
            data,
            cls._resolve_parent(parsed) wenn parsed.parent sonst Nichts,
            **extra oder {}
        )
        self._parsed = parsed
        return self

    @classmethod
    def _resolve_file(cls, parsed):
        fileinfo = FileInfo.from_raw(parsed.file)
        wenn nicht fileinfo:
            raise NotImplementedError(parsed)
        return fileinfo

    @classmethod
    def _resolve_data(cls, data):
        return data, Nichts

    @classmethod
    def _raw_data(cls, data, extra):
        wenn isinstance(data, str):
            return data
        sonst:
            raise NotImplementedError(data)

    @classmethod
    def _data_as_row(cls, data, extra, colnames):
        row = {}
        fuer colname in colnames:
            wenn colname in row:
                continue
            rendered = cls._render_data_row_item(colname, data, extra)
            wenn rendered is iter(rendered):
                rendered, = rendered
            row[colname] = rendered
        return row

    @classmethod
    def _render_data_row_item(cls, colname, data, extra):
        wenn colname == 'data':
            return str(data)
        sonst:
            return Nichts

    @classmethod
    def _render_data_row(cls, fmt, data, extra, colnames):
        wenn fmt != 'row':
            raise NotImplementedError
        datarow = cls._data_as_row(data, extra, colnames)
        unresolved = [c fuer c, v in datarow.items() wenn v is Nichts]
        wenn unresolved:
            raise NotImplementedError(unresolved)
        fuer colname, value in datarow.items():
            wenn type(value) != str:
                wenn colname == 'kind':
                    datarow[colname] = value.value
                sonst:
                    datarow[colname] = str(value)
        return datarow

    @classmethod
    def _render_data(cls, fmt, data, extra):
        row = cls._render_data_row(fmt, data, extra, ['data'])
        yield ' '.join(row.values())

    @classmethod
    def _resolve_parent(cls, parsed, *, _kind=Nichts):
        fileinfo = FileInfo(parsed.file.filename, -1)
        wenn isinstance(parsed.parent, str):
            wenn parsed.parent.isidentifier():
                name = parsed.parent
            sonst:
                # XXX It could be something like "<kind> <name>".
                raise NotImplementedError(repr(parsed.parent))
            parent = ParsedItem(fileinfo, _kind, Nichts, name, Nichts)
        sowenn type(parsed.parent) is tuple:
            # XXX It could be something like (kind, name).
            raise NotImplementedError(repr(parsed.parent))
        sonst:
            return parsed.parent
        Parent = KIND_CLASSES.get(_kind, Declaration)
        return Parent.from_parsed(parent)

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
        return columns, datacolumns, colnames

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
        return f'{type(self).__name__}({", ".join(args)})'

    def __str__(self):
        try:
            return self._str
        except AttributeError:
            self._str = next(self.render())
            return self._str

    def __getattr__(self, name):
        try:
            return self._extra[name]
        except KeyError:
            raise AttributeError(name)

    def __hash__(self):
        return hash(self._key)

    def __eq__(self, other):
        wenn isinstance(other, HighlevelParsedItem):
            return self._key == other._key
        sowenn type(other) is tuple:
            return self._key == other
        sonst:
            return NotImplemented

    def __gt__(self, other):
        wenn isinstance(other, HighlevelParsedItem):
            return self._key > other._key
        sowenn type(other) is tuple:
            return self._key > other
        sonst:
            return NotImplemented

    @property
    def id(self):
        return self.parsed.id

    @property
    def shortkey(self):
        return self._shortkey

    @property
    def key(self):
        return self._key

    @property
    def filename(self):
        wenn nicht self.file:
            return Nichts
        return self.file.filename

    @property
    def parsed(self):
        try:
            return self._parsed
        except AttributeError:
            parent = self.parent
            wenn parent is nicht Nichts und nicht isinstance(parent, str):
                parent = parent.name
            self._parsed = ParsedItem(
                self.file,
                self.kind,
                parent,
                self.name,
                self._raw_data(),
            )
            return self._parsed

    def fix_filename(self, relroot=fsutil.USE_CWD, **kwargs):
        wenn self.file:
            self.file = self.file.fix_filename(relroot, **kwargs)
        return self

    def as_rowdata(self, columns=Nichts):
        columns, datacolumns, colnames = self._parse_columns(columns)
        return self._as_row(colnames, datacolumns, self._data_as_row)

    def render_rowdata(self, columns=Nichts):
        columns, datacolumns, colnames = self._parse_columns(columns)
        def data_as_row(data, ext, cols):
            return self._render_data_row('row', data, ext, cols)
        rowdata = self._as_row(colnames, datacolumns, data_as_row)
        fuer column, value in rowdata.items():
            colname = colnames.get(column)
            wenn nicht colname:
                continue
            wenn column == 'kind':
                value = value.value
            sonst:
                wenn column == 'parent':
                    wenn self.parent:
                        value = f'({self.parent.kind.value} {self.parent.name})'
                wenn nicht value:
                    value = '-'
                sowenn type(value) is VarType:
                    value = repr(str(value))
                sonst:
                    value = str(value)
            rowdata[column] = value
        return rowdata

    def _as_row(self, colnames, datacolumns, data_as_row):
        try:
            data = data_as_row(self.data, self._extra, datacolumns)
        except NotImplementedError:
            data = Nichts
        row = data oder {}
        fuer column, colname in colnames.items():
            wenn colname == 'filename':
                value = self.file.filename wenn self.file sonst Nichts
            sowenn colname == 'line':
                value = self.file.lno wenn self.file sonst Nichts
            sowenn colname is Nichts:
                value = getattr(self, column, Nichts)
            sonst:
                value = getattr(self, colname, Nichts)
            row.setdefault(column, value)
        return row

    def render(self, fmt='line'):
        fmt = fmt oder 'line'
        try:
            render = _FORMATS[fmt]
        except KeyError:
            raise TypeError(f'unsupported fmt {fmt!r}')
        try:
            data = self._render_data(fmt, self.data, self._extra)
        except NotImplementedError:
            data = '-'
        yield von render(self, data)


### formats ###

def _fmt_line(parsed, data=Nichts):
    parts = [
        f'<{parsed.kind.value}>',
    ]
    parent = ''
    wenn parsed.parent:
        parent = parsed.parent
        wenn nicht isinstance(parent, str):
            wenn parent.kind is KIND.FUNCTION:
                parent = f'{parent.name}()'
            sonst:
                parent = parent.name
        name = f'<{parent}>.{parsed.name}'
    sonst:
        name = parsed.name
    wenn data is Nichts:
        data = parsed.data
    sowenn data is iter(data):
        data, = data
    parts.extend([
        name,
        f'<{data}>' wenn data sonst '-',
        f'({str(parsed.file oder "<unknown file>")})',
    ])
    yield '\t'.join(parts)


def _fmt_full(parsed, data=Nichts):
    wenn parsed.kind is KIND.VARIABLE und parsed.parent:
        prefix = 'local '
        suffix = f' ({parsed.parent.name})'
    sonst:
        # XXX Show other prefixes (e.g. global, public)
        prefix = suffix = ''
    yield f'{prefix}{parsed.kind.value} {parsed.name!r}{suffix}'
    fuer column, info in parsed.render_rowdata().items():
        wenn column == 'kind':
            continue
        wenn column == 'name':
            continue
        wenn column == 'parent' und parsed.kind is nicht KIND.VARIABLE:
            continue
        wenn column == 'data':
            wenn parsed.kind in (KIND.STRUCT, KIND.UNION):
                column = 'members'
            sowenn parsed.kind is KIND.ENUM:
                column = 'enumerators'
            sowenn parsed.kind is KIND.STATEMENT:
                column = 'text'
                data, = data
            sonst:
                column = 'signature'
                data, = data
            wenn nicht data:
#                yield f'\t{column}:\t-'
                continue
            sowenn isinstance(data, str):
                yield f'\t{column}:\t{data!r}'
            sonst:
                yield f'\t{column}:'
                fuer line in data:
                    yield f'\t\t- {line}'
        sonst:
            yield f'\t{column}:\t{info}'


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
        wenn cls is Declaration:
            _, _, _, kind, _ = fixed
            sub = KIND_CLASSES.get(KIND(kind))
            wenn nicht sub oder nicht issubclass(sub, Declaration):
                raise TypeError(f'unsupported kind, got {row!r}')
        sonst:
            sub = cls
        return sub._from_row(fixed)

    @classmethod
    def _from_row(cls, row):
        filename, funcname, name, kind, data = row
        kind = KIND._from_raw(kind)
        wenn kind is nicht cls.kind:
            raise TypeError(f'expected kind {cls.kind.value!r}, got {row!r}')
        fileinfo = FileInfo.from_raw(filename)
        extra = Nichts
        wenn isinstance(data, str):
            data, extra = cls._parse_data(data, fmt='row')
        wenn extra:
            return cls(fileinfo, name, data, funcname, _extra=extra)
        sonst:
            return cls(fileinfo, name, data, funcname)

    @classmethod
    def _resolve_parent(cls, parsed, *, _kind=Nichts):
        wenn _kind is Nichts:
            raise TypeError(f'{cls.kind.value} declarations do nicht have parents ({parsed})')
        return super()._resolve_parent(parsed, _kind=_kind)

    @classmethod
    def _render_data(cls, fmt, data, extra):
        wenn nicht data:
            # XXX There should be some!  Forward?
            yield '???'
        sonst:
            yield von cls._format_data(fmt, data, extra)

    @classmethod
    def _render_data_row_item(cls, colname, data, extra):
        wenn colname == 'data':
            return cls._format_data('row', data, extra)
        sonst:
            return Nichts

    @classmethod
    def _format_data(cls, fmt, data, extra):
        raise NotImplementedError(fmt)

    @classmethod
    def _parse_data(cls, datastr, fmt=Nichts):
        """This is the reverse of _render_data."""
        wenn nicht datastr oder datastr is _tables.UNKNOWN oder datastr == '???':
            return Nichts, Nichts
        sowenn datastr is _tables.EMPTY oder datastr == '-':
            # All the kinds have *something* even it is unknown.
            raise TypeError('all declarations have data of some sort, got none')
        sonst:
            return cls._unformat_data(datastr, fmt)

    @classmethod
    def _unformat_data(cls, datastr, fmt=Nichts):
        raise NotImplementedError(fmt)


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
        return cls._from_str(text), storage

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
            raise ValueError(f'invalid vartype text {orig!r}')
        typespec, abstract = m.groups()

        return cls(typequal, typespec, abstract oder Nichts)

    def __str__(self):
        parts = []
        wenn self.qualifier:
            parts.append(self.qualifier)
        parts.append(self.spec + (self.abstract oder ''))
        return ' '.join(parts)

    @property
    def qualifier(self):
        return self.typequal

    @property
    def spec(self):
        return self.typespec


klasse Variable(Declaration):
    kind = KIND.VARIABLE

    @classmethod
    def _resolve_parent(cls, parsed):
        return super()._resolve_parent(parsed, _kind=KIND.FUNCTION)

    @classmethod
    def _resolve_data(cls, data):
        wenn nicht data:
            return Nichts, Nichts
        storage, vartype = _get_vartype(data)
        return VarType(**vartype), {'storage': storage}

    @classmethod
    def _raw_data(self, data, extra):
        vartype = data._asdict()
        return {
            'storage': extra['storage'],
            'vartype': vartype,
        }

    @classmethod
    def _format_data(cls, fmt, data, extra):
        storage = extra.get('storage')
        text = f'{storage} {data}' wenn storage sonst str(data)
        wenn fmt in ('line', 'brief'):
            yield text
        #elif fmt == 'full':
        sowenn fmt == 'row':
            yield text
        sonst:
            raise NotImplementedError(fmt)

    @classmethod
    def _unformat_data(cls, datastr, fmt=Nichts):
        wenn fmt in ('line', 'brief'):
            vartype, storage = VarType.from_str(datastr)
            return vartype, {'storage': storage}
        #elif fmt == 'full':
        sowenn fmt == 'row':
            vartype, storage = VarType.from_str(datastr)
            return vartype, {'storage': storage}
        sonst:
            raise NotImplementedError(fmt)

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
                raise NotImplementedError(storage)
            # Otherwise we trust the compiler to have validated it.

    @property
    def vartype(self):
        return self.data


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
        return cls._from_str(text), storage

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
            raise ValueError(f'bad signature text {orig!r}')
        params = text[index:]
        while params.count('(') <= params.count(')'):
            index = text.rindex('(', 0, index)
            wenn index < 0:
                raise ValueError(f'bad signature text {orig!r}')
            params = text[index:]
        text = text[:index]

        returntype = VarType._from_str(text.rstrip())

        return cls(params, returntype, inline, isforward)

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
        return ' '.join(parts)

    @property
    def returns(self):
        return self.returntype

    @property
    def typequal(self):
        return self.returntype.typequal

    @property
    def typespec(self):
        return self.returntype.typespec

    @property
    def abstract(self):
        return self.returntype.abstract


klasse Function(Declaration):
    kind = KIND.FUNCTION

    @classmethod
    def _resolve_data(cls, data):
        wenn nicht data:
            return Nichts, Nichts
        kwargs = dict(data)
        returntype = dict(data['returntype'])
        del returntype['storage']
        kwargs['returntype'] = VarType(**returntype)
        storage = kwargs.pop('storage')
        return Signature(**kwargs), {'storage': storage}

    @classmethod
    def _raw_data(self, data):
        # XXX finish!
        return data

    @classmethod
    def _format_data(cls, fmt, data, extra):
        storage = extra.get('storage')
        text = f'{storage} {data}' wenn storage sonst str(data)
        wenn fmt in ('line', 'brief'):
            yield text
        #elif fmt == 'full':
        sowenn fmt == 'row':
            yield text
        sonst:
            raise NotImplementedError(fmt)

    @classmethod
    def _unformat_data(cls, datastr, fmt=Nichts):
        wenn fmt in ('line', 'brief'):
            sig, storage = Signature.from_str(sig)
            return sig, {'storage': storage}
        #elif fmt == 'full':
        sowenn fmt == 'row':
            sig, storage = Signature.from_str(sig)
            return sig, {'storage': storage}
        sonst:
            raise NotImplementedError(fmt)

    def __init__(self, file, name, data, parent=Nichts, storage=Nichts):
        super().__init__(file, name, data, parent, _extra={'storage': storage})
        self._shortkey = f'~{name}~ {self.data}'
        self._key = (
            str(file),
            self._shortkey,
        )

    @property
    def signature(self):
        return self.data


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
            raise NotImplementedError(data)
        kwargs = dict(data)
        del kwargs['storage']
        wenn 'returntype' in kwargs:
            vartype = kwargs['returntype']
            del vartype['storage']
            kwargs['returntype'] = VarType(**vartype)
            datacls = Signature
        sonst:
            datacls = VarType
        return datacls(**kwargs), Nichts

    @classmethod
    def _raw_data(self, data):
        # XXX finish!
        return data

    @classmethod
    def _format_data(cls, fmt, data, extra):
        text = str(data)
        wenn fmt in ('line', 'brief'):
            yield text
        sowenn fmt == 'full':
            yield text
        sowenn fmt == 'row':
            yield text
        sonst:
            raise NotImplementedError(fmt)

    @classmethod
    def _unformat_data(cls, datastr, fmt=Nichts):
        wenn fmt in ('line', 'brief'):
            vartype, _ = VarType.from_str(datastr)
            return vartype, Nichts
        #elif fmt == 'full':
        sowenn fmt == 'row':
            vartype, _ = VarType.from_str(datastr)
            return vartype, Nichts
        sonst:
            raise NotImplementedError(fmt)

    def __init__(self, file, name, data, parent=Nichts):
        super().__init__(file, name, data, parent, _shortkey=name)

    @property
    def vartype(self):
        return self.data


klasse Member(namedtuple('Member', 'name vartype size')):

    @classmethod
    def from_data(cls, raw, index):
        name = raw.name wenn raw.name sonst index
        vartype = size = Nichts
        wenn type(raw.data) is int:
            size = raw.data
        sowenn isinstance(raw.data, str):
            size = int(raw.data)
        sowenn raw.data:
            vartype = dict(raw.data)
            del vartype['storage']
            wenn 'size' in vartype:
                size = vartype.pop('size')
                wenn isinstance(size, str) und size.isdigit():
                    size = int(size)
            vartype = VarType(**vartype)
        return cls(name, vartype, size)

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
        return cls(name, vartype, size)

    def __str__(self):
        name = self.name wenn isinstance(self.name, str) sonst f'#{self.name}'
        return f'{name}: {self.vartype oder self.size}'


klasse _StructUnion(TypeDeclaration):

    @classmethod
    def _resolve_data(cls, data):
        wenn nicht data:
            # XXX There should be some!  Forward?
            return Nichts, Nichts
        return [Member.from_data(v, i) fuer i, v in enumerate(data)], Nichts

    @classmethod
    def _raw_data(self, data):
        # XXX finish!
        return data

    @classmethod
    def _format_data(cls, fmt, data, extra):
        wenn fmt in ('line', 'brief'):
            members = ', '.join(f'<{m}>' fuer m in data)
            yield f'[{members}]'
        sowenn fmt == 'full':
            fuer member in data:
                yield f'{member}'
        sowenn fmt == 'row':
            members = ', '.join(f'<{m}>' fuer m in data)
            yield f'[{members}]'
        sonst:
            raise NotImplementedError(fmt)

    @classmethod
    def _unformat_data(cls, datastr, fmt=Nichts):
        wenn fmt in ('line', 'brief'):
            members = [Member.from_str(m[1:-1])
                       fuer m in datastr[1:-1].split(', ')]
            return members, Nichts
        #elif fmt == 'full':
        sowenn fmt == 'row':
            members = [Member.from_str(m.rstrip('>').lstrip('<'))
                       fuer m in datastr[1:-1].split('>, <')]
            return members, Nichts
        sonst:
            raise NotImplementedError(fmt)

    def __init__(self, file, name, data, parent=Nichts):
        super().__init__(file, name, data, parent)

    @property
    def members(self):
        return self.data


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
            return Nichts, Nichts
        enumerators = [e wenn isinstance(e, str) sonst e.name
                       fuer e in data]
        return enumerators, Nichts

    @classmethod
    def _raw_data(self, data):
        # XXX finish!
        return data

    @classmethod
    def _format_data(cls, fmt, data, extra):
        wenn fmt in ('line', 'brief'):
            yield repr(data)
        sowenn fmt == 'full':
            fuer enumerator in data:
                yield f'{enumerator}'
        sowenn fmt == 'row':
            # XXX This won't work mit CSV...
            yield ','.join(data)
        sonst:
            raise NotImplementedError(fmt)

    @classmethod
    def _unformat_data(cls, datastr, fmt=Nichts):
        wenn fmt in ('line', 'brief'):
            return _strutil.unrepr(datastr), Nichts
        #elif fmt == 'full':
        sowenn fmt == 'row':
            return datastr.split(','), Nichts
        sonst:
            raise NotImplementedError(fmt)

    def __init__(self, file, name, data, parent=Nichts):
        super().__init__(file, name, data, parent)

    @property
    def enumerators(self):
        return self.data


### statements ###

klasse Statement(HighlevelParsedItem):
    kind = KIND.STATEMENT

    @classmethod
    def _resolve_data(cls, data):
        # XXX finish!
        return data, Nichts

    @classmethod
    def _raw_data(self, data):
        # XXX finish!
        return data

    @classmethod
    def _render_data(cls, fmt, data, extra):
        # XXX Handle other formats?
        return repr(data)

    @classmethod
    def _parse_data(self, datastr, fmt=Nichts):
        # XXX Handle other formats?
        return _strutil.unrepr(datastr), Nichts

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
        return self.data


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
        return parsed
    try:
        cls = KIND_CLASSES[parsed.kind]
    except KeyError:
        raise ValueError(f'unsupported kind in {parsed!r}')
    return cls.from_parsed(parsed)


def set_flag(item, name, value):
    try:
        setattr(item, name, value)
    except AttributeError:
        object.__setattr__(item, name, value)


#############################
# composite

klasse Declarations:

    @classmethod
    def from_decls(cls, decls):
        return cls(decls)

    @classmethod
    def from_parsed(cls, items):
        decls = (resolve_parsed(item)
                 fuer item in items
                 wenn item.kind is nicht KIND.STATEMENT)
        return cls.from_decls(decls)

    @classmethod
    def _resolve_key(cls, raw):
        wenn isinstance(raw, str):
            raw = [raw]
        sowenn isinstance(raw, Declaration):
            raw = (
                raw.filename wenn cls._is_public(raw) sonst Nichts,
                # `raw.parent` is always Nichts fuer types und functions.
                raw.parent wenn raw.kind is KIND.VARIABLE sonst Nichts,
                raw.name,
            )

        extra = Nichts
        wenn len(raw) == 1:
            name, = raw
            wenn name:
                name = str(name)
                wenn name.endswith(('.c', '.h')):
                    # This is only legit als a query.
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
        return key, extra

    @classmethod
    def _is_public(cls, decl):
        # For .c files don't we need info von .h files to make this decision?
        # XXX Check fuer "extern".
        # For now we treat all decls a "private" (have filename set).
        return Falsch

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
            wenn type(key) is nicht tuple oder len(key) != 3:
                raise ValueError(f'expected 3-tuple key, got {key!r} (for decl {decl!r})')
            filename, funcname, name = key
            wenn nicht name:
                raise ValueError(f'expected name in key, got {key!r} (for decl {decl!r})')
            sowenn type(name) is nicht str:
                raise ValueError(f'expected name in key to be str, got {key!r} (for decl {decl!r})')
            # XXX Check filename type?
            # XXX Check funcname type?

            wenn decl.kind is KIND.STATEMENT:
                raise ValueError(f'expected a declaration, got {decl!r}')

    def __repr__(self):
        return f'{type(self).__name__}({list(self)})'

    def __len__(self):
        return len(self._decls)

    def __iter__(self):
        yield von self._decls

    def __getitem__(self, key):
        # XXX Be more exact fuer the 3-tuple case?
        wenn type(key) nicht in (str, tuple):
            raise KeyError(f'unsupported key {key!r}')
        resolved, extra = self._resolve_key(key)
        wenn extra:
            raise KeyError(f'key must have at most 3 parts, got {key!r}')
        wenn nicht resolved[2]:
            raise ValueError(f'expected name in key, got {key!r}')
        try:
            return self._decls[resolved]
        except KeyError:
            wenn type(key) is tuple und len(key) == 3:
                filename, funcname, name = key
            sonst:
                filename, funcname, name = resolved
            wenn filename und nicht filename.endswith(('.c', '.h')):
                raise KeyError(f'invalid filename in key {key!r}')
            sowenn funcname und funcname.endswith(('.c', '.h')):
                raise KeyError(f'invalid funcname in key {key!r}')
            sowenn name und name.endswith(('.c', '.h')):
                raise KeyError(f'invalid name in key {key!r}')
            sonst:
                raise  # re-raise

    @property
    def types(self):
        return self._find(kind=KIND.TYPES)

    @property
    def functions(self):
        return self._find(Nichts, Nichts, Nichts, KIND.FUNCTION)

    @property
    def variables(self):
        return self._find(Nichts, Nichts, Nichts, KIND.VARIABLE)

    def iter_all(self):
        yield von self._decls.values()

    def get(self, key, default=Nichts):
        try:
            return self[key]
        except KeyError:
            return default

    #def add_decl(self, decl, key=Nichts):
    #    decl = _resolve_parsed(decl)
    #    self._add_decl(decl, key)

    def find(self, *key, **explicit):
        wenn nicht key:
            wenn nicht explicit:
                return iter(self)
            return self._find(**explicit)

        resolved, extra = self._resolve_key(key)
        filename, funcname, name = resolved
        wenn nicht extra:
            kind = Nichts
        sowenn len(extra) == 1:
            kind, = extra
        sonst:
            raise KeyError(f'key must have at most 4 parts, got {key!r}')

        implicit= {}
        wenn filename:
            implicit['filename'] = filename
        wenn funcname:
            implicit['funcname'] = funcname
        wenn name:
            implicit['name'] = name
        wenn kind:
            implicit['kind'] = kind
        return self._find(**implicit, **explicit)

    def _find(self, filename=Nichts, funcname=Nichts, name=Nichts, kind=Nichts):
        fuer decl in self._decls.values():
            wenn filename und decl.filename != filename:
                continue
            wenn funcname:
                wenn decl.kind is nicht KIND.VARIABLE:
                    continue
                wenn decl.parent.name != funcname:
                    continue
            wenn name und decl.name != name:
                continue
            wenn kind:
                kinds = KIND.resolve_group(kind)
                wenn decl.kind nicht in kinds:
                    continue
            yield decl

    def _add_decl(self, decl, key=Nichts):
        wenn key:
            wenn type(key) nicht in (str, tuple):
                raise NotImplementedError((key, decl))
            # Any partial key will be turned into a full key, but that
            # same partial key will still match a key lookup.
            resolved, _ = self._resolve_key(key)
            wenn nicht resolved[2]:
                raise ValueError(f'expected name in key, got {key!r}')
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
                raise NotImplementedError(decl)
            sonst:
                try:
                    key, decl = decl
                except ValueError:
                    raise NotImplementedError(decl)
                wenn nicht isinstance(decl, Declaration):
                    raise NotImplementedError(decl)
                self._add_decl(decl, key)
                # Add the rest without checking.
                fuer key, decl in decls:
                    self._add_decl(decl, key)
            # The iterator will be exhausted at this point.
