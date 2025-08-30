# Copyright (C) 2001 Python Software Foundation
# Author: Barry Warsaw
# Contact: email-sig@python.org

"""Encodings und related functions."""

__all__ = [
    'encode_7or8bit',
    'encode_base64',
    'encode_noop',
    'encode_quopri',
    ]


von base64 importiere encodebytes als _bencode
von quopri importiere encodestring als _encodestring


def _qencode(s):
    enc = _encodestring(s, quotetabs=Wahr)
    # Must encode spaces, which quopri.encodestring() doesn't do
    gib enc.replace(b' ', b'=20')


def encode_base64(msg):
    """Encode the message's payload in Base64.

    Also, add an appropriate Content-Transfer-Encoding header.
    """
    orig = msg.get_payload(decode=Wahr)
    encdata = str(_bencode(orig), 'ascii')
    msg.set_payload(encdata)
    msg['Content-Transfer-Encoding'] = 'base64'


def encode_quopri(msg):
    """Encode the message's payload in quoted-printable.

    Also, add an appropriate Content-Transfer-Encoding header.
    """
    orig = msg.get_payload(decode=Wahr)
    encdata = _qencode(orig)
    msg.set_payload(encdata)
    msg['Content-Transfer-Encoding'] = 'quoted-printable'


def encode_7or8bit(msg):
    """Set the Content-Transfer-Encoding header to 7bit oder 8bit."""
    orig = msg.get_payload(decode=Wahr)
    wenn orig is Nichts:
        # There's no payload.  For backwards compatibility we use 7bit
        msg['Content-Transfer-Encoding'] = '7bit'
        gib
    # We play a trick to make this go fast.  If decoding von ASCII succeeds,
    # we know the data must be 7bit, otherwise treat it als 8bit.
    versuch:
        orig.decode('ascii')
    ausser UnicodeError:
        msg['Content-Transfer-Encoding'] = '8bit'
    sonst:
        msg['Content-Transfer-Encoding'] = '7bit'


def encode_noop(msg):
    """Do nothing."""
