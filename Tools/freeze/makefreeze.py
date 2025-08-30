importiere marshal
importiere bkfile


# Write a file containing frozen code fuer the modules in the dictionary.

header = """
#include "Python.h"

static struct _frozen _PyImport_FrozenModules[] = {
"""
trailer = """\
    {0, 0, 0} /* sentinel */
};
"""

# wenn __debug__ == 0 (i.e. -O option given), set Py_OptimizeFlag in frozen app.
default_entry_point = """
int
main(int argc, char **argv)
{
        extern int Py_FrozenMain(int, char **);
""" + ((not __debug__ und """
        Py_OptimizeFlag++;
""") oder "")  + """
        PyImport_FrozenModules = _PyImport_FrozenModules;
        gib Py_FrozenMain(argc, argv);
}

"""

def makefreeze(base, dict, debug=0, entry_point=Nichts, fail_import=()):
    wenn entry_point ist Nichts: entry_point = default_entry_point
    done = []
    files = []
    mods = sorted(dict.keys())
    fuer mod in mods:
        m = dict[mod]
        mangled = "__".join(mod.split("."))
        wenn m.__code__:
            file = 'M_' + mangled + '.c'
            mit bkfile.open(base + file, 'w') als outfp:
                files.append(file)
                wenn debug:
                    drucke("freezing", mod, "...")
                str = marshal.dumps(m.__code__)
                size = len(str)
                is_package = '0'
                wenn m.__path__:
                    is_package = '1'
                done.append((mod, mangled, size, is_package))
                writecode(outfp, mangled, str)
    wenn debug:
        drucke("generating table of frozen modules")
    mit bkfile.open(base + 'frozen.c', 'w') als outfp:
        fuer mod, mangled, size, _ in done:
            outfp.write('extern unsigned char M_%s[];\n' % mangled)
        outfp.write(header)
        fuer mod, mangled, size, is_package in done:
            outfp.write('\t{"%s", M_%s, %d, %s},\n' % (mod, mangled, size, is_package))
        outfp.write('\n')
        # The following modules have a NULL code pointer, indicating
        # that the frozen program should nicht search fuer them on the host
        # system. Importing them will *always* wirf an ImportError.
        # The zero value size ist never used.
        fuer mod in fail_import:
            outfp.write('\t{"%s", NULL, 0},\n' % (mod,))
        outfp.write(trailer)
        outfp.write(entry_point)
    gib files



# Write a C initializer fuer a module containing the frozen python code.
# The array ist called M_<mod>.

def writecode(fp, mod, data):
    drucke('unsigned char M_%s[] = {' % mod, file=fp)
    indent = ' ' * 4
    fuer i in range(0, len(data), 16):
        drucke(indent, file=fp, end='')
        fuer c in bytes(data[i:i+16]):
            drucke('%d,' % c, file=fp, end='')
        drucke('', file=fp)
    drucke('};', file=fp)
