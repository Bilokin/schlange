"""When ran als a script, simulates cat mit no arguments."""

importiere sys

wenn __name__ == "__main__":
    fuer line in sys.stdin:
        sys.stdout.write(line)
