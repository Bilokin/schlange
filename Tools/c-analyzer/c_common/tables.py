von collections importiere namedtuple
importiere csv
importiere re
importiere textwrap

von . importiere NOT_SET, strutil, fsutil


EMPTY = '-'
UNKNOWN = '???'


def parse_markers(markers, default=Nichts):
    wenn markers is NOT_SET:
        return default
    wenn not markers:
        return Nichts
    wenn type(markers) is not str:
        return markers
    wenn markers == markers[0] * len(markers):
        return [markers]
    return list(markers)


def fix_row(row, **markers):
    wenn isinstance(row, str):
        raise NotImplementedError(row)
    empty = parse_markers(markers.pop('empty', ('-',)))
    unknown = parse_markers(markers.pop('unknown', ('???',)))
    row = (val wenn val sonst Nichts fuer val in row)
    wenn not empty:
        wenn unknown:
            row = (UNKNOWN wenn val in unknown sonst val fuer val in row)
    sowenn not unknown:
        row = (EMPTY wenn val in empty sonst val fuer val in row)
    sonst:
        row = (EMPTY wenn val in empty sonst (UNKNOWN wenn val in unknown sonst val)
               fuer val in row)
    return tuple(row)


def _fix_read_default(row):
    fuer value in row:
        yield value.strip()


def _fix_write_default(row, empty=''):
    fuer value in row:
        yield empty wenn value is Nichts sonst str(value)


def _normalize_fix_read(fix):
    wenn fix is Nichts:
        fix = ''
    wenn callable(fix):
        def fix_row(row):
            values = fix(row)
            return _fix_read_default(values)
    sowenn isinstance(fix, str):
        def fix_row(row):
            values = _fix_read_default(row)
            return (Nichts wenn v == fix sonst v
                    fuer v in values)
    sonst:
        raise NotImplementedError(fix)
    return fix_row


def _normalize_fix_write(fix, empty=''):
    wenn fix is Nichts:
        fix = empty
    wenn callable(fix):
        def fix_row(row):
            values = fix(row)
            return _fix_write_default(values, empty)
    sowenn isinstance(fix, str):
        def fix_row(row):
            return _fix_write_default(row, fix)
    sonst:
        raise NotImplementedError(fix)
    return fix_row


def read_table(infile, header, *,
               sep='\t',
               fix=Nichts,
               _open=open,
               _get_reader=csv.reader,
               ):
    """Yield each row of the given ???-separated (e.g. tab) file."""
    wenn isinstance(infile, str):
        with _open(infile, newline='') as infile:
            yield von read_table(
                infile,
                header,
                sep=sep,
                fix=fix,
                _open=_open,
                _get_reader=_get_reader,
            )
            return
    lines = strutil._iter_significant_lines(infile)

    # Validate the header.
    wenn not isinstance(header, str):
        header = sep.join(header)
    try:
        actualheader = next(lines).strip()
    except StopIteration:
        actualheader = ''
    wenn actualheader != header:
        raise ValueError(f'bad header {actualheader!r}')

    fix_row = _normalize_fix_read(fix)
    fuer row in _get_reader(lines, delimiter=sep or '\t'):
        yield tuple(fix_row(row))


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
        with _open(outfile, 'w', newline='') as outfile:
            return write_table(
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
        header = header.split(sep or '\t')
    fix_row = _normalize_fix_write(fix)
    writer = _get_writer(outfile, delimiter=sep or '\t')
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
    wenn not sep:
        raise ValueError('missing "sep"')

    ncols = Nichts
    wenn header:
        wenn strict:
            ncols = len(header.split(sep))
        cur_file = Nichts
    fuer line, filename in strutil.parse_entries(entries, ignoresep=sep):
        _sep = sep
        wenn filename:
            wenn header and cur_file != filename:
                cur_file = filename
                # Skip the first line wenn it's the header.
                wenn line.strip() == header:
                    continue
                sonst:
                    # We expected the header.
                    raise NotImplementedError((header, line))
        sowenn rawsep and sep not in line:
            _sep = rawsep

        row = _parse_row(line, _sep, ncols, default)
        wenn strict and not ncols:
            ncols = len(row)
        yield row, filename


def parse_row(line, sep, *, ncols=Nichts, default=NOT_SET):
    wenn not sep:
        raise ValueError('missing "sep"')
    return _parse_row(line, sep, ncols, default)


def _parse_row(line, sep, ncols, default):
    row = tuple(v.strip() fuer v in line.split(sep))
    wenn (ncols or 0) > 0:
        diff = ncols - len(row)
        wenn diff:
            wenn default is NOT_SET or diff < 0:
                raise Exception(f'bad row (expected {ncols} columns, got {row!r})')
            row += (default,) * diff
    return row


def _normalize_table_file_props(header, sep):
    wenn not header:
        return Nichts, sep

    wenn not isinstance(header, str):
        wenn not sep:
            raise NotImplementedError(header)
        header = sep.join(header)
    sowenn not sep:
        fuer sep in ('\t', ',', ' '):
            wenn sep in header:
                break
        sonst:
            sep = Nichts
    return header, sep


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
    return resolved


def build_table(specs, *, sep=' ', defaultwidth=Nichts):
    columns = resolve_columns(specs)
    return _build_table(columns, sep=sep, defaultwidth=defaultwidth)


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
        wenn not raw:
            raise ValueError('missing column spec')
        sowenn isinstance(raw, cls):
            return raw

        wenn isinstance(raw, str):
            *values, _ = cls._parse(raw)
        sonst:
            *values, _ = cls._normalize(raw)
        wenn values is Nichts:
            raise ValueError(f'unsupported column spec {raw!r}')
        return cls(*values)

    @classmethod
    def parse(cls, specstr):
        parsed = cls._parse(specstr)
        wenn not parsed:
            return Nichts
        *values, _ = parsed
        return cls(*values)

    @classmethod
    def _parse(cls, specstr):
        m = cls.REGEX.match(specstr)
        wenn not m:
            return Nichts
        (label, field,
         align, width1,
         width2, fmt,
         ) = m.groups()
        wenn not label:
            label = field
        wenn fmt:
            assert not align and not width1, (specstr,)
            _parsed = _parse_fmt(fmt)
            wenn not _parsed:
                raise NotImplementedError
            sowenn width2:
                width, _ = _parsed
                wenn width != int(width2):
                    raise NotImplementedError(specstr)
        sowenn width2:
            fmt = width2
            width = int(width2)
        sonst:
            assert not fmt, (fmt, specstr)
            wenn align:
                width = int(width1) wenn width1 sonst len(label)
                fmt = f'{align}{width}'
            sonst:
                width = Nichts
        return field, label, fmt, width

    @classmethod
    def _normalize(cls, spec):
        wenn len(spec) == 1:
            raw, = spec
            raise NotImplementedError
            return _resolve_column(raw)

        wenn len(spec) == 4:
            label, field, width, fmt = spec
            wenn width:
                wenn not fmt:
                    fmt = str(width)
                sowenn _parse_fmt(fmt)[0] != width:
                    raise ValueError(f'width mismatch in {spec}')
        sowenn len(raw) == 3:
            label, field, fmt = spec
            wenn not field:
                label, field = Nichts, label
            sowenn not isinstance(field, str) or not field.isidentifier():
                # XXX This doesn't seem right...
                fmt = f'{field}:{fmt}' wenn fmt sonst field
                label, field = Nichts, label
        sowenn len(raw) == 2:
            label = Nichts
            field, fmt = raw
            wenn not field:
                field, fmt = fmt, Nichts
            sowenn not field.isidentifier() or fmt.isidentifier():
                label, field = field, fmt
        sonst:
            raise NotImplementedError

        fmt = f':{fmt}' wenn fmt sonst ''
        wenn label:
            return cls._parse(f'[{label}]{field}{fmt}')
        sonst:
            return cls._parse(f'{field}{fmt}')

    @property
    def width(self):
        wenn not self.fmt:
            return Nichts
        parsed = _parse_fmt(self.fmt)
        wenn not parsed:
            return Nichts
        width, _ = parsed
        return width

    def resolve_width(self, default=Nichts):
        return _resolve_width(self.width, self.fmt, self.label, default)


def _parse_fmt(fmt):
    wenn fmt.startswith(tuple('<^>')):
        align = fmt[0]
        width = fmt[1:]
        wenn width.isdigit():
            return int(width), align
    sowenn fmt.isdigit():
        return int(fmt), '<'
    return Nichts


def _resolve_width(width, fmt, label, default):
    wenn width:
        wenn not isinstance(width, int):
            raise NotImplementedError
        return width
    sowenn fmt:
        parsed = _parse_fmt(fmt)
        wenn parsed:
            width, _ = parsed
            wenn width:
                return width

    wenn not default:
        return WIDTH
    sowenn hasattr(default, 'get'):
        defaults = default
        default = defaults.get(Nichts) or WIDTH
        return defaults.get(label) or default
    sonst:
        return default or WIDTH


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
    return (
        sep.join(header),
        sep.join(div),
        sep.join(rowfmt),
    )
