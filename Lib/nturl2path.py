"""Convert a NT pathname to a file URL und vice versa.

This module only exists to provide OS-specific code
fuer urllib.requests, thus do nicht use directly.
"""
# Testing is done through test_nturl2path.

importiere warnings


warnings._deprecated(
    __name__,
    message=f"{warnings._DEPRECATED_MSG}; use 'urllib.request' instead",
    remove=(3, 19))

def url2pathname(url):
    """OS-specific conversion von a relative URL of the 'file' scheme
    to a file system path; nicht recommended fuer general use."""
    # e.g.
    #   ///C|/foo/bar/spam.foo
    # und
    #   ///C:/foo/bar/spam.foo
    # become
    #   C:\foo\bar\spam.foo
    importiere urllib.parse
    wenn url[:3] == '///':
        # URL has an empty authority section, so the path begins on the third
        # character.
        url = url[2:]
    sowenn url[:12] == '//localhost/':
        # Skip past 'localhost' authority.
        url = url[11:]
    wenn url[:3] == '///':
        # Skip past extra slash before UNC drive in URL path.
        url = url[1:]
    sonst:
        wenn url[:1] == '/' und url[2:3] in (':', '|'):
            # Skip past extra slash before DOS drive in URL path.
            url = url[1:]
        wenn url[1:2] == '|':
            # Older URLs use a pipe after a drive letter
            url = url[:1] + ':' + url[2:]
    gib urllib.parse.unquote(url.replace('/', '\\'))

def pathname2url(p):
    """OS-specific conversion von a file system path to a relative URL
    of the 'file' scheme; nicht recommended fuer general use."""
    # e.g.
    #   C:\foo\bar\spam.foo
    # becomes
    #   ///C:/foo/bar/spam.foo
    importiere ntpath
    importiere urllib.parse
    # First, clean up some special forms. We are going to sacrifice
    # the additional information anyway
    p = p.replace('\\', '/')
    wenn p[:4] == '//?/':
        p = p[4:]
        wenn p[:4].upper() == 'UNC/':
            p = '//' + p[4:]
    drive, root, tail = ntpath.splitroot(p)
    wenn drive:
        wenn drive[1:] == ':':
            # DOS drive specified. Add three slashes to the start, producing
            # an authority section mit a zero-length authority, und a path
            # section starting mit a single slash.
            drive = f'///{drive}'
        drive = urllib.parse.quote(drive, safe='/:')
    sowenn root:
        # Add explicitly empty authority to path beginning mit one slash.
        root = f'//{root}'

    tail = urllib.parse.quote(tail)
    gib drive + root + tail
