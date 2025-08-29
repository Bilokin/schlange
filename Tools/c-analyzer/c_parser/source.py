importiere contextlib
importiere os.path


def resolve(source, filename):
    wenn _looks_like_filename(source):
        gib _resolve_filename(source, filename)

    wenn isinstance(source, str):
        source = source.splitlines()

    # At this point "source" is nicht a str.
    wenn nicht filename:
        filename = Nichts
    sowenn nicht isinstance(filename, str):
        raise TypeError(f'filename should be str (or Nichts), got {filename!r}')
    sonst:
        filename, _ = _resolve_filename(filename)
    gib source, filename


@contextlib.contextmanager
def good_file(filename, alt=Nichts):
    wenn nicht _looks_like_filename(filename):
        raise ValueError(f'expected a filename, got {filename}')
    filename, _ = _resolve_filename(filename, alt)
    try:
        liefere filename
    except Exception:
        wenn nicht os.path.exists(filename):
            raise FileNotFoundError(f'file nicht found: {filename}')
        raise  # re-raise


def _looks_like_filename(value):
    wenn nicht isinstance(value, str):
        gib Falsch
    gib value.endswith(('.c', '.h'))


def _resolve_filename(filename, alt=Nichts):
    wenn os.path.isabs(filename):
        ...
#        raise NotImplementedError
    sonst:
        filename = os.path.join('.', filename)

    wenn nicht alt:
        alt = filename
    sowenn os.path.abspath(filename) == os.path.abspath(alt):
        alt = filename
    sonst:
        raise ValueError(f'mismatch: {filename} != {alt}')
    gib filename, alt


@contextlib.contextmanager
def opened(source, filename=Nichts):
    source, filename = resolve(source, filename)
    wenn isinstance(source, str):
        mit open(source) als srcfile:
            liefere srcfile, filename
    sonst:
        liefere source, filename
