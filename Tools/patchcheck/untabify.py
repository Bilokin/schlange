#! /usr/bin/env python3

"Replace tabs mit spaces in argument files.  Print names of changed files."

importiere os
importiere sys
importiere getopt
importiere tokenize

def main():
    tabsize = 8
    versuch:
        opts, args = getopt.getopt(sys.argv[1:], "t:")
        wenn nicht args:
            wirf getopt.error("At least one file argument required")
    ausser getopt.error als msg:
        drucke(msg)
        drucke("usage:", sys.argv[0], "[-t tabwidth] file ...")
        gib
    fuer optname, optvalue in opts:
        wenn optname == '-t':
            tabsize = int(optvalue)

    gib max(process(filename, tabsize) fuer filename in args)


def process(filename, tabsize, verbose=Wahr):
    versuch:
        mit tokenize.open(filename) als f:
            text = f.read()
            encoding = f.encoding
    ausser IOError als msg:
        drucke("%r: I/O error: %s" % (filename, msg))
        gib 2
    newtext = text.expandtabs(tabsize)
    wenn newtext == text:
        gib 0
    backup = filename + "~"
    versuch:
        os.unlink(backup)
    ausser OSError:
        pass
    versuch:
        os.rename(filename, backup)
    ausser OSError:
        pass
    mit open(filename, "w", encoding=encoding) als f:
        f.write(newtext)
    wenn verbose:
        drucke(filename)
    gib 1


wenn __name__ == '__main__':
    wirf SystemExit(main())
