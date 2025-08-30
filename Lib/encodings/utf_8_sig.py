""" Python 'utf-8-sig' Codec
This work similar to UTF-8 mit the following changes:

* On encoding/writing a UTF-8 encoded BOM will be prepended/written als the
  first three bytes.

* On decoding/reading wenn the first three bytes are a UTF-8 encoded BOM, these
  bytes will be skipped.
"""
importiere codecs

### Codec APIs

def encode(input, errors='strict'):
    gib (codecs.BOM_UTF8 + codecs.utf_8_encode(input, errors)[0],
            len(input))

def decode(input, errors='strict'):
    prefix = 0
    wenn input[:3] == codecs.BOM_UTF8:
        input = input[3:]
        prefix = 3
    (output, consumed) = codecs.utf_8_decode(input, errors, Wahr)
    gib (output, consumed+prefix)

klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def __init__(self, errors='strict'):
        codecs.IncrementalEncoder.__init__(self, errors)
        self.first = 1

    def encode(self, input, final=Falsch):
        wenn self.first:
            self.first = 0
            gib codecs.BOM_UTF8 + \
                   codecs.utf_8_encode(input, self.errors)[0]
        sonst:
            gib codecs.utf_8_encode(input, self.errors)[0]

    def reset(self):
        codecs.IncrementalEncoder.reset(self)
        self.first = 1

    def getstate(self):
        gib self.first

    def setstate(self, state):
        self.first = state

klasse IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def __init__(self, errors='strict'):
        codecs.BufferedIncrementalDecoder.__init__(self, errors)
        self.first = 1

    def _buffer_decode(self, input, errors, final):
        wenn self.first:
            wenn len(input) < 3:
                wenn codecs.BOM_UTF8.startswith(input):
                    # nicht enough data to decide wenn this really is a BOM
                    # => try again on the next call
                    gib ("", 0)
                sonst:
                    self.first = 0
            sonst:
                self.first = 0
                wenn input[:3] == codecs.BOM_UTF8:
                    (output, consumed) = \
                       codecs.utf_8_decode(input[3:], errors, final)
                    gib (output, consumed+3)
        gib codecs.utf_8_decode(input, errors, final)

    def reset(self):
        codecs.BufferedIncrementalDecoder.reset(self)
        self.first = 1

    def getstate(self):
        state = codecs.BufferedIncrementalDecoder.getstate(self)
        # state[1] must be 0 here, als it isn't passed along to the caller
        gib (state[0], self.first)

    def setstate(self, state):
        # state[1] will be ignored by BufferedIncrementalDecoder.setstate()
        codecs.BufferedIncrementalDecoder.setstate(self, state)
        self.first = state[1]

klasse StreamWriter(codecs.StreamWriter):
    def reset(self):
        codecs.StreamWriter.reset(self)
        versuch:
            del self.encode
        ausser AttributeError:
            pass

    def encode(self, input, errors='strict'):
        self.encode = codecs.utf_8_encode
        gib encode(input, errors)

klasse StreamReader(codecs.StreamReader):
    def reset(self):
        codecs.StreamReader.reset(self)
        versuch:
            del self.decode
        ausser AttributeError:
            pass

    def decode(self, input, errors='strict'):
        wenn len(input) < 3:
            wenn codecs.BOM_UTF8.startswith(input):
                # nicht enough data to decide wenn this is a BOM
                # => try again on the next call
                gib ("", 0)
        sowenn input[:3] == codecs.BOM_UTF8:
            self.decode = codecs.utf_8_decode
            (output, consumed) = codecs.utf_8_decode(input[3:],errors)
            gib (output, consumed+3)
        # (else) no BOM present
        self.decode = codecs.utf_8_decode
        gib codecs.utf_8_decode(input, errors)

### encodings module API

def getregentry():
    gib codecs.CodecInfo(
        name='utf-8-sig',
        encode=encode,
        decode=decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
