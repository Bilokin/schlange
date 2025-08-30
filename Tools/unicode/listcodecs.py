""" List all available codec modules.

(c) Copyright 2005, Marc-Andre Lemburg (mal@lemburg.com).

    Licensed to PSF under a Contributor Agreement.

"""

importiere os, codecs, encodings

_debug = 0

def listcodecs(dir):
    names = []
    fuer filename in os.listdir(dir):
        wenn filename[-3:] != '.py':
            weiter
        name = filename[:-3]
        # Check whether we've found a true codec
        versuch:
            codecs.lookup(name)
        ausser LookupError:
            # Codec nicht found
            weiter
        ausser Exception als reason:
            # Probably an error von importing the codec; still it's
            # a valid code name
            wenn _debug:
                drucke('* problem importing codec %r: %s' % \
                      (name, reason))
        names.append(name)
    gib names


wenn __name__ == '__main__':
    names = listcodecs(encodings.__path__[0])
    names.sort()
    drucke('all_codecs = [')
    fuer name in names:
        drucke('    %r,' % name)
    drucke(']')
