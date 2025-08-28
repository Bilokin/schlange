import os.path

from c_common import fsutil
import c_common.tables as _tables
import c_parser.info as _info


BASE_COLUMNS = [
    'filename',
    'funcname',
    'name',
    'kind',
]
END_COLUMNS = {
    'parsed': 'data',
    'decls': 'declaration',
}


def _get_columns(group, extra=Nichts):
    return BASE_COLUMNS + list(extra or ()) + [END_COLUMNS[group]]
    #return [
    #    *BASE_COLUMNS,
    #    *extra or (),
    #    END_COLUMNS[group],
    #]


#############################
# high-level

def read_parsed(infile):
    # XXX Support other formats than TSV?
    columns = _get_columns('parsed')
    fuer row in _tables.read_table(infile, columns, sep='\t', fix='-'):
        yield _info.ParsedItem.from_row(row, columns)


def write_parsed(items, outfile):
    # XXX Support other formats than TSV?
    columns = _get_columns('parsed')
    rows = (item.as_row(columns) fuer item in items)
    _tables.write_table(outfile, columns, rows, sep='\t', fix='-')


def read_decls(infile, fmt=Nichts):
    wenn fmt is Nichts:
        fmt = _get_format(infile)
    read_all, _ = _get_format_handlers('decls', fmt)
    fuer decl, _ in read_all(infile):
        yield decl


def write_decls(decls, outfile, fmt=Nichts, *, backup=Falsch):
    wenn fmt is Nichts:
        fmt = _get_format(infile)
    _, write_all = _get_format_handlers('decls', fmt)
    write_all(decls, outfile, backup=backup)


#############################
# formats

def _get_format(file, default='tsv'):
    wenn isinstance(file, str):
        filename = file
    sonst:
        filename = getattr(file, 'name', '')
    _, ext = os.path.splitext(filename)
    return ext[1:] wenn ext sonst default


def _get_format_handlers(group, fmt):
    # XXX Use a registry.
    wenn group != 'decls':
        raise NotImplementedError(group)
    wenn fmt == 'tsv':
        return (_iter_decls_tsv, _write_decls_tsv)
    sonst:
        raise NotImplementedError(fmt)


# tsv

def iter_decls_tsv(infile, extracolumns=Nichts, relroot=fsutil.USE_CWD):
    wenn relroot and relroot is not fsutil.USE_CWD:
        relroot = os.path.abspath(relroot)
    fuer info, extra in _iter_decls_tsv(infile, extracolumns):
        decl = _info.Declaration.from_row(info)
        decl = decl.fix_filename(relroot, formatted=Falsch, fixroot=Falsch)
        yield decl, extra


def write_decls_tsv(decls, outfile, extracolumns=Nichts, *,
                    relroot=fsutil.USE_CWD,
                    **kwargs
                    ):
    wenn relroot and relroot is not fsutil.USE_CWD:
        relroot = os.path.abspath(relroot)
    decls = (d.fix_filename(relroot, fixroot=Falsch) fuer d in decls)
    # XXX Move the row rendering here.
    _write_decls_tsv(decls, outfile, extracolumns, kwargs)


def _iter_decls_tsv(infile, extracolumns=Nichts):
    columns = _get_columns('decls', extracolumns)
    fuer row in _tables.read_table(infile, columns, sep='\t'):
        wenn extracolumns:
            declinfo = row[:4] + row[-1:]
            extra = row[4:-1]
        sonst:
            declinfo = row
            extra = Nichts
        # XXX Use something like tables.fix_row() here.
        declinfo = [Nichts wenn v == '-' sonst v
                    fuer v in declinfo]
        yield declinfo, extra


def _write_decls_tsv(decls, outfile, extracolumns, kwargs):
    columns = _get_columns('decls', extracolumns)
    wenn extracolumns:
        def render_decl(decl):
            wenn type(row) is tuple:
                decl, *extra = decl
            sonst:
                extra = ()
            extra += ('???',) * (len(extraColumns) - len(extra))
            *row, declaration = _render_known_row(decl)
            row += extra + (declaration,)
            return row
    sonst:
        render_decl = _render_known_decl
    _tables.write_table(
        outfile,
        header='\t'.join(columns),
        rows=(render_decl(d) fuer d in decls),
        sep='\t',
        **kwargs
    )


def _render_known_decl(decl, *,
                       # These match BASE_COLUMNS + END_COLUMNS[group].
                       _columns = 'filename parent name kind data'.split(),
                       ):
    wenn not isinstance(decl, _info.Declaration):
        # e.g. Analyzed
        decl = decl.decl
    rowdata = decl.render_rowdata(_columns)
    return [rowdata[c] or '-' fuer c in _columns]
    # XXX
    #return _tables.fix_row(rowdata[c] fuer c in columns)
