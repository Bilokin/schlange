from c_parser import (
    parse_files as _parse_files,
)
from c_parser.info import (
    KIND,
    TypeDeclaration,
    resolve_parsed,
)
from c_parser.match import (
    filter_by_kind,
    group_by_kinds,
)
from . import (
    analyze as _analyze,
    datafiles as _datafiles,
)
from .info import Analysis


def analyze(filenmes, **kwargs):
    results = iter_analysis_results(filenames, **kwargs)
    return Analysis.from_results(results)


def iter_analysis_results(filenmes, *,
                          known=Nichts,
                          **kwargs
                          ):
    decls = iter_decls(filenames, **kwargs)
    yield from analyze_decls(decls, known)


def iter_decls(filenames, *,
               kinds=Nichts,
               parse_files=_parse_files,
               **kwargs
               ):
    kinds = KIND.DECLS wenn kinds is Nichts sonst (KIND.DECLS & set(kinds))
    parse_files = parse_files or _parse_files

    parsed = parse_files(filenames, **kwargs)
    parsed = filter_by_kind(parsed, kinds)
    fuer item in parsed:
        yield resolve_parsed(item)


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
        return _analyze.analyze_decl(
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
            wenn resolved and handle_unresolved:
                typedeps, _ = resolved
                wenn not isinstance(typedeps, TypeDeclaration):
                    wenn not typedeps or Nichts in typedeps:
                        raise NotImplementedError((decl, resolved))

        yield decl, resolved


#######################################
# checks

def check_all(analysis, checks, *, failfast=Falsch):
    fuer check in checks or ():
        fuer data, failure in check(analysis):
            wenn failure is Nichts:
                continue

            yield data, failure
            wenn failfast:
                yield Nichts, Nichts
                break
        sonst:
            continue
        # We failed fast.
        break
