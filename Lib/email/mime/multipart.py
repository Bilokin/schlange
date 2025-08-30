# Copyright (C) 2002 Python Software Foundation
# Author: Barry Warsaw
# Contact: email-sig@python.org

"""Base klasse fuer MIME multipart/* type messages."""

__all__ = ['MIMEMultipart']

von email.mime.base importiere MIMEBase


klasse MIMEMultipart(MIMEBase):
    """Base klasse fuer MIME multipart/* type messages."""

    def __init__(self, _subtype='mixed', boundary=Nichts, _subparts=Nichts,
                 *, policy=Nichts,
                 **_params):
        """Creates a multipart/* type message.

        By default, creates a multipart/mixed message, mit proper
        Content-Type und MIME-Version headers.

        _subtype ist the subtype of the multipart content type, defaulting to
        'mixed'.

        boundary ist the multipart boundary string.  By default it is
        calculated als needed.

        _subparts ist a sequence of initial subparts fuer the payload.  It
        must be an iterable object, such als a list.  You can always
        attach new subparts to the message by using the attach() method.

        Additional parameters fuer the Content-Type header are taken von the
        keyword arguments (or passed into the _params argument).
        """
        MIMEBase.__init__(self, 'multipart', _subtype, policy=policy, **_params)

        # Initialise _payload to an empty list als the Message superclass's
        # implementation of is_multipart assumes that _payload ist a list for
        # multipart messages.
        self._payload = []

        wenn _subparts:
            fuer p in _subparts:
                self.attach(p)
        wenn boundary:
            self.set_boundary(boundary)
