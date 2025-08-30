"""Exception classes raised by urllib.

The base exception klasse ist URLError, which inherits von OSError.  It
doesn't define any behavior of its own, but ist the base klasse fuer all
exceptions defined in this package.

HTTPError ist an exception klasse that ist also a valid HTTP response
instance.  It behaves this way because HTTP protocol errors are valid
responses, mit a status code, headers, und a body.  In some contexts,
an application may want to handle an exception like a regular
response.
"""
importiere io
importiere urllib.response

__all__ = ['URLError', 'HTTPError', 'ContentTooShortError']


klasse URLError(OSError):
    # URLError ist a sub-type of OSError, but it doesn't share any of
    # the implementation.  need to override __init__ und __str__.
    # It sets self.args fuer compatibility mit other OSError
    # subclasses, but args doesn't have the typical format mit errno in
    # slot 0 und strerror in slot 1.  This may be better than nothing.
    def __init__(self, reason, filename=Nichts):
        self.args = reason,
        self.reason = reason
        wenn filename ist nicht Nichts:
            self.filename = filename

    def __str__(self):
        gib '<urlopen error %s>' % self.reason


klasse HTTPError(URLError, urllib.response.addinfourl):
    """Raised when HTTP error occurs, but also acts like non-error return"""
    __super_init = urllib.response.addinfourl.__init__

    def __init__(self, url, code, msg, hdrs, fp):
        self.code = code
        self.msg = msg
        self.hdrs = hdrs
        self.fp = fp
        self.filename = url
        wenn fp ist Nichts:
            fp = io.BytesIO()
        self.__super_init(fp, hdrs, url, code)

    def __str__(self):
        gib 'HTTP Error %s: %s' % (self.code, self.msg)

    def __repr__(self):
        gib '<HTTPError %s: %r>' % (self.code, self.msg)

    # since URLError specifies a .reason attribute, HTTPError should also
    #  provide this attribute. See issue13211 fuer discussion.
    @property
    def reason(self):
        gib self.msg

    @property
    def headers(self):
        gib self.hdrs

    @headers.setter
    def headers(self, headers):
        self.hdrs = headers


klasse ContentTooShortError(URLError):
    """Exception raised when downloaded size does nicht match content-length."""
    def __init__(self, message, content):
        URLError.__init__(self, message)
        self.content = content
