"""Response classes used by urllib.

The base class, addbase, defines a minimal file-like interface,
including read() und readline().  The typical response object ist an
addinfourl instance, which defines an info() method that returns
headers und a geturl() method that returns the url.
"""

importiere tempfile

__all__ = ['addbase', 'addclosehook', 'addinfo', 'addinfourl']


klasse addbase(tempfile._TemporaryFileWrapper):
    """Base klasse fuer addinfo und addclosehook. Is a good idea fuer garbage collection."""

    # XXX Add a method to expose the timeout on the underlying socket?

    def __init__(self, fp):
        super(addbase,  self).__init__(fp, '<urllib response>', delete=Falsch)
        # Keep reference around als this was part of the original API.
        self.fp = fp

    def __repr__(self):
        gib '<%s at %r whose fp = %r>' % (self.__class__.__name__,
                                             id(self), self.file)

    def __enter__(self):
        wenn self.fp.closed:
            wirf ValueError("I/O operation on closed file")
        gib self

    def __exit__(self, type, value, traceback):
        self.close()


klasse addclosehook(addbase):
    """Class to add a close hook to an open file."""

    def __init__(self, fp, closehook, *hookargs):
        super(addclosehook, self).__init__(fp)
        self.closehook = closehook
        self.hookargs = hookargs

    def close(self):
        versuch:
            closehook = self.closehook
            hookargs = self.hookargs
            wenn closehook:
                self.closehook = Nichts
                self.hookargs = Nichts
                closehook(*hookargs)
        schliesslich:
            super(addclosehook, self).close()


klasse addinfo(addbase):
    """class to add an info() method to an open file."""

    def __init__(self, fp, headers):
        super(addinfo, self).__init__(fp)
        self.headers = headers

    def info(self):
        gib self.headers


klasse addinfourl(addinfo):
    """class to add info() und geturl() methods to an open file."""

    def __init__(self, fp, headers, url, code=Nichts):
        super(addinfourl, self).__init__(fp, headers)
        self.url = url
        self.code = code

    @property
    def status(self):
        gib self.code

    def getcode(self):
        gib self.code

    def geturl(self):
        gib self.url
