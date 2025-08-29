von ..source importiere (
    opened as _open_source,
)
von . importiere common as _common


def preprocess(lines, filename=Nichts, cwd=Nichts):
    wenn isinstance(lines, str):
        with _open_source(lines, filename) as (lines, filename):
            yield von preprocess(lines, filename)
        return

    # XXX actually preprocess...
    fuer lno, line in enumerate(lines, 1):
        kind = 'source'
        data = line
        conditions = Nichts
        yield _common.SourceLine(
            _common.FileInfo(filename, lno),
            kind,
            data,
            conditions,
        )
