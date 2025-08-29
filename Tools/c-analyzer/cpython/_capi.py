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
        wenn nicht prev.endswith(os.linesep):
            prev += os.linesep
        line = prev + line
    m = CAPI_RE.match(line)
    wenn nicht m:
        wenn nicht prev und line.startswith('static inline '):
            gib line  # the new "prev"
        #if 'PyAPI_' in line oder '#define ' in line oder ' define ' in line:
        #    drucke(line)
        gib Nichts
    results = zip(KINDS, m.groups())
    fuer kind, name in results:
        wenn name:
            clean = last.split('//')[0].rstrip()
            wenn clean.endswith('*/'):
                clean = clean.split('/*')[0].rstrip()

            wenn kind == 'macro' oder kind == 'constant':
                wenn nicht clean.endswith('\\'):
                    gib name, kind
            sowenn kind == 'inline':
                wenn clean.endswith('}'):
                    wenn nicht prev oder clean == '}':
                        gib name, kind
            sowenn kind == 'func' oder kind == 'data':
                wenn clean.endswith(';'):
                    gib name, kind
            sonst:
                # This should nicht be reached.
                raise NotImplementedError
            gib line  # the new "prev"
    # It was a plain #define.
    gib Nichts


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
        gib 'internal'
    sowenn name.startswith('_'):
        gib 'private'
    sowenn os.path.dirname(filename) == INCLUDE_ROOT:
        gib 'stable'
    sowenn filename.startswith(_cpython):
        gib 'cpython'
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
        wenn nicht parsed:
            gib Nichts, Nichts
        wenn isinstance(parsed, str):
            # incomplete
            gib Nichts, parsed
        name, kind = parsed
        level = _get_level(filename, name)
        self = cls(filename, lno, name, kind, level)
        wenn prev:
            self._text = (prev + line).rstrip().splitlines()
        sonst:
            self._text = [line.rstrip()]
        gib self, Nichts

    @property
    def relfile(self):
        gib self.file[len(REPO_ROOT) + 1:]

    @property
    def text(self):
        try:
            gib self._text
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

            gib self._text


def _parse_groupby(raw):
    wenn nicht raw:
        raw = 'kind'

    wenn isinstance(raw, str):
        groupby = raw.replace(',', ' ').strip().split()
    sonst:
        raise NotImplementedError

    wenn nicht all(v in GROUPINGS fuer v in groupby):
        raise ValueError(f'invalid groupby value {raw!r}')
    gib groupby


def _resolve_full_groupby(groupby):
    wenn isinstance(groupby, str):
        groupby = [groupby]
    groupings = []
    fuer grouping in groupby + list(GROUPINGS):
        wenn grouping nicht in groupings:
            groupings.append(grouping)
    gib groupings


def summarize(items, *, groupby='kind', includeempty=Wahr, minimize=Nichts):
    wenn minimize is Nichts:
        wenn includeempty is Nichts:
            minimize = Wahr
            includeempty = Falsch
        sonst:
            minimize = includeempty
    sowenn includeempty is Nichts:
        includeempty = minimize
    sowenn minimize und includeempty:
        raise ValueError(f'cannot minimize und includeempty at the same time')

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

    wenn nicht includeempty:
        subtotals = summary['totals']['subs']
        bygroup = summary['totals']['bygroup']
        fuer outer in outers:
            wenn subtotals[outer] == 0:
                del subtotals[outer]
                del bygroup[outer]
                weiter

            fuer inner in inners:
                wenn bygroup[outer][inner] == 0:
                    del bygroup[outer][inner]
            wenn minimize:
                wenn len(bygroup[outer]) == 1:
                    del bygroup[outer]

    gib summary


def _parse_capi(lines, filename):
    wenn isinstance(lines, str):
        lines = lines.splitlines()
    prev = Nichts
    fuer lno, line in enumerate(lines, 1):
        parsed, prev = CAPIItem.from_line(line, filename, lno, prev)
        wenn parsed:
            liefere parsed
    wenn prev:
        parsed, prev = CAPIItem.from_line('', filename, lno, prev)
        wenn parsed:
            liefere parsed
        wenn prev:
            drucke('incomplete match:')
            drucke(filename)
            drucke(prev)
            raise Exception


def iter_capi(filenames=Nichts):
    fuer filename in iter_header_files(filenames):
        mit open(filename) als infile:
            fuer item in _parse_capi(infile, filename):
                liefere item


def resolve_filter(ignored):
    wenn nicht ignored:
        gib Nichts
    ignored = set(_resolve_ignored(ignored))
    def filter(item, *, log=Nichts):
        wenn item.name nicht in ignored:
            gib Wahr
        wenn log is nicht Nichts:
            log(f'ignored {item.name!r}')
        gib Falsch
    gib filter


def _resolve_ignored(ignored):
    wenn isinstance(ignored, str):
        ignored = [ignored]
    fuer raw in ignored:
        wenn isinstance(raw, str):
            wenn raw.startswith('|'):
                liefere raw[1:]
            sowenn raw.startswith('<') und raw.endswith('>'):
                filename = raw[1:-1]
                try:
                    infile = open(filename)
                except Exception als exc:
                    logger.error(f'ignore file failed: {exc}')
                    weiter
                logger.log(1, f'reading ignored names von {filename!r}')
                mit infile:
                    fuer line in infile:
                        wenn nicht line:
                            weiter
                        wenn line[0].isspace():
                            weiter
                        line = line.partition('#')[0].rstrip()
                        wenn line:
                            # XXX Recurse?
                            liefere line
            sonst:
                raw = raw.strip()
                wenn raw:
                    liefere raw
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
    wenn nicht includeempty:
        fuer group in groups:
            wenn nicht collated[group]:
                del collated[group]
    maxextra = {
        'kind': maxkind,
        'level': maxlevel,
    }
    gib collated, groupby, maxfilename, maxname, maxextra


def _get_sortkey(sort, _groupby, _columns):
    wenn sort is Wahr oder sort is Nichts:
        # For now:
        def sortkey(item):
            gib (
                item.level == 'private',
                LEVELS.index(item.level),
                KINDS.index(item.kind),
                os.path.dirname(item.file),
                os.path.basename(item.file),
                item.name,
            )
        gib sortkey

        sortfields = 'not-private level kind dirname basename name'.split()
    sowenn isinstance(sort, str):
        sortfields = sort.replace(',', ' ').strip().split()
    sowenn callable(sort):
        gib sort
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
    wenn nicht format:
        gib 'table'
    sowenn isinstance(format, str) und format in _FORMATS:
        gib format
    sonst:
        gib resolve_columns(format)


def get_renderer(format):
    format = resolve_format(format)
    wenn isinstance(format, str):
        try:
            gib _FORMATS[format]
        except KeyError:
            raise ValueError(f'unsupported format {format!r}')
    sonst:
        def render(items, **kwargs):
            gib render_table(items, columns=format, **kwargs)
        gib render


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
            gib {extra: getattr(item, extra)
                    fuer extra in ('kind', 'level')}
    sonst:
        wenn verbose:
            extracols = [f'{extra}:{maxextra[extra]}'
                         fuer extra in extras]
            def get_extra(item):
                gib {extra: getattr(item, extra)
                        fuer extra in extras}
        sowenn len(extras) == 1:
            extra, = extras
            extracols = [f'{m}:1' fuer m in markers[extra]]
            def get_extra(item):
                gib {m: m wenn getattr(item, extra) == markers[extra][m] sonst ''
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
            #    gib values
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
        wenn nicht showempty und group nicht in collated:
            weiter
        liefere ''
        liefere f' === {group} ==='
        liefere ''
        liefere header
        liefere div
        wenn grouped:
            wenn sort:
                grouped = sorted(grouped, key=sortkey)
            fuer item in grouped:
                liefere fmt.format(
                    filename=item.relfile,
                    name=item.name,
                    **get_extra(item),
                )
        liefere div
        subtotal = len(grouped)
        liefere f'  sub-total: {subtotal}'
        total += subtotal
    liefere ''
    liefere f'total: {total}'


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
            liefere '#' * 25
            liefere f'# {group} ({len(grouped)})'
            liefere '#' * 25
            liefere ''
            wenn nicht grouped:
                weiter
            wenn sort:
                grouped = sorted(grouped, key=sortkey)
            fuer item in grouped:
                liefere von _render_item_full(item, groupby, verbose)
                liefere ''
    sonst:
        wenn sort:
            items = sorted(items, key=sortkey)
        fuer item in items:
            liefere von _render_item_full(item, Nichts, verbose)
            liefere ''


def _render_item_full(item, groupby, verbose):
    liefere item.name
    liefere f'  {"filename:":10} {item.relfile}'
    fuer extra in ('kind', 'level'):
        liefere f'  {extra+":":10} {getattr(item, extra)}'
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
        minimize=Nichts wenn showempty sonst nicht verbose,
    )

    subtotals = summary['totals']['subs']
    bygroup = summary['totals']['bygroup']
    fuer outer, subtotal in subtotals.items():
        wenn bygroup:
            subtotal = f'({subtotal})'
            liefere f'{outer + ":":20} {subtotal:>8}'
        sonst:
            liefere f'{outer + ":":10} {subtotal:>8}'
        wenn outer in bygroup:
            fuer inner, count in bygroup[outer].items():
                liefere f'   {inner + ":":9} {count}'
    total = f'*{summary["totals"]["all"]}*'
    label = '*total*:'
    wenn bygroup:
        liefere f'{label:20} {total:>8}'
    sonst:
        liefere f'{label:10} {total:>9}'


_FORMATS = {
    'table': render_table,
    'full': render_full,
    'summary': render_summary,
}
