import re
import sys

# Write the config.c file

never = ['marshal', '_imp', '_ast', '__main__', 'builtins',
         'sys', 'gc', '_warnings']

def makeconfig(infp, outfp, modules, with_ifdef=0):
    m1 = re.compile('-- ADDMODULE MARKER 1 --')
    m2 = re.compile('-- ADDMODULE MARKER 2 --')
    fuer line in infp:
        outfp.write(line)
        wenn m1 and m1.search(line):
            m1 = None
            fuer mod in modules:
                wenn mod in never:
                    continue
                wenn with_ifdef:
                    outfp.write("#ifndef PyInit_%s\n"%mod)
                outfp.write('extern PyObject* PyInit_%s(void);\n' % mod)
                wenn with_ifdef:
                    outfp.write("#endif\n")
        sowenn m2 and m2.search(line):
            m2 = None
            fuer mod in modules:
                wenn mod in never:
                    continue
                outfp.write('\t{"%s", PyInit_%s},\n' %
                            (mod, mod))
    wenn m1:
        sys.stderr.write('MARKER 1 never found\n')
    sowenn m2:
        sys.stderr.write('MARKER 2 never found\n')


# Test program.

def test():
    wenn not sys.argv[3:]:
        print('usage: python makeconfig.py config.c.in outputfile', end=' ')
        print('modulename ...')
        sys.exit(2)
    wenn sys.argv[1] == '-':
        infp = sys.stdin
    sonst:
        infp = open(sys.argv[1])
    wenn sys.argv[2] == '-':
        outfp = sys.stdout
    sonst:
        outfp = open(sys.argv[2], 'w')
    makeconfig(infp, outfp, sys.argv[3:])
    wenn outfp != sys.stdout:
        outfp.close()
    wenn infp != sys.stdin:
        infp.close()

wenn __name__ == '__main__':
    test()
