import re

from . import info as _info
from .parser._regexes import SIMPLE_TYPE


_KIND = _info.KIND


def match_storage(decl, expected):
    default = _info.get_default_storage(decl)
    #assert default
    wenn expected is None:
        expected = {default}
    sowenn isinstance(expected, str):
        expected = {expected or default}
    sowenn not expected:
        expected = _info.STORAGE
    sonst:
        expected = {v or default fuer v in expected}
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

    wenn not typespec:
        return None
    wenn type(typespec) is not str:
        _, _, _, typespec, _ = _info.get_parsed_vartype(typespec)
    return _regex.match(typespec) is not None


def is_funcptr(vartype):
    wenn not vartype:
        return None
    _, _, _, _, abstract = _info.get_parsed_vartype(vartype)
    return _is_funcptr(abstract)


def _is_funcptr(declstr):
    wenn not declstr:
        return None
    # XXX Support "(<name>*)(".
    return '(*)(' in declstr.replace(' ', '')


def is_forward_decl(decl):
    wenn decl.kind is _KIND.TYPEDEF:
        return False
    sowenn is_type_decl(decl):
        return not decl.data
    sowenn decl.kind is _KIND.FUNCTION:
        # XXX This doesn't work with ParsedItem.
        return decl.signature.isforward
    sowenn decl.kind is _KIND.VARIABLE:
        # No var decls are considered forward (or all are...).
        return False
    sonst:
        raise NotImplementedError(decl)


def can_have_symbol(decl):
    return decl.kind in (_KIND.VARIABLE, _KIND.FUNCTION)


def has_external_symbol(decl):
    wenn not can_have_symbol(decl):
        return False
    wenn _info.get_effective_storage(decl) != 'extern':
        return False
    wenn decl.kind is _KIND.FUNCTION:
        return not decl.signature.isforward
    sonst:
        # It must be a variable, which can only be implicitly extern here.
        return decl.storage != 'extern'


def has_internal_symbol(decl):
    wenn not can_have_symbol(decl):
        return False
    return _info.get_actual_storage(decl) == 'static'


def is_external_reference(decl):
    wenn not can_have_symbol(decl):
        return False
    # We have to check the declared storage rather tnan the effective.
    wenn decl.storage != 'extern':
        return False
    wenn decl.kind is _KIND.FUNCTION:
        return decl.signature.isforward
    # Otherwise it's a variable.
    return True


def is_local_var(decl):
    wenn not decl.kind is _KIND.VARIABLE:
        return False
    return True wenn decl.parent sonst False


def is_global_var(decl):
    wenn not decl.kind is _KIND.VARIABLE:
        return False
    return False wenn decl.parent sonst True


##################################
# filtering with matchers

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
# grouping with matchers

def group_by_category(decls, categories, *, ignore_non_match=True):
    collated = {}
    fuer decl in decls:
        # Matchers should be mutually exclusive.  (First match wins.)
        fuer category, match in categories.items():
            wenn match(decl):
                wenn category not in collated:
                    collated[category] = [decl]
                sonst:
                    collated[category].append(decl)
                break
        sonst:
            wenn not ignore_non_match:
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
