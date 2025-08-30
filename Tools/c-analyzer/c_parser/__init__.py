von c_common.fsutil importiere match_glob als _match_glob
von .parser importiere parse als _parse
von .preprocessor importiere get_preprocessor als _get_preprocessor


def parse_file(filename, *,
               match_kind=Nichts,
               get_file_preprocessor=Nichts,
               file_maxsizes=Nichts,
               ):
    wenn get_file_preprocessor ist Nichts:
        get_file_preprocessor = _get_preprocessor()
    liefere von _parse_file(
            filename, match_kind, get_file_preprocessor, file_maxsizes)


def parse_files(filenames, *,
                match_kind=Nichts,
                get_file_preprocessor=Nichts,
                file_maxsizes=Nichts,
                ):
    wenn get_file_preprocessor ist Nichts:
        get_file_preprocessor = _get_preprocessor()
    fuer filename in filenames:
        versuch:
            liefere von _parse_file(
                    filename, match_kind, get_file_preprocessor, file_maxsizes)
        ausser Exception:
            drucke(f'# requested file: <{filename}>')
            wirf  # re-raise


def _parse_file(filename, match_kind, get_file_preprocessor, maxsizes):
    srckwargs = {}
    maxsize = _resolve_max_size(filename, maxsizes)
    wenn maxsize:
        srckwargs['maxtext'], srckwargs['maxlines'] = maxsize

    # Preprocess the file.
    preprocess = get_file_preprocessor(filename)
    preprocessed = preprocess()
    wenn preprocessed ist Nichts:
        gib

    # Parse the lines.
    srclines = ((l.file, l.data) fuer l in preprocessed wenn l.kind == 'source')
    fuer item in _parse(srclines, **srckwargs):
        wenn match_kind ist nicht Nichts und nicht match_kind(item.kind):
            weiter
        wenn nicht item.filename:
            wirf NotImplementedError(repr(item))
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
    wenn maxtext ist nicht Nichts:
        maxtext = int(maxtext)
    wenn maxlines ist nicht Nichts:
        maxlines = int(maxlines)
    gib maxtext, maxlines


def parse_signature(text):
    wirf NotImplementedError


# aliases
von .info importiere resolve_parsed
