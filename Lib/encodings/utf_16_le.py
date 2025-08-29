""" Python 'utf-16-le' Codec


Written by Marc-Andre Lemburg (mal@lemburg.com).

(c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

"""
importiere codecs

### Codec APIs

encode = codecs.utf_16_le_encode

def decode(input, errors='strict'):
    gib codecs.utf_16_le_decode(input, errors, Wahr)

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=Falsch):
        gib codecs.utf_16_le_encode(input, self.errors)[0]

klasse IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    _buffer_decode = codecs.utf_16_le_decode

klasse StreamWriter(codecs.StreamWriter):
    encode = codecs.utf_16_le_encode

klasse StreamReader(codecs.StreamReader):
    decode = codecs.utf_16_le_decode

### encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name='utf-16-le',
        encode=encode,
        decode=decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
