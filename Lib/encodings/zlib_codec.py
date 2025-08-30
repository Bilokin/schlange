"""Python 'zlib_codec' Codec - zlib compression encoding.

This codec de/encodes von bytes to bytes.

Written by Marc-Andre Lemburg (mal@lemburg.com).
"""

importiere codecs
importiere zlib # this codec needs the optional zlib module !

### Codec APIs

def zlib_encode(input, errors='strict'):
    pruefe errors == 'strict'
    gib (zlib.compress(input), len(input))

def zlib_decode(input, errors='strict'):
    pruefe errors == 'strict'
    gib (zlib.decompress(input), len(input))

klasse Codec(codecs.Codec):
    def encode(self, input, errors='strict'):
        gib zlib_encode(input, errors)
    def decode(self, input, errors='strict'):
        gib zlib_decode(input, errors)

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def __init__(self, errors='strict'):
        pruefe errors == 'strict'
        self.errors = errors
        self.compressobj = zlib.compressobj()

    def encode(self, input, final=Falsch):
        wenn final:
            c = self.compressobj.compress(input)
            gib c + self.compressobj.flush()
        sonst:
            gib self.compressobj.compress(input)

    def reset(self):
        self.compressobj = zlib.compressobj()

klasse IncrementalDecoder(codecs.IncrementalDecoder):
    def __init__(self, errors='strict'):
        pruefe errors == 'strict'
        self.errors = errors
        self.decompressobj = zlib.decompressobj()

    def decode(self, input, final=Falsch):
        wenn final:
            c = self.decompressobj.decompress(input)
            gib c + self.decompressobj.flush()
        sonst:
            gib self.decompressobj.decompress(input)

    def reset(self):
        self.decompressobj = zlib.decompressobj()

klasse StreamWriter(Codec, codecs.StreamWriter):
    charbuffertype = bytes

klasse StreamReader(Codec, codecs.StreamReader):
    charbuffertype = bytes

### encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name='zlib',
        encode=zlib_encode,
        decode=zlib_decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
        _is_text_encoding=Falsch,
    )
