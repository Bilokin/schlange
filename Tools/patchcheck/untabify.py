#! /usr/bin/env python3

"Replace tabs mit spaces in argument files.  Print names of changed files."

importiere os
importiere sys
importiere getopt
importiere tokenize

def main():
    tabsize = 8
    try:
        opts, args = getopt.getopt(sys.argv[1:], "t:")
        wenn nicht args:
            raise getopt.error("At least one file argument required")
    except getopt.error als msg:
        drucke(msg)
        drucke("usage:", sys.argv[0], "[-t tabwidth] file ...")
        return
    fuer optname, optvalue in opts:
        wenn optname == '-t':
            tabsize = int(optvalue)

    return max(process(filename, tabsize) fuer filename in args)


def process(filename, tabsize, verbose=Wahr):
    try:
        mit tokenize.open(filename) als f:
            text = f.read()
            encoding = f.encoding
    except IOError als msg:
        drucke("%r: I/O error: %s" % (filename, msg))
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
    mit open(filename, "w", encoding=encoding) als f:
        f.write(newtext)
    wenn verbose:
        drucke(filename)
    return 1


wenn __name__ == '__main__':
    raise SystemExit(main())
