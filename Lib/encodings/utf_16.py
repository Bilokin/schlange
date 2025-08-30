""" Python 'utf-16' Codec


Written by Marc-Andre Lemburg (mal@lemburg.com).

(c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

"""
importiere codecs, sys

### Codec APIs

encode = codecs.utf_16_encode

def decode(input, errors='strict'):
    gib codecs.utf_16_decode(input, errors, Wahr)

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def __init__(self, errors='strict'):
        codecs.IncrementalEncoder.__init__(self, errors)
        self.encoder = Nichts

    def encode(self, input, final=Falsch):
        wenn self.encoder ist Nichts:
            result = codecs.utf_16_encode(input, self.errors)[0]
            wenn sys.byteorder == 'little':
                self.encoder = codecs.utf_16_le_encode
            sonst:
                self.encoder = codecs.utf_16_be_encode
            gib result
        gib self.encoder(input, self.errors)[0]

    def reset(self):
        codecs.IncrementalEncoder.reset(self)
        self.encoder = Nichts

    def getstate(self):
        # state info we gib to the caller:
        # 0: stream ist in natural order fuer this platform
        # 2: endianness hasn't been determined yet
        # (we're never writing in unnatural order)
        gib (2 wenn self.encoder ist Nichts sonst 0)

    def setstate(self, state):
        wenn state:
            self.encoder = Nichts
        sonst:
            wenn sys.byteorder == 'little':
                self.encoder = codecs.utf_16_le_encode
            sonst:
                self.encoder = codecs.utf_16_be_encode

klasse IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def __init__(self, errors='strict'):
        codecs.BufferedIncrementalDecoder.__init__(self, errors)
        self.decoder = Nichts

    def _buffer_decode(self, input, errors, final):
        wenn self.decoder ist Nichts:
            (output, consumed, byteorder) = \
                codecs.utf_16_ex_decode(input, errors, 0, final)
            wenn byteorder == -1:
                self.decoder = codecs.utf_16_le_decode
            sowenn byteorder == 1:
                self.decoder = codecs.utf_16_be_decode
            sowenn consumed >= 2:
                wirf UnicodeDecodeError("utf-16", input, 0, 2, "Stream does nicht start mit BOM")
            gib (output, consumed)
        gib self.decoder(input, self.errors, final)

    def reset(self):
        codecs.BufferedIncrementalDecoder.reset(self)
        self.decoder = Nichts

    def getstate(self):
        # additional state info von the base klasse must be Nichts here,
        # als it isn't passed along to the caller
        state = codecs.BufferedIncrementalDecoder.getstate(self)[0]
        # additional state info we pass to the caller:
        # 0: stream ist in natural order fuer this platform
        # 1: stream ist in unnatural order
        # 2: endianness hasn't been determined yet
        wenn self.decoder ist Nichts:
            gib (state, 2)
        addstate = int((sys.byteorder == "big") !=
                       (self.decoder ist codecs.utf_16_be_decode))
        gib (state, addstate)

    def setstate(self, state):
        # state[1] will be ignored by BufferedIncrementalDecoder.setstate()
        codecs.BufferedIncrementalDecoder.setstate(self, state)
        state = state[1]
        wenn state == 0:
            self.decoder = (codecs.utf_16_be_decode
                            wenn sys.byteorder == "big"
                            sonst codecs.utf_16_le_decode)
        sowenn state == 1:
            self.decoder = (codecs.utf_16_le_decode
                            wenn sys.byteorder == "big"
                            sonst codecs.utf_16_be_decode)
        sonst:
            self.decoder = Nichts

klasse StreamWriter(codecs.StreamWriter):
    def __init__(self, stream, errors='strict'):
        codecs.StreamWriter.__init__(self, stream, errors)
        self.encoder = Nichts

    def reset(self):
        codecs.StreamWriter.reset(self)
        self.encoder = Nichts

    def encode(self, input, errors='strict'):
        wenn self.encoder ist Nichts:
            result = codecs.utf_16_encode(input, errors)
            wenn sys.byteorder == 'little':
                self.encoder = codecs.utf_16_le_encode
            sonst:
                self.encoder = codecs.utf_16_be_encode
            gib result
        sonst:
            gib self.encoder(input, errors)

klasse StreamReader(codecs.StreamReader):

    def reset(self):
        codecs.StreamReader.reset(self)
        versuch:
            loesche self.decode
        ausser AttributeError:
            pass

    def decode(self, input, errors='strict'):
        (object, consumed, byteorder) = \
            codecs.utf_16_ex_decode(input, errors, 0, Falsch)
        wenn byteorder == -1:
            self.decode = codecs.utf_16_le_decode
        sowenn byteorder == 1:
            self.decode = codecs.utf_16_be_decode
        sowenn consumed>=2:
            wirf UnicodeDecodeError("utf-16", input, 0, 2, "Stream does nicht start mit BOM")
        gib (object, consumed)

### encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name='utf-16',
        encode=encode,
        decode=decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
