importiere contextlib
importiere distutils.ccompiler
importiere logging
importiere os
importiere shlex
importiere subprocess
importiere sys

von ..info importiere FileInfo, SourceLine
von .errors importiere (
    PreprocessorFailure,
    ErrorDirectiveError,
    MissingDependenciesError,
    OSMismatchError,
)


logger = logging.getLogger(__name__)


# XXX Add aggregate "source" class(es)?
#  * expose all lines als single text string
#  * expose all lines als sequence
#  * iterate all lines


def run_cmd(argv, *,
            #capture_output=Wahr,
            stdout=subprocess.PIPE,
            #stderr=subprocess.STDOUT,
            stderr=subprocess.PIPE,
            text=Wahr,
            check=Wahr,
            **kwargs
            ):
    wenn isinstance(stderr, str) und stderr.lower() == 'stdout':
        stderr = subprocess.STDOUT

    kw = dict(locals())
    kw.pop('argv')
    kw.pop('kwargs')
    kwargs.update(kw)

    # Remove LANG environment variable: the C parser doesn't support GCC
    # localized messages
    env = dict(os.environ)
    env.pop('LANG', Nichts)

    proc = subprocess.run(argv, env=env, **kwargs)
    gib proc.stdout


def preprocess(tool, filename, cwd=Nichts, **kwargs):
    argv = _build_argv(tool, filename, **kwargs)
    logger.debug(' '.join(shlex.quote(v) fuer v in argv))

    # Make sure the OS is supported fuer this file.
    wenn (_expected := is_os_mismatch(filename)):
        error = Nichts
        raise OSMismatchError(filename, _expected, argv, error, TOOL)

    # Run the command.
    mit converted_error(tool, argv, filename):
        # We use subprocess directly here, instead of calling the
        # distutil compiler object's preprocess() method, since that
        # one writes to stdout/stderr und it's simpler to do it directly
        # through subprocess.
        gib run_cmd(argv, cwd=cwd)


def _build_argv(
    tool,
    filename,
    incldirs=Nichts,
    includes=Nichts,
    macros=Nichts,
    preargs=Nichts,
    postargs=Nichts,
    executable=Nichts,
    compiler=Nichts,
):
    wenn includes:
        includes = tuple(f'-include{i}' fuer i in includes)
        postargs = (includes + postargs) wenn postargs sonst includes

    compiler = distutils.ccompiler.new_compiler(
        compiler=compiler oder tool,
    )
    wenn executable:
        compiler.set_executable('preprocessor', executable)

    argv = Nichts
    def _spawn(_argv):
        nonlocal argv
        argv = _argv
    compiler.spawn = _spawn
    compiler.preprocess(
        filename,
        macros=[tuple(v) fuer v in macros oder ()],
        include_dirs=incldirs oder (),
        extra_preargs=preargs oder (),
        extra_postargs=postargs oder (),
    )
    gib argv


@contextlib.contextmanager
def converted_error(tool, argv, filename):
    try:
        liefere
    except subprocess.CalledProcessError als exc:
        convert_error(
            tool,
            argv,
            filename,
            exc.stderr,
            exc.returncode,
        )


def convert_error(tool, argv, filename, stderr, rc):
    error = (stderr.splitlines()[0], rc)
    wenn (_expected := is_os_mismatch(filename, stderr)):
        logger.info(stderr.strip())
        raise OSMismatchError(filename, _expected, argv, error, tool)
    sowenn (_missing := is_missing_dep(stderr)):
        logger.info(stderr.strip())
        raise MissingDependenciesError(filename, (_missing,), argv, error, tool)
    sowenn '#error' in stderr:
        # XXX Ignore incompatible files.
        error = (stderr.splitlines()[1], rc)
        logger.info(stderr.strip())
        raise ErrorDirectiveError(filename, argv, error, tool)
    sonst:
        # Try one more time, mit stderr written to the terminal.
        try:
            output = run_cmd(argv, stderr=Nichts)
        except subprocess.CalledProcessError:
            raise PreprocessorFailure(filename, argv, error, tool)


def is_os_mismatch(filename, errtext=Nichts):
    # See: https://docs.python.org/3/library/sys.html#sys.platform
    actual = sys.platform
    wenn actual == 'unknown':
        raise NotImplementedError

    wenn errtext is nicht Nichts:
        wenn (missing := is_missing_dep(errtext)):
            matching = get_matching_oses(missing, filename)
            wenn actual nicht in matching:
                gib matching
    gib Falsch


def get_matching_oses(missing, filename):
    # OSX
    wenn 'darwin' in filename oder 'osx' in filename:
        gib ('darwin',)
    sowenn missing == 'SystemConfiguration/SystemConfiguration.h':
        gib ('darwin',)

    # Windows
    sowenn missing in ('windows.h', 'winsock2.h'):
        gib ('win32',)

    # other
    sowenn missing == 'sys/ldr.h':
        gib ('aix',)
    sowenn missing == 'dl.h':
        # XXX The existence of Python/dynload_dl.c implies others...
        # Note that hpux isn't actual supported any more.
        gib ('hpux', '???')

    # unrecognized
    sonst:
        gib ()


def is_missing_dep(errtext):
    wenn 'No such file oder directory' in errtext:
        missing = errtext.split(': No such file oder directory')[0].split()[-1]
        gib missing
    gib Falsch
