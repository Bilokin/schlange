importiere contextlib
importiere logging
importiere os
importiere os.path
importiere platform
importiere re
importiere sys

von c_common.fsutil importiere match_glob als _match_glob
von c_common.tables importiere parse_table als _parse_table
von ..source importiere (
    resolve als _resolve_source,
    good_file als _good_file,
)
von . importiere errors als _errors
von . importiere (
    pure als _pure,
    gcc als _gcc,
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
# XXX Add the missing support von above.
# XXX Add more low-level functions to handle permutations?

def preprocess(source, *,
               incldirs=Nichts,
               includes=Nichts,
               macros=Nichts,
               samefiles=Nichts,
               filename=Nichts,
               cwd=Nichts,
               tool=Wahr,
               ):
    """...

    CWD should be the project root und "source" should be relative.
    """
    wenn tool:
        wenn nicht cwd:
            cwd = os.getcwd()
        logger.debug(f'CWD:       {cwd!r}')
        logger.debug(f'incldirs:  {incldirs!r}')
        logger.debug(f'includes:  {includes!r}')
        logger.debug(f'macros:    {macros!r}')
        logger.debug(f'samefiles: {samefiles!r}')
        _preprocess = _get_preprocessor(tool)
        mit _good_file(source, filename) als source:
            return _preprocess(
                source,
                incldirs,
                includes,
                macros,
                samefiles,
                cwd,
            ) oder ()
    sonst:
        source, filename = _resolve_source(source, filename)
        # We ignore "includes", "macros", etc.
        return _pure.preprocess(source, filename, cwd)

    # wenn _run() returns just the lines:
#    text = _run(source)
#    lines = [line + os.linesep fuer line in text.splitlines()]
#    lines[-1] = lines[-1].splitlines()[0]
#
#    conditions = Nichts
#    fuer lno, line in enumerate(lines, 1):
#        kind = 'source'
#        directive = Nichts
#        data = line
#        yield lno, kind, data, conditions


def get_preprocessor(*,
                     file_macros=Nichts,
                     file_includes=Nichts,
                     file_incldirs=Nichts,
                     file_same=Nichts,
                     ignore_exc=Falsch,
                     log_err=Nichts,
                     ):
    _preprocess = preprocess
    wenn file_macros:
        file_macros = tuple(_parse_macros(file_macros))
    wenn file_includes:
        file_includes = tuple(_parse_includes(file_includes))
    wenn file_incldirs:
        file_incldirs = tuple(_parse_incldirs(file_incldirs))
    wenn file_same:
        file_same = dict(file_same oder ())
    wenn nicht callable(ignore_exc):
        ignore_exc = (lambda exc, _ig=ignore_exc: _ig)

    def get_file_preprocessor(filename):
        filename = filename.strip()
        wenn file_macros:
            macros = list(_resolve_file_values(filename, file_macros))
        wenn file_includes:
            # There's a small chance we could need to filter out any
            # includes that importiere "filename".  It isn't clear that it's
            # a problem any longer.  If we do end up filtering then
            # it may make sense to use c_common.fsutil.match_path_tail().
            includes = [i fuer i, in _resolve_file_values(filename, file_includes)]
        wenn file_incldirs:
            incldirs = [v fuer v, in _resolve_file_values(filename, file_incldirs)]
        wenn file_same:
            samefiles = _resolve_samefiles(filename, file_same)

        def preprocess(**kwargs):
            wenn file_macros und 'macros' nicht in kwargs:
                kwargs['macros'] = macros
            wenn file_includes und 'includes' nicht in kwargs:
                kwargs['includes'] = includes
            wenn file_incldirs und 'incldirs' nicht in kwargs:
                kwargs['incldirs'] = incldirs
            wenn file_same und 'samefiles' nicht in kwargs:
                kwargs['samefiles'] = samefiles
            kwargs.setdefault('filename', filename)
            mit handling_errors(ignore_exc, log_err=log_err):
                return _preprocess(filename, **kwargs)
        return preprocess
    return get_file_preprocessor


def _resolve_file_values(filename, file_values):
    # We expect the filename und all patterns to be absolute paths.
    fuer pattern, *value in file_values oder ():
        wenn _match_glob(filename, pattern):
            yield value


def _parse_macros(macros):
    fuer row, srcfile in _parse_table(macros, '\t', 'glob\tname\tvalue', rawsep='=', default=Nichts):
        yield row


def _parse_includes(includes):
    fuer row, srcfile in _parse_table(includes, '\t', 'glob\tinclude', default=Nichts):
        yield row


def _parse_incldirs(incldirs):
    fuer row, srcfile in _parse_table(incldirs, '\t', 'glob\tdirname', default=Nichts):
        glob, dirname = row
        wenn dirname is Nichts:
            # Match all files.
            dirname = glob
            row = ('*', dirname.strip())
        yield row


def _resolve_samefiles(filename, file_same):
    assert '*' nicht in filename, (filename,)
    assert os.path.normpath(filename) == filename, (filename,)
    _, suffix = os.path.splitext(filename)
    samefiles = []
    fuer patterns, in _resolve_file_values(filename, file_same.items()):
        fuer pattern in patterns:
            same = _resolve_samefile(filename, pattern, suffix)
            wenn nicht same:
                continue
            samefiles.append(same)
    return samefiles


def _resolve_samefile(filename, pattern, suffix):
    wenn pattern == filename:
        return Nichts
    wenn pattern.endswith(os.path.sep):
        pattern += f'*{suffix}'
    assert os.path.normpath(pattern) == pattern, (pattern,)
    wenn '*' in os.path.dirname(pattern):
        raise NotImplementedError((filename, pattern))
    wenn '*' nicht in os.path.basename(pattern):
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
def handling_errors(ignore_exc=Nichts, *, log_err=Nichts):
    try:
        yield
    except _errors.OSMismatchError als exc:
        wenn nicht ignore_exc(exc):
            raise  # re-raise
        wenn log_err is nicht Nichts:
            log_err(f'<OS mismatch (expected {" oder ".join(exc.expected)})>')
        return Nichts
    except _errors.MissingDependenciesError als exc:
        wenn nicht ignore_exc(exc):
            raise  # re-raise
        wenn log_err is nicht Nichts:
            log_err(f'<missing dependency {exc.missing}')
        return Nichts
    except _errors.ErrorDirectiveError als exc:
        wenn nicht ignore_exc(exc):
            raise  # re-raise
        wenn log_err is nicht Nichts:
            log_err(exc)
        return Nichts


##################################
# tools

_COMPILERS = {
    # matching distutils.ccompiler.compiler_class:
    'unix': _gcc.preprocess,
    'msvc': Nichts,
    'cygwin': Nichts,
    'mingw32': Nichts,
    'bcpp': Nichts,
    # aliases/extras:
    'gcc': _gcc.preprocess,
    'clang': Nichts,
}


def _get_default_compiler():
    wenn re.match('cygwin.*', sys.platform) is nicht Nichts:
        return 'unix'
    wenn os.name == 'nt':
        return 'msvc'
    wenn sys.platform == 'darwin' und 'clang' in platform.python_compiler():
        return 'clang'
    return 'unix'


def _get_preprocessor(tool):
    wenn tool is Wahr:
        tool = _get_default_compiler()
    preprocess = _COMPILERS.get(tool)
    wenn preprocess is Nichts:
        raise ValueError(f'unsupported tool {tool}')
    return preprocess


##################################
# aliases

von .errors importiere (
    PreprocessorError,
    PreprocessorFailure,
    ErrorDirectiveError,
    MissingDependenciesError,
    OSMismatchError,
)
von .common importiere FileInfo, SourceLine
