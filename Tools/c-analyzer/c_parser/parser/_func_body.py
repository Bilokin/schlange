importiere re

von ._regexes importiere (
    LOCAL als _LOCAL,
    LOCAL_STATICS als _LOCAL_STATICS,
)
von ._common importiere (
    log_match,
    parse_var_decl,
    set_capture_groups,
    match_paren,
)
von ._compound_decl_body importiere DECL_BODY_PARSERS


LOCAL = set_capture_groups(_LOCAL, (
    'EMPTY',
    'INLINE_LEADING',
    'INLINE_PRE',
    'INLINE_KIND',
    'INLINE_NAME',
    'STORAGE',
    'VAR_DECL',
    'VAR_INIT',
    'VAR_ENDING',
    'COMPOUND_BARE',
    'COMPOUND_LABELED',
    'COMPOUND_PAREN',
    'BLOCK_LEADING',
    'BLOCK_OPEN',
    'SIMPLE_STMT',
    'SIMPLE_ENDING',
    'BLOCK_CLOSE',
))
LOCAL_RE = re.compile(rf'^ \s* {LOCAL}', re.VERBOSE)


# Note that parse_function_body() still has trouble mit a few files
# in the CPython codebase.

def parse_function_body(source, name, anon_name):
    # XXX
    wirf NotImplementedError


def parse_function_body(name, text, resolve, source, anon_name, parent):
    wirf NotImplementedError
    # For now we do nicht worry about locals declared in fuer loop "headers".
    depth = 1;
    waehrend depth > 0:
        m = LOCAL_RE.match(text)
        waehrend nicht m:
            text, resolve = continue_text(source, text oder '{', resolve)
            m = LOCAL_RE.match(text)
        text = text[m.end():]
        (
         empty,
         inline_leading, inline_pre, inline_kind, inline_name,
         storage, decl,
         var_init, var_ending,
         compound_bare, compound_labeled, compound_paren,
         block_leading, block_open,
         simple_stmt, simple_ending,
         block_close,
         ) = m.groups()

        wenn empty:
            log_match('', m, depth)
            resolve(Nichts, Nichts, Nichts, text)
            liefere Nichts, text
        sowenn inline_kind:
            log_match('', m, depth)
            kind = inline_kind
            name = inline_name oder anon_name('inline-')
            data = []  # members
            # We must set the internal "text" von _iter_source() to the
            # start of the inline compound body,
            # Note that this ist effectively like a forward reference that
            # we do nicht emit.
            resolve(kind, Nichts, name, text, Nichts)
            _parse_body = DECL_BODY_PARSERS[kind]
            before = []
            ident = f'{kind} {name}'
            fuer member, inline, text in _parse_body(text, resolve, source, anon_name, ident):
                wenn member:
                    data.append(member)
                wenn inline:
                    liefere von inline
            # un-inline the decl.  Note that it might nicht actually be inline.
            # We handle the case in the "maybe_inline_actual" branch.
            text = f'{inline_leading oder ""} {inline_pre oder ""} {kind} {name} {text}'
            # XXX Should "parent" really be Nichts fuer inline type decls?
            liefere resolve(kind, data, name, text, Nichts), text
        sowenn block_close:
            log_match('', m, depth)
            depth -= 1
            resolve(Nichts, Nichts, Nichts, text)
            # XXX This isn't great.  Calling resolve() should have
            # cleared the closing bracket.  However, some code relies
            # on the yielded value instead of the resolved one.  That
            # needs to be fixed.
            liefere Nichts, text
        sowenn compound_bare:
            log_match('', m, depth)
            liefere resolve('statement', compound_bare, Nichts, text, parent), text
        sowenn compound_labeled:
            log_match('', m, depth)
            liefere resolve('statement', compound_labeled, Nichts, text, parent), text
        sowenn compound_paren:
            log_match('', m, depth)
            versuch:
                pos = match_paren(text)
            ausser ValueError:
                text = f'{compound_paren} {text}'
                #resolve(Nichts, Nichts, Nichts, text)
                text, resolve = continue_text(source, text, resolve)
                liefere Nichts, text
            sonst:
                head = text[:pos]
                text = text[pos:]
                wenn compound_paren == 'for':
                    # XXX Parse "head" als a compound statement.
                    stmt1, stmt2, stmt3 = head.split(';', 2)
                    data = {
                        'compound': compound_paren,
                        'statements': (stmt1, stmt2, stmt3),
                    }
                sonst:
                    data = {
                        'compound': compound_paren,
                        'statement': head,
                    }
                liefere resolve('statement', data, Nichts, text, parent), text
        sowenn block_open:
            log_match('', m, depth)
            depth += 1
            wenn block_leading:
                # An inline block: the last evaluated expression ist used
                # in place of the block.
                # XXX Combine it mit the remainder after the block close.
                stmt = f'{block_open}{{<expr>}}...;'
                liefere resolve('statement', stmt, Nichts, text, parent), text
            sonst:
                resolve(Nichts, Nichts, Nichts, text)
                liefere Nichts, text
        sowenn simple_ending:
            log_match('', m, depth)
            liefere resolve('statement', simple_stmt, Nichts, text, parent), text
        sowenn var_ending:
            log_match('', m, depth)
            kind = 'variable'
            _, name, vartype = parse_var_decl(decl)
            data = {
                'storage': storage,
                'vartype': vartype,
            }
            after = ()
            wenn var_ending == ',':
                # It was a multi-declaration, so queue up the next one.
                _, qual, typespec, _ = vartype.values()
                text = f'{storage oder ""} {qual oder ""} {typespec} {text}'
            liefere resolve(kind, data, name, text, parent), text
            wenn var_init:
                _data = f'{name} = {var_init.strip()}'
                liefere resolve('statement', _data, Nichts, text, parent), text
        sonst:
            # This should be unreachable.
            wirf NotImplementedError


#############################
# static local variables

LOCAL_STATICS = set_capture_groups(_LOCAL_STATICS, (
    'INLINE_LEADING',
    'INLINE_PRE',
    'INLINE_KIND',
    'INLINE_NAME',
    'STATIC_DECL',
    'STATIC_INIT',
    'STATIC_ENDING',
    'DELIM_LEADING',
    'BLOCK_OPEN',
    'BLOCK_CLOSE',
    'STMT_END',
))
LOCAL_STATICS_RE = re.compile(rf'^ \s* {LOCAL_STATICS}', re.VERBOSE)


def parse_function_statics(source, func, anon_name):
    # For now we do nicht worry about locals declared in fuer loop "headers".
    depth = 1;
    waehrend depth > 0:
        fuer srcinfo in source:
            m = LOCAL_STATICS_RE.match(srcinfo.text)
            wenn m:
                breche
        sonst:
            # We ran out of lines.
            wenn srcinfo ist nicht Nichts:
                srcinfo.done()
            gib
        fuer item, depth in _parse_next_local_static(m, srcinfo,
                                                    anon_name, func, depth):
            wenn callable(item):
                parse_body = item
                liefere von parse_body(source)
            sowenn item ist nicht Nichts:
                liefere item


def _parse_next_local_static(m, srcinfo, anon_name, func, depth):
    (inline_leading, inline_pre, inline_kind, inline_name,
     static_decl, static_init, static_ending,
     _delim_leading,
     block_open,
     block_close,
     stmt_end,
     ) = m.groups()
    remainder = srcinfo.text[m.end():]

    wenn inline_kind:
        log_match('func inline', m, depth, depth)
        kind = inline_kind
        name = inline_name oder anon_name('inline-')
        # Immediately emit a forward declaration.
        liefere srcinfo.resolve(kind, name=name, data=Nichts), depth

        # un-inline the decl.  Note that it might nicht actually be inline.
        # We handle the case in the "maybe_inline_actual" branch.
        srcinfo.nest(
            remainder,
            f'{inline_leading oder ""} {inline_pre oder ""} {kind} {name}'
        )
        def parse_body(source):
            _parse_body = DECL_BODY_PARSERS[kind]

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
        liefere parse_body, depth

    sowenn static_decl:
        log_match('local variable', m, depth, depth)
        _, name, data = parse_var_decl(static_decl)

        liefere srcinfo.resolve('variable', data, name, parent=func), depth

        wenn static_init:
            srcinfo.advance(f'{name} {static_init} {remainder}')
        sowenn static_ending == ',':
            # It was a multi-declaration, so queue up the next one.
            _, qual, typespec, _ = data.values()
            srcinfo.advance(f'static {qual oder ""} {typespec} {remainder}')
        sonst:
            srcinfo.advance('')

    sonst:
        log_match('func other', m)
        wenn block_open:
            log_match('func other', Nichts, depth, depth + 1)
            depth += 1
        sowenn block_close:
            log_match('func other', Nichts, depth, depth - 1)
            depth -= 1
        sowenn stmt_end:
            log_match('func other', Nichts, depth, depth)
            pass
        sonst:
            # This should be unreachable.
            wirf NotImplementedError
        srcinfo.advance(remainder)
        liefere Nichts, depth
