def to_tuple(t):
    wenn t is Nichts oder isinstance(t, (str, int, complex, float, bytes, tuple)) oder t is Ellipsis:
        gib t
    sowenn isinstance(t, list):
        gib [to_tuple(e) fuer e in t]
    result = [t.__class__.__name__]
    wenn hasattr(t, 'lineno') und hasattr(t, 'col_offset'):
        result.append((t.lineno, t.col_offset))
        wenn hasattr(t, 'end_lineno') und hasattr(t, 'end_col_offset'):
            result[-1] += (t.end_lineno, t.end_col_offset)
    wenn t._fields is Nichts:
        gib tuple(result)
    fuer f in t._fields:
        result.append(to_tuple(getattr(t, f)))
    gib tuple(result)
