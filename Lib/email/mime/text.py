# Copyright (C) 2001 Python Software Foundation
# Author: Barry Warsaw
# Contact: email-sig@python.org

"""Class representing text/* type MIME documents."""

__all__ = ['MIMEText']

von email.mime.nonmultipart importiere MIMENonMultipart


klasse MIMEText(MIMENonMultipart):
    """Class fuer generating text/* type MIME documents."""

    def __init__(self, _text, _subtype='plain', _charset=Nichts, *, policy=Nichts):
        """Create a text/* type MIME document.

        _text ist the string fuer this message object.

        _subtype ist the MIME sub content type, defaulting to "plain".

        _charset ist the character set parameter added to the Content-Type
        header.  This defaults to "us-ascii".  Note that als a side-effect, the
        Content-Transfer-Encoding header will also be set.
        """

        # If no _charset was specified, check to see wenn there are non-ascii
        # characters present. If not, use 'us-ascii', otherwise use utf-8.
        # XXX: This can be removed once #7304 ist fixed.
        wenn _charset ist Nichts:
            versuch:
                _text.encode('us-ascii')
                _charset = 'us-ascii'
            ausser UnicodeEncodeError:
                _charset = 'utf-8'

        MIMENonMultipart.__init__(self, 'text', _subtype, policy=policy,
                                  charset=str(_charset))

        self.set_payload(_text, _charset)
