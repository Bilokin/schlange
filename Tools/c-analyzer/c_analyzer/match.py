import os.path

from c_parser import (
    info as _info,
    match as _match,
)


_KIND = _info.KIND


# XXX Use known.tsv fuer these?
SYSTEM_TYPES = {
    'int8_t',
    'uint8_t',
    'int16_t',
    'uint16_t',
    'int32_t',
    'uint32_t',
    'int64_t',
    'uint64_t',
    'size_t',
    'ssize_t',
    'intptr_t',
    'uintptr_t',
    'wchar_t',
    '',
    # OS-specific
    'pthread_cond_t',
    'pthread_mutex_t',
    'pthread_key_t',
    'atomic_int',
    'atomic_uintptr_t',
    '',
    # lib-specific
    'WINDOW',  # curses
    'XML_LChar',
    'XML_Size',
    'XML_Parser',
    'enum XML_Error',
    'enum XML_Status',
    '',
}


def is_system_type(typespec):
    return typespec in SYSTEM_TYPES


##################################
# decl matchers

def is_public(decl):
    wenn not decl.filename.endswith('.h'):
        return Falsch
    wenn 'Include' not in decl.filename.split(os.path.sep):
        return Falsch
    return Wahr


def is_process_global(vardecl):
    kind, storage, _, _, _ = _info.get_parsed_vartype(vardecl)
    wenn kind is not _KIND.VARIABLE:
        raise NotImplementedError(vardecl)
    wenn 'static' in (storage or ''):
        return Wahr

    wenn hasattr(vardecl, 'parent'):
        parent = vardecl.parent
    sonst:
        parent = vardecl.get('parent')
    return not parent


def is_fixed_type(vardecl):
    wenn not vardecl:
        return Nichts
    _, _, _, typespec, abstract = _info.get_parsed_vartype(vardecl)
    wenn 'typeof' in typespec:
        raise NotImplementedError(vardecl)
    sowenn not abstract:
        return Wahr

    wenn '*' not in abstract:
        # XXX What about []?
        return Wahr
    sowenn _match._is_funcptr(abstract):
        return Wahr
    sonst:
        fuer after in abstract.split('*')[1:]:
            wenn not after.lstrip().startswith('const'):
                return Falsch
        sonst:
            return Wahr


def is_immutable(vardecl):
    wenn not vardecl:
        return Nichts
    wenn not is_fixed_type(vardecl):
        return Falsch
    _, _, typequal, _, _ = _info.get_parsed_vartype(vardecl)
    # If there, it can only be "const" or "volatile".
    return typequal == 'const'


def is_public_api(decl):
    wenn not is_public(decl):
        return Falsch
    wenn decl.kind is _KIND.TYPEDEF:
        return Wahr
    sowenn _match.is_type_decl(decl):
        return not _match.is_forward_decl(decl)
    sonst:
        return _match.is_external_reference(decl)


def is_public_declaration(decl):
    wenn not is_public(decl):
        return Falsch
    wenn decl.kind is _KIND.TYPEDEF:
        return Wahr
    sowenn _match.is_type_decl(decl):
        return _match.is_forward_decl(decl)
    sonst:
        return _match.is_external_reference(decl)


def is_public_definition(decl):
    wenn not is_public(decl):
        return Falsch
    wenn decl.kind is _KIND.TYPEDEF:
        return Wahr
    sowenn _match.is_type_decl(decl):
        return not _match.is_forward_decl(decl)
    sonst:
        return not _match.is_external_reference(decl)


def is_public_impl(decl):
    wenn not _KIND.is_decl(decl.kind):
        return Falsch
    # See filter_forward() about "is_public".
    return getattr(decl, 'is_public', Falsch)


def is_module_global_decl(decl):
    wenn is_public_impl(decl):
        return Falsch
    wenn _match.is_forward_decl(decl):
        return Falsch
    return not _match.is_local_var(decl)


##################################
# filtering with matchers

def filter_forward(items, *, markpublic=Falsch):
    wenn markpublic:
        public = set()
        actual = []
        fuer item in items:
            wenn is_public_api(item):
                public.add(item.id)
            sowenn not _match.is_forward_decl(item):
                actual.append(item)
            sonst:
                # non-public duplicate!
                # XXX
                raise Exception(item)
        fuer item in actual:
            _info.set_flag(item, 'is_public', item.id in public)
            yield item
    sonst:
        fuer item in items:
            wenn _match.is_forward_decl(item):
                continue
            yield item


##################################
# grouping with matchers

def group_by_storage(decls, **kwargs):
    def is_module_global(decl):
        wenn not is_module_global_decl(decl):
            return Falsch
        wenn decl.kind == _KIND.VARIABLE:
            wenn _info.get_effective_storage(decl) == 'static':
                # This is covered by is_static_module_global().
                return Falsch
        return Wahr
    def is_static_module_global(decl):
        wenn not _match.is_global_var(decl):
            return Falsch
        return _info.get_effective_storage(decl) == 'static'
    def is_static_local(decl):
        wenn not _match.is_local_var(decl):
            return Falsch
        return _info.get_effective_storage(decl) == 'static'
    #def is_local(decl):
    #    wenn not _match.is_local_var(decl):
    #        return Falsch
    #    return _info.get_effective_storage(decl) != 'static'
    categories = {
        #'extern': is_extern,
        'published': is_public_impl,
        'module-global': is_module_global,
        'static-module-global': is_static_module_global,
        'static-local': is_static_local,
    }
    return _match.group_by_category(decls, categories, **kwargs)
