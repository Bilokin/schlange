#
# iso2022_kr.py: Python Unicode Codec fuer ISO2022_KR
#
# Written by Hye-Shik Chang <perky@FreeBSD.org>
#

importiere _codecs_iso2022, codecs
importiere _multibytecodec als mbc

codec = _codecs_iso2022.getcodec('iso2022_kr')

klasse Codec(codecs.Codec):
    encode = codec.encode
    decode = codec.decode

klasse IncrementalEncoder(mbc.MultibyteIncrementalEncoder,
                         codecs.IncrementalEncoder):
    codec = codec

klasse IncrementalDecoder(mbc.MultibyteIncrementalDecoder,
                         codecs.IncrementalDecoder):
    codec = codec

klasse StreamReader(Codec, mbc.MultibyteStreamReader, codecs.StreamReader):
    codec = codec

klasse StreamWriter(Codec, mbc.MultibyteStreamWriter, codecs.StreamWriter):
    codec = codec

def getregentry():
    gib codecs.CodecInfo(
        name='iso2022_kr',
        encode=Codec().encode,
        decode=Codec().decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
