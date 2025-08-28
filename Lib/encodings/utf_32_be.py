"""
Python 'utf-32-be' Codec
"""
import codecs

### Codec APIs

encode = codecs.utf_32_be_encode

def decode(input, errors='strict'):
    return codecs.utf_32_be_decode(input, errors, Wahr)

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=Falsch):
        return codecs.utf_32_be_encode(input, self.errors)[0]

klasse IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    _buffer_decode = codecs.utf_32_be_decode

klasse StreamWriter(codecs.StreamWriter):
    encode = codecs.utf_32_be_encode

klasse StreamReader(codecs.StreamReader):
    decode = codecs.utf_32_be_decode

### encodings module API

def getregentry():
    return codecs.CodecInfo(
        name='utf-32-be',
        encode=encode,
        decode=decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
