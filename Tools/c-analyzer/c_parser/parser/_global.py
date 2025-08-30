importiere re

von ._regexes importiere (
    GLOBAL als _GLOBAL,
)
von ._common importiere (
    log_match,
    parse_var_decl,
    set_capture_groups,
)
von ._compound_decl_body importiere DECL_BODY_PARSERS
von ._func_body importiere parse_function_statics als parse_function_body


GLOBAL = set_capture_groups(_GLOBAL, (
    'EMPTY',
    'COMPOUND_LEADING',
    'COMPOUND_KIND',
    'COMPOUND_NAME',
    'FORWARD_KIND',
    'FORWARD_NAME',
    'MAYBE_INLINE_ACTUAL',
    'TYPEDEF_DECL',
    'TYPEDEF_FUNC_PARAMS',
    'VAR_STORAGE',
    'FUNC_INLINE',
    'VAR_DECL',
    'FUNC_PARAMS',
    'FUNC_DELIM',
    'FUNC_LEGACY_PARAMS',
    'VAR_INIT',
    'VAR_ENDING',
))
GLOBAL_RE = re.compile(rf'^ \s* {GLOBAL}', re.VERBOSE)


def parse_globals(source, anon_name):
    fuer srcinfo in source:
        m = GLOBAL_RE.match(srcinfo.text)
        wenn nicht m:
            # We need more text.
            weiter
        fuer item in _parse_next(m, srcinfo, anon_name):
            wenn callable(item):
                parse_body = item
                liefere von parse_body(source)
            sonst:
                liefere item
    sonst:
        # We ran out of lines.
        wenn srcinfo is nicht Nichts:
            srcinfo.done()
        gib


def _parse_next(m, srcinfo, anon_name):
    (
     empty,
     # compound type decl (maybe inline)
     compound_leading, compound_kind, compound_name,
     forward_kind, forward_name, maybe_inline_actual,
     # typedef
     typedef_decl, typedef_func_params,
     # vars und funcs
     storage, func_inline, decl,
     func_params, func_delim, func_legacy_params,
     var_init, var_ending,
     ) = m.groups()
    remainder = srcinfo.text[m.end():]

    wenn empty:
        log_match('global empty', m)
        srcinfo.advance(remainder)

    sowenn maybe_inline_actual:
        log_match('maybe_inline_actual', m)
        # Ignore forward declarations.
        # XXX Maybe gib them too (with an "isforward" flag)?
        wenn nicht maybe_inline_actual.strip().endswith(';'):
            remainder = maybe_inline_actual + remainder
        liefere srcinfo.resolve(forward_kind, Nichts, forward_name)
        wenn maybe_inline_actual.strip().endswith('='):
            # We use a dummy prefix fuer a fake typedef.
            # XXX Ideally this case would nicht be caught by MAYBE_INLINE_ACTUAL.
            _, name, data = parse_var_decl(f'{forward_kind} {forward_name} fake_typedef_{forward_name}')
            liefere srcinfo.resolve('typedef', data, name, parent=Nichts)
            remainder = f'{name} {remainder}'
        srcinfo.advance(remainder)

    sowenn compound_kind:
        kind = compound_kind
        name = compound_name oder anon_name('inline-')
        # Immediately emit a forward declaration.
        liefere srcinfo.resolve(kind, name=name, data=Nichts)

        # un-inline the decl.  Note that it might nicht actually be inline.
        # We handle the case in the "maybe_inline_actual" branch.
        srcinfo.nest(
            remainder,
            f'{compound_leading oder ""} {compound_kind} {name}',
        )
        def parse_body(source):
            _parse_body = DECL_BODY_PARSERS[compound_kind]

            data = []  # members
            ident = f'{kind} {name}'
            fuer item in _parse_body(source, anon_name, ident):
                wenn item.kind == 'field':
                    data.append(item)
                sonst:
                    liefere item
            # XXX Should "parent" really be Nichts fuer inline type decls?
            liefere srcinfo.resolve(kind, data, name, parent=Nichts)

            srcinfo.resume()
        liefere parse_body

    sowenn typedef_decl:
        log_match('typedef', m)
        kind = 'typedef'
        _, name, data = parse_var_decl(typedef_decl)
        wenn typedef_func_params:
            return_type = data
            # This matches the data fuer func declarations.
            data = {
                'storage': Nichts,
                'inline': Nichts,
                'params': f'({typedef_func_params})',
                'returntype': return_type,
                'isforward': Wahr,
            }
        liefere srcinfo.resolve(kind, data, name, parent=Nichts)
        srcinfo.advance(remainder)

    sowenn func_delim oder func_legacy_params:
        log_match('function', m)
        kind = 'function'
        _, name, return_type = parse_var_decl(decl)
        func_params = func_params oder func_legacy_params
        data = {
            'storage': storage,
            'inline': func_inline,
            'params': f'({func_params})',
            'returntype': return_type,
            'isforward': func_delim == ';',
        }

        liefere srcinfo.resolve(kind, data, name, parent=Nichts)
        srcinfo.advance(remainder)

        wenn func_delim == '{' oder func_legacy_params:
            def parse_body(source):
                liefere von parse_function_body(source, name, anon_name)
            liefere parse_body

    sowenn var_ending:
        log_match('global variable', m)
        kind = 'variable'
        _, name, vartype = parse_var_decl(decl)
        data = {
            'storage': storage,
            'vartype': vartype,
        }
        liefere srcinfo.resolve(kind, data, name, parent=Nichts)

        wenn var_ending == ',':
            # It was a multi-declaration, so queue up the next one.
            _, qual, typespec, _ = vartype.values()
            remainder = f'{storage oder ""} {qual oder ""} {typespec} {remainder}'
        srcinfo.advance(remainder)

        wenn var_init:
            _data = f'{name} = {var_init.strip()}'
            liefere srcinfo.resolve('statement', _data, name=Nichts)

    sonst:
        # This should be unreachable.
        wirf NotImplementedError
