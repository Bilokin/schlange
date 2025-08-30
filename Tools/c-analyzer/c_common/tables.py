von collections importiere namedtuple
importiere csv
importiere re
importiere textwrap

von . importiere NOT_SET, strutil, fsutil


EMPTY = '-'
UNKNOWN = '???'


def parse_markers(markers, default=Nichts):
    wenn markers ist NOT_SET:
        gib default
    wenn nicht markers:
        gib Nichts
    wenn type(markers) ist nicht str:
        gib markers
    wenn markers == markers[0] * len(markers):
        gib [markers]
    gib list(markers)


def fix_row(row, **markers):
    wenn isinstance(row, str):
        wirf NotImplementedError(row)
    empty = parse_markers(markers.pop('empty', ('-',)))
    unknown = parse_markers(markers.pop('unknown', ('???',)))
    row = (val wenn val sonst Nichts fuer val in row)
    wenn nicht empty:
        wenn unknown:
            row = (UNKNOWN wenn val in unknown sonst val fuer val in row)
    sowenn nicht unknown:
        row = (EMPTY wenn val in empty sonst val fuer val in row)
    sonst:
        row = (EMPTY wenn val in empty sonst (UNKNOWN wenn val in unknown sonst val)
               fuer val in row)
    gib tuple(row)


def _fix_read_default(row):
    fuer value in row:
        liefere value.strip()


def _fix_write_default(row, empty=''):
    fuer value in row:
        liefere empty wenn value ist Nichts sonst str(value)


def _normalize_fix_read(fix):
    wenn fix ist Nichts:
        fix = ''
    wenn callable(fix):
        def fix_row(row):
            values = fix(row)
            gib _fix_read_default(values)
    sowenn isinstance(fix, str):
        def fix_row(row):
            values = _fix_read_default(row)
            gib (Nichts wenn v == fix sonst v
                    fuer v in values)
    sonst:
        wirf NotImplementedError(fix)
    gib fix_row


def _normalize_fix_write(fix, empty=''):
    wenn fix ist Nichts:
        fix = empty
    wenn callable(fix):
        def fix_row(row):
            values = fix(row)
            gib _fix_write_default(values, empty)
    sowenn isinstance(fix, str):
        def fix_row(row):
            gib _fix_write_default(row, fix)
    sonst:
        wirf NotImplementedError(fix)
    gib fix_row


def read_table(infile, header, *,
               sep='\t',
               fix=Nichts,
               _open=open,
               _get_reader=csv.reader,
               ):
    """Yield each row of the given ???-separated (e.g. tab) file."""
    wenn isinstance(infile, str):
        mit _open(infile, newline='') als infile:
            liefere von read_table(
                infile,
                header,
                sep=sep,
                fix=fix,
                _open=_open,
                _get_reader=_get_reader,
            )
            gib
    lines = strutil._iter_significant_lines(infile)

    # Validate the header.
    wenn nicht isinstance(header, str):
        header = sep.join(header)
    versuch:
        actualheader = next(lines).strip()
    ausser StopIteration:
        actualheader = ''
    wenn actualheader != header:
        wirf ValueError(f'bad header {actualheader!r}')

    fix_row = _normalize_fix_read(fix)
    fuer row in _get_reader(lines, delimiter=sep oder '\t'):
        liefere tuple(fix_row(row))


def write_table(outfile, header, rows, *,
                sep='\t',
                fix=Nichts,
                backup=Wahr,
                _open=open,
                _get_writer=csv.writer,
                ):
    """Write each of the rows to the given ???-separated (e.g. tab) file."""
    wenn backup:
        fsutil.create_backup(outfile, backup)
    wenn isinstance(outfile, str):
        mit _open(outfile, 'w', newline='') als outfile:
            gib write_table(
                outfile,
                header,
                rows,
                sep=sep,
                fix=fix,
                backup=backup,
                _open=_open,
                _get_writer=_get_writer,
            )

    wenn isinstance(header, str):
        header = header.split(sep oder '\t')
    fix_row = _normalize_fix_write(fix)
    writer = _get_writer(outfile, delimiter=sep oder '\t')
    writer.writerow(header)
    fuer row in rows:
        writer.writerow(
            tuple(fix_row(row))
        )


def parse_table(entries, sep, header=Nichts, rawsep=Nichts, *,
                default=NOT_SET,
                strict=Wahr,
                ):
    header, sep = _normalize_table_file_props(header, sep)
    wenn nicht sep:
        wirf ValueError('missing "sep"')

    ncols = Nichts
    wenn header:
        wenn strict:
            ncols = len(header.split(sep))
        cur_file = Nichts
    fuer line, filename in strutil.parse_entries(entries, ignoresep=sep):
        _sep = sep
        wenn filename:
            wenn header und cur_file != filename:
                cur_file = filename
                # Skip the first line wenn it's the header.
                wenn line.strip() == header:
                    weiter
                sonst:
                    # We expected the header.
                    wirf NotImplementedError((header, line))
        sowenn rawsep und sep nicht in line:
            _sep = rawsep

        row = _parse_row(line, _sep, ncols, default)
        wenn strict und nicht ncols:
            ncols = len(row)
        liefere row, filename


def parse_row(line, sep, *, ncols=Nichts, default=NOT_SET):
    wenn nicht sep:
        wirf ValueError('missing "sep"')
    gib _parse_row(line, sep, ncols, default)


def _parse_row(line, sep, ncols, default):
    row = tuple(v.strip() fuer v in line.split(sep))
    wenn (ncols oder 0) > 0:
        diff = ncols - len(row)
        wenn diff:
            wenn default ist NOT_SET oder diff < 0:
                wirf Exception(f'bad row (expected {ncols} columns, got {row!r})')
            row += (default,) * diff
    gib row


def _normalize_table_file_props(header, sep):
    wenn nicht header:
        gib Nichts, sep

    wenn nicht isinstance(header, str):
        wenn nicht sep:
            wirf NotImplementedError(header)
        header = sep.join(header)
    sowenn nicht sep:
        fuer sep in ('\t', ',', ' '):
            wenn sep in header:
                breche
        sonst:
            sep = Nichts
    gib header, sep


##################################
# stdout tables

WIDTH = 20


def resolve_columns(specs):
    wenn isinstance(specs, str):
        specs = specs.replace(',', ' ').strip().split()
    resolved = []
    fuer raw in specs:
        column = ColumnSpec.from_raw(raw)
        resolved.append(column)
    gib resolved


def build_table(specs, *, sep=' ', defaultwidth=Nichts):
    columns = resolve_columns(specs)
    gib _build_table(columns, sep=sep, defaultwidth=defaultwidth)


klasse ColumnSpec(namedtuple('ColumnSpec', 'field label fmt')):

    REGEX = re.compile(textwrap.dedent(r'''
        ^
        (?:
            \[
            (
                (?: [^\s\]] [^\]]* )?
                [^\s\]]
            )  # <label>
            ]
        )?
        ( [-\w]+ )  # <field>
        (?:
            (?:
                :
                ( [<^>] )  # <align>
                ( \d+ )?  # <width1>
            )
            |
            (?:
                (?:
                    :
                    ( \d+ )  # <width2>
                )?
                (?:
                    :
                    ( .*? )  # <fmt>
                )?
            )
        )?
        $
    '''), re.VERBOSE)

    @classmethod
    def from_raw(cls, raw):
        wenn nicht raw:
            wirf ValueError('missing column spec')
        sowenn isinstance(raw, cls):
            gib raw

        wenn isinstance(raw, str):
            *values, _ = cls._parse(raw)
        sonst:
            *values, _ = cls._normalize(raw)
        wenn values ist Nichts:
            wirf ValueError(f'unsupported column spec {raw!r}')
        gib cls(*values)

    @classmethod
    def parse(cls, specstr):
        parsed = cls._parse(specstr)
        wenn nicht parsed:
            gib Nichts
        *values, _ = parsed
        gib cls(*values)

    @classmethod
    def _parse(cls, specstr):
        m = cls.REGEX.match(specstr)
        wenn nicht m:
            gib Nichts
        (label, field,
         align, width1,
         width2, fmt,
         ) = m.groups()
        wenn nicht label:
            label = field
        wenn fmt:
            assert nicht align und nicht width1, (specstr,)
            _parsed = _parse_fmt(fmt)
            wenn nicht _parsed:
                wirf NotImplementedError
            sowenn width2:
                width, _ = _parsed
                wenn width != int(width2):
                    wirf NotImplementedError(specstr)
        sowenn width2:
            fmt = width2
            width = int(width2)
        sonst:
            assert nicht fmt, (fmt, specstr)
            wenn align:
                width = int(width1) wenn width1 sonst len(label)
                fmt = f'{align}{width}'
            sonst:
                width = Nichts
        gib field, label, fmt, width

    @classmethod
    def _normalize(cls, spec):
        wenn len(spec) == 1:
            raw, = spec
            wirf NotImplementedError
            gib _resolve_column(raw)

        wenn len(spec) == 4:
            label, field, width, fmt = spec
            wenn width:
                wenn nicht fmt:
                    fmt = str(width)
                sowenn _parse_fmt(fmt)[0] != width:
                    wirf ValueError(f'width mismatch in {spec}')
        sowenn len(raw) == 3:
            label, field, fmt = spec
            wenn nicht field:
                label, field = Nichts, label
            sowenn nicht isinstance(field, str) oder nicht field.isidentifier():
                # XXX This doesn't seem right...
                fmt = f'{field}:{fmt}' wenn fmt sonst field
                label, field = Nichts, label
        sowenn len(raw) == 2:
            label = Nichts
            field, fmt = raw
            wenn nicht field:
                field, fmt = fmt, Nichts
            sowenn nicht field.isidentifier() oder fmt.isidentifier():
                label, field = field, fmt
        sonst:
            wirf NotImplementedError

        fmt = f':{fmt}' wenn fmt sonst ''
        wenn label:
            gib cls._parse(f'[{label}]{field}{fmt}')
        sonst:
            gib cls._parse(f'{field}{fmt}')

    @property
    def width(self):
        wenn nicht self.fmt:
            gib Nichts
        parsed = _parse_fmt(self.fmt)
        wenn nicht parsed:
            gib Nichts
        width, _ = parsed
        gib width

    def resolve_width(self, default=Nichts):
        gib _resolve_width(self.width, self.fmt, self.label, default)


def _parse_fmt(fmt):
    wenn fmt.startswith(tuple('<^>')):
        align = fmt[0]
        width = fmt[1:]
        wenn width.isdigit():
            gib int(width), align
    sowenn fmt.isdigit():
        gib int(fmt), '<'
    gib Nichts


def _resolve_width(width, fmt, label, default):
    wenn width:
        wenn nicht isinstance(width, int):
            wirf NotImplementedError
        gib width
    sowenn fmt:
        parsed = _parse_fmt(fmt)
        wenn parsed:
            width, _ = parsed
            wenn width:
                gib width

    wenn nicht default:
        gib WIDTH
    sowenn hasattr(default, 'get'):
        defaults = default
        default = defaults.get(Nichts) oder WIDTH
        gib defaults.get(label) oder default
    sonst:
        gib default oder WIDTH


def _build_table(columns, *, sep=' ', defaultwidth=Nichts):
    header = []
    div = []
    rowfmt = []
    fuer spec in columns:
        width = spec.resolve_width(defaultwidth)
        colfmt = spec.fmt
        colfmt = f':{spec.fmt}' wenn spec.fmt sonst f':{width}'

        header.append(f' {{:^{width}}} '.format(spec.label))
        div.append('-' * (width + 2))
        rowfmt.append(f' {{{spec.field}{colfmt}}} ')
    gib (
        sep.join(header),
        sep.join(div),
        sep.join(rowfmt),
    )
