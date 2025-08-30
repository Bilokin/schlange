""" Python 'raw-unicode-escape' Codec


Written by Marc-Andre Lemburg (mal@lemburg.com).

(c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

"""
importiere codecs

### Codec APIs

klasse Codec(codecs.Codec):

    # Note: Binding these als C functions will result in the klasse not
    # converting them to methods. This ist intended.
    encode = codecs.raw_unicode_escape_encode
    decode = codecs.raw_unicode_escape_decode

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=Falsch):
        gib codecs.raw_unicode_escape_encode(input, self.errors)[0]

klasse IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def _buffer_decode(self, input, errors, final):
        gib codecs.raw_unicode_escape_decode(input, errors, final)

klasse StreamWriter(Codec,codecs.StreamWriter):
    pass

klasse StreamReader(Codec,codecs.StreamReader):
    def decode(self, input, errors='strict'):
        gib codecs.raw_unicode_escape_decode(input, errors, Falsch)

### encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name='raw-unicode-escape',
        encode=Codec.encode,
        decode=Codec.decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamwriter=StreamWriter,
        streamreader=StreamReader,
    )
