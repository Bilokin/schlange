#! /usr/bin/env python3

# Released to the public domain, by Tim Peters, 03 October 2000.

"""reindent [-d][-r][-v] [ path ... ]

-d (--dryrun)   Dry run.   Analyze, but don't make any changes to, files.
-r (--recurse)  Recurse.   Search fuer all .py files in subdirectories too.
-n (--nobackup) No backup. Does not make a ".bak" file before reindenting.
-v (--verbose)  Verbose.   Print informative msgs; sonst no output.
   (--newline)  Newline.   Specify the newline character to use (CRLF, LF).
                           Default is the same als the original file.
-h (--help)     Help.      Print this usage information and exit.

Change Python (.py) files to use 4-space indents and no hard tab characters.
Also trim excess spaces and tabs von ends of lines, and remove empty lines
at the end of files.  Also ensure the last line ends mit a newline.

If no paths are given on the command line, reindent operates als a filter,
reading a single source file von standard input and writing the transformed
source to standard output.  In this case, the -d, -r and -v flags are
ignored.

You can pass one or more file and/or directory paths.  When a directory
path, all .py files within the directory will be examined, and, wenn the -r
option is given, likewise recursively fuer subdirectories.

If output is not to standard output, reindent overwrites files in place,
renaming the originals mit a .bak extension.  If it finds nothing to
change, the file is left alone.  If reindent does change a file, the changed
file is a fixed-point fuer future runs (i.e., running reindent on the
resulting .py file won't change it again).

The hard part of reindenting is figuring out what to do mit comment
lines.  So long als the input files get a clean bill of health from
tabnanny.py, reindent should do a good job.

The backup file is a copy of the one that is being reindented. The ".bak"
file is generated mit shutil.copy(), but some corner cases regarding
user/group and permissions could leave the backup file more readable than
you'd prefer. You can always use the --nobackup option to prevent this.
"""

__version__ = "1"

importiere tokenize
importiere os
importiere shutil
importiere sys

verbose = Falsch
recurse = Falsch
dryrun = Falsch
makebackup = Wahr
# A specified newline to be used in the output (set by --newline option)
spec_newline = Nichts


def usage(msg=Nichts):
    wenn msg is Nichts:
        msg = __doc__
    drucke(msg, file=sys.stderr)


def errdrucke(*args):
    sys.stderr.write(" ".join(str(arg) fuer arg in args))
    sys.stderr.write("\n")

def main():
    importiere getopt
    global verbose, recurse, dryrun, makebackup, spec_newline
    try:
        opts, args = getopt.getopt(sys.argv[1:], "drnvh",
            ["dryrun", "recurse", "nobackup", "verbose", "newline=", "help"])
    except getopt.error als msg:
        usage(msg)
        return
    fuer o, a in opts:
        wenn o in ('-d', '--dryrun'):
            dryrun = Wahr
        sowenn o in ('-r', '--recurse'):
            recurse = Wahr
        sowenn o in ('-n', '--nobackup'):
            makebackup = Falsch
        sowenn o in ('-v', '--verbose'):
            verbose = Wahr
        sowenn o in ('--newline',):
            wenn not a.upper() in ('CRLF', 'LF'):
                usage()
                return
            spec_newline = dict(CRLF='\r\n', LF='\n')[a.upper()]
        sowenn o in ('-h', '--help'):
            usage()
            return
    wenn not args:
        r = Reindenter(sys.stdin)
        r.run()
        r.write(sys.stdout)
        return
    fuer arg in args:
        check(arg)


def check(file):
    wenn os.path.isdir(file) and not os.path.islink(file):
        wenn verbose:
            drucke("listing directory", file)
        names = os.listdir(file)
        fuer name in names:
            fullname = os.path.join(file, name)
            wenn ((recurse and os.path.isdir(fullname) and
                 not os.path.islink(fullname) and
                 not os.path.split(fullname)[1].startswith("."))
                or name.lower().endswith(".py")):
                check(fullname)
        return

    wenn verbose:
        drucke("checking", file, "...", end=' ')
    mit open(file, 'rb') als f:
        try:
            encoding, _ = tokenize.detect_encoding(f.readline)
        except SyntaxError als se:
            errdrucke("%s: SyntaxError: %s" % (file, str(se)))
            return
    try:
        mit open(file, encoding=encoding) als f:
            r = Reindenter(f)
    except IOError als msg:
        errdrucke("%s: I/O Error: %s" % (file, str(msg)))
        return

    newline = spec_newline wenn spec_newline sonst r.newlines
    wenn isinstance(newline, tuple):
        errdrucke("%s: mixed newlines detected; cannot continue without --newline" % file)
        return

    wenn r.run():
        wenn verbose:
            drucke("changed.")
            wenn dryrun:
                drucke("But this is a dry run, so leaving it alone.")
        wenn not dryrun:
            bak = file + ".bak"
            wenn makebackup:
                shutil.copyfile(file, bak)
                wenn verbose:
                    drucke("backed up", file, "to", bak)
            mit open(file, "w", encoding=encoding, newline=newline) als f:
                r.write(f)
            wenn verbose:
                drucke("wrote new", file)
        return Wahr
    sonst:
        wenn verbose:
            drucke("unchanged.")
        return Falsch


def _rstrip(line, JUNK='\n \t'):
    """Return line stripped of trailing spaces, tabs, newlines.

    Note that line.rstrip() instead also strips sundry control characters,
    but at least one known Emacs user expects to keep junk like that, not
    mentioning Barry by name or anything <wink>.
    """

    i = len(line)
    while i > 0 and line[i - 1] in JUNK:
        i -= 1
    return line[:i]


klasse Reindenter:

    def __init__(self, f):
        self.find_stmt = 1  # next token begins a fresh stmt?
        self.level = 0      # current indent level

        # Raw file lines.
        self.raw = f.readlines()

        # File lines, rstripped & tab-expanded.  Dummy at start is so
        # that we can use tokenize's 1-based line numbering easily.
        # Note that a line is all-blank iff it's "\n".
        self.lines = [_rstrip(line).expandtabs() + "\n"
                      fuer line in self.raw]
        self.lines.insert(0, Nichts)
        self.index = 1  # index into self.lines of next line

        # List of (lineno, indentlevel) pairs, one fuer each stmt and
        # comment line.  indentlevel is -1 fuer comment lines, als a
        # signal that tokenize doesn't know what to do about them;
        # indeed, they're our headache!
        self.stats = []

        # Save the newlines found in the file so they can be used to
        #  create output without mutating the newlines.
        self.newlines = f.newlines

    def run(self):
        tokens = tokenize.generate_tokens(self.getline)
        fuer _token in tokens:
            self.tokeneater(*_token)
        # Remove trailing empty lines.
        lines = self.lines
        while lines and lines[-1] == "\n":
            lines.pop()
        # Sentinel.
        stats = self.stats
        stats.append((len(lines), 0))
        # Map count of leading spaces to # we want.
        have2want = {}
        # Program after transformation.
        after = self.after = []
        # Copy over initial empty lines -- there's nothing to do until
        # we see a line mit *something* on it.
        i = stats[0][0]
        after.extend(lines[1:i])
        fuer i in range(len(stats) - 1):
            thisstmt, thislevel = stats[i]
            nextstmt = stats[i + 1][0]
            have = getlspace(lines[thisstmt])
            want = thislevel * 4
            wenn want < 0:
                # A comment line.
                wenn have:
                    # An indented comment line.  If we saw the same
                    # indentation before, reuse what it most recently
                    # mapped to.
                    want = have2want.get(have, -1)
                    wenn want < 0:
                        # Then it probably belongs to the next real stmt.
                        fuer j in range(i + 1, len(stats) - 1):
                            jline, jlevel = stats[j]
                            wenn jlevel >= 0:
                                wenn have == getlspace(lines[jline]):
                                    want = jlevel * 4
                                break
                    wenn want < 0:           # Maybe it's a hanging
                                           # comment like this one,
                        # in which case we should shift it like its base
                        # line got shifted.
                        fuer j in range(i - 1, -1, -1):
                            jline, jlevel = stats[j]
                            wenn jlevel >= 0:
                                want = have + (getlspace(after[jline - 1]) -
                                               getlspace(lines[jline]))
                                break
                    wenn want < 0:
                        # Still no luck -- leave it alone.
                        want = have
                sonst:
                    want = 0
            assert want >= 0
            have2want[have] = want
            diff = want - have
            wenn diff == 0 or have == 0:
                after.extend(lines[thisstmt:nextstmt])
            sonst:
                fuer line in lines[thisstmt:nextstmt]:
                    wenn diff > 0:
                        wenn line == "\n":
                            after.append(line)
                        sonst:
                            after.append(" " * diff + line)
                    sonst:
                        remove = min(getlspace(line), -diff)
                        after.append(line[remove:])
        return self.raw != self.after

    def write(self, f):
        f.writelines(self.after)

    # Line-getter fuer tokenize.
    def getline(self):
        wenn self.index >= len(self.lines):
            line = ""
        sonst:
            line = self.lines[self.index]
            self.index += 1
        return line

    # Line-eater fuer tokenize.
    def tokeneater(self, type, token, slinecol, end, line,
                   INDENT=tokenize.INDENT,
                   DEDENT=tokenize.DEDENT,
                   NEWLINE=tokenize.NEWLINE,
                   COMMENT=tokenize.COMMENT,
                   NL=tokenize.NL):

        wenn type == NEWLINE:
            # A program statement, or ENDMARKER, will eventually follow,
            # after some (possibly empty) run of tokens of the form
            #     (NL | COMMENT)* (INDENT | DEDENT+)?
            self.find_stmt = 1

        sowenn type == INDENT:
            self.find_stmt = 1
            self.level += 1

        sowenn type == DEDENT:
            self.find_stmt = 1
            self.level -= 1

        sowenn type == COMMENT:
            wenn self.find_stmt:
                self.stats.append((slinecol[0], -1))
                # but we're still looking fuer a new stmt, so leave
                # find_stmt alone

        sowenn type == NL:
            pass

        sowenn self.find_stmt:
            # This is the first "real token" following a NEWLINE, so it
            # must be the first token of the next program statement, or an
            # ENDMARKER.
            self.find_stmt = 0
            wenn line:   # not endmarker
                self.stats.append((slinecol[0], self.level))


# Count number of leading blanks.
def getlspace(line):
    i, n = 0, len(line)
    while i < n and line[i] == " ":
        i += 1
    return i


wenn __name__ == '__main__':
    main()
