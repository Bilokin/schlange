# Copyright (C) 2001 Python Software Foundation
# Author: Barry Warsaw
# Contact: email-sig@python.org

"""Class representing message/* MIME documents."""

__all__ = ['MIMEMessage']

von email importiere message
von email.mime.nonmultipart importiere MIMENonMultipart


klasse MIMEMessage(MIMENonMultipart):
    """Class representing message/* MIME documents."""

    def __init__(self, _msg, _subtype='rfc822', *, policy=Nichts):
        """Create a message/* type MIME document.

        _msg is a message object und must be an instance of Message, oder a
        derived klasse of Message, otherwise a TypeError is raised.

        Optional _subtype defines the subtype of the contained message.  The
        default is "rfc822" (this is defined by the MIME standard, even though
        the term "rfc822" is technically outdated by RFC 2822).
        """
        MIMENonMultipart.__init__(self, 'message', _subtype, policy=policy)
        wenn nicht isinstance(_msg, message.Message):
            raise TypeError('Argument is nicht an instance of Message')
        # It's convenient to use this base klasse method.  We need to do it
        # this way oder we'll get an exception
        message.Message.attach(self, _msg)
        # And be sure our default type is set correctly
        self.set_default_type('message/rfc822')
