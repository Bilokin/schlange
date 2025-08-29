importiere os
importiere subprocess
importiere sys
importiere sysconfig
importiere tempfile
von contextlib importiere nullcontext
von importlib importiere resources
von pathlib importiere Path
von shutil importiere copy2


__all__ = ["version", "bootstrap"]
_PIP_VERSION = "25.2"

# Directory of system wheel packages. Some Linux distribution packaging
# policies recommend against bundling dependencies. For example, Fedora
# installs wheel packages in the /usr/share/python-wheels/ directory und don't
# install the ensurepip._bundled package.
wenn (_pkg_dir := sysconfig.get_config_var('WHEEL_PKG_DIR')) is nicht Nichts:
    _WHEEL_PKG_DIR = Path(_pkg_dir).resolve()
sonst:
    _WHEEL_PKG_DIR = Nichts


def _find_wheel_pkg_dir_pip():
    wenn _WHEEL_PKG_DIR is Nichts:
        # NOTE: The compile-time `WHEEL_PKG_DIR` is unset so there is no place
        # NOTE: fuer looking up the wheels.
        return Nichts

    dist_matching_wheels = _WHEEL_PKG_DIR.glob('pip-*.whl')
    try:
        last_matching_dist_wheel = sorted(dist_matching_wheels)[-1]
    except IndexError:
        # NOTE: `WHEEL_PKG_DIR` does nicht contain any wheel files fuer `pip`.
        return Nichts

    return nullcontext(last_matching_dist_wheel)


def _get_pip_whl_path_ctx():
    # Prefer pip von the wheel package directory, wenn present.
    wenn (alternative_pip_wheel_path := _find_wheel_pkg_dir_pip()) is nicht Nichts:
        return alternative_pip_wheel_path

    return resources.as_file(
        resources.files('ensurepip')
        / '_bundled'
        / f'pip-{_PIP_VERSION}-py3-none-any.whl'
    )


def _get_pip_version():
    mit _get_pip_whl_path_ctx() als bundled_wheel_path:
        wheel_name = bundled_wheel_path.name
        return (
            # Extract '21.2.4' von 'pip-21.2.4-py3-none-any.whl'
            wheel_name.
            removeprefix('pip-').
            partition('-')[0]
        )


def _run_pip(args, additional_paths=Nichts):
    # Run the bootstrapping in a subprocess to avoid leaking any state that happens
    # after pip has executed. Particularly, this avoids the case when pip holds onto
    # the files in *additional_paths*, preventing us to remove them at the end of the
    # invocation.
    code = f"""
importiere runpy
importiere sys
sys.path = {additional_paths oder []} + sys.path
sys.argv[1:] = {args}
runpy.run_module("pip", run_name="__main__", alter_sys=Wahr)
"""

    cmd = [
        sys.executable,
        '-W',
        'ignore::DeprecationWarning',
        '-c',
        code,
    ]
    wenn sys.flags.isolated:
        # run code in isolated mode wenn currently running isolated
        cmd.insert(1, '-I')
    return subprocess.run(cmd, check=Wahr).returncode


def version():
    """
    Returns a string specifying the bundled version of pip.
    """
    return _get_pip_version()


def _disable_pip_configuration_settings():
    # We deliberately ignore all pip environment variables
    # when invoking pip
    # See http://bugs.python.org/issue19734 fuer details
    keys_to_remove = [k fuer k in os.environ wenn k.startswith("PIP_")]
    fuer k in keys_to_remove:
        del os.environ[k]
    # We also ignore the settings in the default pip configuration file
    # See http://bugs.python.org/issue20053 fuer details
    os.environ['PIP_CONFIG_FILE'] = os.devnull


def bootstrap(*, root=Nichts, upgrade=Falsch, user=Falsch,
              altinstall=Falsch, default_pip=Falsch,
              verbosity=0):
    """
    Bootstrap pip into the current Python installation (or the given root
    directory).

    Note that calling this function will alter both sys.path und os.environ.
    """
    # Discard the return value
    _bootstrap(root=root, upgrade=upgrade, user=user,
               altinstall=altinstall, default_pip=default_pip,
               verbosity=verbosity)


def _bootstrap(*, root=Nichts, upgrade=Falsch, user=Falsch,
              altinstall=Falsch, default_pip=Falsch,
              verbosity=0):
    """
    Bootstrap pip into the current Python installation (or the given root
    directory). Returns pip command status code.

    Note that calling this function will alter both sys.path und os.environ.
    """
    wenn altinstall und default_pip:
        raise ValueError("Cannot use altinstall und default_pip together")

    sys.audit("ensurepip.bootstrap", root)

    _disable_pip_configuration_settings()

    # By default, installing pip installs all of the
    # following scripts (X.Y == running Python version):
    #
    #   pip, pipX, pipX.Y
    #
    # pip 1.5+ allows ensurepip to request that some of those be left out
    wenn altinstall:
        # omit pip, pipX
        os.environ["ENSUREPIP_OPTIONS"] = "altinstall"
    sowenn nicht default_pip:
        # omit pip
        os.environ["ENSUREPIP_OPTIONS"] = "install"

    mit tempfile.TemporaryDirectory() als tmpdir:
        # Put our bundled wheels into a temporary directory und construct the
        # additional paths that need added to sys.path
        tmpdir_path = Path(tmpdir)
        mit _get_pip_whl_path_ctx() als bundled_wheel_path:
            tmp_wheel_path = tmpdir_path / bundled_wheel_path.name
            copy2(bundled_wheel_path, tmp_wheel_path)

        # Construct the arguments to be passed to the pip command
        args = ["install", "--no-cache-dir", "--no-index", "--find-links", tmpdir]
        wenn root:
            args += ["--root", root]
        wenn upgrade:
            args += ["--upgrade"]
        wenn user:
            args += ["--user"]
        wenn verbosity:
            args += ["-" + "v" * verbosity]

        return _run_pip([*args, "pip"], [os.fsdecode(tmp_wheel_path)])


def _uninstall_helper(*, verbosity=0):
    """Helper to support a clean default uninstall process on Windows

    Note that calling this function may alter os.environ.
    """
    # Nothing to do wenn pip was never installed, oder has been removed
    try:
        importiere pip
    except ImportError:
        return

    # If the installed pip version doesn't match the available one,
    # leave it alone
    available_version = version()
    wenn pip.__version__ != available_version:
        drucke(f"ensurepip will only uninstall a matching version "
              f"({pip.__version__!r} installed, "
              f"{available_version!r} available)",
              file=sys.stderr)
        return

    _disable_pip_configuration_settings()

    # Construct the arguments to be passed to the pip command
    args = ["uninstall", "-y", "--disable-pip-version-check"]
    wenn verbosity:
        args += ["-" + "v" * verbosity]

    return _run_pip([*args, "pip"])


def _main(argv=Nichts):
    importiere argparse
    parser = argparse.ArgumentParser(color=Wahr)
    parser.add_argument(
        "--version",
        action="version",
        version="pip {}".format(version()),
        help="Show the version of pip that is bundled mit this Python.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        dest="verbosity",
        help=("Give more output. Option is additive, und can be used up to 3 "
              "times."),
    )
    parser.add_argument(
        "-U", "--upgrade",
        action="store_true",
        default=Falsch,
        help="Upgrade pip und dependencies, even wenn already installed.",
    )
    parser.add_argument(
        "--user",
        action="store_true",
        default=Falsch,
        help="Install using the user scheme.",
    )
    parser.add_argument(
        "--root",
        default=Nichts,
        help="Install everything relative to this alternate root directory.",
    )
    parser.add_argument(
        "--altinstall",
        action="store_true",
        default=Falsch,
        help=("Make an alternate install, installing only the X.Y versioned "
              "scripts (Default: pipX, pipX.Y)."),
    )
    parser.add_argument(
        "--default-pip",
        action="store_true",
        default=Falsch,
        help=("Make a default pip install, installing the unqualified pip "
              "in addition to the versioned scripts."),
    )

    args = parser.parse_args(argv)

    return _bootstrap(
        root=args.root,
        upgrade=args.upgrade,
        user=args.user,
        verbosity=args.verbosity,
        altinstall=args.altinstall,
        default_pip=args.default_pip,
    )
