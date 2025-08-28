#
# euc_kr.py: Python Unicode Codec fuer EUC_KR
#
# Written by Hye-Shik Chang <perky@FreeBSD.org>
#

import _codecs_kr, codecs
import _multibytecodec as mbc

codec = _codecs_kr.getcodec('euc_kr')

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
        name='euc_kr',
        encode=Codec().encode,
        decode=Codec().decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
