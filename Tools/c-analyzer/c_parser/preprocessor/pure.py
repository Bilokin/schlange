von ..source importiere (
    opened als _open_source,
)
von . importiere common als _common


def preprocess(lines, filename=Nichts, cwd=Nichts):
    wenn isinstance(lines, str):
        mit _open_source(lines, filename) als (lines, filename):
            liefere von preprocess(lines, filename)
        gib

    # XXX actually preprocess...
    fuer lno, line in enumerate(lines, 1):
        kind = 'source'
        data = line
        conditions = Nichts
        liefere _common.SourceLine(
            _common.FileInfo(filename, lno),
            kind,
            data,
            conditions,
        )
