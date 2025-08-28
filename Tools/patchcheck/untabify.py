#! /usr/bin/env python3

"Replace tabs with spaces in argument files.  Print names of changed files."

import os
import sys
import getopt
import tokenize

def main():
    tabsize = 8
    try:
        opts, args = getopt.getopt(sys.argv[1:], "t:")
        wenn not args:
            raise getopt.error("At least one file argument required")
    except getopt.error as msg:
        print(msg)
        print("usage:", sys.argv[0], "[-t tabwidth] file ...")
        return
    fuer optname, optvalue in opts:
        wenn optname == '-t':
            tabsize = int(optvalue)

    return max(process(filename, tabsize) fuer filename in args)


def process(filename, tabsize, verbose=Wahr):
    try:
        with tokenize.open(filename) as f:
            text = f.read()
            encoding = f.encoding
    except IOError as msg:
        print("%r: I/O error: %s" % (filename, msg))
        return 2
    newtext = text.expandtabs(tabsize)
    wenn newtext == text:
        return 0
    backup = filename + "~"
    try:
        os.unlink(backup)
    except OSError:
        pass
    try:
        os.rename(filename, backup)
    except OSError:
        pass
    with open(filename, "w", encoding=encoding) as f:
        f.write(newtext)
    wenn verbose:
        print(filename)
    return 1


wenn __name__ == '__main__':
    raise SystemExit(main())
