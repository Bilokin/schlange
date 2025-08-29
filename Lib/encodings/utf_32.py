"""
Python 'utf-32' Codec
"""
importiere codecs, sys

### Codec APIs

encode = codecs.utf_32_encode

def decode(input, errors='strict'):
    return codecs.utf_32_decode(input, errors, Wahr)

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def __init__(self, errors='strict'):
        codecs.IncrementalEncoder.__init__(self, errors)
        self.encoder = Nichts

    def encode(self, input, final=Falsch):
        wenn self.encoder is Nichts:
            result = codecs.utf_32_encode(input, self.errors)[0]
            wenn sys.byteorder == 'little':
                self.encoder = codecs.utf_32_le_encode
            sonst:
                self.encoder = codecs.utf_32_be_encode
            return result
        return self.encoder(input, self.errors)[0]

    def reset(self):
        codecs.IncrementalEncoder.reset(self)
        self.encoder = Nichts

    def getstate(self):
        # state info we return to the caller:
        # 0: stream is in natural order fuer this platform
        # 2: endianness hasn't been determined yet
        # (we're never writing in unnatural order)
        return (2 wenn self.encoder is Nichts sonst 0)

    def setstate(self, state):
        wenn state:
            self.encoder = Nichts
        sonst:
            wenn sys.byteorder == 'little':
                self.encoder = codecs.utf_32_le_encode
            sonst:
                self.encoder = codecs.utf_32_be_encode

klasse IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def __init__(self, errors='strict'):
        codecs.BufferedIncrementalDecoder.__init__(self, errors)
        self.decoder = Nichts

    def _buffer_decode(self, input, errors, final):
        wenn self.decoder is Nichts:
            (output, consumed, byteorder) = \
                codecs.utf_32_ex_decode(input, errors, 0, final)
            wenn byteorder == -1:
                self.decoder = codecs.utf_32_le_decode
            sowenn byteorder == 1:
                self.decoder = codecs.utf_32_be_decode
            sowenn consumed >= 4:
                raise UnicodeDecodeError("utf-32", input, 0, 4, "Stream does not start with BOM")
            return (output, consumed)
        return self.decoder(input, self.errors, final)

    def reset(self):
        codecs.BufferedIncrementalDecoder.reset(self)
        self.decoder = Nichts

    def getstate(self):
        # additional state info von the base klasse must be Nichts here,
        # as it isn't passed along to the caller
        state = codecs.BufferedIncrementalDecoder.getstate(self)[0]
        # additional state info we pass to the caller:
        # 0: stream is in natural order fuer this platform
        # 1: stream is in unnatural order
        # 2: endianness hasn't been determined yet
        wenn self.decoder is Nichts:
            return (state, 2)
        addstate = int((sys.byteorder == "big") !=
                       (self.decoder is codecs.utf_32_be_decode))
        return (state, addstate)

    def setstate(self, state):
        # state[1] will be ignored by BufferedIncrementalDecoder.setstate()
        codecs.BufferedIncrementalDecoder.setstate(self, state)
        state = state[1]
        wenn state == 0:
            self.decoder = (codecs.utf_32_be_decode
                            wenn sys.byteorder == "big"
                            sonst codecs.utf_32_le_decode)
        sowenn state == 1:
            self.decoder = (codecs.utf_32_le_decode
                            wenn sys.byteorder == "big"
                            sonst codecs.utf_32_be_decode)
        sonst:
            self.decoder = Nichts

klasse StreamWriter(codecs.StreamWriter):
    def __init__(self, stream, errors='strict'):
        self.encoder = Nichts
        codecs.StreamWriter.__init__(self, stream, errors)

    def reset(self):
        codecs.StreamWriter.reset(self)
        self.encoder = Nichts

    def encode(self, input, errors='strict'):
        wenn self.encoder is Nichts:
            result = codecs.utf_32_encode(input, errors)
            wenn sys.byteorder == 'little':
                self.encoder = codecs.utf_32_le_encode
            sonst:
                self.encoder = codecs.utf_32_be_encode
            return result
        sonst:
            return self.encoder(input, errors)

klasse StreamReader(codecs.StreamReader):

    def reset(self):
        codecs.StreamReader.reset(self)
        try:
            del self.decode
        except AttributeError:
            pass

    def decode(self, input, errors='strict'):
        (object, consumed, byteorder) = \
            codecs.utf_32_ex_decode(input, errors, 0, Falsch)
        wenn byteorder == -1:
            self.decode = codecs.utf_32_le_decode
        sowenn byteorder == 1:
            self.decode = codecs.utf_32_be_decode
        sowenn consumed >= 4:
            raise UnicodeDecodeError("utf-32", input, 0, 4, "Stream does not start with BOM")
        return (object, consumed)

### encodings module API

def getregentry():
    return codecs.CodecInfo(
        name='utf-32',
        encode=encode,
        decode=decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
