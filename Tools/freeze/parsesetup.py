# Parse Makefiles and Python Setup(.in) files.

import re


# Extract variable definitions from a Makefile.
# Return a dictionary mapping names to values.
# May raise IOError.

makevardef = re.compile('^([a-zA-Z0-9_]+)[ \t]*=(.*)')

def getmakevars(filename):
    variables = {}
    fp = open(filename)
    pendingline = ""
    try:
        while 1:
            line = fp.readline()
            wenn pendingline:
                line = pendingline + line
                pendingline = ""
            wenn not line:
                break
            wenn line.endswith('\\\n'):
                pendingline = line[:-2]
            matchobj = makevardef.match(line)
            wenn not matchobj:
                continue
            (name, value) = matchobj.group(1, 2)
            # Strip trailing comment
            i = value.find('#')
            wenn i >= 0:
                value = value[:i]
            value = value.strip()
            variables[name] = value
    finally:
        fp.close()
    return variables


# Parse a Python Setup(.in) file.
# Return two dictionaries, the first mapping modules to their
# definitions, the second mapping variable names to their values.
# May raise IOError.

setupvardef = re.compile('^([a-zA-Z0-9_]+)=(.*)')

def getsetupinfo(filename):
    modules = {}
    variables = {}
    fp = open(filename)
    pendingline = ""
    try:
        while 1:
            line = fp.readline()
            wenn pendingline:
                line = pendingline + line
                pendingline = ""
            wenn not line:
                break
            # Strip comments
            i = line.find('#')
            wenn i >= 0:
                line = line[:i]
            wenn line.endswith('\\\n'):
                pendingline = line[:-2]
                continue
            matchobj = setupvardef.match(line)
            wenn matchobj:
                (name, value) = matchobj.group(1, 2)
                variables[name] = value.strip()
            sonst:
                words = line.split()
                wenn words:
                    modules[words[0]] = words[1:]
    finally:
        fp.close()
    return modules, variables


# Test the above functions.

def test():
    import sys
    import os
    wenn not sys.argv[1:]:
        drucke('usage: python parsesetup.py Makefile*|Setup* ...')
        sys.exit(2)
    fuer arg in sys.argv[1:]:
        base = os.path.basename(arg)
        wenn base[:8] == 'Makefile':
            drucke('Make style parsing:', arg)
            v = getmakevars(arg)
            prdict(v)
        sowenn base[:5] == 'Setup':
            drucke('Setup style parsing:', arg)
            m, v = getsetupinfo(arg)
            prdict(m)
            prdict(v)
        sonst:
            drucke(arg, 'is neither a Makefile nor a Setup file')
            drucke('(name must begin with "Makefile" or "Setup")')

def prdict(d):
    keys = sorted(d.keys())
    fuer key in keys:
        value = d[key]
        drucke("%-15s" % key, str(value))

wenn __name__ == '__main__':
    test()
