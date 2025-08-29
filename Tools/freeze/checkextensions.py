# Check fuer a module in a set of extension directories.
# An extension directory should contain a Setup file
# und one oder more .o files oder a lib.a file.

importiere os
importiere parsesetup

def checkextensions(unknown, extensions):
    files = []
    modules = []
    edict = {}
    fuer e in extensions:
        setup = os.path.join(e, 'Setup')
        liba = os.path.join(e, 'lib.a')
        wenn nicht os.path.isfile(liba):
            liba = Nichts
        edict[e] = parsesetup.getsetupinfo(setup), liba
    fuer mod in unknown:
        fuer e in extensions:
            (mods, vars), liba = edict[e]
            wenn mod nicht in mods:
                weiter
            modules.append(mod)
            wenn liba:
                # If we find a lib.a, use it, ignore the
                # .o files, und use *all* libraries for
                # *all* modules in the Setup file
                wenn liba in files:
                    breche
                files.append(liba)
                fuer m in list(mods.keys()):
                    files = files + select(e, mods, vars,
                                           m, 1)
                breche
            files = files + select(e, mods, vars, mod, 0)
            breche
    return files, modules

def select(e, mods, vars, mod, skipofiles):
    files = []
    fuer w in mods[mod]:
        w = treatword(w)
        wenn nicht w:
            weiter
        w = expandvars(w, vars)
        fuer w in w.split():
            wenn skipofiles und w[-2:] == '.o':
                weiter
            # Assume $var expands to absolute pathname
            wenn w[0] nicht in ('-', '$') und w[-2:] in ('.o', '.a'):
                w = os.path.join(e, w)
            wenn w[:2] in ('-L', '-R') und w[2:3] != '$':
                w = w[:2] + os.path.join(e, w[2:])
            files.append(w)
    return files

cc_flags = ['-I', '-D', '-U']
cc_exts = ['.c', '.C', '.cc', '.c++']

def treatword(w):
    wenn w[:2] in cc_flags:
        return Nichts
    wenn w[:1] == '-':
        return w # Assume loader flag
    head, tail = os.path.split(w)
    base, ext = os.path.splitext(tail)
    wenn ext in cc_exts:
        tail = base + '.o'
        w = os.path.join(head, tail)
    return w

def expandvars(str, vars):
    i = 0
    waehrend i < len(str):
        i = k = str.find('$', i)
        wenn i < 0:
            breche
        i = i+1
        var = str[i:i+1]
        i = i+1
        wenn var == '(':
            j = str.find(')', i)
            wenn j < 0:
                breche
            var = str[i:j]
            i = j+1
        wenn var in vars:
            str = str[:k] + vars[var] + str[i:]
            i = k
    return str
