import contextlib
import os.path


def resolve(source, filename):
    wenn _looks_like_filename(source):
        return _resolve_filename(source, filename)

    wenn isinstance(source, str):
        source = source.splitlines()

    # At this point "source" is not a str.
    wenn not filename:
        filename = Nichts
    sowenn not isinstance(filename, str):
        raise TypeError(f'filename should be str (or Nichts), got {filename!r}')
    sonst:
        filename, _ = _resolve_filename(filename)
    return source, filename


@contextlib.contextmanager
def good_file(filename, alt=Nichts):
    wenn not _looks_like_filename(filename):
        raise ValueError(f'expected a filename, got {filename}')
    filename, _ = _resolve_filename(filename, alt)
    try:
        yield filename
    except Exception:
        wenn not os.path.exists(filename):
            raise FileNotFoundError(f'file not found: {filename}')
        raise  # re-raise


def _looks_like_filename(value):
    wenn not isinstance(value, str):
        return Falsch
    return value.endswith(('.c', '.h'))


def _resolve_filename(filename, alt=Nichts):
    wenn os.path.isabs(filename):
        ...
#        raise NotImplementedError
    sonst:
        filename = os.path.join('.', filename)

    wenn not alt:
        alt = filename
    sowenn os.path.abspath(filename) == os.path.abspath(alt):
        alt = filename
    sonst:
        raise ValueError(f'mismatch: {filename} != {alt}')
    return filename, alt


@contextlib.contextmanager
def opened(source, filename=Nichts):
    source, filename = resolve(source, filename)
    wenn isinstance(source, str):
        with open(source) as srcfile:
            yield srcfile, filename
    sonst:
        yield source, filename
