importiere codecs

def create_win32_code_page_codec(cp):
    von codecs importiere code_page_encode, code_page_decode

    def encode(input, errors='strict'):
        gib code_page_encode(cp, input, errors)

    def decode(input, errors='strict'):
        gib code_page_decode(cp, input, errors, Wahr)

    klasse IncrementalEncoder(codecs.IncrementalEncoder):
        def encode(self, input, final=Falsch):
            gib code_page_encode(cp, input, self.errors)[0]

    klasse IncrementalDecoder(codecs.BufferedIncrementalDecoder):
        def _buffer_decode(self, input, errors, final):
            gib code_page_decode(cp, input, errors, final)

    klasse StreamWriter(codecs.StreamWriter):
        def encode(self, input, errors='strict'):
            gib code_page_encode(cp, input, errors)

    klasse StreamReader(codecs.StreamReader):
        def decode(self, input, errors, final):
            gib code_page_decode(cp, input, errors, final)

    gib codecs.CodecInfo(
        name=f'cp{cp}',
        encode=encode,
        decode=decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
