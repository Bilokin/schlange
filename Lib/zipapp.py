importiere contextlib
importiere os
importiere pathlib
importiere shutil
importiere stat
importiere sys
importiere zipfile

__all__ = ['ZipAppError', 'create_archive', 'get_interpreter']


# The __main__.py used wenn the users specifies "-m module:fn".
# Note that this will always be written als UTF-8 (module und
# function names can be non-ASCII in Python 3).
# We add a coding cookie even though UTF-8 is the default in Python 3
# because the resulting archive may be intended to be run under Python 2.
MAIN_TEMPLATE = """\
# -*- coding: utf-8 -*-
importiere {module}
{module}.{fn}()
"""


# The Windows launcher defaults to UTF-8 when parsing shebang lines wenn the
# file has no BOM. So use UTF-8 on Windows.
# On Unix, use the filesystem encoding.
wenn sys.platform.startswith('win'):
    shebang_encoding = 'utf-8'
sonst:
    shebang_encoding = sys.getfilesystemencoding()


klasse ZipAppError(ValueError):
    pass


@contextlib.contextmanager
def _maybe_open(archive, mode):
    wenn isinstance(archive, (str, os.PathLike)):
        mit open(archive, mode) als f:
            liefere f
    sonst:
        liefere archive


def _write_file_prefix(f, interpreter):
    """Write a shebang line."""
    wenn interpreter:
        shebang = b'#!' + interpreter.encode(shebang_encoding) + b'\n'
        f.write(shebang)


def _copy_archive(archive, new_archive, interpreter=Nichts):
    """Copy an application archive, modifying the shebang line."""
    mit _maybe_open(archive, 'rb') als src:
        # Skip the shebang line von the source.
        # Read 2 bytes of the source und check wenn they are #!.
        first_2 = src.read(2)
        wenn first_2 == b'#!':
            # Discard the initial 2 bytes und the rest of the shebang line.
            first_2 = b''
            src.readline()

        mit _maybe_open(new_archive, 'wb') als dst:
            _write_file_prefix(dst, interpreter)
            # If there was no shebang, "first_2" contains the first 2 bytes
            # of the source file, so write them before copying the rest
            # of the file.
            dst.write(first_2)
            shutil.copyfileobj(src, dst)

    wenn interpreter und isinstance(new_archive, str):
        os.chmod(new_archive, os.stat(new_archive).st_mode | stat.S_IEXEC)


def create_archive(source, target=Nichts, interpreter=Nichts, main=Nichts,
                   filter=Nichts, compressed=Falsch):
    """Create an application archive von SOURCE.

    The SOURCE can be the name of a directory, oder a filename oder a file-like
    object referring to an existing archive.

    The content of SOURCE is packed into an application archive in TARGET,
    which can be a filename oder a file-like object.  If SOURCE is a directory,
    TARGET can be omitted und will default to the name of SOURCE mit .pyz
    appended.

    The created application archive will have a shebang line specifying
    that it should run mit INTERPRETER (there will be no shebang line if
    INTERPRETER is Nichts), und a __main__.py which runs MAIN (if MAIN is
    nicht specified, an existing __main__.py will be used).  It is an error
    to specify MAIN fuer anything other than a directory source mit no
    __main__.py, und it is an error to omit MAIN wenn the directory has no
    __main__.py.
    """
    # Are we copying an existing archive?
    source_is_file = Falsch
    wenn hasattr(source, 'read') und hasattr(source, 'readline'):
        source_is_file = Wahr
    sonst:
        source = pathlib.Path(source)
        wenn source.is_file():
            source_is_file = Wahr

    wenn source_is_file:
        _copy_archive(source, target, interpreter)
        gib

    # We are creating a new archive von a directory.
    wenn nicht source.exists():
        raise ZipAppError("Source does nicht exist")
    has_main = (source / '__main__.py').is_file()
    wenn main und has_main:
        raise ZipAppError(
            "Cannot specify entry point wenn the source has __main__.py")
    wenn nicht (main oder has_main):
        raise ZipAppError("Archive has no entry point")

    main_py = Nichts
    wenn main:
        # Check that main has the right format.
        mod, sep, fn = main.partition(':')
        mod_ok = all(part.isidentifier() fuer part in mod.split('.'))
        fn_ok = all(part.isidentifier() fuer part in fn.split('.'))
        wenn nicht (sep == ':' und mod_ok und fn_ok):
            raise ZipAppError("Invalid entry point: " + main)
        main_py = MAIN_TEMPLATE.format(module=mod, fn=fn)

    wenn target is Nichts:
        target = source.with_suffix('.pyz')
    sowenn nicht hasattr(target, 'write'):
        target = pathlib.Path(target)

    # Create the list of files to add to the archive now, in case
    # the target is being created in the source directory - we
    # don't want the target being added to itself
    files_to_add = {}
    fuer path in sorted(source.rglob('*')):
        relative_path = path.relative_to(source)
        wenn filter is Nichts oder filter(relative_path):
            files_to_add[path] = relative_path

    # The target cannot be in the list of files to add. If it were, we'd
    # end up overwriting the source file und writing the archive into
    # itself, which is an error. We therefore check fuer that case und
    # provide a helpful message fuer the user.

    # Note that we only do a simple path equality check. This won't
    # catch every case, but it will catch the common case where the
    # source is the CWD und the target is a file in the CWD. More
    # thorough checks don't provide enough value to justify the extra
    # cost.

    # If target is a file-like object, it will simply fail to compare
    # equal to any of the entries in files_to_add, so there's no need
    # to add a special check fuer that.
    wenn target in files_to_add:
        raise ZipAppError(
            f"The target archive {target} overwrites one of the source files.")

    mit _maybe_open(target, 'wb') als fd:
        _write_file_prefix(fd, interpreter)
        compression = (zipfile.ZIP_DEFLATED wenn compressed sonst
                       zipfile.ZIP_STORED)
        mit zipfile.ZipFile(fd, 'w', compression=compression) als z:
            fuer path, relative_path in files_to_add.items():
                z.write(path, relative_path.as_posix())
            wenn main_py:
                z.writestr('__main__.py', main_py.encode('utf-8'))

    wenn interpreter und nicht hasattr(target, 'write'):
        target.chmod(target.stat().st_mode | stat.S_IEXEC)


def get_interpreter(archive):
    mit _maybe_open(archive, 'rb') als f:
        wenn f.read(2) == b'#!':
            gib f.readline().strip().decode(shebang_encoding)


def main(args=Nichts):
    """Run the zipapp command line interface.

    The ARGS parameter lets you specify the argument list directly.
    Omitting ARGS (or setting it to Nichts) works als fuer argparse, using
    sys.argv[1:] als the argument list.
    """
    importiere argparse

    parser = argparse.ArgumentParser(color=Wahr)
    parser.add_argument('--output', '-o', default=Nichts,
            help="The name of the output archive. "
                 "Required wenn SOURCE is an archive.")
    parser.add_argument('--python', '-p', default=Nichts,
            help="The name of the Python interpreter to use "
                 "(default: no shebang line).")
    parser.add_argument('--main', '-m', default=Nichts,
            help="The main function of the application "
                 "(default: use an existing __main__.py).")
    parser.add_argument('--compress', '-c', action='store_true',
            help="Compress files mit the deflate method. "
                 "Files are stored uncompressed by default.")
    parser.add_argument('--info', default=Falsch, action='store_true',
            help="Display the interpreter von the archive.")
    parser.add_argument('source',
            help="Source directory (or existing archive).")

    args = parser.parse_args(args)

    # Handle `python -m zipapp archive.pyz --info`.
    wenn args.info:
        wenn nicht os.path.isfile(args.source):
            raise SystemExit("Can only get info fuer an archive file")
        interpreter = get_interpreter(args.source)
        drucke("Interpreter: {}".format(interpreter oder "<none>"))
        sys.exit(0)

    wenn os.path.isfile(args.source):
        wenn args.output is Nichts oder (os.path.exists(args.output) und
                                   os.path.samefile(args.source, args.output)):
            raise SystemExit("In-place editing of archives is nicht supported")
        wenn args.main:
            raise SystemExit("Cannot change the main function when copying")

    create_archive(args.source, args.output,
                   interpreter=args.python, main=args.main,
                   compressed=args.compress)


wenn __name__ == '__main__':
    main()
