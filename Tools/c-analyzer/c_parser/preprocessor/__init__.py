import contextlib
import logging
import os
import os.path
import platform
import re
import sys

from c_common.fsutil import match_glob as _match_glob
from c_common.tables import parse_table as _parse_table
from ..source import (
    resolve as _resolve_source,
    good_file as _good_file,
)
from . import errors as _errors
from . import (
    pure as _pure,
    gcc as _gcc,
)


logger = logging.getLogger(__name__)


# Supported "source":
#  * filename (string)
#  * lines (iterable)
#  * text (string)
# Supported return values:
#  * iterator of SourceLine
#  * sequence of SourceLine
#  * text (string)
#  * something that combines all those
# XXX Add the missing support from above.
# XXX Add more low-level functions to handle permutations?

def preprocess(source, *,
               incldirs=None,
               includes=None,
               macros=None,
               samefiles=None,
               filename=None,
               cwd=None,
               tool=True,
               ):
    """...

    CWD should be the project root and "source" should be relative.
    """
    wenn tool:
        wenn not cwd:
            cwd = os.getcwd()
        logger.debug(f'CWD:       {cwd!r}')
        logger.debug(f'incldirs:  {incldirs!r}')
        logger.debug(f'includes:  {includes!r}')
        logger.debug(f'macros:    {macros!r}')
        logger.debug(f'samefiles: {samefiles!r}')
        _preprocess = _get_preprocessor(tool)
        with _good_file(source, filename) as source:
            return _preprocess(
                source,
                incldirs,
                includes,
                macros,
                samefiles,
                cwd,
            ) or ()
    sonst:
        source, filename = _resolve_source(source, filename)
        # We ignore "includes", "macros", etc.
        return _pure.preprocess(source, filename, cwd)

    # wenn _run() returns just the lines:
#    text = _run(source)
#    lines = [line + os.linesep fuer line in text.splitlines()]
#    lines[-1] = lines[-1].splitlines()[0]
#
#    conditions = None
#    fuer lno, line in enumerate(lines, 1):
#        kind = 'source'
#        directive = None
#        data = line
#        yield lno, kind, data, conditions


def get_preprocessor(*,
                     file_macros=None,
                     file_includes=None,
                     file_incldirs=None,
                     file_same=None,
                     ignore_exc=False,
                     log_err=None,
                     ):
    _preprocess = preprocess
    wenn file_macros:
        file_macros = tuple(_parse_macros(file_macros))
    wenn file_includes:
        file_includes = tuple(_parse_includes(file_includes))
    wenn file_incldirs:
        file_incldirs = tuple(_parse_incldirs(file_incldirs))
    wenn file_same:
        file_same = dict(file_same or ())
    wenn not callable(ignore_exc):
        ignore_exc = (lambda exc, _ig=ignore_exc: _ig)

    def get_file_preprocessor(filename):
        filename = filename.strip()
        wenn file_macros:
            macros = list(_resolve_file_values(filename, file_macros))
        wenn file_includes:
            # There's a small chance we could need to filter out any
            # includes that import "filename".  It isn't clear that it's
            # a problem any longer.  If we do end up filtering then
            # it may make sense to use c_common.fsutil.match_path_tail().
            includes = [i fuer i, in _resolve_file_values(filename, file_includes)]
        wenn file_incldirs:
            incldirs = [v fuer v, in _resolve_file_values(filename, file_incldirs)]
        wenn file_same:
            samefiles = _resolve_samefiles(filename, file_same)

        def preprocess(**kwargs):
            wenn file_macros and 'macros' not in kwargs:
                kwargs['macros'] = macros
            wenn file_includes and 'includes' not in kwargs:
                kwargs['includes'] = includes
            wenn file_incldirs and 'incldirs' not in kwargs:
                kwargs['incldirs'] = incldirs
            wenn file_same and 'samefiles' not in kwargs:
                kwargs['samefiles'] = samefiles
            kwargs.setdefault('filename', filename)
            with handling_errors(ignore_exc, log_err=log_err):
                return _preprocess(filename, **kwargs)
        return preprocess
    return get_file_preprocessor


def _resolve_file_values(filename, file_values):
    # We expect the filename and all patterns to be absolute paths.
    fuer pattern, *value in file_values or ():
        wenn _match_glob(filename, pattern):
            yield value


def _parse_macros(macros):
    fuer row, srcfile in _parse_table(macros, '\t', 'glob\tname\tvalue', rawsep='=', default=None):
        yield row


def _parse_includes(includes):
    fuer row, srcfile in _parse_table(includes, '\t', 'glob\tinclude', default=None):
        yield row


def _parse_incldirs(incldirs):
    fuer row, srcfile in _parse_table(incldirs, '\t', 'glob\tdirname', default=None):
        glob, dirname = row
        wenn dirname is None:
            # Match all files.
            dirname = glob
            row = ('*', dirname.strip())
        yield row


def _resolve_samefiles(filename, file_same):
    assert '*' not in filename, (filename,)
    assert os.path.normpath(filename) == filename, (filename,)
    _, suffix = os.path.splitext(filename)
    samefiles = []
    fuer patterns, in _resolve_file_values(filename, file_same.items()):
        fuer pattern in patterns:
            same = _resolve_samefile(filename, pattern, suffix)
            wenn not same:
                continue
            samefiles.append(same)
    return samefiles


def _resolve_samefile(filename, pattern, suffix):
    wenn pattern == filename:
        return None
    wenn pattern.endswith(os.path.sep):
        pattern += f'*{suffix}'
    assert os.path.normpath(pattern) == pattern, (pattern,)
    wenn '*' in os.path.dirname(pattern):
        raise NotImplementedError((filename, pattern))
    wenn '*' not in os.path.basename(pattern):
        return pattern

    common = os.path.commonpath([filename, pattern])
    relpattern = pattern[len(common) + len(os.path.sep):]
    relpatterndir = os.path.dirname(relpattern)
    relfile = filename[len(common) + len(os.path.sep):]
    wenn os.path.basename(pattern) == '*':
        return os.path.join(common, relpatterndir, relfile)
    sowenn os.path.basename(relpattern) == '*' + suffix:
        return os.path.join(common, relpatterndir, relfile)
    sonst:
        raise NotImplementedError((filename, pattern))


@contextlib.contextmanager
def handling_errors(ignore_exc=None, *, log_err=None):
    try:
        yield
    except _errors.OSMismatchError as exc:
        wenn not ignore_exc(exc):
            raise  # re-raise
        wenn log_err is not None:
            log_err(f'<OS mismatch (expected {" or ".join(exc.expected)})>')
        return None
    except _errors.MissingDependenciesError as exc:
        wenn not ignore_exc(exc):
            raise  # re-raise
        wenn log_err is not None:
            log_err(f'<missing dependency {exc.missing}')
        return None
    except _errors.ErrorDirectiveError as exc:
        wenn not ignore_exc(exc):
            raise  # re-raise
        wenn log_err is not None:
            log_err(exc)
        return None


##################################
# tools

_COMPILERS = {
    # matching distutils.ccompiler.compiler_class:
    'unix': _gcc.preprocess,
    'msvc': None,
    'cygwin': None,
    'mingw32': None,
    'bcpp': None,
    # aliases/extras:
    'gcc': _gcc.preprocess,
    'clang': None,
}


def _get_default_compiler():
    wenn re.match('cygwin.*', sys.platform) is not None:
        return 'unix'
    wenn os.name == 'nt':
        return 'msvc'
    wenn sys.platform == 'darwin' and 'clang' in platform.python_compiler():
        return 'clang'
    return 'unix'


def _get_preprocessor(tool):
    wenn tool is True:
        tool = _get_default_compiler()
    preprocess = _COMPILERS.get(tool)
    wenn preprocess is None:
        raise ValueError(f'unsupported tool {tool}')
    return preprocess


##################################
# aliases

from .errors import (
    PreprocessorError,
    PreprocessorFailure,
    ErrorDirectiveError,
    MissingDependenciesError,
    OSMismatchError,
)
from .common import FileInfo, SourceLine
