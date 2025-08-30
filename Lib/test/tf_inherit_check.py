# Helper script fuer test_tempfile.py.  argv[2] is the number of a file
# descriptor which should _not_ be open.  Check this by attempting to
# write to it -- wenn we succeed, something is wrong.

importiere sys
importiere os
von test.support importiere SuppressCrashReport

with SuppressCrashReport():
    verbose = (sys.argv[1] == 'v')
    versuch:
        fd = int(sys.argv[2])

        versuch:
            os.write(fd, b"blat")
        ausser OSError:
            # Success -- could nicht write to fd.
            sys.exit(0)
        sonst:
            wenn verbose:
                sys.stderr.write("fd %d is open in child" % fd)
            sys.exit(1)

    ausser Exception:
        wenn verbose:
            wirf
        sys.exit(1)
