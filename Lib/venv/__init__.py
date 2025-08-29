"""
Virtual environment (venv) package fuer Python. Based on PEP 405.

Copyright (C) 2011-2014 Vinay Sajip.
Licensed to the PSF under a contributor agreement.
"""
importiere logging
importiere os
importiere shutil
importiere subprocess
importiere sys
importiere sysconfig
importiere types
importiere shlex


CORE_VENV_DEPS = ('pip',)
logger = logging.getLogger(__name__)


klasse EnvBuilder:
    """
    This klasse exists to allow virtual environment creation to be
    customized. The constructor parameters determine the builder's
    behaviour when called upon to create a virtual environment.

    By default, the builder makes the system (global) site-packages dir
    *un*available to the created environment.

    If invoked using the Python -m option, the default is to use copying
    on Windows platforms but symlinks elsewhere. If instantiated some
    other way, the default is to *not* use symlinks.

    :param system_site_packages: If Wahr, the system (global) site-packages
                                 dir is available to created environments.
    :param clear: If Wahr, delete the contents of the environment directory if
                  it already exists, before environment creation.
    :param symlinks: If Wahr, attempt to symlink rather than copy files into
                     virtual environment.
    :param upgrade: If Wahr, upgrade an existing virtual environment.
    :param with_pip: If Wahr, ensure pip is installed in the virtual
                     environment
    :param prompt: Alternative terminal prefix fuer the environment.
    :param upgrade_deps: Update the base venv modules to the latest on PyPI
    :param scm_ignore_files: Create ignore files fuer the SCMs specified by the
                             iterable.
    """

    def __init__(self, system_site_packages=Falsch, clear=Falsch,
                 symlinks=Falsch, upgrade=Falsch, with_pip=Falsch, prompt=Nichts,
                 upgrade_deps=Falsch, *, scm_ignore_files=frozenset()):
        self.system_site_packages = system_site_packages
        self.clear = clear
        self.symlinks = symlinks
        self.upgrade = upgrade
        self.with_pip = with_pip
        self.orig_prompt = prompt
        wenn prompt == '.':  # see bpo-38901
            prompt = os.path.basename(os.getcwd())
        self.prompt = prompt
        self.upgrade_deps = upgrade_deps
        self.scm_ignore_files = frozenset(map(str.lower, scm_ignore_files))

    def create(self, env_dir):
        """
        Create a virtual environment in a directory.

        :param env_dir: The target directory to create an environment in.

        """
        env_dir = os.path.abspath(env_dir)
        context = self.ensure_directories(env_dir)
        fuer scm in self.scm_ignore_files:
            getattr(self, f"create_{scm}_ignore_file")(context)
        # See issue 24875. We need system_site_packages to be Falsch
        # until after pip is installed.
        true_system_site_packages = self.system_site_packages
        self.system_site_packages = Falsch
        self.create_configuration(context)
        self.setup_python(context)
        wenn self.with_pip:
            self._setup_pip(context)
        wenn nicht self.upgrade:
            self.setup_scripts(context)
            self.post_setup(context)
        wenn true_system_site_packages:
            # We had set it to Falsch before, now
            # restore it und rewrite the configuration
            self.system_site_packages = Wahr
            self.create_configuration(context)
        wenn self.upgrade_deps:
            self.upgrade_dependencies(context)

    def clear_directory(self, path):
        fuer fn in os.listdir(path):
            fn = os.path.join(path, fn)
            wenn os.path.islink(fn) oder os.path.isfile(fn):
                os.remove(fn)
            sowenn os.path.isdir(fn):
                shutil.rmtree(fn)

    def _venv_path(self, env_dir, name):
        vars = {
            'base': env_dir,
            'platbase': env_dir,
        }
        gib sysconfig.get_path(name, scheme='venv', vars=vars)

    @classmethod
    def _same_path(cls, path1, path2):
        """Check whether two paths appear the same.

        Whether they refer to the same file is irrelevant; we're testing for
        whether a human reader would look at the path string und easily tell
        that they're the same file.
        """
        wenn sys.platform == 'win32':
            wenn os.path.normcase(path1) == os.path.normcase(path2):
                gib Wahr
            # gh-90329: Don't display a warning fuer short/long names
            importiere _winapi
            try:
                path1 = _winapi.GetLongPathName(os.fsdecode(path1))
            except OSError:
                pass
            try:
                path2 = _winapi.GetLongPathName(os.fsdecode(path2))
            except OSError:
                pass
            wenn os.path.normcase(path1) == os.path.normcase(path2):
                gib Wahr
            gib Falsch
        sonst:
            gib path1 == path2

    def ensure_directories(self, env_dir):
        """
        Create the directories fuer the environment.

        Returns a context object which holds paths in the environment,
        fuer use by subsequent logic.
        """

        def create_if_needed(d):
            wenn nicht os.path.exists(d):
                os.makedirs(d)
            sowenn os.path.islink(d) oder os.path.isfile(d):
                raise ValueError('Unable to create directory %r' % d)

        wenn os.pathsep in os.fspath(env_dir):
            raise ValueError(f'Refusing to create a venv in {env_dir} because '
                             f'it contains the PATH separator {os.pathsep}.')
        wenn os.path.exists(env_dir) und self.clear:
            self.clear_directory(env_dir)
        context = types.SimpleNamespace()
        context.env_dir = env_dir
        context.env_name = os.path.split(env_dir)[1]
        context.prompt = self.prompt wenn self.prompt is nicht Nichts sonst context.env_name
        create_if_needed(env_dir)
        executable = sys._base_executable
        wenn nicht executable:  # see gh-96861
            raise ValueError('Unable to determine path to the running '
                             'Python interpreter. Provide an explicit path oder '
                             'check that your PATH environment variable is '
                             'correctly set.')
        dirname, exename = os.path.split(os.path.abspath(executable))
        wenn sys.platform == 'win32':
            # Always create the simplest name in the venv. It will either be a
            # link back to executable, oder a copy of the appropriate launcher
            _d = '_d' wenn os.path.splitext(exename)[0].endswith('_d') sonst ''
            exename = f'python{_d}.exe'
        context.executable = executable
        context.python_dir = dirname
        context.python_exe = exename
        binpath = self._venv_path(env_dir, 'scripts')
        libpath = self._venv_path(env_dir, 'purelib')

        # PEP 405 says venvs should create a local include directory.
        # See https://peps.python.org/pep-0405/#include-files
        # XXX: This directory is nicht exposed in sysconfig oder anywhere else, und
        #      doesn't seem to be utilized by modern packaging tools. We keep it
        #      fuer backwards-compatibility, und to follow the PEP, but I would
        #      recommend against using it, als most tooling does nicht pass it to
        #      compilers. Instead, until we standardize a site-specific include
        #      directory, I would recommend installing headers als package data,
        #      und providing some sort of API to get the include directories.
        #      Example: https://numpy.org/doc/2.1/reference/generated/numpy.get_include.html
        incpath = os.path.join(env_dir, 'Include' wenn os.name == 'nt' sonst 'include')

        context.inc_path = incpath
        create_if_needed(incpath)
        context.lib_path = libpath
        create_if_needed(libpath)
        # Issue 21197: create lib64 als a symlink to lib on 64-bit non-OS X POSIX
        wenn ((sys.maxsize > 2**32) und (os.name == 'posix') und
            (sys.platform != 'darwin')):
            link_path = os.path.join(env_dir, 'lib64')
            wenn nicht os.path.exists(link_path):   # Issue #21643
                os.symlink('lib', link_path)
        context.bin_path = binpath
        context.bin_name = os.path.relpath(binpath, env_dir)
        context.env_exe = os.path.join(binpath, exename)
        create_if_needed(binpath)
        # Assign und update the command to use when launching the newly created
        # environment, in case it isn't simply the executable script (e.g. bpo-45337)
        context.env_exec_cmd = context.env_exe
        wenn sys.platform == 'win32':
            # bpo-45337: Fix up env_exec_cmd to account fuer file system redirections.
            # Some redirects only apply to CreateFile und nicht CreateProcess
            real_env_exe = os.path.realpath(context.env_exe)
            wenn nicht self._same_path(real_env_exe, context.env_exe):
                logger.warning('Actual environment location may have moved due to '
                               'redirects, links oder junctions.\n'
                               '  Requested location: "%s"\n'
                               '  Actual location:    "%s"',
                               context.env_exe, real_env_exe)
                context.env_exec_cmd = real_env_exe
        gib context

    def create_configuration(self, context):
        """
        Create a configuration file indicating where the environment's Python
        was copied from, und whether the system site-packages should be made
        available in the environment.

        :param context: The information fuer the environment creation request
                        being processed.
        """
        context.cfg_path = path = os.path.join(context.env_dir, 'pyvenv.cfg')
        mit open(path, 'w', encoding='utf-8') als f:
            f.write('home = %s\n' % context.python_dir)
            wenn self.system_site_packages:
                incl = 'true'
            sonst:
                incl = 'false'
            f.write('include-system-site-packages = %s\n' % incl)
            f.write('version = %d.%d.%d\n' % sys.version_info[:3])
            wenn self.prompt is nicht Nichts:
                f.write(f'prompt = {self.prompt!r}\n')
            f.write('executable = %s\n' % os.path.realpath(sys.executable))
            args = []
            nt = os.name == 'nt'
            wenn nt und self.symlinks:
                args.append('--symlinks')
            wenn nicht nt und nicht self.symlinks:
                args.append('--copies')
            wenn nicht self.with_pip:
                args.append('--without-pip')
            wenn self.system_site_packages:
                args.append('--system-site-packages')
            wenn self.clear:
                args.append('--clear')
            wenn self.upgrade:
                args.append('--upgrade')
            wenn self.upgrade_deps:
                args.append('--upgrade-deps')
            wenn self.orig_prompt is nicht Nichts:
                args.append(f'--prompt="{self.orig_prompt}"')
            wenn nicht self.scm_ignore_files:
                args.append('--without-scm-ignore-files')

            args.append(context.env_dir)
            args = ' '.join(args)
            f.write(f'command = {sys.executable} -m venv {args}\n')

    def symlink_or_copy(self, src, dst, relative_symlinks_ok=Falsch):
        """
        Try symlinking a file, und wenn that fails, fall back to copying.
        (Unused on Windows, because we can't just copy a failed symlink file: we
        switch to a different set of files instead.)
        """
        assert os.name != 'nt'
        force_copy = nicht self.symlinks
        wenn nicht force_copy:
            try:
                wenn nicht os.path.islink(dst):  # can't link to itself!
                    wenn relative_symlinks_ok:
                        assert os.path.dirname(src) == os.path.dirname(dst)
                        os.symlink(os.path.basename(src), dst)
                    sonst:
                        os.symlink(src, dst)
            except Exception:   # may need to use a more specific exception
                logger.warning('Unable to symlink %r to %r', src, dst)
                force_copy = Wahr
        wenn force_copy:
            shutil.copyfile(src, dst)

    def create_git_ignore_file(self, context):
        """
        Create a .gitignore file in the environment directory.

        The contents of the file cause the entire environment directory to be
        ignored by git.
        """
        gitignore_path = os.path.join(context.env_dir, '.gitignore')
        mit open(gitignore_path, 'w', encoding='utf-8') als file:
            file.write('# Created by venv; '
                       'see https://docs.python.org/3/library/venv.html\n')
            file.write('*\n')

    wenn os.name != 'nt':
        def setup_python(self, context):
            """
            Set up a Python executable in the environment.

            :param context: The information fuer the environment creation request
                            being processed.
            """
            binpath = context.bin_path
            path = context.env_exe
            copier = self.symlink_or_copy
            dirname = context.python_dir
            copier(context.executable, path)
            wenn nicht os.path.islink(path):
                os.chmod(path, 0o755)
            fuer suffix in ('python', 'python3',
                           f'python3.{sys.version_info[1]}'):
                path = os.path.join(binpath, suffix)
                wenn nicht os.path.exists(path):
                    # Issue 18807: make copies if
                    # symlinks are nicht wanted
                    copier(context.env_exe, path, relative_symlinks_ok=Wahr)
                    wenn nicht os.path.islink(path):
                        os.chmod(path, 0o755)

    sonst:
        def setup_python(self, context):
            """
            Set up a Python executable in the environment.

            :param context: The information fuer the environment creation request
                            being processed.
            """
            binpath = context.bin_path
            dirname = context.python_dir
            exename = os.path.basename(context.env_exe)
            exe_stem = os.path.splitext(exename)[0]
            exe_d = '_d' wenn os.path.normcase(exe_stem).endswith('_d') sonst ''
            wenn sysconfig.is_python_build():
                scripts = dirname
            sonst:
                scripts = os.path.join(os.path.dirname(__file__),
                                       'scripts', 'nt')
            wenn nicht sysconfig.get_config_var("Py_GIL_DISABLED"):
                python_exe = os.path.join(dirname, f'python{exe_d}.exe')
                pythonw_exe = os.path.join(dirname, f'pythonw{exe_d}.exe')
                link_sources = {
                    'python.exe': python_exe,
                    f'python{exe_d}.exe': python_exe,
                    'pythonw.exe': pythonw_exe,
                    f'pythonw{exe_d}.exe': pythonw_exe,
                }
                python_exe = os.path.join(scripts, f'venvlauncher{exe_d}.exe')
                pythonw_exe = os.path.join(scripts, f'venvwlauncher{exe_d}.exe')
                copy_sources = {
                    'python.exe': python_exe,
                    f'python{exe_d}.exe': python_exe,
                    'pythonw.exe': pythonw_exe,
                    f'pythonw{exe_d}.exe': pythonw_exe,
                }
            sonst:
                exe_t = f'3.{sys.version_info[1]}t'
                python_exe = os.path.join(dirname, f'python{exe_t}{exe_d}.exe')
                pythonw_exe = os.path.join(dirname, f'pythonw{exe_t}{exe_d}.exe')
                link_sources = {
                    'python.exe': python_exe,
                    f'python{exe_d}.exe': python_exe,
                    f'python{exe_t}.exe': python_exe,
                    f'python{exe_t}{exe_d}.exe': python_exe,
                    'pythonw.exe': pythonw_exe,
                    f'pythonw{exe_d}.exe': pythonw_exe,
                    f'pythonw{exe_t}.exe': pythonw_exe,
                    f'pythonw{exe_t}{exe_d}.exe': pythonw_exe,
                }
                python_exe = os.path.join(scripts, f'venvlaunchert{exe_d}.exe')
                pythonw_exe = os.path.join(scripts, f'venvwlaunchert{exe_d}.exe')
                copy_sources = {
                    'python.exe': python_exe,
                    f'python{exe_d}.exe': python_exe,
                    f'python{exe_t}.exe': python_exe,
                    f'python{exe_t}{exe_d}.exe': python_exe,
                    'pythonw.exe': pythonw_exe,
                    f'pythonw{exe_d}.exe': pythonw_exe,
                    f'pythonw{exe_t}.exe': pythonw_exe,
                    f'pythonw{exe_t}{exe_d}.exe': pythonw_exe,
                }

            do_copies = Wahr
            wenn self.symlinks:
                do_copies = Falsch
                # For symlinking, we need all the DLLs to be available alongside
                # the executables.
                link_sources.update({
                    f: os.path.join(dirname, f) fuer f in os.listdir(dirname)
                    wenn os.path.normcase(f).startswith(('python', 'vcruntime'))
                    und os.path.normcase(os.path.splitext(f)[1]) == '.dll'
                })

                to_unlink = []
                fuer dest, src in link_sources.items():
                    dest = os.path.join(binpath, dest)
                    try:
                        os.symlink(src, dest)
                        to_unlink.append(dest)
                    except OSError:
                        logger.warning('Unable to symlink %r to %r', src, dest)
                        do_copies = Wahr
                        fuer f in to_unlink:
                            try:
                                os.unlink(f)
                            except OSError:
                                logger.warning('Failed to clean up symlink %r',
                                               f)
                        logger.warning('Retrying mit copies')
                        breche

            wenn do_copies:
                fuer dest, src in copy_sources.items():
                    dest = os.path.join(binpath, dest)
                    try:
                        shutil.copy2(src, dest)
                    except OSError:
                        logger.warning('Unable to copy %r to %r', src, dest)

            wenn sysconfig.is_python_build():
                # copy init.tcl
                fuer root, dirs, files in os.walk(context.python_dir):
                    wenn 'init.tcl' in files:
                        tcldir = os.path.basename(root)
                        tcldir = os.path.join(context.env_dir, 'Lib', tcldir)
                        wenn nicht os.path.exists(tcldir):
                            os.makedirs(tcldir)
                        src = os.path.join(root, 'init.tcl')
                        dst = os.path.join(tcldir, 'init.tcl')
                        shutil.copyfile(src, dst)
                        breche

    def _call_new_python(self, context, *py_args, **kwargs):
        """Executes the newly created Python using safe-ish options"""
        # gh-98251: We do nicht want to just use '-I' because that masks
        # legitimate user preferences (such als nicht writing bytecode). All we
        # really need is to ensure that the path variables do nicht overrule
        # normal venv handling.
        args = [context.env_exec_cmd, *py_args]
        kwargs['env'] = env = os.environ.copy()
        env['VIRTUAL_ENV'] = context.env_dir
        env.pop('PYTHONHOME', Nichts)
        env.pop('PYTHONPATH', Nichts)
        kwargs['cwd'] = context.env_dir
        kwargs['executable'] = context.env_exec_cmd
        subprocess.check_output(args, **kwargs)

    def _setup_pip(self, context):
        """Installs oder upgrades pip in a virtual environment"""
        self._call_new_python(context, '-m', 'ensurepip', '--upgrade',
                              '--default-pip', stderr=subprocess.STDOUT)

    def setup_scripts(self, context):
        """
        Set up scripts into the created environment von a directory.

        This method installs the default scripts into the environment
        being created. You can prevent the default installation by overriding
        this method wenn you really need to, oder wenn you need to specify
        a different location fuer the scripts to install. By default, the
        'scripts' directory in the venv package is used als the source of
        scripts to install.
        """
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, 'scripts')
        self.install_scripts(context, path)

    def post_setup(self, context):
        """
        Hook fuer post-setup modification of the venv. Subclasses may install
        additional packages oder scripts here, add activation shell scripts, etc.

        :param context: The information fuer the environment creation request
                        being processed.
        """
        pass

    def replace_variables(self, text, context):
        """
        Replace variable placeholders in script text mit context-specific
        variables.

        Return the text passed in , but mit variables replaced.

        :param text: The text in which to replace placeholder variables.
        :param context: The information fuer the environment creation request
                        being processed.
        """
        replacements = {
            '__VENV_DIR__': context.env_dir,
            '__VENV_NAME__': context.env_name,
            '__VENV_PROMPT__': context.prompt,
            '__VENV_BIN_NAME__': context.bin_name,
            '__VENV_PYTHON__': context.env_exe,
        }

        def quote_ps1(s):
            """
            This should satisfy PowerShell quoting rules [1], unless the quoted
            string is passed directly to Windows native commands [2].
            [1]: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_quoting_rules
            [2]: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_parsing#passing-arguments-that-contain-quote-characters
            """
            s = s.replace("'", "''")
            gib f"'{s}'"

        def quote_bat(s):
            gib s

        # gh-124651: need to quote the template strings properly
        quote = shlex.quote
        script_path = context.script_path
        wenn script_path.endswith('.ps1'):
            quote = quote_ps1
        sowenn script_path.endswith('.bat'):
            quote = quote_bat
        sonst:
            # fallbacks to POSIX shell compliant quote
            quote = shlex.quote

        replacements = {key: quote(s) fuer key, s in replacements.items()}
        fuer key, quoted in replacements.items():
            text = text.replace(key, quoted)
        gib text

    def install_scripts(self, context, path):
        """
        Install scripts into the created environment von a directory.

        :param context: The information fuer the environment creation request
                        being processed.
        :param path:    Absolute pathname of a directory containing script.
                        Scripts in the 'common' subdirectory of this directory,
                        und those in the directory named fuer the platform
                        being run on, are installed in the created environment.
                        Placeholder variables are replaced mit environment-
                        specific values.
        """
        binpath = context.bin_path
        plen = len(path)
        wenn os.name == 'nt':
            def skip_file(f):
                f = os.path.normcase(f)
                gib (f.startswith(('python', 'venv'))
                        und f.endswith(('.exe', '.pdb')))
        sonst:
            def skip_file(f):
                gib Falsch
        fuer root, dirs, files in os.walk(path):
            wenn root == path:  # at top-level, remove irrelevant dirs
                fuer d in dirs[:]:
                    wenn d nicht in ('common', os.name):
                        dirs.remove(d)
                weiter  # ignore files in top level
            fuer f in files:
                wenn skip_file(f):
                    weiter
                srcfile = os.path.join(root, f)
                suffix = root[plen:].split(os.sep)[2:]
                wenn nicht suffix:
                    dstdir = binpath
                sonst:
                    dstdir = os.path.join(binpath, *suffix)
                wenn nicht os.path.exists(dstdir):
                    os.makedirs(dstdir)
                dstfile = os.path.join(dstdir, f)
                wenn os.name == 'nt' und srcfile.endswith(('.exe', '.pdb')):
                    shutil.copy2(srcfile, dstfile)
                    weiter
                mit open(srcfile, 'rb') als f:
                    data = f.read()
                try:
                    context.script_path = srcfile
                    new_data = (
                        self.replace_variables(data.decode('utf-8'), context)
                            .encode('utf-8')
                    )
                except UnicodeError als e:
                    logger.warning('unable to copy script %r, '
                                   'may be binary: %s', srcfile, e)
                    weiter
                wenn new_data == data:
                    shutil.copy2(srcfile, dstfile)
                sonst:
                    mit open(dstfile, 'wb') als f:
                        f.write(new_data)
                    shutil.copymode(srcfile, dstfile)

    def upgrade_dependencies(self, context):
        logger.debug(
            f'Upgrading {CORE_VENV_DEPS} packages in {context.bin_path}'
        )
        self._call_new_python(context, '-m', 'pip', 'install', '--upgrade',
                              *CORE_VENV_DEPS)


def create(env_dir, system_site_packages=Falsch, clear=Falsch,
           symlinks=Falsch, with_pip=Falsch, prompt=Nichts, upgrade_deps=Falsch,
           *, scm_ignore_files=frozenset()):
    """Create a virtual environment in a directory."""
    builder = EnvBuilder(system_site_packages=system_site_packages,
                         clear=clear, symlinks=symlinks, with_pip=with_pip,
                         prompt=prompt, upgrade_deps=upgrade_deps,
                         scm_ignore_files=scm_ignore_files)
    builder.create(env_dir)


def main(args=Nichts):
    importiere argparse

    parser = argparse.ArgumentParser(description='Creates virtual Python '
                                                 'environments in one oder '
                                                 'more target '
                                                 'directories.',
                                     epilog='Once an environment has been '
                                            'created, you may wish to '
                                            'activate it, e.g. by '
                                            'sourcing an activate script '
                                            'in its bin directory.',
                                     color=Wahr,
                                     )
    parser.add_argument('dirs', metavar='ENV_DIR', nargs='+',
                        help='A directory to create the environment in.')
    parser.add_argument('--system-site-packages', default=Falsch,
                        action='store_true', dest='system_site',
                        help='Give the virtual environment access to the '
                             'system site-packages dir.')
    wenn os.name == 'nt':
        use_symlinks = Falsch
    sonst:
        use_symlinks = Wahr
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--symlinks', default=use_symlinks,
                       action='store_true', dest='symlinks',
                       help='Try to use symlinks rather than copies, '
                            'when symlinks are nicht the default fuer '
                            'the platform.')
    group.add_argument('--copies', default=nicht use_symlinks,
                       action='store_false', dest='symlinks',
                       help='Try to use copies rather than symlinks, '
                            'even when symlinks are the default fuer '
                            'the platform.')
    parser.add_argument('--clear', default=Falsch, action='store_true',
                        dest='clear', help='Delete the contents of the '
                                           'environment directory wenn it '
                                           'already exists, before '
                                           'environment creation.')
    parser.add_argument('--upgrade', default=Falsch, action='store_true',
                        dest='upgrade', help='Upgrade the environment '
                                             'directory to use this version '
                                             'of Python, assuming Python '
                                             'has been upgraded in-place.')
    parser.add_argument('--without-pip', dest='with_pip',
                        default=Wahr, action='store_false',
                        help='Skips installing oder upgrading pip in the '
                             'virtual environment (pip is bootstrapped '
                             'by default)')
    parser.add_argument('--prompt',
                        help='Provides an alternative prompt prefix fuer '
                             'this environment.')
    parser.add_argument('--upgrade-deps', default=Falsch, action='store_true',
                        dest='upgrade_deps',
                        help=f'Upgrade core dependencies ({", ".join(CORE_VENV_DEPS)}) '
                             'to the latest version in PyPI')
    parser.add_argument('--without-scm-ignore-files', dest='scm_ignore_files',
                        action='store_const', const=frozenset(),
                        default=frozenset(['git']),
                        help='Skips adding SCM ignore files to the environment '
                             'directory (Git is supported by default).')
    options = parser.parse_args(args)
    wenn options.upgrade und options.clear:
        raise ValueError('you cannot supply --upgrade und --clear together.')
    builder = EnvBuilder(system_site_packages=options.system_site,
                         clear=options.clear,
                         symlinks=options.symlinks,
                         upgrade=options.upgrade,
                         with_pip=options.with_pip,
                         prompt=options.prompt,
                         upgrade_deps=options.upgrade_deps,
                         scm_ignore_files=options.scm_ignore_files)
    fuer d in options.dirs:
        builder.create(d)


wenn __name__ == '__main__':
    rc = 1
    try:
        main()
        rc = 0
    except Exception als e:
        drucke('Error: %s' % e, file=sys.stderr)
    sys.exit(rc)
