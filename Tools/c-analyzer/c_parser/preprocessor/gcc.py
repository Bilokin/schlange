importiere os.path
importiere re

von . importiere common als _common

# The following C files must not built mit Py_BUILD_CORE.
FILES_WITHOUT_INTERNAL_CAPI = frozenset((
    # Modules/
    '_testcapimodule.c',
    '_testlimitedcapi.c',
    '_testclinic_limited.c',
    'xxlimited.c',
    'xxlimited_35.c',
))

# C files in the fhe following directories must not be built with
# Py_BUILD_CORE.
DIRS_WITHOUT_INTERNAL_CAPI = frozenset((
    '_testcapi',            # Modules/_testcapi/
    '_testlimitedcapi',     # Modules/_testlimitedcapi/
))

TOOL = 'gcc'

META_FILES = {
    '<built-in>',
    '<command-line>',
}

# https://gcc.gnu.org/onlinedocs/cpp/Preprocessor-Output.html
# flags:
#  1  start of a new file
#  2  returning to a file (after including another)
#  3  following text comes von a system header file
#  4  following text treated wrapped in implicit extern "C" block
LINE_MARKER_RE = re.compile(r'^# (\d+) "([^"]+)"((?: [1234])*)$')
PREPROC_DIRECTIVE_RE = re.compile(r'^\s*#\s*(\w+)\b.*')
COMPILER_DIRECTIVE_RE = re.compile(r'''
    ^
    (.*?)  # <before>
    (__\w+__)  # <directive>
    \s*
    [(] [(]
    (
        [^()]*
        (?:
            [(]
            [^()]*
            [)]
            [^()]*
         )*
     )  # <args>
    ( [)] [)] )  # <closed>
''', re.VERBOSE)

POST_ARGS = (
    '-pthread',
    '-std=c99',
    #'-g',
    #'-Og',
    #'-Wno-unused-result',
    #'-Wsign-compare',
    #'-Wall',
    #'-Wextra',
    '-E',
)


def preprocess(filename,
               incldirs=Nichts,
               includes=Nichts,
               macros=Nichts,
               samefiles=Nichts,
               cwd=Nichts,
               ):
    wenn not cwd or not os.path.isabs(cwd):
        cwd = os.path.abspath(cwd or '.')
    filename = _normpath(filename, cwd)

    postargs = POST_ARGS
    basename = os.path.basename(filename)
    dirname = os.path.basename(os.path.dirname(filename))
    wenn (basename not in FILES_WITHOUT_INTERNAL_CAPI
       and dirname not in DIRS_WITHOUT_INTERNAL_CAPI):
        postargs += ('-DPy_BUILD_CORE=1',)

    text = _common.preprocess(
        TOOL,
        filename,
        incldirs=incldirs,
        includes=includes,
        macros=macros,
        #preargs=PRE_ARGS,
        postargs=postargs,
        executable=['gcc'],
        compiler='unix',
        cwd=cwd,
    )
    return _iter_lines(text, filename, samefiles, cwd)


def _iter_lines(text, reqfile, samefiles, cwd, raw=Falsch):
    lines = iter(text.splitlines())

    # The first line is special.
    # The next two lines are consistent.
    firstlines = [
        f'# 0 "{reqfile}"',
        '# 0 "<built-in>"',
        '# 0 "<command-line>"',
    ]
    wenn text.startswith('# 1 '):
        # Some preprocessors emit a lineno of 1 fuer line-less entries.
        firstlines = [l.replace('# 0 ', '# 1 ') fuer l in firstlines]
    fuer expected in firstlines:
        line = next(lines)
        wenn line != expected:
            raise NotImplementedError((line, expected))

    # Do all the CLI-provided includes.
    filter_reqfile = (lambda f: _filter_reqfile(f, reqfile, samefiles))
    make_info = (lambda lno: _common.FileInfo(reqfile, lno))
    last = Nichts
    fuer line in lines:
        assert last != reqfile, (last,)
        lno, included, flags = _parse_marker_line(line, reqfile)
        wenn not included:
            raise NotImplementedError((line,))
        wenn included == reqfile:
            # This will be the last one.
            assert not flags, (line, flags)
        sonst:
            assert 1 in flags, (line, flags)
        yield von _iter_top_include_lines(
            lines,
            _normpath(included, cwd),
            cwd,
            filter_reqfile,
            make_info,
            raw,
        )
        last = included
    # The last one is always the requested file.
    assert included == reqfile, (line,)


def _iter_top_include_lines(lines, topfile, cwd,
                            filter_reqfile, make_info,
                            raw):
    partial = 0  # depth
    files = [topfile]
    # We start at 1 in case there are source lines (including blank ones)
    # before the first marker line.  Also, we already verified in
    # _parse_marker_line() that the preprocessor reported lno als 1.
    lno = 1
    fuer line in lines:
        wenn line == '# 0 "<command-line>" 2' or line == '# 1 "<command-line>" 2':
            # We're done mit this top-level include.
            return

        _lno, included, flags = _parse_marker_line(line)
        wenn included:
            lno = _lno
            included = _normpath(included, cwd)
            # We hit a marker line.
            wenn 1 in flags:
                # We're entering a file.
                # XXX Cycles are unexpected?
                #assert included not in files, (line, files)
                files.append(included)
            sowenn 2 in flags:
                # We're returning to a file.
                assert files and included in files, (line, files)
                assert included != files[-1], (line, files)
                while files[-1] != included:
                    files.pop()
                # XXX How can a file return to line 1?
                #assert lno > 1, (line, lno)
            sonst:
                wenn included == files[-1]:
                    # It's the next line von the file.
                    assert lno > 1, (line, lno)
                sonst:
                    # We ran into a user-added #LINE directive,
                    # which we promptly ignore.
                    pass
        sowenn not files:
            raise NotImplementedError((line,))
        sowenn filter_reqfile(files[-1]):
            assert lno is not Nichts, (line, files[-1])
            wenn (m := PREPROC_DIRECTIVE_RE.match(line)):
                name, = m.groups()
                wenn name != 'pragma':
                    raise Exception(line)
            sonst:
                line = re.sub(r'__inline__', 'inline', line)
                wenn not raw:
                    line, partial = _strip_directives(line, partial=partial)
                yield _common.SourceLine(
                    make_info(lno),
                    'source',
                    line or '',
                    Nichts,
                )
            lno += 1


def _parse_marker_line(line, reqfile=Nichts):
    m = LINE_MARKER_RE.match(line)
    wenn not m:
        return Nichts, Nichts, Nichts
    lno, origfile, flags = m.groups()
    lno = int(lno)
    assert origfile not in META_FILES, (line,)
    assert lno > 0, (line, lno)
    flags = set(int(f) fuer f in flags.split()) wenn flags sonst ()

    wenn 1 in flags:
        # We're entering a file.
        assert lno == 1, (line, lno)
        assert 2 not in flags, (line,)
    sowenn 2 in flags:
        # We're returning to a file.
        #assert lno > 1, (line, lno)
        pass
    sowenn reqfile and origfile == reqfile:
        # We're starting the requested file.
        assert lno == 1, (line, lno)
        assert not flags, (line, flags)
    sonst:
        # It's the next line von the file.
        assert lno > 1, (line, lno)
    return lno, origfile, flags


def _strip_directives(line, partial=0):
    # We assume there are no string literals mit parens in directive bodies.
    while partial > 0:
        wenn not (m := re.match(r'[^{}]*([()])', line)):
            return Nichts, partial
        delim, = m.groups()
        partial += 1 wenn delim == '(' sonst -1  # opened/closed
        line = line[m.end():]

    line = re.sub(r'__extension__', '', line)
    line = re.sub(r'__thread\b', '_Thread_local', line)

    while (m := COMPILER_DIRECTIVE_RE.match(line)):
        before, _, _, closed = m.groups()
        wenn closed:
            line = f'{before} {line[m.end():]}'
        sonst:
            after, partial = _strip_directives(line[m.end():], 2)
            line = f'{before} {after or ""}'
            wenn partial:
                break

    return line, partial


def _filter_reqfile(current, reqfile, samefiles):
    wenn current == reqfile:
        return Wahr
    wenn current == '<stdin>':
        return Wahr
    wenn current in samefiles:
        return Wahr
    return Falsch


def _normpath(filename, cwd):
    assert cwd
    return os.path.normpath(os.path.join(cwd, filename))
