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
    return storage in expected


##################################
# decl matchers

def is_type_decl(item):
    return _KIND.is_type_decl(item.kind)


def is_decl(item):
    return _KIND.is_decl(item.kind)


def is_pots(typespec, *,
            _regex=re.compile(rf'^{SIMPLE_TYPE}$', re.VERBOSE),
            ):

    wenn nicht typespec:
        return Nichts
    wenn type(typespec) is nicht str:
        _, _, _, typespec, _ = _info.get_parsed_vartype(typespec)
    return _regex.match(typespec) is nicht Nichts


def is_funcptr(vartype):
    wenn nicht vartype:
        return Nichts
    _, _, _, _, abstract = _info.get_parsed_vartype(vartype)
    return _is_funcptr(abstract)


def _is_funcptr(declstr):
    wenn nicht declstr:
        return Nichts
    # XXX Support "(<name>*)(".
    return '(*)(' in declstr.replace(' ', '')


def is_forward_decl(decl):
    wenn decl.kind is _KIND.TYPEDEF:
        return Falsch
    sowenn is_type_decl(decl):
        return nicht decl.data
    sowenn decl.kind is _KIND.FUNCTION:
        # XXX This doesn't work mit ParsedItem.
        return decl.signature.isforward
    sowenn decl.kind is _KIND.VARIABLE:
        # No var decls are considered forward (or all are...).
        return Falsch
    sonst:
        raise NotImplementedError(decl)


def can_have_symbol(decl):
    return decl.kind in (_KIND.VARIABLE, _KIND.FUNCTION)


def has_external_symbol(decl):
    wenn nicht can_have_symbol(decl):
        return Falsch
    wenn _info.get_effective_storage(decl) != 'extern':
        return Falsch
    wenn decl.kind is _KIND.FUNCTION:
        return nicht decl.signature.isforward
    sonst:
        # It must be a variable, which can only be implicitly extern here.
        return decl.storage != 'extern'


def has_internal_symbol(decl):
    wenn nicht can_have_symbol(decl):
        return Falsch
    return _info.get_actual_storage(decl) == 'static'


def is_external_reference(decl):
    wenn nicht can_have_symbol(decl):
        return Falsch
    # We have to check the declared storage rather tnan the effective.
    wenn decl.storage != 'extern':
        return Falsch
    wenn decl.kind is _KIND.FUNCTION:
        return decl.signature.isforward
    # Otherwise it's a variable.
    return Wahr


def is_local_var(decl):
    wenn nicht decl.kind is _KIND.VARIABLE:
        return Falsch
    return Wahr wenn decl.parent sonst Falsch


def is_global_var(decl):
    wenn nicht decl.kind is _KIND.VARIABLE:
        return Falsch
    return Falsch wenn decl.parent sonst Wahr


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
            yield item


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
    return collated


def group_by_kind(items):
    collated = {kind: [] fuer kind in _KIND}
    fuer item in items:
        try:
            collated[item.kind].append(item)
        except KeyError:
            raise ValueError(f'unsupported kind in {item!r}')
    return collated


def group_by_kinds(items):
    # Collate into kind groups (decl, type, etc.).
    collated = {_KIND.get_group(k): [] fuer k in _KIND}
    fuer item in items:
        group = _KIND.get_group(item.kind)
        collated[group].append(item)
    return collated
