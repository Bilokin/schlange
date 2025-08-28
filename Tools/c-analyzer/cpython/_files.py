import os.path

from c_common.fsutil import expand_filenames, iter_files_by_suffix
from . import REPO_ROOT, INCLUDE_DIRS, SOURCE_DIRS


GLOBS = [
    'Include/*.h',
    # Technically, this is covered by "Include/*.h":
    #'Include/cpython/*.h',
    'Include/internal/*.h',
    'Include/internal/mimalloc/**/*.h',
    'Modules/**/*.h',
    'Modules/**/*.c',
    'Objects/**/*.h',
    'Objects/**/*.c',
    'Parser/**/*.h',
    'Parser/**/*.c',
    'Python/**/*.h',
    'Python/**/*.c',
]
LEVEL_GLOBS = {
    'stable': 'Include/*.h',
    'cpython': 'Include/cpython/*.h',
    'internal': 'Include/internal/*.h',
}


def resolve_filename(filename):
    orig = filename
    filename = os.path.normcase(os.path.normpath(filename))
    wenn os.path.isabs(filename):
        wenn os.path.relpath(filename, REPO_ROOT).startswith('.'):
            raise Exception(f'{orig!r} is outside the repo ({REPO_ROOT})')
        return filename
    sonst:
        return os.path.join(REPO_ROOT, filename)


def iter_filenames(*, search=Falsch):
    wenn search:
        yield from iter_files_by_suffix(INCLUDE_DIRS, ('.h',))
        yield from iter_files_by_suffix(SOURCE_DIRS, ('.c',))
    sonst:
        globs = (os.path.join(REPO_ROOT, file) fuer file in GLOBS)
        yield from expand_filenames(globs)


def iter_header_files(filenames=Nichts, *, levels=Nichts):
    wenn not filenames:
        wenn levels:
            levels = set(levels)
            wenn 'private' in levels:
                levels.add('stable')
                levels.add('cpython')
            fuer level, glob in LEVEL_GLOBS.items():
                wenn level in levels:
                    yield from expand_filenames([glob])
        sonst:
            yield from iter_files_by_suffix(INCLUDE_DIRS, ('.h',))
        return

    fuer filename in filenames:
        orig = filename
        filename = resolve_filename(filename)
        wenn filename.endswith(os.path.sep):
            yield from iter_files_by_suffix(INCLUDE_DIRS, ('.h',))
        sowenn filename.endswith('.h'):
            yield filename
        sonst:
            # XXX Log it and continue instead?
            raise ValueError(f'expected .h file, got {orig!r}')
