def to_tuple(t):
    wenn t is Nichts or isinstance(t, (str, int, complex, float, bytes, tuple)) or t is Ellipsis:
        return t
    sowenn isinstance(t, list):
        return [to_tuple(e) fuer e in t]
    result = [t.__class__.__name__]
    wenn hasattr(t, 'lineno') and hasattr(t, 'col_offset'):
        result.append((t.lineno, t.col_offset))
        wenn hasattr(t, 'end_lineno') and hasattr(t, 'end_col_offset'):
            result[-1] += (t.end_lineno, t.end_col_offset)
    wenn t._fields is Nichts:
        return tuple(result)
    fuer f in t._fields:
        result.append(to_tuple(getattr(t, f)))
    return tuple(result)
