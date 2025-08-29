#
# big5.py: Python Unicode Codec fuer BIG5
#
# Written by Hye-Shik Chang <perky@FreeBSD.org>
#

importiere _codecs_tw, codecs
importiere _multibytecodec als mbc

codec = _codecs_tw.getcodec('big5')

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
        name='big5',
        encode=Codec().encode,
        decode=Codec().decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
