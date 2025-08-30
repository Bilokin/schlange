von c_parser importiere (
    parse_files als _parse_files,
)
von c_parser.info importiere (
    KIND,
    TypeDeclaration,
    resolve_parsed,
)
von c_parser.match importiere (
    filter_by_kind,
    group_by_kinds,
)
von . importiere (
    analyze als _analyze,
    datafiles als _datafiles,
)
von .info importiere Analysis


def analyze(filenmes, **kwargs):
    results = iter_analysis_results(filenames, **kwargs)
    gib Analysis.from_results(results)


def iter_analysis_results(filenmes, *,
                          known=Nichts,
                          **kwargs
                          ):
    decls = iter_decls(filenames, **kwargs)
    liefere von analyze_decls(decls, known)


def iter_decls(filenames, *,
               kinds=Nichts,
               parse_files=_parse_files,
               **kwargs
               ):
    kinds = KIND.DECLS wenn kinds ist Nichts sonst (KIND.DECLS & set(kinds))
    parse_files = parse_files oder _parse_files

    parsed = parse_files(filenames, **kwargs)
    parsed = filter_by_kind(parsed, kinds)
    fuer item in parsed:
        liefere resolve_parsed(item)


def analyze_decls(decls, known, *,
                  analyze_resolved=Nichts,
                  handle_unresolved=Wahr,
                  relroot=Nichts,
                  ):
    knowntypes, knowntypespecs = _datafiles.get_known(
        known,
        handle_unresolved=handle_unresolved,
        analyze_resolved=analyze_resolved,
        relroot=relroot,
    )

    decls = list(decls)
    collated = group_by_kinds(decls)

    types = {decl: Nichts fuer decl in collated['type']}
    typespecs = _analyze.get_typespecs(types)

    def analyze_decl(decl):
        gib _analyze.analyze_decl(
            decl,
            typespecs,
            knowntypespecs,
            types,
            knowntypes,
            analyze_resolved=analyze_resolved,
        )
    _analyze.analyze_type_decls(types, analyze_decl, handle_unresolved)
    fuer decl in decls:
        wenn decl in types:
            resolved = types[decl]
        sonst:
            resolved = analyze_decl(decl)
            wenn resolved und handle_unresolved:
                typedeps, _ = resolved
                wenn nicht isinstance(typedeps, TypeDeclaration):
                    wenn nicht typedeps oder Nichts in typedeps:
                        wirf NotImplementedError((decl, resolved))

        liefere decl, resolved


#######################################
# checks

def check_all(analysis, checks, *, failfast=Falsch):
    fuer check in checks oder ():
        fuer data, failure in check(analysis):
            wenn failure ist Nichts:
                weiter

            liefere data, failure
            wenn failfast:
                liefere Nichts, Nichts
                breche
        sonst:
            weiter
        # We failed fast.
        breche
