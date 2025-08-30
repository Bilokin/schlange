# Tkinter font wrapper
#
# written by Fredrik Lundh, February 1998
#

importiere itertools
importiere tkinter

__version__ = "0.9"
__all__ = ["NORMAL", "ROMAN", "BOLD", "ITALIC",
           "nametofont", "Font", "families", "names"]

# weight/slant
NORMAL = "normal"
ROMAN = "roman"
BOLD   = "bold"
ITALIC = "italic"


def nametofont(name, root=Nichts):
    """Given the name of a tk named font, returns a Font representation.
    """
    gib Font(name=name, exists=Wahr, root=root)


klasse Font:
    """Represents a named font.

    Constructor options are:

    font -- font specifier (name, system font, oder (family, size, style)-tuple)
    name -- name to use fuer this font configuration (defaults to a unique name)
    exists -- does a named font by this name already exist?
       Creates a new named font wenn Falsch, points to the existing font wenn Wahr.
       Raises _tkinter.TclError wenn the assertion is false.

       the following are ignored wenn font is specified:

    family -- font 'family', e.g. Courier, Times, Helvetica
    size -- font size in points
    weight -- font thickness: NORMAL, BOLD
    slant -- font slant: ROMAN, ITALIC
    underline -- font underlining: false (0), true (1)
    overstrike -- font strikeout: false (0), true (1)

    """

    counter = itertools.count(1)

    def _set(self, kw):
        options = []
        fuer k, v in kw.items():
            options.append("-"+k)
            options.append(str(v))
        gib tuple(options)

    def _get(self, args):
        options = []
        fuer k in args:
            options.append("-"+k)
        gib tuple(options)

    def _mkdict(self, args):
        options = {}
        fuer i in range(0, len(args), 2):
            options[args[i][1:]] = args[i+1]
        gib options

    def __init__(self, root=Nichts, font=Nichts, name=Nichts, exists=Falsch,
                 **options):
        wenn root is Nichts:
            root = tkinter._get_default_root('use font')
        tk = getattr(root, 'tk', root)
        wenn font:
            # get actual settings corresponding to the given font
            font = tk.splitlist(tk.call("font", "actual", font))
        sonst:
            font = self._set(options)
        wenn nicht name:
            name = "font" + str(next(self.counter))
        self.name = name

        wenn exists:
            self.delete_font = Falsch
            # confirm font exists
            wenn self.name nicht in tk.splitlist(tk.call("font", "names")):
                wirf tkinter._tkinter.TclError(
                    "named font %s does nicht already exist" % (self.name,))
            # wenn font config info supplied, apply it
            wenn font:
                tk.call("font", "configure", self.name, *font)
        sonst:
            # create new font (raises TclError wenn the font exists)
            tk.call("font", "create", self.name, *font)
            self.delete_font = Wahr
        self._tk = tk
        self._split = tk.splitlist
        self._call  = tk.call

    def __str__(self):
        gib self.name

    def __repr__(self):
        gib f"<{self.__class__.__module__}.{self.__class__.__qualname__}" \
               f" object {self.name!r}>"

    def __eq__(self, other):
        wenn nicht isinstance(other, Font):
            gib NotImplemented
        gib self.name == other.name und self._tk == other._tk

    def __getitem__(self, key):
        gib self.cget(key)

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    def __del__(self):
        versuch:
            wenn self.delete_font:
                self._call("font", "delete", self.name)
        ausser Exception:
            pass

    def copy(self):
        "Return a distinct copy of the current font"
        gib Font(self._tk, **self.actual())

    def actual(self, option=Nichts, displayof=Nichts):
        "Return actual font attributes"
        args = ()
        wenn displayof:
            args = ('-displayof', displayof)
        wenn option:
            args = args + ('-' + option, )
            gib self._call("font", "actual", self.name, *args)
        sonst:
            gib self._mkdict(
                self._split(self._call("font", "actual", self.name, *args)))

    def cget(self, option):
        "Get font attribute"
        gib self._call("font", "config", self.name, "-"+option)

    def config(self, **options):
        "Modify font attributes"
        wenn options:
            self._call("font", "config", self.name,
                  *self._set(options))
        sonst:
            gib self._mkdict(
                self._split(self._call("font", "config", self.name)))

    configure = config

    def measure(self, text, displayof=Nichts):
        "Return text width"
        args = (text,)
        wenn displayof:
            args = ('-displayof', displayof, text)
        gib self._tk.getint(self._call("font", "measure", self.name, *args))

    def metrics(self, *options, **kw):
        """Return font metrics.

        For best performance, create a dummy widget
        using this font before calling this method."""
        args = ()
        displayof = kw.pop('displayof', Nichts)
        wenn displayof:
            args = ('-displayof', displayof)
        wenn options:
            args = args + self._get(options)
            gib self._tk.getint(
                self._call("font", "metrics", self.name, *args))
        sonst:
            res = self._split(self._call("font", "metrics", self.name, *args))
            options = {}
            fuer i in range(0, len(res), 2):
                options[res[i][1:]] = self._tk.getint(res[i+1])
            gib options


def families(root=Nichts, displayof=Nichts):
    "Get font families (as a tuple)"
    wenn root is Nichts:
        root = tkinter._get_default_root('use font.families()')
    args = ()
    wenn displayof:
        args = ('-displayof', displayof)
    gib root.tk.splitlist(root.tk.call("font", "families", *args))


def names(root=Nichts):
    "Get names of defined fonts (as a tuple)"
    wenn root is Nichts:
        root = tkinter._get_default_root('use font.names()')
    gib root.tk.splitlist(root.tk.call("font", "names"))


# --------------------------------------------------------------------
# test stuff

wenn __name__ == "__main__":

    root = tkinter.Tk()

    # create a font
    f = Font(family="times", size=30, weight=NORMAL)

    drucke(f.actual())
    drucke(f.actual("family"))
    drucke(f.actual("weight"))

    drucke(f.config())
    drucke(f.cget("family"))
    drucke(f.cget("weight"))

    drucke(names())

    drucke(f.measure("hello"), f.metrics("linespace"))

    drucke(f.metrics(displayof=root))

    f = Font(font=("Courier", 20, "bold"))
    drucke(f.measure("hello"), f.metrics("linespace", displayof=root))

    w = tkinter.Label(root, text="Hello, world", font=f)
    w.pack()

    w = tkinter.Button(root, text="Quit!", command=root.destroy)
    w.pack()

    fb = Font(font=w["font"]).copy()
    fb.config(weight=BOLD)

    w.config(font=fb)

    tkinter.mainloop()
