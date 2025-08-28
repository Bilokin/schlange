""" Generic Python Character Mapping Codec.

    Use this codec directly rather than through the automatic
    conversion mechanisms supplied by unicode() and .encode().


Written by Marc-Andre Lemburg (mal@lemburg.com).

(c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

"""#"

import codecs

### Codec APIs

klasse Codec(codecs.Codec):

    # Note: Binding these as C functions will result in the klasse not
    # converting them to methods. This is intended.
    encode = codecs.charmap_encode
    decode = codecs.charmap_decode

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def __init__(self, errors='strict', mapping=Nichts):
        codecs.IncrementalEncoder.__init__(self, errors)
        self.mapping = mapping

    def encode(self, input, final=Falsch):
        return codecs.charmap_encode(input, self.errors, self.mapping)[0]

klasse IncrementalDecoder(codecs.IncrementalDecoder):
    def __init__(self, errors='strict', mapping=Nichts):
        codecs.IncrementalDecoder.__init__(self, errors)
        self.mapping = mapping

    def decode(self, input, final=Falsch):
        return codecs.charmap_decode(input, self.errors, self.mapping)[0]

klasse StreamWriter(Codec,codecs.StreamWriter):

    def __init__(self,stream,errors='strict',mapping=Nichts):
        codecs.StreamWriter.__init__(self,stream,errors)
        self.mapping = mapping

    def encode(self,input,errors='strict'):
        return Codec.encode(input,errors,self.mapping)

klasse StreamReader(Codec,codecs.StreamReader):

    def __init__(self,stream,errors='strict',mapping=Nichts):
        codecs.StreamReader.__init__(self,stream,errors)
        self.mapping = mapping

    def decode(self,input,errors='strict'):
        return Codec.decode(input,errors,self.mapping)

### encodings module API

def getregentry():
    return codecs.CodecInfo(
        name='charmap',
        encode=Codec.encode,
        decode=Codec.decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamwriter=StreamWriter,
        streamreader=StreamReader,
    )
