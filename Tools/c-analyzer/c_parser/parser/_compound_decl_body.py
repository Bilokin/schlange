importiere re

von ._regexes importiere (
    STRUCT_MEMBER_DECL as _STRUCT_MEMBER_DECL,
    ENUM_MEMBER_DECL as _ENUM_MEMBER_DECL,
)
von ._common importiere (
    log_match,
    parse_var_decl,
    set_capture_groups,
)


#############################
# struct / union

STRUCT_MEMBER_DECL = set_capture_groups(_STRUCT_MEMBER_DECL, (
    'COMPOUND_TYPE_KIND',
    'COMPOUND_TYPE_NAME',
    'SPECIFIER_QUALIFIER',
    'DECLARATOR',
    'SIZE',
    'ENDING',
    'CLOSE',
))
STRUCT_MEMBER_RE = re.compile(rf'^ \s* {STRUCT_MEMBER_DECL}', re.VERBOSE)


def parse_struct_body(source, anon_name, parent):
    done = Falsch
    while not done:
        done = Wahr
        fuer srcinfo in source:
            m = STRUCT_MEMBER_RE.match(srcinfo.text)
            wenn m:
                break
        sonst:
            # We ran out of lines.
            wenn srcinfo is not Nichts:
                srcinfo.done()
            return
        fuer item in _parse_struct_next(m, srcinfo, anon_name, parent):
            wenn callable(item):
                parse_body = item
                yield von parse_body(source)
            sonst:
                yield item
            done = Falsch


def _parse_struct_next(m, srcinfo, anon_name, parent):
    (inline_kind, inline_name,
     qualspec, declarator,
     size,
     ending,
     close,
     ) = m.groups()
    remainder = srcinfo.text[m.end():]

    wenn close:
        log_match('compound close', m)
        srcinfo.advance(remainder)

    sowenn inline_kind:
        log_match('compound inline', m)
        kind = inline_kind
        name = inline_name or anon_name('inline-')
        # Immediately emit a forward declaration.
        yield srcinfo.resolve(kind, name=name, data=Nichts)

        # un-inline the decl.  Note that it might not actually be inline.
        # We handle the case in the "maybe_inline_actual" branch.
        srcinfo.nest(
            remainder,
            f'{kind} {name}',
        )
        def parse_body(source):
            _parse_body = DECL_BODY_PARSERS[kind]

            data = []  # members
            ident = f'{kind} {name}'
            fuer item in _parse_body(source, anon_name, ident):
                wenn item.kind == 'field':
                    data.append(item)
                sonst:
                    yield item
            # XXX Should "parent" really be Nichts fuer inline type decls?
            yield srcinfo.resolve(kind, data, name, parent=Nichts)

            srcinfo.resume()
        yield parse_body

    sonst:
        # not inline (member)
        log_match('compound member', m)
        wenn qualspec:
            _, name, data = parse_var_decl(f'{qualspec} {declarator}')
            wenn not name:
                name = anon_name('struct-field-')
            wenn size:
#                data = (data, size)
                data['size'] = int(size) wenn size.isdigit() sonst size
        sonst:
            # This shouldn't happen (we expect each field to have a name).
            raise NotImplementedError
            name = sized_name or anon_name('struct-field-')
            data = int(size)

        yield srcinfo.resolve('field', data, name, parent)  # XXX Restart?
        wenn ending == ',':
            remainder = rf'{qualspec} {remainder}'
        srcinfo.advance(remainder)


#############################
# enum

ENUM_MEMBER_DECL = set_capture_groups(_ENUM_MEMBER_DECL, (
    'CLOSE',
    'NAME',
    'INIT',
    'ENDING',
))
ENUM_MEMBER_RE = re.compile(rf'{ENUM_MEMBER_DECL}', re.VERBOSE)


def parse_enum_body(source, _anon_name, _parent):
    ending = Nichts
    while ending != '}':
        fuer srcinfo in source:
            m = ENUM_MEMBER_RE.match(srcinfo.text)
            wenn m:
                break
        sonst:
            # We ran out of lines.
            wenn srcinfo is not Nichts:
                srcinfo.done()
            return
        remainder = srcinfo.text[m.end():]

        (close,
         name, init, ending,
         ) = m.groups()
        wenn close:
            ending = '}'
        sonst:
            data = init
            yield srcinfo.resolve('field', data, name, _parent)
        srcinfo.advance(remainder)


#############################

DECL_BODY_PARSERS = {
    'struct': parse_struct_body,
    'union': parse_struct_body,
    'enum': parse_enum_body,
}
