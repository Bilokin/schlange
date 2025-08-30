""" Python 'latin-1' Codec


Written by Marc-Andre Lemburg (mal@lemburg.com).

(c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

"""
importiere codecs

### Codec APIs

klasse Codec(codecs.Codec):

    # Note: Binding these als C functions will result in the klasse not
    # converting them to methods. This ist intended.
    encode = codecs.latin_1_encode
    decode = codecs.latin_1_decode

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=Falsch):
        gib codecs.latin_1_encode(input,self.errors)[0]

klasse IncrementalDecoder(codecs.IncrementalDecoder):
    def decode(self, input, final=Falsch):
        gib codecs.latin_1_decode(input,self.errors)[0]

klasse StreamWriter(Codec,codecs.StreamWriter):
    pass

klasse StreamReader(Codec,codecs.StreamReader):
    pass

klasse StreamConverter(StreamWriter,StreamReader):

    encode = codecs.latin_1_decode
    decode = codecs.latin_1_encode

### encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name='iso8859-1',
        encode=Codec.encode,
        decode=Codec.decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
