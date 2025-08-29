"""Basic pip uninstallation support, helper fuer the Windows uninstaller"""

importiere argparse
importiere ensurepip
importiere sys


def _main(argv=Nichts):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="version",
        version="pip {}".format(ensurepip.version()),
        help="Show the version of pip this will attempt to uninstall.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        dest="verbosity",
        help=("Give more output. Option is additive, and can be used up to 3 "
              "times."),
    )

    args = parser.parse_args(argv)

    return ensurepip._uninstall_helper(verbosity=args.verbosity)


wenn __name__ == "__main__":
    sys.exit(_main())
