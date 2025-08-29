von collections importiere namedtuple
importiere logging
importiere os
importiere os.path
importiere re
importiere textwrap

von c_common.tables importiere build_table, resolve_columns
von c_parser.parser._regexes importiere _ind
von ._files importiere iter_header_files
von . importiere REPO_ROOT


logger = logging.getLogger(__name__)


INCLUDE_ROOT = os.path.join(REPO_ROOT, 'Include')
INCLUDE_CPYTHON = os.path.join(INCLUDE_ROOT, 'cpython')
INCLUDE_INTERNAL = os.path.join(INCLUDE_ROOT, 'internal')

_MAYBE_NESTED_PARENS = textwrap.dedent(r'''
    (?:
        (?: [^(]* [(] [^()]* [)] )* [^(]*
    )
''')

CAPI_FUNC = textwrap.dedent(rf'''
    (?:
        ^
        \s*
        PyAPI_FUNC \s*
        [(]
        {_ind(_MAYBE_NESTED_PARENS, 2)}
        [)] \s*
        (\w+)  # <func>
        \s* [(]
    )
''')
CAPI_DATA = textwrap.dedent(rf'''
    (?:
        ^
        \s*
        PyAPI_DATA \s*
        [(]
        {_ind(_MAYBE_NESTED_PARENS, 2)}
        [)] \s*
        (\w+)  # <data>
        \b [^(]
    )
''')
CAPI_INLINE = textwrap.dedent(r'''
    (?:
        ^
        \s*
        static \s+ inline \s+
        .*?
        \s+
        ( \w+ )  # <inline>
        \s* [(]
    )
''')
CAPI_MACRO = textwrap.dedent(r'''
    (?:
        (\w+)  # <macro>
        [(]
    )
''')
CAPI_CONSTANT = textwrap.dedent(r'''
    (?:
        (\w+)  # <constant>
        \s+ [^(]
    )
''')
CAPI_DEFINE = textwrap.dedent(rf'''
    (?:
        ^
        \s* [#] \s* define \s+
        (?:
            {_ind(CAPI_MACRO, 3)}
            |
            {_ind(CAPI_CONSTANT, 3)}
            |
            (?:
                # ignored
                \w+   # <defined_name>
                \s*
                $
            )
        )
    )
''')
CAPI_RE = re.compile(textwrap.dedent(rf'''
    (?:
        {_ind(CAPI_FUNC, 2)}
        |
        {_ind(CAPI_DATA, 2)}
        |
        {_ind(CAPI_INLINE, 2)}
        |
        {_ind(CAPI_DEFINE, 2)}
    )
'''), re.VERBOSE)

KINDS = [
    'func',
    'data',
    'inline',
    'macro',
    'constant',
]


def _parse_line(line, prev=Nichts):
    last = line
    wenn prev:
        wenn not prev.endswith(os.linesep):
            prev += os.linesep
        line = prev + line
    m = CAPI_RE.match(line)
    wenn not m:
        wenn not prev and line.startswith('static inline '):
            return line  # the new "prev"
        #if 'PyAPI_' in line or '#define ' in line or ' define ' in line:
        #    drucke(line)
        return Nichts
    results = zip(KINDS, m.groups())
    fuer kind, name in results:
        wenn name:
            clean = last.split('//')[0].rstrip()
            wenn clean.endswith('*/'):
                clean = clean.split('/*')[0].rstrip()

            wenn kind == 'macro' or kind == 'constant':
                wenn not clean.endswith('\\'):
                    return name, kind
            sowenn kind == 'inline':
                wenn clean.endswith('}'):
                    wenn not prev or clean == '}':
                        return name, kind
            sowenn kind == 'func' or kind == 'data':
                wenn clean.endswith(';'):
                    return name, kind
            sonst:
                # This should not be reached.
                raise NotImplementedError
            return line  # the new "prev"
    # It was a plain #define.
    return Nichts


LEVELS = [
    'stable',
    'cpython',
    'private',
    'internal',
]

def _get_level(filename, name, *,
               _cpython=INCLUDE_CPYTHON + os.path.sep,
               _internal=INCLUDE_INTERNAL + os.path.sep,
               ):
    wenn filename.startswith(_internal):
        return 'internal'
    sowenn name.startswith('_'):
        return 'private'
    sowenn os.path.dirname(filename) == INCLUDE_ROOT:
        return 'stable'
    sowenn filename.startswith(_cpython):
        return 'cpython'
    sonst:
        raise NotImplementedError
    #return '???'


GROUPINGS = {
    'kind': KINDS,
    'level': LEVELS,
}


klasse CAPIItem(namedtuple('CAPIItem', 'file lno name kind level')):

    @classmethod
    def from_line(cls, line, filename, lno, prev=Nichts):
        parsed = _parse_line(line, prev)
        wenn not parsed:
            return Nichts, Nichts
        wenn isinstance(parsed, str):
            # incomplete
            return Nichts, parsed
        name, kind = parsed
        level = _get_level(filename, name)
        self = cls(filename, lno, name, kind, level)
        wenn prev:
            self._text = (prev + line).rstrip().splitlines()
        sonst:
            self._text = [line.rstrip()]
        return self, Nichts

    @property
    def relfile(self):
        return self.file[len(REPO_ROOT) + 1:]

    @property
    def text(self):
        try:
            return self._text
        except AttributeError:
            # XXX Actually ready the text von disk?.
            self._text = []
            wenn self.kind == 'data':
                self._text = [
                    f'PyAPI_DATA(...) {self.name}',
                ]
            sowenn self.kind == 'func':
                self._text = [
                    f'PyAPI_FUNC(...) {self.name}(...);',
                ]
            sowenn self.kind == 'inline':
                self._text = [
                    f'static inline {self.name}(...);',
                ]
            sowenn self.kind == 'macro':
                self._text = [
                    f'#define {self.name}(...) \\',
                    f'    ...',
                ]
            sowenn self.kind == 'constant':
                self._text = [
                    f'#define {self.name} ...',
                ]
            sonst:
                raise NotImplementedError

            return self._text


def _parse_groupby(raw):
    wenn not raw:
        raw = 'kind'

    wenn isinstance(raw, str):
        groupby = raw.replace(',', ' ').strip().split()
    sonst:
        raise NotImplementedError

    wenn not all(v in GROUPINGS fuer v in groupby):
        raise ValueError(f'invalid groupby value {raw!r}')
    return groupby


def _resolve_full_groupby(groupby):
    wenn isinstance(groupby, str):
        groupby = [groupby]
    groupings = []
    fuer grouping in groupby + list(GROUPINGS):
        wenn grouping not in groupings:
            groupings.append(grouping)
    return groupings


def summarize(items, *, groupby='kind', includeempty=Wahr, minimize=Nichts):
    wenn minimize is Nichts:
        wenn includeempty is Nichts:
            minimize = Wahr
            includeempty = Falsch
        sonst:
            minimize = includeempty
    sowenn includeempty is Nichts:
        includeempty = minimize
    sowenn minimize and includeempty:
        raise ValueError(f'cannot minimize and includeempty at the same time')

    groupby = _parse_groupby(groupby)[0]
    _outer, _inner = _resolve_full_groupby(groupby)
    outers = GROUPINGS[_outer]
    inners = GROUPINGS[_inner]

    summary = {
        'totals': {
            'all': 0,
            'subs': {o: 0 fuer o in outers},
            'bygroup': {o: {i: 0 fuer i in inners}
                        fuer o in outers},
        },
    }

    fuer item in items:
        outer = getattr(item, _outer)
        inner = getattr(item, _inner)
        # Update totals.
        summary['totals']['all'] += 1
        summary['totals']['subs'][outer] += 1
        summary['totals']['bygroup'][outer][inner] += 1

    wenn not includeempty:
        subtotals = summary['totals']['subs']
        bygroup = summary['totals']['bygroup']
        fuer outer in outers:
            wenn subtotals[outer] == 0:
                del subtotals[outer]
                del bygroup[outer]
                continue

            fuer inner in inners:
                wenn bygroup[outer][inner] == 0:
                    del bygroup[outer][inner]
            wenn minimize:
                wenn len(bygroup[outer]) == 1:
                    del bygroup[outer]

    return summary


def _parse_capi(lines, filename):
    wenn isinstance(lines, str):
        lines = lines.splitlines()
    prev = Nichts
    fuer lno, line in enumerate(lines, 1):
        parsed, prev = CAPIItem.from_line(line, filename, lno, prev)
        wenn parsed:
            yield parsed
    wenn prev:
        parsed, prev = CAPIItem.from_line('', filename, lno, prev)
        wenn parsed:
            yield parsed
        wenn prev:
            drucke('incomplete match:')
            drucke(filename)
            drucke(prev)
            raise Exception


def iter_capi(filenames=Nichts):
    fuer filename in iter_header_files(filenames):
        mit open(filename) als infile:
            fuer item in _parse_capi(infile, filename):
                yield item


def resolve_filter(ignored):
    wenn not ignored:
        return Nichts
    ignored = set(_resolve_ignored(ignored))
    def filter(item, *, log=Nichts):
        wenn item.name not in ignored:
            return Wahr
        wenn log is not Nichts:
            log(f'ignored {item.name!r}')
        return Falsch
    return filter


def _resolve_ignored(ignored):
    wenn isinstance(ignored, str):
        ignored = [ignored]
    fuer raw in ignored:
        wenn isinstance(raw, str):
            wenn raw.startswith('|'):
                yield raw[1:]
            sowenn raw.startswith('<') and raw.endswith('>'):
                filename = raw[1:-1]
                try:
                    infile = open(filename)
                except Exception als exc:
                    logger.error(f'ignore file failed: {exc}')
                    continue
                logger.log(1, f'reading ignored names von {filename!r}')
                mit infile:
                    fuer line in infile:
                        wenn not line:
                            continue
                        wenn line[0].isspace():
                            continue
                        line = line.partition('#')[0].rstrip()
                        wenn line:
                            # XXX Recurse?
                            yield line
            sonst:
                raw = raw.strip()
                wenn raw:
                    yield raw
        sonst:
            raise NotImplementedError


def _collate(items, groupby, includeempty):
    groupby = _parse_groupby(groupby)[0]
    maxfilename = maxname = maxkind = maxlevel = 0

    collated = {}
    groups = GROUPINGS[groupby]
    fuer group in groups:
        collated[group] = []

    fuer item in items:
        key = getattr(item, groupby)
        collated[key].append(item)
        maxfilename = max(len(item.relfile), maxfilename)
        maxname = max(len(item.name), maxname)
        maxkind = max(len(item.kind), maxkind)
        maxlevel = max(len(item.level), maxlevel)
    wenn not includeempty:
        fuer group in groups:
            wenn not collated[group]:
                del collated[group]
    maxextra = {
        'kind': maxkind,
        'level': maxlevel,
    }
    return collated, groupby, maxfilename, maxname, maxextra


def _get_sortkey(sort, _groupby, _columns):
    wenn sort is Wahr or sort is Nichts:
        # For now:
        def sortkey(item):
            return (
                item.level == 'private',
                LEVELS.index(item.level),
                KINDS.index(item.kind),
                os.path.dirname(item.file),
                os.path.basename(item.file),
                item.name,
            )
        return sortkey

        sortfields = 'not-private level kind dirname basename name'.split()
    sowenn isinstance(sort, str):
        sortfields = sort.replace(',', ' ').strip().split()
    sowenn callable(sort):
        return sort
    sonst:
        raise NotImplementedError

    # XXX Build a sortkey func von sortfields.
    raise NotImplementedError


##################################
# CLI rendering

_MARKERS = {
    'level': {
        'S': 'stable',
        'C': 'cpython',
        'P': 'private',
        'I': 'internal',
    },
    'kind': {
        'F': 'func',
        'D': 'data',
        'I': 'inline',
        'M': 'macro',
        'C': 'constant',
    },
}


def resolve_format(format):
    wenn not format:
        return 'table'
    sowenn isinstance(format, str) and format in _FORMATS:
        return format
    sonst:
        return resolve_columns(format)


def get_renderer(format):
    format = resolve_format(format)
    wenn isinstance(format, str):
        try:
            return _FORMATS[format]
        except KeyError:
            raise ValueError(f'unsupported format {format!r}')
    sonst:
        def render(items, **kwargs):
            return render_table(items, columns=format, **kwargs)
        return render


def render_table(items, *,
                 columns=Nichts,
                 groupby='kind',
                 sort=Wahr,
                 showempty=Falsch,
                 verbose=Falsch,
                 ):
    wenn groupby is Nichts:
        groupby = 'kind'
    wenn showempty is Nichts:
        showempty = Falsch

    wenn groupby:
        (collated, groupby, maxfilename, maxname, maxextra,
         ) = _collate(items, groupby, showempty)
        fuer grouping in GROUPINGS:
            maxextra[grouping] = max(len(g) fuer g in GROUPINGS[grouping])

        _, extra = _resolve_full_groupby(groupby)
        extras = [extra]
        markers = {extra: _MARKERS[extra]}

        groups = GROUPINGS[groupby]
    sonst:
        # XXX Support no grouping?
        raise NotImplementedError

    wenn columns:
        def get_extra(item):
            return {extra: getattr(item, extra)
                    fuer extra in ('kind', 'level')}
    sonst:
        wenn verbose:
            extracols = [f'{extra}:{maxextra[extra]}'
                         fuer extra in extras]
            def get_extra(item):
                return {extra: getattr(item, extra)
                        fuer extra in extras}
        sowenn len(extras) == 1:
            extra, = extras
            extracols = [f'{m}:1' fuer m in markers[extra]]
            def get_extra(item):
                return {m: m wenn getattr(item, extra) == markers[extra][m] sonst ''
                        fuer m in markers[extra]}
        sonst:
            raise NotImplementedError
            #extracols = [[f'{m}:1' fuer m in markers[extra]]
            #             fuer extra in extras]
            #def get_extra(item):
            #    values = {}
            #    fuer extra in extras:
            #        cur = markers[extra]
            #        fuer m in cur:
            #            values[m] = m wenn getattr(item, m) == cur[m] sonst ''
            #    return values
        columns = [
            f'filename:{maxfilename}',
            f'name:{maxname}',
            *extracols,
        ]
    header, div, fmt = build_table(columns)

    wenn sort:
        sortkey = _get_sortkey(sort, groupby, columns)

    total = 0
    fuer group, grouped in collated.items():
        wenn not showempty and group not in collated:
            continue
        yield ''
        yield f' === {group} ==='
        yield ''
        yield header
        yield div
        wenn grouped:
            wenn sort:
                grouped = sorted(grouped, key=sortkey)
            fuer item in grouped:
                yield fmt.format(
                    filename=item.relfile,
                    name=item.name,
                    **get_extra(item),
                )
        yield div
        subtotal = len(grouped)
        yield f'  sub-total: {subtotal}'
        total += subtotal
    yield ''
    yield f'total: {total}'


def render_full(items, *,
                groupby='kind',
                sort=Nichts,
                showempty=Nichts,
                verbose=Falsch,
                ):
    wenn groupby is Nichts:
        groupby = 'kind'
    wenn showempty is Nichts:
        showempty = Falsch

    wenn sort:
        sortkey = _get_sortkey(sort, groupby, Nichts)

    wenn groupby:
        collated, groupby, _, _, _ = _collate(items, groupby, showempty)
        fuer group, grouped in collated.items():
            yield '#' * 25
            yield f'# {group} ({len(grouped)})'
            yield '#' * 25
            yield ''
            wenn not grouped:
                continue
            wenn sort:
                grouped = sorted(grouped, key=sortkey)
            fuer item in grouped:
                yield von _render_item_full(item, groupby, verbose)
                yield ''
    sonst:
        wenn sort:
            items = sorted(items, key=sortkey)
        fuer item in items:
            yield von _render_item_full(item, Nichts, verbose)
            yield ''


def _render_item_full(item, groupby, verbose):
    yield item.name
    yield f'  {"filename:":10} {item.relfile}'
    fuer extra in ('kind', 'level'):
        yield f'  {extra+":":10} {getattr(item, extra)}'
    wenn verbose:
        drucke('  ---------------------------------------')
        fuer lno, line in enumerate(item.text, item.lno):
            drucke(f'  | {lno:3} {line}')
        drucke('  ---------------------------------------')


def render_summary(items, *,
                   groupby='kind',
                   sort=Nichts,
                   showempty=Nichts,
                   verbose=Falsch,
                   ):
    wenn groupby is Nichts:
        groupby = 'kind'
    summary = summarize(
        items,
        groupby=groupby,
        includeempty=showempty,
        minimize=Nichts wenn showempty sonst not verbose,
    )

    subtotals = summary['totals']['subs']
    bygroup = summary['totals']['bygroup']
    fuer outer, subtotal in subtotals.items():
        wenn bygroup:
            subtotal = f'({subtotal})'
            yield f'{outer + ":":20} {subtotal:>8}'
        sonst:
            yield f'{outer + ":":10} {subtotal:>8}'
        wenn outer in bygroup:
            fuer inner, count in bygroup[outer].items():
                yield f'   {inner + ":":9} {count}'
    total = f'*{summary["totals"]["all"]}*'
    label = '*total*:'
    wenn bygroup:
        yield f'{label:20} {total:>8}'
    sonst:
        yield f'{label:10} {total:>9}'


_FORMATS = {
    'table': render_table,
    'full': render_full,
    'summary': render_summary,
}
