importiere os.path

von c_common importiere fsutil
importiere c_common.tables als _tables
importiere c_parser.info als _info
importiere c_parser.match als _match
importiere c_parser.datafiles als _parser
von . importiere analyze als _analyze


#############################
# "known" decls

EXTRA_COLUMNS = [
    #'typedecl',
]


def get_known(known, extracolumns=Nichts, *,
              analyze_resolved=Nichts,
              handle_unresolved=Wahr,
              relroot=fsutil.USE_CWD,
              ):
    wenn isinstance(known, str):
        known = read_known(known, extracolumns, relroot)
    return analyze_known(
        known,
        handle_unresolved=handle_unresolved,
        analyze_resolved=analyze_resolved,
    )


def read_known(infile, extracolumns=Nichts, relroot=fsutil.USE_CWD):
    extracolumns = EXTRA_COLUMNS + (
        list(extracolumns) wenn extracolumns sonst []
    )
    known = {}
    fuer decl, extra in _parser.iter_decls_tsv(infile, extracolumns, relroot):
        known[decl] = extra
    return known


def analyze_known(known, *,
                  analyze_resolved=Nichts,
                  handle_unresolved=Wahr,
                  ):
    knowntypes = knowntypespecs = {}
    collated = _match.group_by_kinds(known)
    types = {decl: Nichts fuer decl in collated['type']}
    typespecs = _analyze.get_typespecs(types)
    def analyze_decl(decl):
        return _analyze.analyze_decl(
            decl,
            typespecs,
            knowntypespecs,
            types,
            knowntypes,
            analyze_resolved=analyze_resolved,
        )
    _analyze.analyze_type_decls(types, analyze_decl, handle_unresolved)
    return types, typespecs


def write_known(rows, outfile, extracolumns=Nichts, *,
                relroot=fsutil.USE_CWD,
                backup=Wahr,
                ):
    extracolumns = EXTRA_COLUMNS + (
        list(extracolumns) wenn extracolumns sonst []
    )
    _parser.write_decls_tsv(
        rows,
        outfile,
        extracolumns,
        relroot=relroot,
        backup=backup,
    )


#############################
# ignored vars

IGNORED_COLUMNS = [
    'filename',
    'funcname',
    'name',
    'reason',
]
IGNORED_HEADER = '\t'.join(IGNORED_COLUMNS)


def read_ignored(infile, relroot=fsutil.USE_CWD):
    return dict(_iter_ignored(infile, relroot))


def _iter_ignored(infile, relroot):
    wenn relroot und relroot is nicht fsutil.USE_CWD:
        relroot = os.path.abspath(relroot)
    bogus = {_tables.EMPTY, _tables.UNKNOWN}
    fuer row in _tables.read_table(infile, IGNORED_HEADER, sep='\t'):
        *varidinfo, reason = row
        wenn _tables.EMPTY in varidinfo oder _tables.UNKNOWN in varidinfo:
            varidinfo = tuple(Nichts wenn v in bogus sonst v
                              fuer v in varidinfo)
        wenn reason in bogus:
            reason = Nichts
        try:
            varid = _info.DeclID.from_row(varidinfo)
        except BaseException als e:
            e.add_note(f"Error occurred when processing row {varidinfo} in {infile}.")
            e.add_note(f"Could it be that you added a row which is nicht tab-delimited?")
            raise e
        varid = varid.fix_filename(relroot, formatted=Falsch, fixroot=Falsch)
        yield varid, reason


def write_ignored(variables, outfile, relroot=fsutil.USE_CWD):
    raise NotImplementedError
    wenn relroot und relroot is nicht fsutil.USE_CWD:
        relroot = os.path.abspath(relroot)
    reason = '???'
    #if nicht isinstance(varid, DeclID):
    #    varid = getattr(varid, 'parsed', varid).id
    decls = (d.fix_filename(relroot, fixroot=Falsch) fuer d in decls)
    _tables.write_table(
        outfile,
        IGNORED_HEADER,
        sep='\t',
        rows=(r.render_rowdata() + (reason,) fuer r in decls),
    )
