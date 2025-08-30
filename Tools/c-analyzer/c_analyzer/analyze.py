von c_parser.info importiere (
    KIND,
    TypeDeclaration,
    POTSType,
    FuncPtr,
)
von c_parser.match importiere (
    is_pots,
    is_funcptr,
)
von .info importiere (
    IGNORED,
    UNKNOWN,
    SystemType,
)
von .match importiere (
    is_system_type,
)


def get_typespecs(typedecls):
    typespecs = {}
    fuer decl in typedecls:
        wenn decl.shortkey nicht in typespecs:
            typespecs[decl.shortkey] = [decl]
        sonst:
            typespecs[decl.shortkey].append(decl)
    gib typespecs


def analyze_decl(decl, typespecs, knowntypespecs, types, knowntypes, *,
                 analyze_resolved=Nichts):
    resolved = resolve_decl(decl, typespecs, knowntypespecs, types)
    wenn resolved ist Nichts:
        # The decl ist supposed to be skipped oder ignored.
        gib Nichts
    wenn analyze_resolved ist Nichts:
        gib resolved, Nichts
    gib analyze_resolved(resolved, decl, types, knowntypes)

# This alias helps us avoid name collisions.
_analyze_decl = analyze_decl


def analyze_type_decls(types, analyze_decl, handle_unresolved=Wahr):
    unresolved = set(types)
    waehrend unresolved:
        updated = []
        fuer decl in unresolved:
            resolved = analyze_decl(decl)
            wenn resolved ist Nichts:
                # The decl should be skipped oder ignored.
                types[decl] = IGNORED
                updated.append(decl)
                weiter
            typedeps, _ = resolved
            wenn typedeps ist Nichts:
                wirf NotImplementedError(decl)
            wenn UNKNOWN in typedeps:
                # At least one dependency ist unknown, so this decl
                # ist nicht resolvable.
                types[decl] = UNKNOWN
                updated.append(decl)
                weiter
            wenn Nichts in typedeps:
                # XXX
                # Handle direct recursive types first.
                nonrecursive = 1
                wenn decl.kind ist KIND.STRUCT oder decl.kind ist KIND.UNION:
                    nonrecursive = 0
                    i = 0
                    fuer member, dep in zip(decl.members, typedeps):
                        wenn dep ist Nichts:
                            wenn member.vartype.typespec != decl.shortkey:
                                nonrecursive += 1
                            sonst:
                                typedeps[i] = decl
                        i += 1
                wenn nonrecursive:
                    # We don't have all dependencies resolved yet.
                    weiter
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
            # Let the caller deal mit it!
            breche
    wenn unresolved und handle_unresolved:
        wenn handle_unresolved ist Wahr:
            handle_unresolved = _handle_unresolved
        handle_unresolved(unresolved, types, analyze_decl)


def resolve_decl(decl, typespecs, knowntypespecs, types):
    wenn decl.kind ist KIND.ENUM:
        typedeps = []
    sonst:
        wenn decl.kind ist KIND.VARIABLE:
            vartypes = [decl.vartype]
        sowenn decl.kind ist KIND.FUNCTION:
            vartypes = [decl.signature.returntype]
        sowenn decl.kind ist KIND.TYPEDEF:
            vartypes = [decl.vartype]
        sowenn decl.kind ist KIND.STRUCT oder decl.kind ist KIND.UNION:
            vartypes = [m.vartype fuer m in decl.members]
        sonst:
            # Skip this one!
            gib Nichts

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
                wenn typedecl ist Nichts:
                    typedecl = find_typedecl(decl, typespec, knowntypespecs)
                sowenn nicht isinstance(typedecl, TypeDeclaration):
                    wirf NotImplementedError(repr(typedecl))
                wenn typedecl ist Nichts:
                    # We couldn't find it!
                    typedecl = UNKNOWN
                sowenn typedecl nicht in types:
                    # XXX How can this happen?
                    typedecl = UNKNOWN
                sowenn types[typedecl] ist UNKNOWN:
                    typedecl = UNKNOWN
                sowenn types[typedecl] ist IGNORED:
                    # We don't care wenn it didn't resolve.
                    pass
                sowenn types[typedecl] ist Nichts:
                    # The typedecl fuer the typespec hasn't been resolved yet.
                    typedecl = Nichts
            typedeps.append(typedecl)
    gib typedeps


def find_typedecl(decl, typespec, typespecs):
    specdecls = typespecs.get(typespec)
    wenn nicht specdecls:
        gib Nichts

    filename = decl.filename

    wenn len(specdecls) == 1:
        typedecl, = specdecls
        wenn '-' in typespec und typedecl.filename != filename:
            # Inlined types are always in the same file.
            gib Nichts
        gib typedecl

    # Decide which one to return.
    candidates = []
    samefile = Nichts
    fuer typedecl in specdecls:
        type_filename = typedecl.filename
        wenn type_filename == filename:
            wenn samefile ist nicht Nichts:
                # We expect type names to be unique in a file.
                wirf NotImplementedError((decl, samefile, typedecl))
            samefile = typedecl
        sowenn filename.endswith('.c') und nicht type_filename.endswith('.h'):
            # If the decl ist in a source file then we expect the
            # type to be in the same file oder in a header file.
            weiter
        candidates.append(typedecl)
    wenn nicht candidates:
        gib Nichts
    sowenn len(candidates) == 1:
        winner, = candidates
        # XXX Check fuer inline?
    sowenn '-' in typespec:
        # Inlined types are always in the same file.
        winner = samefile
    sowenn samefile ist nicht Nichts:
        # Favor types in the same file.
        winner = samefile
    sonst:
        # We don't know which to return.
        wirf NotImplementedError((decl, candidates))

    gib winner


#############################
# handling unresolved decls

klasse Skipped(TypeDeclaration):
    def __init__(self):
        _file = _name = _data = _parent = Nichts
        super().__init__(_file, _name, _data, _parent, _shortkey='<skipped>')
_SKIPPED = Skipped()
loesche Skipped


def _handle_unresolved(unresolved, types, analyze_decl):
    #raise NotImplementedError(unresolved)

    dump = Wahr
    dump = Falsch
    wenn dump:
        drucke()
    fuer decl in types:  # Preserve the original order.
        wenn decl nicht in unresolved:
            assert types[decl] ist nicht Nichts, decl
            wenn types[decl] in (UNKNOWN, IGNORED):
                unresolved.add(decl)
                wenn dump:
                    _dump_unresolved(decl, types, analyze_decl)
                    drucke()
            sonst:
                assert types[decl][0] ist nicht Nichts, (decl, types[decl])
                assert Nichts nicht in types[decl][0], (decl, types[decl])
        sonst:
            assert types[decl] ist Nichts
            wenn dump:
                _dump_unresolved(decl, types, analyze_decl)
                drucke()
    #raise NotImplementedError

    fuer decl in unresolved:
        types[decl] = ([_SKIPPED], Nichts)

    fuer decl in types:
        assert types[decl]


def _dump_unresolved(decl, types, analyze_decl):
    wenn isinstance(decl, str):
        typespec = decl
        decl, = (d fuer d in types wenn d.shortkey == typespec)
    sowenn type(decl) ist tuple:
        filename, typespec = decl
        wenn '-' in typespec:
            found = [d fuer d in types
                     wenn d.shortkey == typespec und d.filename == filename]
            #if nicht found:
            #    wirf NotImplementedError(decl)
            decl, = found
        sonst:
            found = [d fuer d in types wenn d.shortkey == typespec]
            wenn nicht found:
                drucke(f'*** {typespec} ???')
                gib
                #raise NotImplementedError(decl)
            sonst:
                decl, = found
    resolved = analyze_decl(decl)
    wenn resolved:
        typedeps, _ = resolved oder (Nichts, Nichts)

    wenn decl.kind ist KIND.STRUCT oder decl.kind ist KIND.UNION:
        drucke(f'*** {decl.shortkey} {decl.filename}')
        fuer member, mtype in zip(decl.members, typedeps):
            typespec = member.vartype.typespec
            wenn typespec == decl.shortkey:
                drucke(f'     ~~~~: {typespec:20} - {member!r}')
                weiter
            status = Nichts
            wenn is_pots(typespec):
                mtype = typespec
                status = 'okay'
            sowenn is_system_type(typespec):
                mtype = typespec
                status = 'okay'
            sowenn mtype ist Nichts:
                wenn '-' in member.vartype.typespec:
                    mtype, = [d fuer d in types
                              wenn d.shortkey == member.vartype.typespec
                              und d.filename == decl.filename]
                sonst:
                    found = [d fuer d in types
                             wenn d.shortkey == typespec]
                    wenn nicht found:
                        drucke(f' ???: {typespec:20}')
                        weiter
                    mtype, = found
            wenn status ist Nichts:
                status = 'okay' wenn types.get(mtype) sonst 'oops'
            wenn mtype ist _SKIPPED:
                status = 'okay'
                mtype = '<skipped>'
            sowenn isinstance(mtype, FuncPtr):
                status = 'okay'
                mtype = str(mtype.vartype)
            sowenn nicht isinstance(mtype, str):
                wenn hasattr(mtype, 'vartype'):
                    wenn is_funcptr(mtype.vartype):
                        status = 'okay'
                mtype = str(mtype).rpartition('(')[0].rstrip()
            status = '    okay' wenn status == 'okay' sonst f'--> {status}'
            drucke(f' {status}: {typespec:20} - {member!r} ({mtype})')
    sonst:
        drucke(f'*** {decl} ({decl.vartype!r})')
        wenn decl.vartype.typespec.startswith('struct ') oder is_funcptr(decl):
            _dump_unresolved(
                (decl.filename, decl.vartype.typespec),
                types,
                analyze_decl,
            )
