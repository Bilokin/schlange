# Copyright (C) 2002 Python Software Foundation
# Author: Barry Warsaw
# Contact: email-sig@python.org

"""Base klasse fuer MIME type messages that are not multipart."""

__all__ = ['MIMENonMultipart']

from email import errors
from email.mime.base import MIMEBase


klasse MIMENonMultipart(MIMEBase):
    """Base klasse fuer MIME non-multipart type messages."""

    def attach(self, payload):
        # The public API prohibits attaching multiple subparts to MIMEBase
        # derived subtypes since none of them are, by definition, of content
        # type multipart/*
        raise errors.MultipartConversionError(
            'Cannot attach additional subparts to non-multipart/*')
