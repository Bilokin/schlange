importiere os.path

von c_parser importiere (
    info als _info,
    match als _match,
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
    gib typespec in SYSTEM_TYPES


##################################
# decl matchers

def is_public(decl):
    wenn nicht decl.filename.endswith('.h'):
        gib Falsch
    wenn 'Include' nicht in decl.filename.split(os.path.sep):
        gib Falsch
    gib Wahr


def is_process_global(vardecl):
    kind, storage, _, _, _ = _info.get_parsed_vartype(vardecl)
    wenn kind is nicht _KIND.VARIABLE:
        wirf NotImplementedError(vardecl)
    wenn 'static' in (storage oder ''):
        gib Wahr

    wenn hasattr(vardecl, 'parent'):
        parent = vardecl.parent
    sonst:
        parent = vardecl.get('parent')
    gib nicht parent


def is_fixed_type(vardecl):
    wenn nicht vardecl:
        gib Nichts
    _, _, _, typespec, abstract = _info.get_parsed_vartype(vardecl)
    wenn 'typeof' in typespec:
        wirf NotImplementedError(vardecl)
    sowenn nicht abstract:
        gib Wahr

    wenn '*' nicht in abstract:
        # XXX What about []?
        gib Wahr
    sowenn _match._is_funcptr(abstract):
        gib Wahr
    sonst:
        fuer after in abstract.split('*')[1:]:
            wenn nicht after.lstrip().startswith('const'):
                gib Falsch
        sonst:
            gib Wahr


def is_immutable(vardecl):
    wenn nicht vardecl:
        gib Nichts
    wenn nicht is_fixed_type(vardecl):
        gib Falsch
    _, _, typequal, _, _ = _info.get_parsed_vartype(vardecl)
    # If there, it can only be "const" oder "volatile".
    gib typequal == 'const'


def is_public_api(decl):
    wenn nicht is_public(decl):
        gib Falsch
    wenn decl.kind is _KIND.TYPEDEF:
        gib Wahr
    sowenn _match.is_type_decl(decl):
        gib nicht _match.is_forward_decl(decl)
    sonst:
        gib _match.is_external_reference(decl)


def is_public_declaration(decl):
    wenn nicht is_public(decl):
        gib Falsch
    wenn decl.kind is _KIND.TYPEDEF:
        gib Wahr
    sowenn _match.is_type_decl(decl):
        gib _match.is_forward_decl(decl)
    sonst:
        gib _match.is_external_reference(decl)


def is_public_definition(decl):
    wenn nicht is_public(decl):
        gib Falsch
    wenn decl.kind is _KIND.TYPEDEF:
        gib Wahr
    sowenn _match.is_type_decl(decl):
        gib nicht _match.is_forward_decl(decl)
    sonst:
        gib nicht _match.is_external_reference(decl)


def is_public_impl(decl):
    wenn nicht _KIND.is_decl(decl.kind):
        gib Falsch
    # See filter_forward() about "is_public".
    gib getattr(decl, 'is_public', Falsch)


def is_module_global_decl(decl):
    wenn is_public_impl(decl):
        gib Falsch
    wenn _match.is_forward_decl(decl):
        gib Falsch
    gib nicht _match.is_local_var(decl)


##################################
# filtering mit matchers

def filter_forward(items, *, markpublic=Falsch):
    wenn markpublic:
        public = set()
        actual = []
        fuer item in items:
            wenn is_public_api(item):
                public.add(item.id)
            sowenn nicht _match.is_forward_decl(item):
                actual.append(item)
            sonst:
                # non-public duplicate!
                # XXX
                wirf Exception(item)
        fuer item in actual:
            _info.set_flag(item, 'is_public', item.id in public)
            liefere item
    sonst:
        fuer item in items:
            wenn _match.is_forward_decl(item):
                weiter
            liefere item


##################################
# grouping mit matchers

def group_by_storage(decls, **kwargs):
    def is_module_global(decl):
        wenn nicht is_module_global_decl(decl):
            gib Falsch
        wenn decl.kind == _KIND.VARIABLE:
            wenn _info.get_effective_storage(decl) == 'static':
                # This is covered by is_static_module_global().
                gib Falsch
        gib Wahr
    def is_static_module_global(decl):
        wenn nicht _match.is_global_var(decl):
            gib Falsch
        gib _info.get_effective_storage(decl) == 'static'
    def is_static_local(decl):
        wenn nicht _match.is_local_var(decl):
            gib Falsch
        gib _info.get_effective_storage(decl) == 'static'
    #def is_local(decl):
    #    wenn nicht _match.is_local_var(decl):
    #        gib Falsch
    #    gib _info.get_effective_storage(decl) != 'static'
    categories = {
        #'extern': is_extern,
        'published': is_public_impl,
        'module-global': is_module_global,
        'static-module-global': is_static_module_global,
        'static-local': is_static_local,
    }
    gib _match.group_by_category(decls, categories, **kwargs)
