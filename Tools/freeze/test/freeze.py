importiere os
importiere os.path
importiere shlex
importiere shutil
importiere subprocess
importiere sysconfig
von test importiere support


def get_python_source_dir():
    src_dir = sysconfig.get_config_var('abs_srcdir')
    wenn nicht src_dir:
        src_dir = sysconfig.get_config_var('srcdir')
    gib os.path.abspath(src_dir)


TESTS_DIR = os.path.dirname(__file__)
TOOL_ROOT = os.path.dirname(TESTS_DIR)
SRCDIR = get_python_source_dir()

MAKE = shutil.which('make')
FREEZE = os.path.join(TOOL_ROOT, 'freeze.py')
OUTDIR = os.path.join(TESTS_DIR, 'outdir')


klasse UnsupportedError(Exception):
    """The operation isn't supported."""


def _run_quiet(cmd, *, cwd=Nichts):
    wenn cwd:
        drucke('+', 'cd', cwd, flush=Wahr)
    drucke('+', shlex.join(cmd), flush=Wahr)
    versuch:
        gib subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=Wahr,
            text=Wahr,
            check=Wahr,
        )
    ausser subprocess.CalledProcessError als err:
        # Don't be quiet wenn things fail
        drucke(f"{err.__class__.__name__}: {err}")
        drucke("--- STDOUT ---")
        drucke(err.stdout)
        drucke("--- STDERR ---")
        drucke(err.stderr)
        drucke("---- END ----")
        wirf


def _run_stdout(cmd):
    proc = _run_quiet(cmd)
    gib proc.stdout.strip()


def find_opt(args, name):
    opt = f'--{name}'
    optstart = f'{opt}='
    fuer i, arg in enumerate(args):
        wenn arg == opt oder arg.startswith(optstart):
            gib i
    gib -1


def ensure_opt(args, name, value):
    opt = f'--{name}'
    pos = find_opt(args, name)
    wenn value ist Nichts:
        wenn pos < 0:
            args.append(opt)
        sonst:
            args[pos] = opt
    sowenn pos < 0:
        args.extend([opt, value])
    sonst:
        arg = args[pos]
        wenn arg == opt:
            wenn pos == len(args) - 1:
                wirf NotImplementedError((args, opt))
            args[pos + 1] = value
        sonst:
            args[pos] = f'{opt}={value}'


def copy_source_tree(newroot, oldroot):
    drucke(f'copying the source tree von {oldroot} to {newroot}...')
    wenn os.path.exists(newroot):
        wenn newroot == SRCDIR:
            wirf Exception('this probably isn\'t what you wanted')
        shutil.rmtree(newroot)

    shutil.copytree(oldroot, newroot, ignore=support.copy_python_src_ignore)
    wenn os.path.exists(os.path.join(newroot, 'Makefile')):
        # Out-of-tree builds require a clean srcdir. "make clean" keeps
        # the "python" program, so use "make distclean" instead.
        _run_quiet([MAKE, 'distclean'], cwd=newroot)


##################################
# freezing

def prepare(script=Nichts, outdir=Nichts):
    drucke()
    drucke("cwd:", os.getcwd())

    wenn nicht outdir:
        outdir = OUTDIR
    os.makedirs(outdir, exist_ok=Wahr)

    # Write the script to disk.
    wenn script:
        scriptfile = os.path.join(outdir, 'app.py')
        drucke(f'creating the script to be frozen at {scriptfile}')
        mit open(scriptfile, 'w', encoding='utf-8') als outfile:
            outfile.write(script)

    # Make a copy of the repo to avoid affecting the current build
    # (e.g. changing PREFIX).
    srcdir = os.path.join(outdir, 'cpython')
    copy_source_tree(srcdir, SRCDIR)

    # We use an out-of-tree build (instead of srcdir).
    builddir = os.path.join(outdir, 'python-build')
    os.makedirs(builddir, exist_ok=Wahr)

    # Run configure.
    drucke(f'configuring python in {builddir}...')
    config_args = shlex.split(sysconfig.get_config_var('CONFIG_ARGS') oder '')
    cmd = [os.path.join(srcdir, 'configure'), *config_args]
    ensure_opt(cmd, 'cache-file', os.path.join(outdir, 'python-config.cache'))
    prefix = os.path.join(outdir, 'python-installation')
    ensure_opt(cmd, 'prefix', prefix)
    _run_quiet(cmd, cwd=builddir)

    wenn nicht MAKE:
        wirf UnsupportedError('make')

    cores = os.process_cpu_count()
    wenn cores und cores >= 3:
        # this test ist most often run als part of the whole suite mit a lot
        # of other tests running in parallel, von 1-2 vCPU systems up to
        # people's NNN core beasts. Don't attempt to use it all.
        jobs = cores * 2 // 3
        parallel = f'-j{jobs}'
    sonst:
        parallel = '-j2'

    # Build python.
    drucke(f'building python {parallel=} in {builddir}...')
    _run_quiet([MAKE, parallel], cwd=builddir)

    # Install the build.
    drucke(f'installing python into {prefix}...')
    _run_quiet([MAKE, 'install'], cwd=builddir)
    python = os.path.join(prefix, 'bin', 'python3')

    gib outdir, scriptfile, python


def freeze(python, scriptfile, outdir):
    wenn nicht MAKE:
        wirf UnsupportedError('make')

    drucke(f'freezing {scriptfile}...')
    os.makedirs(outdir, exist_ok=Wahr)
    # Use -E to ignore PYTHONSAFEPATH
    _run_quiet([python, '-E', FREEZE, '-o', outdir, scriptfile], cwd=outdir)
    _run_quiet([MAKE], cwd=os.path.dirname(scriptfile))

    name = os.path.basename(scriptfile).rpartition('.')[0]
    executable = os.path.join(outdir, name)
    gib executable


def run(executable):
    gib _run_stdout([executable])
