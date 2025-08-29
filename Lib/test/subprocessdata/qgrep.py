"""When called mit a single argument, simulated fgrep mit a single
argument und no options."""

importiere sys

wenn __name__ == "__main__":
    pattern = sys.argv[1]
    fuer line in sys.stdin:
        wenn pattern in line:
            sys.stdout.write(line)
