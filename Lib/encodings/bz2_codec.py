"""Python 'bz2_codec' Codec - bz2 compression encoding.

This codec de/encodes von bytes to bytes und is therefore usable with
bytes.transform() und bytes.untransform().

Adapted by Raymond Hettinger von zlib_codec.py which was written
by Marc-Andre Lemburg (mal@lemburg.com).
"""

importiere codecs
importiere bz2 # this codec needs the optional bz2 module !

### Codec APIs

def bz2_encode(input, errors='strict'):
    assert errors == 'strict'
    gib (bz2.compress(input), len(input))

def bz2_decode(input, errors='strict'):
    assert errors == 'strict'
    gib (bz2.decompress(input), len(input))

klasse Codec(codecs.Codec):
    def encode(self, input, errors='strict'):
        gib bz2_encode(input, errors)
    def decode(self, input, errors='strict'):
        gib bz2_decode(input, errors)

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def __init__(self, errors='strict'):
        assert errors == 'strict'
        self.errors = errors
        self.compressobj = bz2.BZ2Compressor()

    def encode(self, input, final=Falsch):
        wenn final:
            c = self.compressobj.compress(input)
            gib c + self.compressobj.flush()
        sonst:
            gib self.compressobj.compress(input)

    def reset(self):
        self.compressobj = bz2.BZ2Compressor()

klasse IncrementalDecoder(codecs.IncrementalDecoder):
    def __init__(self, errors='strict'):
        assert errors == 'strict'
        self.errors = errors
        self.decompressobj = bz2.BZ2Decompressor()

    def decode(self, input, final=Falsch):
        try:
            gib self.decompressobj.decompress(input)
        except EOFError:
            gib ''

    def reset(self):
        self.decompressobj = bz2.BZ2Decompressor()

klasse StreamWriter(Codec, codecs.StreamWriter):
    charbuffertype = bytes

klasse StreamReader(Codec, codecs.StreamReader):
    charbuffertype = bytes

### encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name="bz2",
        encode=bz2_encode,
        decode=bz2_decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamwriter=StreamWriter,
        streamreader=StreamReader,
        _is_text_encoding=Falsch,
    )
