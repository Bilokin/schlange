""" Python 'oem' Codec for Windows

"""
# Import them explicitly to cause an ImportError
# on non-Windows systems
from codecs import oem_encode, oem_decode
# for IncrementalDecoder, IncrementalEncoder, ...
import codecs

### Codec APIs

encode = oem_encode

def decode(input, errors='strict'):
    return oem_decode(input, errors, True)

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=False):
        return oem_encode(input, self.errors)[0]

klasse IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    _buffer_decode = oem_decode

klasse StreamWriter(codecs.StreamWriter):
    encode = oem_encode

klasse StreamReader(codecs.StreamReader):
    decode = oem_decode

### encodings module API

def getregentry():
    return codecs.CodecInfo(
        name='oem',
        encode=encode,
        decode=decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
