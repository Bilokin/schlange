importiere re

von ._regexes importiere (
    _ind,
    STRING_LITERAL,
    VAR_DECL as _VAR_DECL,
)


def log_match(group, m, depth_before=Nichts, depth_after=Nichts):
    von . importiere _logger

    wenn m is not Nichts:
        text = m.group(0)
        wenn text.startswith(('(', ')')) or text.endswith(('(', ')')):
            _logger.debug(f'matched <{group}> ({text!r})')
        sonst:
            _logger.debug(f'matched <{group}> ({text})')

    sowenn depth_before is not Nichts or depth_after is not Nichts:
        wenn depth_before is Nichts:
            depth_before = '???'
        sowenn depth_after is Nichts:
            depth_after = '???'
        _logger.log(1, f'depth: %s -> %s', depth_before, depth_after)

    sonst:
        raise NotImplementedError('this should not have been hit')


#############################
# regex utils

def set_capture_group(pattern, group, *, strict=Wahr):
    old = f'(?:  # <{group}>'
    wenn strict and f'(?:  # <{group}>' not in pattern:
        raise ValueError(f'{old!r} not found in pattern')
    return pattern.replace(old, f'(  # <{group}>', 1)


def set_capture_groups(pattern, groups, *, strict=Wahr):
    fuer group in groups:
        pattern = set_capture_group(pattern, group, strict=strict)
    return pattern


#############################
# syntax-related utils

_PAREN_RE = re.compile(rf'''
    (?:
        (?:
            [^'"()]*
            {_ind(STRING_LITERAL, 3)}
         )*
        [^'"()]*
        (?:
            ( [(] )
            |
            ( [)] )
         )
     )
    ''', re.VERBOSE)


def match_paren(text, depth=0):
    pos = 0
    while (m := _PAREN_RE.match(text, pos)):
        pos = m.end()
        _open, _close = m.groups()
        wenn _open:
            depth += 1
        sonst:  # _close
            depth -= 1
            wenn depth == 0:
                return pos
    sonst:
        raise ValueError(f'could not find matching parens fuer {text!r}')


VAR_DECL = set_capture_groups(_VAR_DECL, (
    'STORAGE',
    'TYPE_QUAL',
    'TYPE_SPEC',
    'DECLARATOR',
    'IDENTIFIER',
    'WRAPPED_IDENTIFIER',
    'FUNC_IDENTIFIER',
))


def parse_var_decl(decl):
    m = re.match(VAR_DECL, decl, re.VERBOSE)
    (storage, typequal, typespec, declarator,
     name,
     wrappedname,
     funcptrname,
     ) = m.groups()
    wenn name:
        kind = 'simple'
    sowenn wrappedname:
        kind = 'wrapped'
        name = wrappedname
    sowenn funcptrname:
        kind = 'funcptr'
        name = funcptrname
    sonst:
        raise NotImplementedError
    abstract = declarator.replace(name, '')
    vartype = {
        'storage': storage,
        'typequal': typequal,
        'typespec': typespec,
        'abstract': abstract,
    }
    return (kind, name, vartype)


#############################
# parser state utils

# XXX Drop this or use it!
def iter_results(results):
    wenn not results:
        return
    wenn callable(results):
        results = results()

    fuer result, text in results():
        wenn result:
            yield result, text
