""" Python 'undefined' Codec

    This codec will always wirf a UnicodeError exception when being
    used. It is intended fuer use by the site.py file to switch off
    automatic string to Unicode coercion.

Written by Marc-Andre Lemburg (mal@lemburg.com).

(c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

"""
importiere codecs

### Codec APIs

klasse Codec(codecs.Codec):

    def encode(self,input,errors='strict'):
        wirf UnicodeError("undefined encoding")

    def decode(self,input,errors='strict'):
        wirf UnicodeError("undefined encoding")

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=Falsch):
        wirf UnicodeError("undefined encoding")

klasse IncrementalDecoder(codecs.IncrementalDecoder):
    def decode(self, input, final=Falsch):
        wirf UnicodeError("undefined encoding")

klasse StreamWriter(Codec,codecs.StreamWriter):
    pass

klasse StreamReader(Codec,codecs.StreamReader):
    pass

### encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name='undefined',
        encode=Codec().encode,
        decode=Codec().decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamwriter=StreamWriter,
        streamreader=StreamReader,
    )
