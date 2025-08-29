#
# big5hkscs.py: Python Unicode Codec fuer BIG5HKSCS
#
# Written by Hye-Shik Chang <perky@FreeBSD.org>
#

importiere _codecs_hk, codecs
importiere _multibytecodec als mbc

codec = _codecs_hk.getcodec('big5hkscs')

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
    return codecs.CodecInfo(
        name='big5hkscs',
        encode=Codec().encode,
        decode=Codec().decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
