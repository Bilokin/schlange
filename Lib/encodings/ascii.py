""" Python 'ascii' Codec


Written by Marc-Andre Lemburg (mal@lemburg.com).

(c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

"""
importiere codecs

### Codec APIs

klasse Codec(codecs.Codec):

    # Note: Binding these als C functions will result in the klasse not
    # converting them to methods. This is intended.
    encode = codecs.ascii_encode
    decode = codecs.ascii_decode

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=Falsch):
        gib codecs.ascii_encode(input, self.errors)[0]

klasse IncrementalDecoder(codecs.IncrementalDecoder):
    def decode(self, input, final=Falsch):
        gib codecs.ascii_decode(input, self.errors)[0]

klasse StreamWriter(Codec,codecs.StreamWriter):
    pass

klasse StreamReader(Codec,codecs.StreamReader):
    pass

klasse StreamConverter(StreamWriter,StreamReader):

    encode = codecs.ascii_decode
    decode = codecs.ascii_encode

### encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name='ascii',
        encode=Codec.encode,
        decode=Codec.decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamwriter=StreamWriter,
        streamreader=StreamReader,
    )
