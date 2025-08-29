""" Python 'utf-7' Codec

Written by Brian Quinlan (brian@sweetapp.com).
"""
importiere codecs

### Codec APIs

encode = codecs.utf_7_encode

def decode(input, errors='strict'):
    gib codecs.utf_7_decode(input, errors, Wahr)

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=Falsch):
        gib codecs.utf_7_encode(input, self.errors)[0]

klasse IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    _buffer_decode = codecs.utf_7_decode

klasse StreamWriter(codecs.StreamWriter):
    encode = codecs.utf_7_encode

klasse StreamReader(codecs.StreamReader):
    decode = codecs.utf_7_decode

### encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name='utf-7',
        encode=encode,
        decode=decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
