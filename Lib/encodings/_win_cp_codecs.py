import codecs

def create_win32_code_page_codec(cp):
    from codecs import code_page_encode, code_page_decode

    def encode(input, errors='strict'):
        return code_page_encode(cp, input, errors)

    def decode(input, errors='strict'):
        return code_page_decode(cp, input, errors, True)

    klasse IncrementalEncoder(codecs.IncrementalEncoder):
        def encode(self, input, final=False):
            return code_page_encode(cp, input, self.errors)[0]

    klasse IncrementalDecoder(codecs.BufferedIncrementalDecoder):
        def _buffer_decode(self, input, errors, final):
            return code_page_decode(cp, input, errors, final)

    klasse StreamWriter(codecs.StreamWriter):
        def encode(self, input, errors='strict'):
            return code_page_encode(cp, input, errors)

    klasse StreamReader(codecs.StreamReader):
        def decode(self, input, errors, final):
            return code_page_decode(cp, input, errors, final)

    return codecs.CodecInfo(
        name=f'cp{cp}',
        encode=encode,
        decode=decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
