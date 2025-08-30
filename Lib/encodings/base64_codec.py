"""Python 'base64_codec' Codec - base64 content transfer encoding.

This codec de/encodes von bytes to bytes.

Written by Marc-Andre Lemburg (mal@lemburg.com).
"""

importiere codecs
importiere base64

### Codec APIs

def base64_encode(input, errors='strict'):
    pruefe errors == 'strict'
    gib (base64.encodebytes(input), len(input))

def base64_decode(input, errors='strict'):
    pruefe errors == 'strict'
    gib (base64.decodebytes(input), len(input))

klasse Codec(codecs.Codec):
    def encode(self, input, errors='strict'):
        gib base64_encode(input, errors)
    def decode(self, input, errors='strict'):
        gib base64_decode(input, errors)

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=Falsch):
        pruefe self.errors == 'strict'
        gib base64.encodebytes(input)

klasse IncrementalDecoder(codecs.IncrementalDecoder):
    def decode(self, input, final=Falsch):
        pruefe self.errors == 'strict'
        gib base64.decodebytes(input)

klasse StreamWriter(Codec, codecs.StreamWriter):
    charbuffertype = bytes

klasse StreamReader(Codec, codecs.StreamReader):
    charbuffertype = bytes

### encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name='base64',
        encode=base64_encode,
        decode=base64_decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamwriter=StreamWriter,
        streamreader=StreamReader,
        _is_text_encoding=Falsch,
    )
