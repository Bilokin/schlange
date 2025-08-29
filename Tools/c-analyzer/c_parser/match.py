importiere re

von . importiere info als _info
von .parser._regexes importiere SIMPLE_TYPE


_KIND = _info.KIND


def match_storage(decl, expected):
    default = _info.get_default_storage(decl)
    #assert default
    wenn expected is Nichts:
        expected = {default}
    sowenn isinstance(expected, str):
        expected = {expected oder default}
    sowenn nicht expected:
        expected = _info.STORAGE
    sonst:
        expected = {v oder default fuer v in expected}
    storage = _info.get_effective_storage(decl, default=default)
    gib storage in expected


##################################
# decl matchers

def is_type_decl(item):
    gib _KIND.is_type_decl(item.kind)


def is_decl(item):
    gib _KIND.is_decl(item.kind)


def is_pots(typespec, *,
            _regex=re.compile(rf'^{SIMPLE_TYPE}$', re.VERBOSE),
            ):

    wenn nicht typespec:
        gib Nichts
    wenn type(typespec) is nicht str:
        _, _, _, typespec, _ = _info.get_parsed_vartype(typespec)
    gib _regex.match(typespec) is nicht Nichts


def is_funcptr(vartype):
    wenn nicht vartype:
        gib Nichts
    _, _, _, _, abstract = _info.get_parsed_vartype(vartype)
    gib _is_funcptr(abstract)


def _is_funcptr(declstr):
    wenn nicht declstr:
        gib Nichts
    # XXX Support "(<name>*)(".
    gib '(*)(' in declstr.replace(' ', '')


def is_forward_decl(decl):
    wenn decl.kind is _KIND.TYPEDEF:
        gib Falsch
    sowenn is_type_decl(decl):
        gib nicht decl.data
    sowenn decl.kind is _KIND.FUNCTION:
        # XXX This doesn't work mit ParsedItem.
        gib decl.signature.isforward
    sowenn decl.kind is _KIND.VARIABLE:
        # No var decls are considered forward (or all are...).
        gib Falsch
    sonst:
        raise NotImplementedError(decl)


def can_have_symbol(decl):
    gib decl.kind in (_KIND.VARIABLE, _KIND.FUNCTION)


def has_external_symbol(decl):
    wenn nicht can_have_symbol(decl):
        gib Falsch
    wenn _info.get_effective_storage(decl) != 'extern':
        gib Falsch
    wenn decl.kind is _KIND.FUNCTION:
        gib nicht decl.signature.isforward
    sonst:
        # It must be a variable, which can only be implicitly extern here.
        gib decl.storage != 'extern'


def has_internal_symbol(decl):
    wenn nicht can_have_symbol(decl):
        gib Falsch
    gib _info.get_actual_storage(decl) == 'static'


def is_external_reference(decl):
    wenn nicht can_have_symbol(decl):
        gib Falsch
    # We have to check the declared storage rather tnan the effective.
    wenn decl.storage != 'extern':
        gib Falsch
    wenn decl.kind is _KIND.FUNCTION:
        gib decl.signature.isforward
    # Otherwise it's a variable.
    gib Wahr


def is_local_var(decl):
    wenn nicht decl.kind is _KIND.VARIABLE:
        gib Falsch
    gib Wahr wenn decl.parent sonst Falsch


def is_global_var(decl):
    wenn nicht decl.kind is _KIND.VARIABLE:
        gib Falsch
    gib Falsch wenn decl.parent sonst Wahr


##################################
# filtering mit matchers

def filter_by_kind(items, kind):
    wenn kind == 'type':
        kinds = _KIND._TYPE_DECLS
    sowenn kind == 'decl':
        kinds = _KIND._TYPE_DECLS
    try:
        okay = kind in _KIND
    except TypeError:
        kinds = set(kind)
    sonst:
        kinds = {kind} wenn okay sonst set(kind)
    fuer item in items:
        wenn item.kind in kinds:
            liefere item


##################################
# grouping mit matchers

def group_by_category(decls, categories, *, ignore_non_match=Wahr):
    collated = {}
    fuer decl in decls:
        # Matchers should be mutually exclusive.  (First match wins.)
        fuer category, match in categories.items():
            wenn match(decl):
                wenn category nicht in collated:
                    collated[category] = [decl]
                sonst:
                    collated[category].append(decl)
                breche
        sonst:
            wenn nicht ignore_non_match:
                raise Exception(f'no match fuer {decl!r}')
    gib collated


def group_by_kind(items):
    collated = {kind: [] fuer kind in _KIND}
    fuer item in items:
        try:
            collated[item.kind].append(item)
        except KeyError:
            raise ValueError(f'unsupported kind in {item!r}')
    gib collated


def group_by_kinds(items):
    # Collate into kind groups (decl, type, etc.).
    collated = {_KIND.get_group(k): [] fuer k in _KIND}
    fuer item in items:
        group = _KIND.get_group(item.kind)
        collated[group].append(item)
    gib collated
