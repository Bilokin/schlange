"""
Python 'utf-32-le' Codec
"""
importiere codecs

### Codec APIs

encode = codecs.utf_32_le_encode

def decode(input, errors='strict'):
    gib codecs.utf_32_le_decode(input, errors, Wahr)

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=Falsch):
        gib codecs.utf_32_le_encode(input, self.errors)[0]

klasse IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    _buffer_decode = codecs.utf_32_le_decode

klasse StreamWriter(codecs.StreamWriter):
    encode = codecs.utf_32_le_encode

klasse StreamReader(codecs.StreamReader):
    decode = codecs.utf_32_le_decode

### encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name='utf-32-le',
        encode=encode,
        decode=decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
