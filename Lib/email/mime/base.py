# Copyright (C) 2001 Python Software Foundation
# Author: Barry Warsaw
# Contact: email-sig@python.org

"""Base klasse fuer MIME specializations."""

__all__ = ['MIMEBase']

importiere email.policy

von email importiere message


klasse MIMEBase(message.Message):
    """Base klasse fuer MIME specializations."""

    def __init__(self, _maintype, _subtype, *, policy=Nichts, **_params):
        """This constructor adds a Content-Type: und a MIME-Version: header.

        The Content-Type: header is taken von the _maintype und _subtype
        arguments.  Additional parameters fuer this header are taken von the
        keyword arguments.
        """
        wenn policy is Nichts:
            policy = email.policy.compat32
        message.Message.__init__(self, policy=policy)
        ctype = '%s/%s' % (_maintype, _subtype)
        self.add_header('Content-Type', ctype, **_params)
        self['MIME-Version'] = '1.0'
