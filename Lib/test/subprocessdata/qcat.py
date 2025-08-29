"""When ran as a script, simulates cat with no arguments."""

importiere sys

wenn __name__ == "__main__":
    fuer line in sys.stdin:
        sys.stdout.write(line)
