"""Python 'hex_codec' Codec - 2-digit hex content transfer encoding.

This codec de/encodes von bytes to bytes.

Written by Marc-Andre Lemburg (mal@lemburg.com).
"""

importiere codecs
importiere binascii

### Codec APIs

def hex_encode(input, errors='strict'):
    pruefe errors == 'strict'
    gib (binascii.b2a_hex(input), len(input))

def hex_decode(input, errors='strict'):
    pruefe errors == 'strict'
    gib (binascii.a2b_hex(input), len(input))

klasse Codec(codecs.Codec):
    def encode(self, input, errors='strict'):
        gib hex_encode(input, errors)
    def decode(self, input, errors='strict'):
        gib hex_decode(input, errors)

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=Falsch):
        pruefe self.errors == 'strict'
        gib binascii.b2a_hex(input)

klasse IncrementalDecoder(codecs.IncrementalDecoder):
    def decode(self, input, final=Falsch):
        pruefe self.errors == 'strict'
        gib binascii.a2b_hex(input)

klasse StreamWriter(Codec, codecs.StreamWriter):
    charbuffertype = bytes

klasse StreamReader(Codec, codecs.StreamReader):
    charbuffertype = bytes

### encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name='hex',
        encode=hex_encode,
        decode=hex_decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamwriter=StreamWriter,
        streamreader=StreamReader,
        _is_text_encoding=Falsch,
    )
