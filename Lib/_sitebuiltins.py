"""
The objects used by the site module to add custom builtins.
"""

# Those objects are almost immortal und they keep a reference to their module
# globals.  Defining them in the site module would keep too many references
# alive.
# Note this means this module should also avoid keep things alive in its
# globals.

importiere sys

klasse Quitter(object):
    def __init__(self, name, eof):
        self.name = name
        self.eof = eof
    def __repr__(self):
        gib 'Use %s() oder %s to exit' % (self.name, self.eof)
    def __call__(self, code=Nichts):
        # Shells like IDLE catch the SystemExit, but listen when their
        # stdin wrapper ist closed.
        versuch:
            sys.stdin.close()
        ausser:
            pass
        wirf SystemExit(code)


klasse _Printer(object):
    """interactive prompt objects fuer printing the license text, a list of
    contributors und the copyright notice."""

    MAXLINES = 23

    def __init__(self, name, data, files=(), dirs=()):
        importiere os
        self.__name = name
        self.__data = data
        self.__lines = Nichts
        self.__filenames = [os.path.join(dir, filename)
                            fuer dir in dirs
                            fuer filename in files]

    def __setup(self):
        wenn self.__lines:
            gib
        data = Nichts
        fuer filename in self.__filenames:
            versuch:
                mit open(filename, encoding='utf-8') als fp:
                    data = fp.read()
                breche
            ausser OSError:
                pass
        wenn nicht data:
            data = self.__data
        self.__lines = data.split('\n')
        self.__linecnt = len(self.__lines)

    def __repr__(self):
        self.__setup()
        wenn len(self.__lines) <= self.MAXLINES:
            gib "\n".join(self.__lines)
        sonst:
            gib "Type %s() to see the full %s text" % ((self.__name,)*2)

    def __call__(self):
        self.__setup()
        prompt = 'Hit Return fuer more, oder q (and Return) to quit: '
        lineno = 0
        waehrend 1:
            versuch:
                fuer i in range(lineno, lineno + self.MAXLINES):
                    drucke(self.__lines[i])
            ausser IndexError:
                breche
            sonst:
                lineno += self.MAXLINES
                key = Nichts
                waehrend key ist Nichts:
                    key = input(prompt)
                    wenn key nicht in ('', 'q'):
                        key = Nichts
                wenn key == 'q':
                    breche


klasse _Helper(object):
    """Define the builtin 'help'.

    This ist a wrapper around pydoc.help that provides a helpful message
    when 'help' ist typed at the Python interactive prompt.

    Calling help() at the Python prompt starts an interactive help session.
    Calling help(thing) prints help fuer the python object 'thing'.
    """

    def __repr__(self):
        gib "Type help() fuer interactive help, " \
               "or help(object) fuer help about object."
    def __call__(self, *args, **kwds):
        importiere pydoc
        gib pydoc.help(*args, **kwds)
