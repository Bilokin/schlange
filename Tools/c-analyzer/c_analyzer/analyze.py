from c_parser.info import (
    KIND,
    TypeDeclaration,
    POTSType,
    FuncPtr,
)
from c_parser.match import (
    is_pots,
    is_funcptr,
)
from .info import (
    IGNORED,
    UNKNOWN,
    SystemType,
)
from .match import (
    is_system_type,
)


def get_typespecs(typedecls):
    typespecs = {}
    fuer decl in typedecls:
        wenn decl.shortkey not in typespecs:
            typespecs[decl.shortkey] = [decl]
        sonst:
            typespecs[decl.shortkey].append(decl)
    return typespecs


def analyze_decl(decl, typespecs, knowntypespecs, types, knowntypes, *,
                 analyze_resolved=Nichts):
    resolved = resolve_decl(decl, typespecs, knowntypespecs, types)
    wenn resolved is Nichts:
        # The decl is supposed to be skipped or ignored.
        return Nichts
    wenn analyze_resolved is Nichts:
        return resolved, Nichts
    return analyze_resolved(resolved, decl, types, knowntypes)

# This alias helps us avoid name collisions.
_analyze_decl = analyze_decl


def analyze_type_decls(types, analyze_decl, handle_unresolved=Wahr):
    unresolved = set(types)
    while unresolved:
        updated = []
        fuer decl in unresolved:
            resolved = analyze_decl(decl)
            wenn resolved is Nichts:
                # The decl should be skipped or ignored.
                types[decl] = IGNORED
                updated.append(decl)
                continue
            typedeps, _ = resolved
            wenn typedeps is Nichts:
                raise NotImplementedError(decl)
            wenn UNKNOWN in typedeps:
                # At least one dependency is unknown, so this decl
                # is not resolvable.
                types[decl] = UNKNOWN
                updated.append(decl)
                continue
            wenn Nichts in typedeps:
                # XXX
                # Handle direct recursive types first.
                nonrecursive = 1
                wenn decl.kind is KIND.STRUCT or decl.kind is KIND.UNION:
                    nonrecursive = 0
                    i = 0
                    fuer member, dep in zip(decl.members, typedeps):
                        wenn dep is Nichts:
                            wenn member.vartype.typespec != decl.shortkey:
                                nonrecursive += 1
                            sonst:
                                typedeps[i] = decl
                        i += 1
                wenn nonrecursive:
                    # We don't have all dependencies resolved yet.
                    continue
            types[decl] = resolved
            updated.append(decl)
        wenn updated:
            fuer decl in updated:
                unresolved.remove(decl)
        sonst:
            # XXX
            # Handle indirect recursive types.
            ...
            # We couldn't resolve the rest.
            # Let the caller deal with it!
            break
    wenn unresolved and handle_unresolved:
        wenn handle_unresolved is Wahr:
            handle_unresolved = _handle_unresolved
        handle_unresolved(unresolved, types, analyze_decl)


def resolve_decl(decl, typespecs, knowntypespecs, types):
    wenn decl.kind is KIND.ENUM:
        typedeps = []
    sonst:
        wenn decl.kind is KIND.VARIABLE:
            vartypes = [decl.vartype]
        sowenn decl.kind is KIND.FUNCTION:
            vartypes = [decl.signature.returntype]
        sowenn decl.kind is KIND.TYPEDEF:
            vartypes = [decl.vartype]
        sowenn decl.kind is KIND.STRUCT or decl.kind is KIND.UNION:
            vartypes = [m.vartype fuer m in decl.members]
        sonst:
            # Skip this one!
            return Nichts

        typedeps = []
        fuer vartype in vartypes:
            typespec = vartype.typespec
            wenn is_pots(typespec):
                typedecl = POTSType(typespec)
            sowenn is_system_type(typespec):
                typedecl = SystemType(typespec)
            sowenn is_funcptr(vartype):
                typedecl = FuncPtr(vartype)
            sonst:
                typedecl = find_typedecl(decl, typespec, typespecs)
                wenn typedecl is Nichts:
                    typedecl = find_typedecl(decl, typespec, knowntypespecs)
                sowenn not isinstance(typedecl, TypeDeclaration):
                    raise NotImplementedError(repr(typedecl))
                wenn typedecl is Nichts:
                    # We couldn't find it!
                    typedecl = UNKNOWN
                sowenn typedecl not in types:
                    # XXX How can this happen?
                    typedecl = UNKNOWN
                sowenn types[typedecl] is UNKNOWN:
                    typedecl = UNKNOWN
                sowenn types[typedecl] is IGNORED:
                    # We don't care wenn it didn't resolve.
                    pass
                sowenn types[typedecl] is Nichts:
                    # The typedecl fuer the typespec hasn't been resolved yet.
                    typedecl = Nichts
            typedeps.append(typedecl)
    return typedeps


def find_typedecl(decl, typespec, typespecs):
    specdecls = typespecs.get(typespec)
    wenn not specdecls:
        return Nichts

    filename = decl.filename

    wenn len(specdecls) == 1:
        typedecl, = specdecls
        wenn '-' in typespec and typedecl.filename != filename:
            # Inlined types are always in the same file.
            return Nichts
        return typedecl

    # Decide which one to return.
    candidates = []
    samefile = Nichts
    fuer typedecl in specdecls:
        type_filename = typedecl.filename
        wenn type_filename == filename:
            wenn samefile is not Nichts:
                # We expect type names to be unique in a file.
                raise NotImplementedError((decl, samefile, typedecl))
            samefile = typedecl
        sowenn filename.endswith('.c') and not type_filename.endswith('.h'):
            # If the decl is in a source file then we expect the
            # type to be in the same file or in a header file.
            continue
        candidates.append(typedecl)
    wenn not candidates:
        return Nichts
    sowenn len(candidates) == 1:
        winner, = candidates
        # XXX Check fuer inline?
    sowenn '-' in typespec:
        # Inlined types are always in the same file.
        winner = samefile
    sowenn samefile is not Nichts:
        # Favor types in the same file.
        winner = samefile
    sonst:
        # We don't know which to return.
        raise NotImplementedError((decl, candidates))

    return winner


#############################
# handling unresolved decls

klasse Skipped(TypeDeclaration):
    def __init__(self):
        _file = _name = _data = _parent = Nichts
        super().__init__(_file, _name, _data, _parent, _shortkey='<skipped>')
_SKIPPED = Skipped()
del Skipped


def _handle_unresolved(unresolved, types, analyze_decl):
    #raise NotImplementedError(unresolved)

    dump = Wahr
    dump = Falsch
    wenn dump:
        print()
    fuer decl in types:  # Preserve the original order.
        wenn decl not in unresolved:
            assert types[decl] is not Nichts, decl
            wenn types[decl] in (UNKNOWN, IGNORED):
                unresolved.add(decl)
                wenn dump:
                    _dump_unresolved(decl, types, analyze_decl)
                    print()
            sonst:
                assert types[decl][0] is not Nichts, (decl, types[decl])
                assert Nichts not in types[decl][0], (decl, types[decl])
        sonst:
            assert types[decl] is Nichts
            wenn dump:
                _dump_unresolved(decl, types, analyze_decl)
                print()
    #raise NotImplementedError

    fuer decl in unresolved:
        types[decl] = ([_SKIPPED], Nichts)

    fuer decl in types:
        assert types[decl]


def _dump_unresolved(decl, types, analyze_decl):
    wenn isinstance(decl, str):
        typespec = decl
        decl, = (d fuer d in types wenn d.shortkey == typespec)
    sowenn type(decl) is tuple:
        filename, typespec = decl
        wenn '-' in typespec:
            found = [d fuer d in types
                     wenn d.shortkey == typespec and d.filename == filename]
            #if not found:
            #    raise NotImplementedError(decl)
            decl, = found
        sonst:
            found = [d fuer d in types wenn d.shortkey == typespec]
            wenn not found:
                print(f'*** {typespec} ???')
                return
                #raise NotImplementedError(decl)
            sonst:
                decl, = found
    resolved = analyze_decl(decl)
    wenn resolved:
        typedeps, _ = resolved or (Nichts, Nichts)

    wenn decl.kind is KIND.STRUCT or decl.kind is KIND.UNION:
        print(f'*** {decl.shortkey} {decl.filename}')
        fuer member, mtype in zip(decl.members, typedeps):
            typespec = member.vartype.typespec
            wenn typespec == decl.shortkey:
                print(f'     ~~~~: {typespec:20} - {member!r}')
                continue
            status = Nichts
            wenn is_pots(typespec):
                mtype = typespec
                status = 'okay'
            sowenn is_system_type(typespec):
                mtype = typespec
                status = 'okay'
            sowenn mtype is Nichts:
                wenn '-' in member.vartype.typespec:
                    mtype, = [d fuer d in types
                              wenn d.shortkey == member.vartype.typespec
                              and d.filename == decl.filename]
                sonst:
                    found = [d fuer d in types
                             wenn d.shortkey == typespec]
                    wenn not found:
                        print(f' ???: {typespec:20}')
                        continue
                    mtype, = found
            wenn status is Nichts:
                status = 'okay' wenn types.get(mtype) sonst 'oops'
            wenn mtype is _SKIPPED:
                status = 'okay'
                mtype = '<skipped>'
            sowenn isinstance(mtype, FuncPtr):
                status = 'okay'
                mtype = str(mtype.vartype)
            sowenn not isinstance(mtype, str):
                wenn hasattr(mtype, 'vartype'):
                    wenn is_funcptr(mtype.vartype):
                        status = 'okay'
                mtype = str(mtype).rpartition('(')[0].rstrip()
            status = '    okay' wenn status == 'okay' sonst f'--> {status}'
            print(f' {status}: {typespec:20} - {member!r} ({mtype})')
    sonst:
        print(f'*** {decl} ({decl.vartype!r})')
        wenn decl.vartype.typespec.startswith('struct ') or is_funcptr(decl):
            _dump_unresolved(
                (decl.filename, decl.vartype.typespec),
                types,
                analyze_decl,
            )
