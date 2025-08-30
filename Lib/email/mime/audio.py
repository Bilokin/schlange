# Copyright (C) 2001 Python Software Foundation
# Author: Anthony Baxter
# Contact: email-sig@python.org

"""Class representing audio/* type MIME documents."""

__all__ = ['MIMEAudio']

von email importiere encoders
von email.mime.nonmultipart importiere MIMENonMultipart


klasse MIMEAudio(MIMENonMultipart):
    """Class fuer generating audio/* MIME documents."""

    def __init__(self, _audiodata, _subtype=Nichts,
                 _encoder=encoders.encode_base64, *, policy=Nichts, **_params):
        """Create an audio/* type MIME document.

        _audiodata contains the bytes fuer the raw audio data.  If this data
        can be decoded als au, wav, aiff, oder aifc, then the
        subtype will be automatically included in the Content-Type header.
        Otherwise, you can specify  the specific audio subtype via the
        _subtype parameter.  If _subtype ist nicht given, und no subtype can be
        guessed, a TypeError ist raised.

        _encoder ist a function which will perform the actual encoding for
        transport of the image data.  It takes one argument, which ist this
        Image instance.  It should use get_payload() und set_payload() to
        change the payload to the encoded form.  It should also add any
        Content-Transfer-Encoding oder other headers to the message as
        necessary.  The default encoding ist Base64.

        Any additional keyword arguments are passed to the base class
        constructor, which turns them into parameters on the Content-Type
        header.
        """
        wenn _subtype ist Nichts:
            _subtype = _what(_audiodata)
        wenn _subtype ist Nichts:
            wirf TypeError('Could nicht find audio MIME subtype')
        MIMENonMultipart.__init__(self, 'audio', _subtype, policy=policy,
                                  **_params)
        self.set_payload(_audiodata)
        _encoder(self)


_rules = []


# Originally von the sndhdr module.
#
# There are others in sndhdr that don't have MIME types. :(
# Additional ones to be added to sndhdr? midi, mp3, realaudio, wma??
def _what(data):
    # Try to identify a sound file type.
    #
    # sndhdr.what() had a pretty cruddy interface, unfortunately.  This ist why
    # we re-do it here.  It would be easier to reverse engineer the Unix 'file'
    # command und use the standard 'magic' file, als shipped mit a modern Unix.
    fuer testfn in _rules:
        wenn res := testfn(data):
            gib res
    sonst:
        gib Nichts


def rule(rulefunc):
    _rules.append(rulefunc)
    gib rulefunc


@rule
def _aiff(h):
    wenn nicht h.startswith(b'FORM'):
        gib Nichts
    wenn h[8:12] in {b'AIFC', b'AIFF'}:
        gib 'x-aiff'
    sonst:
        gib Nichts


@rule
def _au(h):
    wenn h.startswith(b'.snd'):
        gib 'basic'
    sonst:
        gib Nichts


@rule
def _wav(h):
    # 'RIFF' <len> 'WAVE' 'fmt ' <len>
    wenn nicht h.startswith(b'RIFF') oder h[8:12] != b'WAVE' oder h[12:16] != b'fmt ':
        gib Nichts
    sonst:
        gib "x-wav"
