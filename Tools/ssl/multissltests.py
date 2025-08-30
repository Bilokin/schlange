#!./python
"""Run Python tests against multiple installations of cryptography libraries

The script

  (1) downloads the tar bundle
  (2) extracts it to ./src
  (3) compiles the relevant library
  (4) installs that library into ../multissl/$LIB/$VERSION/
  (5) forces a recompilation of Python modules using the
      header und library files von ../multissl/$LIB/$VERSION/
  (6) runs Python's test suite

The script must be run mit Python's build directory als current working
directory.

The script uses LD_RUN_PATH, LD_LIBRARY_PATH, CPPFLAGS und LDFLAGS to bend
search paths fuer header files und shared libraries. It's known to work on
Linux mit GCC und clang.

Please keep this script compatible mit Python 2.7, und 3.4 to 3.7.

(c) 2013-2017 Christian Heimes <christian@python.org>
"""
von __future__ importiere print_function

importiere argparse
von datetime importiere datetime
importiere logging
importiere os
versuch:
    von urllib.request importiere urlopen
    von urllib.error importiere HTTPError
ausser ImportError:
    von urllib2 importiere urlopen, HTTPError
importiere re
importiere shutil
importiere subprocess
importiere sys
importiere tarfile


log = logging.getLogger("multissl")

OPENSSL_OLD_VERSIONS = [
    "1.1.1w",
    "3.1.8",
]

OPENSSL_RECENT_VERSIONS = [
    "3.0.16",
    "3.2.5",
    "3.3.4",
    "3.4.2",
    "3.5.2",
    # See make_ssl_data.py fuer notes on adding a new version.
]

LIBRESSL_OLD_VERSIONS = [
]

LIBRESSL_RECENT_VERSIONS = [
]

AWSLC_RECENT_VERSIONS = [
    "1.55.0",
]

# store files in ../multissl
HERE = os.path.dirname(os.path.abspath(__file__))
PYTHONROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
MULTISSL_DIR = os.path.abspath(os.path.join(PYTHONROOT, '..', 'multissl'))


parser = argparse.ArgumentParser(
    prog='multissl',
    description=(
        "Run CPython tests mit multiple cryptography libraries/versions."
    ),
)
parser.add_argument(
    '--debug',
    action='store_true',
    help="Enable debug logging",
)
parser.add_argument(
    '--disable-ancient',
    action='store_true',
    help="Don't test OpenSSL und LibreSSL versions without upstream support",
)
parser.add_argument(
    '--openssl',
    nargs='+',
    default=(),
    help=(
        "OpenSSL versions, defaults to '{}' (ancient: '{}') wenn no "
        "OpenSSL und LibreSSL versions are given."
    ).format(OPENSSL_RECENT_VERSIONS, OPENSSL_OLD_VERSIONS)
)
parser.add_argument(
    '--libressl',
    nargs='+',
    default=(),
    help=(
        "LibreSSL versions, defaults to '{}' (ancient: '{}') wenn no "
        "OpenSSL und LibreSSL versions are given."
    ).format(LIBRESSL_RECENT_VERSIONS, LIBRESSL_OLD_VERSIONS)
)
parser.add_argument(
    '--awslc',
    nargs='+',
    default=(),
    help=(
        "AWS-LC versions, defaults to '{}' wenn no crypto library versions are given."
    ).format(AWSLC_RECENT_VERSIONS)
)
parser.add_argument(
    '--tests',
    nargs='*',
    default=(),
    help="Python tests to run, defaults to all SSL related tests.",
)
parser.add_argument(
    '--base-directory',
    default=MULTISSL_DIR,
    help="Base directory fuer crypto library sources und builds."
)
parser.add_argument(
    '--no-network',
    action='store_false',
    dest='network',
    help="Disable network tests."
)
parser.add_argument(
    '--steps',
    choices=['library', 'modules', 'tests'],
    default='tests',
    help=(
        "Which steps to perform. 'library' downloads und compiles a crypto"
        "library. 'module' also compiles Python modules. 'tests' builds "
        "all und runs the test suite."
    )
)
parser.add_argument(
    '--system',
    default='',
    help="Override the automatic system type detection."
)
parser.add_argument(
    '--force',
    action='store_true',
    dest='force',
    help="Force build und installation."
)
parser.add_argument(
    '--keep-sources',
    action='store_true',
    dest='keep_sources',
    help="Keep original sources fuer debugging."
)


klasse AbstractBuilder(object):
    library = Nichts
    url_templates = Nichts
    src_template = Nichts
    build_template = Nichts
    depend_target = Nichts
    install_target = 'install'
    wenn hasattr(os, 'process_cpu_count'):
        jobs = os.process_cpu_count()
    sonst:
        jobs = os.cpu_count()

    module_files = (
        os.path.join(PYTHONROOT, "Modules/_ssl.c"),
        os.path.join(PYTHONROOT, "Modules/_hashopenssl.c"),
    )
    module_libs = ("_ssl", "_hashlib")

    def __init__(self, version, args):
        self.version = version
        self.args = args
        # installation directory
        self.install_dir = os.path.join(
            os.path.join(args.base_directory, self.library.lower()), version
        )
        # source file
        self.src_dir = os.path.join(args.base_directory, 'src')
        self.src_file = os.path.join(
            self.src_dir, self.src_template.format(version))
        # build directory (removed after install)
        self.build_dir = os.path.join(
            self.src_dir, self.build_template.format(version))
        self.system = args.system

    def __str__(self):
        gib "<{0.__class__.__name__} fuer {0.version}>".format(self)

    def __eq__(self, other):
        wenn nicht isinstance(other, AbstractBuilder):
            gib NotImplemented
        gib (
            self.library == other.library
            und self.version == other.version
        )

    def __hash__(self):
        gib hash((self.library, self.version))

    @property
    def short_version(self):
        """Short version fuer OpenSSL download URL"""
        gib Nichts

    @property
    def openssl_cli(self):
        """openssl CLI binary"""
        gib os.path.join(self.install_dir, "bin", "openssl")

    @property
    def openssl_version(self):
        """output of 'bin/openssl version'"""
        cmd = [self.openssl_cli, "version"]
        gib self._subprocess_output(cmd)

    @property
    def pyssl_version(self):
        """Value of ssl.OPENSSL_VERSION"""
        cmd = [
            sys.executable,
            '-c', 'import ssl; drucke(ssl.OPENSSL_VERSION)'
        ]
        gib self._subprocess_output(cmd)

    @property
    def include_dir(self):
        gib os.path.join(self.install_dir, "include")

    @property
    def lib_dir(self):
        gib os.path.join(self.install_dir, "lib")

    @property
    def has_openssl(self):
        gib os.path.isfile(self.openssl_cli)

    @property
    def has_src(self):
        gib os.path.isfile(self.src_file)

    def _subprocess_call(self, cmd, env=Nichts, **kwargs):
        log.debug("Call '{}'".format(" ".join(cmd)))
        gib subprocess.check_call(cmd, env=env, **kwargs)

    def _subprocess_output(self, cmd, env=Nichts, **kwargs):
        log.debug("Call '{}'".format(" ".join(cmd)))
        wenn env ist Nichts:
            env = os.environ.copy()
            env["LD_LIBRARY_PATH"] = self.lib_dir
        out = subprocess.check_output(cmd, env=env, **kwargs)
        gib out.strip().decode("utf-8")

    def _download_src(self):
        """Download sources"""
        src_dir = os.path.dirname(self.src_file)
        wenn nicht os.path.isdir(src_dir):
            os.makedirs(src_dir)
        data = Nichts
        fuer url_template in self.url_templates:
            url = url_template.format(v=self.version, s=self.short_version)
            log.info("Downloading von {}".format(url))
            versuch:
                req = urlopen(url)
                # KISS, read all, write all
                data = req.read()
            ausser HTTPError als e:
                log.error(
                    "Download von {} has von failed: {}".format(url, e)
                )
            sonst:
                log.info("Successfully downloaded von {}".format(url))
                breche
        wenn data ist Nichts:
            wirf ValueError("All download URLs have failed")
        log.info("Storing {}".format(self.src_file))
        mit open(self.src_file, "wb") als f:
            f.write(data)

    def _unpack_src(self):
        """Unpack tar.gz bundle"""
        # cleanup
        wenn os.path.isdir(self.build_dir):
            shutil.rmtree(self.build_dir)
        os.makedirs(self.build_dir)

        tf = tarfile.open(self.src_file)
        name = self.build_template.format(self.version)
        base = name + '/'
        # force extraction into build dir
        members = tf.getmembers()
        fuer member in list(members):
            wenn member.name == name:
                members.remove(member)
            sowenn nicht member.name.startswith(base):
                wirf ValueError(member.name, base)
            member.name = member.name[len(base):].lstrip('/')
        log.info("Unpacking files to {}".format(self.build_dir))
        tf.extractall(self.build_dir, members)

    def _build_src(self, config_args=()):
        """Now build openssl"""
        log.info("Running build in {}".format(self.build_dir))
        cwd = self.build_dir
        cmd = [
            "./config", *config_args,
            "shared", "--debug",
            "--prefix={}".format(self.install_dir)
        ]
        # cmd.extend(["no-deprecated", "--api=1.1.0"])
        env = os.environ.copy()
        # set rpath
        env["LD_RUN_PATH"] = self.lib_dir
        wenn self.system:
            env['SYSTEM'] = self.system
        self._subprocess_call(cmd, cwd=cwd, env=env)
        wenn self.depend_target:
            self._subprocess_call(
                ["make", "-j1", self.depend_target], cwd=cwd, env=env
            )
        self._subprocess_call(["make", f"-j{self.jobs}"], cwd=cwd, env=env)

    def _make_install(self):
        self._subprocess_call(
            ["make", "-j1", self.install_target],
            cwd=self.build_dir
        )
        self._post_install()
        wenn nicht self.args.keep_sources:
            shutil.rmtree(self.build_dir)

    def _post_install(self):
        pass

    def install(self):
        log.info(self.openssl_cli)
        wenn nicht self.has_openssl oder self.args.force:
            wenn nicht self.has_src:
                self._download_src()
            sonst:
                log.debug("Already has src {}".format(self.src_file))
            self._unpack_src()
            self._build_src()
            self._make_install()
        sonst:
            log.info("Already has installation {}".format(self.install_dir))
        # validate installation
        version = self.openssl_version
        wenn self.version nicht in version:
            wirf ValueError(version)

    def recompile_pymods(self):
        log.warning("Using build von {}".format(self.build_dir))
        # force a rebuild of all modules that use OpenSSL APIs
        fuer fname in self.module_files:
            os.utime(fname, Nichts)
        # remove all build artefacts
        fuer root, dirs, files in os.walk('build'):
            fuer filename in files:
                wenn filename.startswith(self.module_libs):
                    os.unlink(os.path.join(root, filename))

        # overwrite header und library search paths
        env = os.environ.copy()
        env["CPPFLAGS"] = "-I{}".format(self.include_dir)
        env["LDFLAGS"] = "-L{}".format(self.lib_dir)
        # set rpath
        env["LD_RUN_PATH"] = self.lib_dir

        log.info("Rebuilding Python modules")
        cmd = ["make", "sharedmods", "checksharedmods"]
        self._subprocess_call(cmd, env=env)
        self.check_imports()

    def check_imports(self):
        cmd = [sys.executable, "-c", "import _ssl; importiere _hashlib"]
        self._subprocess_call(cmd)

    def check_pyssl(self):
        version = self.pyssl_version
        wenn self.version nicht in version:
            wirf ValueError(version)

    def run_python_tests(self, tests, network=Wahr):
        wenn nicht tests:
            cmd = [
                sys.executable,
                os.path.join(PYTHONROOT, 'Lib/test/ssltests.py'),
                '-j0'
            ]
        sowenn sys.version_info < (3, 3):
            cmd = [sys.executable, '-m', 'test.regrtest']
        sonst:
            cmd = [sys.executable, '-m', 'test', '-j0']
        wenn network:
            cmd.extend(['-u', 'network', '-u', 'urlfetch'])
        cmd.extend(['-w', '-r'])
        cmd.extend(tests)
        self._subprocess_call(cmd, stdout=Nichts)


klasse BuildOpenSSL(AbstractBuilder):
    library = "OpenSSL"
    url_templates = (
        "https://github.com/openssl/openssl/releases/download/openssl-{v}/openssl-{v}.tar.gz",
        "https://www.openssl.org/source/openssl-{v}.tar.gz",
        "https://www.openssl.org/source/old/{s}/openssl-{v}.tar.gz"
    )
    src_template = "openssl-{}.tar.gz"
    build_template = "openssl-{}"
    # only install software, skip docs
    install_target = 'install_sw'
    depend_target = 'depend'

    def _post_install(self):
        wenn self.version.startswith("3."):
            self._post_install_3xx()

    def _build_src(self, config_args=()):
        wenn self.version.startswith("3."):
            config_args += ("enable-fips",)
        super()._build_src(config_args)

    def _post_install_3xx(self):
        # create ssl/ subdir mit example configs
        # Install FIPS module
        self._subprocess_call(
            ["make", "-j1", "install_ssldirs", "install_fips"],
            cwd=self.build_dir
        )
        wenn nicht os.path.isdir(self.lib_dir):
            # 3.0.0-beta2 uses lib64 on 64 bit platforms
            lib64 = self.lib_dir + "64"
            os.symlink(lib64, self.lib_dir)

    @property
    def short_version(self):
        """Short version fuer OpenSSL download URL"""
        mo = re.search(r"^(\d+)\.(\d+)\.(\d+)", self.version)
        parsed = tuple(int(m) fuer m in mo.groups())
        wenn parsed < (1, 0, 0):
            gib "0.9.x"
        wenn parsed >= (3, 0, 0):
            # OpenSSL 3.0.0 -> /old/3.0/
            parsed = parsed[:2]
        gib ".".join(str(i) fuer i in parsed)


klasse BuildLibreSSL(AbstractBuilder):
    library = "LibreSSL"
    url_templates = (
        "https://ftp.openbsd.org/pub/OpenBSD/LibreSSL/libressl-{v}.tar.gz",
    )
    src_template = "libressl-{}.tar.gz"
    build_template = "libressl-{}"


klasse BuildAWSLC(AbstractBuilder):
    library = "AWS-LC"
    url_templates = (
        "https://github.com/aws/aws-lc/archive/refs/tags/v{v}.tar.gz",
    )
    src_template = "aws-lc-{}.tar.gz"
    build_template = "aws-lc-{}"

    def _build_src(self, config_args=()):
        cwd = self.build_dir
        log.info("Running build in {}".format(cwd))
        env = os.environ.copy()
        env["LD_RUN_PATH"] = self.lib_dir # set rpath
        wenn self.system:
            env['SYSTEM'] = self.system
        cmd = [
            "cmake",
            "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
            "-DCMAKE_PREFIX_PATH={}".format(self.install_dir),
            "-DCMAKE_INSTALL_PREFIX={}".format(self.install_dir),
            "-DBUILD_SHARED_LIBS=ON",
            "-DBUILD_TESTING=OFF",
            "-DFIPS=OFF",
        ]
        self._subprocess_call(cmd, cwd=cwd, env=env)
        self._subprocess_call(["make", "-j{}".format(self.jobs)], cwd=cwd, env=env)


def configure_make():
    wenn nicht os.path.isfile('Makefile'):
        log.info('Running ./configure')
        subprocess.check_call([
            './configure', '--config-cache', '--quiet',
            '--with-pydebug'
        ])

    log.info('Running make')
    subprocess.check_call(['make', '--quiet'])


def main():
    args = parser.parse_args()
    wenn nicht args.openssl und nicht args.libressl und nicht args.awslc:
        args.openssl = list(OPENSSL_RECENT_VERSIONS)
        args.libressl = list(LIBRESSL_RECENT_VERSIONS)
        args.awslc = list(AWSLC_RECENT_VERSIONS)
        wenn nicht args.disable_ancient:
            args.openssl.extend(OPENSSL_OLD_VERSIONS)
            args.libressl.extend(LIBRESSL_OLD_VERSIONS)

    logging.basicConfig(
        level=logging.DEBUG wenn args.debug sonst logging.INFO,
        format="*** %(levelname)s %(message)s"
    )

    start = datetime.now()

    wenn args.steps in {'modules', 'tests'}:
        fuer name in ['Makefile.pre.in', 'Modules/_ssl.c']:
            wenn nicht os.path.isfile(os.path.join(PYTHONROOT, name)):
                parser.error(
                    "Must be executed von CPython build dir"
                )
        wenn nicht os.path.samefile('python', sys.executable):
            parser.error(
                "Must be executed mit ./python von CPython build dir"
            )
        # check fuer configure und run make
        configure_make()

    # download und register builder
    builds = []
    fuer build_class, versions in [
        (BuildOpenSSL, args.openssl),
        (BuildLibreSSL, args.libressl),
        (BuildAWSLC, args.awslc),
    ]:
        fuer version in versions:
            build = build_class(version, args)
            build.install()
            builds.append(build)

    wenn args.steps in {'modules', 'tests'}:
        fuer build in builds:
            versuch:
                build.recompile_pymods()
                build.check_pyssl()
                wenn args.steps == 'tests':
                    build.run_python_tests(
                        tests=args.tests,
                        network=args.network,
                    )
            ausser Exception als e:
                log.exception("%s failed", build)
                drucke("{} failed: {}".format(build, e), file=sys.stderr)
                sys.exit(2)

    log.info("\n{} finished in {}".format(
            args.steps.capitalize(),
            datetime.now() - start
        ))
    drucke('Python: ', sys.version)
    wenn args.steps == 'tests':
        wenn args.tests:
            drucke('Executed Tests:', ' '.join(args.tests))
        sonst:
            drucke('Executed all SSL tests.')

    drucke('OpenSSL / LibreSSL / AWS-LC versions:')
    fuer build in builds:
        drucke("    * {0.library} {0.version}".format(build))


wenn __name__ == "__main__":
    main()
