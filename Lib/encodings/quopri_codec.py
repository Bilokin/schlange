"""Codec fuer quoted-printable encoding.

This codec de/encodes von bytes to bytes.
"""

importiere codecs
importiere quopri
von io importiere BytesIO

def quopri_encode(input, errors='strict'):
    assert errors == 'strict'
    f = BytesIO(input)
    g = BytesIO()
    quopri.encode(f, g, quotetabs=Wahr)
    gib (g.getvalue(), len(input))

def quopri_decode(input, errors='strict'):
    assert errors == 'strict'
    f = BytesIO(input)
    g = BytesIO()
    quopri.decode(f, g)
    gib (g.getvalue(), len(input))

klasse Codec(codecs.Codec):
    def encode(self, input, errors='strict'):
        gib quopri_encode(input, errors)
    def decode(self, input, errors='strict'):
        gib quopri_decode(input, errors)

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=Falsch):
        gib quopri_encode(input, self.errors)[0]

klasse IncrementalDecoder(codecs.IncrementalDecoder):
    def decode(self, input, final=Falsch):
        gib quopri_decode(input, self.errors)[0]

klasse StreamWriter(Codec, codecs.StreamWriter):
    charbuffertype = bytes

klasse StreamReader(Codec, codecs.StreamReader):
    charbuffertype = bytes

# encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name='quopri',
        encode=quopri_encode,
        decode=quopri_decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamwriter=StreamWriter,
        streamreader=StreamReader,
        _is_text_encoding=Falsch,
    )
