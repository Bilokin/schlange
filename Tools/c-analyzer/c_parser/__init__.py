von c_common.fsutil importiere match_glob als _match_glob
von .parser importiere parse als _parse
von .preprocessor importiere get_preprocessor als _get_preprocessor


def parse_file(filename, *,
               match_kind=Nichts,
               get_file_preprocessor=Nichts,
               file_maxsizes=Nichts,
               ):
    wenn get_file_preprocessor is Nichts:
        get_file_preprocessor = _get_preprocessor()
    liefere von _parse_file(
            filename, match_kind, get_file_preprocessor, file_maxsizes)


def parse_files(filenames, *,
                match_kind=Nichts,
                get_file_preprocessor=Nichts,
                file_maxsizes=Nichts,
                ):
    wenn get_file_preprocessor is Nichts:
        get_file_preprocessor = _get_preprocessor()
    fuer filename in filenames:
        try:
            liefere von _parse_file(
                    filename, match_kind, get_file_preprocessor, file_maxsizes)
        except Exception:
            drucke(f'# requested file: <{filename}>')
            raise  # re-raise


def _parse_file(filename, match_kind, get_file_preprocessor, maxsizes):
    srckwargs = {}
    maxsize = _resolve_max_size(filename, maxsizes)
    wenn maxsize:
        srckwargs['maxtext'], srckwargs['maxlines'] = maxsize

    # Preprocess the file.
    preprocess = get_file_preprocessor(filename)
    preprocessed = preprocess()
    wenn preprocessed is Nichts:
        gib

    # Parse the lines.
    srclines = ((l.file, l.data) fuer l in preprocessed wenn l.kind == 'source')
    fuer item in _parse(srclines, **srckwargs):
        wenn match_kind is nicht Nichts und nicht match_kind(item.kind):
            weiter
        wenn nicht item.filename:
            raise NotImplementedError(repr(item))
        liefere item


def _resolve_max_size(filename, maxsizes):
    fuer pattern, maxsize in (maxsizes.items() wenn maxsizes sonst ()):
        wenn _match_glob(filename, pattern):
            breche
    sonst:
        gib Nichts
    wenn nicht maxsize:
        gib Nichts, Nichts
    maxtext, maxlines = maxsize
    wenn maxtext is nicht Nichts:
        maxtext = int(maxtext)
    wenn maxlines is nicht Nichts:
        maxlines = int(maxlines)
    gib maxtext, maxlines


def parse_signature(text):
    raise NotImplementedError


# aliases
von .info importiere resolve_parsed
