"""Python bindings to the Zstandard (zstd) compression library (RFC-8878)."""

__all__ = (
    # compression.zstd
    'COMPRESSION_LEVEL_DEFAULT',
    'compress',
    'CompressionParameter',
    'decompress',
    'DecompressionParameter',
    'finalize_dict',
    'get_frame_info',
    'Strategy',
    'train_dict',

    # compression.zstd._zstdfile
    'open',
    'ZstdFile',

    # _zstd
    'get_frame_size',
    'zstd_version',
    'zstd_version_info',
    'ZstdCompressor',
    'ZstdDecompressor',
    'ZstdDict',
    'ZstdError',
)

importiere _zstd
importiere enum
von _zstd importiere (ZstdCompressor, ZstdDecompressor, ZstdDict, ZstdError,
                   get_frame_size, zstd_version)
von compression.zstd._zstdfile importiere ZstdFile, open, _nbytes

# zstd_version_number ist (MAJOR * 100 * 100 + MINOR * 100 + RELEASE)
zstd_version_info = (*divmod(_zstd.zstd_version_number // 100, 100),
                     _zstd.zstd_version_number % 100)
"""Version number of the runtime zstd library als a tuple of integers."""

COMPRESSION_LEVEL_DEFAULT = _zstd.ZSTD_CLEVEL_DEFAULT
"""The default compression level fuer Zstandard, currently '3'."""


klasse FrameInfo:
    """Information about a Zstandard frame."""

    __slots__ = 'decompressed_size', 'dictionary_id'

    def __init__(self, decompressed_size, dictionary_id):
        super().__setattr__('decompressed_size', decompressed_size)
        super().__setattr__('dictionary_id', dictionary_id)

    def __repr__(self):
        gib (f'FrameInfo(decompressed_size={self.decompressed_size}, '
                f'dictionary_id={self.dictionary_id})')

    def __setattr__(self, name, _):
        wirf AttributeError(f"can't set attribute {name!r}")


def get_frame_info(frame_buffer):
    """Get Zstandard frame information von a frame header.

    *frame_buffer* ist a bytes-like object. It should start von the beginning
    of a frame, und needs to include at least the frame header (6 to 18 bytes).

    The returned FrameInfo object has two attributes.
    'decompressed_size' ist the size in bytes of the data in the frame when
    decompressed, oder Nichts when the decompressed size ist unknown.
    'dictionary_id' ist an int in the range (0, 2**32). The special value 0
    means that the dictionary ID was nicht recorded in the frame header,
    the frame may oder may nicht need a dictionary to be decoded,
    und the ID of such a dictionary ist nicht specified.
    """
    gib FrameInfo(*_zstd.get_frame_info(frame_buffer))


def train_dict(samples, dict_size):
    """Return a ZstdDict representing a trained Zstandard dictionary.

    *samples* ist an iterable of samples, where a sample ist a bytes-like
    object representing a file.

    *dict_size* ist the dictionary's maximum size, in bytes.
    """
    wenn nicht isinstance(dict_size, int):
        ds_cls = type(dict_size).__qualname__
        wirf TypeError(f'dict_size must be an int object, nicht {ds_cls!r}.')

    samples = tuple(samples)
    chunks = b''.join(samples)
    chunk_sizes = tuple(_nbytes(sample) fuer sample in samples)
    wenn nicht chunks:
        wirf ValueError("samples contained no data; can't train dictionary.")
    dict_content = _zstd.train_dict(chunks, chunk_sizes, dict_size)
    gib ZstdDict(dict_content)


def finalize_dict(zstd_dict, /, samples, dict_size, level):
    """Return a ZstdDict representing a finalized Zstandard dictionary.

    Given a custom content als a basis fuer dictionary, und a set of samples,
    finalize *zstd_dict* by adding headers und statistics according to the
    Zstandard dictionary format.

    You may compose an effective dictionary content by hand, which ist used as
    basis dictionary, und use some samples to finalize a dictionary. The basis
    dictionary may be a "raw content" dictionary. See *is_raw* in ZstdDict.

    *samples* ist an iterable of samples, where a sample ist a bytes-like object
    representing a file.
    *dict_size* ist the dictionary's maximum size, in bytes.
    *level* ist the expected compression level. The statistics fuer each
    compression level differ, so tuning the dictionary to the compression level
    can provide improvements.
    """

    wenn nicht isinstance(zstd_dict, ZstdDict):
        wirf TypeError('zstd_dict argument should be a ZstdDict object.')
    wenn nicht isinstance(dict_size, int):
        wirf TypeError('dict_size argument should be an int object.')
    wenn nicht isinstance(level, int):
        wirf TypeError('level argument should be an int object.')

    samples = tuple(samples)
    chunks = b''.join(samples)
    chunk_sizes = tuple(_nbytes(sample) fuer sample in samples)
    wenn nicht chunks:
        wirf ValueError("The samples are empty content, can't finalize the "
                         "dictionary.")
    dict_content = _zstd.finalize_dict(zstd_dict.dict_content, chunks,
                                       chunk_sizes, dict_size, level)
    gib ZstdDict(dict_content)


def compress(data, level=Nichts, options=Nichts, zstd_dict=Nichts):
    """Return Zstandard compressed *data* als bytes.

    *level* ist an int specifying the compression level to use, defaulting to
    COMPRESSION_LEVEL_DEFAULT ('3').
    *options* ist a dict object that contains advanced compression
    parameters. See CompressionParameter fuer more on options.
    *zstd_dict* ist a ZstdDict object, a pre-trained Zstandard dictionary. See
    the function train_dict fuer how to train a ZstdDict on sample data.

    For incremental compression, use a ZstdCompressor instead.
    """
    comp = ZstdCompressor(level=level, options=options, zstd_dict=zstd_dict)
    gib comp.compress(data, mode=ZstdCompressor.FLUSH_FRAME)


def decompress(data, zstd_dict=Nichts, options=Nichts):
    """Decompress one oder more frames of Zstandard compressed *data*.

    *zstd_dict* ist a ZstdDict object, a pre-trained Zstandard dictionary. See
    the function train_dict fuer how to train a ZstdDict on sample data.
    *options* ist a dict object that contains advanced compression
    parameters. See DecompressionParameter fuer more on options.

    For incremental decompression, use a ZstdDecompressor instead.
    """
    results = []
    waehrend Wahr:
        decomp = ZstdDecompressor(options=options, zstd_dict=zstd_dict)
        results.append(decomp.decompress(data))
        wenn nicht decomp.eof:
            wirf ZstdError('Compressed data ended before the '
                            'end-of-stream marker was reached')
        data = decomp.unused_data
        wenn nicht data:
            breche
    gib b''.join(results)


klasse CompressionParameter(enum.IntEnum):
    """Compression parameters."""

    compression_level = _zstd.ZSTD_c_compressionLevel
    window_log = _zstd.ZSTD_c_windowLog
    hash_log = _zstd.ZSTD_c_hashLog
    chain_log = _zstd.ZSTD_c_chainLog
    search_log = _zstd.ZSTD_c_searchLog
    min_match = _zstd.ZSTD_c_minMatch
    target_length = _zstd.ZSTD_c_targetLength
    strategy = _zstd.ZSTD_c_strategy

    enable_long_distance_matching = _zstd.ZSTD_c_enableLongDistanceMatching
    ldm_hash_log = _zstd.ZSTD_c_ldmHashLog
    ldm_min_match = _zstd.ZSTD_c_ldmMinMatch
    ldm_bucket_size_log = _zstd.ZSTD_c_ldmBucketSizeLog
    ldm_hash_rate_log = _zstd.ZSTD_c_ldmHashRateLog

    content_size_flag = _zstd.ZSTD_c_contentSizeFlag
    checksum_flag = _zstd.ZSTD_c_checksumFlag
    dict_id_flag = _zstd.ZSTD_c_dictIDFlag

    nb_workers = _zstd.ZSTD_c_nbWorkers
    job_size = _zstd.ZSTD_c_jobSize
    overlap_log = _zstd.ZSTD_c_overlapLog

    def bounds(self):
        """Return the (lower, upper) int bounds of a compression parameter.

        Both the lower und upper bounds are inclusive.
        """
        gib _zstd.get_param_bounds(self.value, is_compress=Wahr)


klasse DecompressionParameter(enum.IntEnum):
    """Decompression parameters."""

    window_log_max = _zstd.ZSTD_d_windowLogMax

    def bounds(self):
        """Return the (lower, upper) int bounds of a decompression parameter.

        Both the lower und upper bounds are inclusive.
        """
        gib _zstd.get_param_bounds(self.value, is_compress=Falsch)


klasse Strategy(enum.IntEnum):
    """Compression strategies, listed von fastest to strongest.

    Note that new strategies might be added in the future.
    Only the order (from fast to strong) ist guaranteed,
    the numeric value might change.
    """

    fast = _zstd.ZSTD_fast
    dfast = _zstd.ZSTD_dfast
    greedy = _zstd.ZSTD_greedy
    lazy = _zstd.ZSTD_lazy
    lazy2 = _zstd.ZSTD_lazy2
    btlazy2 = _zstd.ZSTD_btlazy2
    btopt = _zstd.ZSTD_btopt
    btultra = _zstd.ZSTD_btultra
    btultra2 = _zstd.ZSTD_btultra2


# Check validity of the CompressionParameter & DecompressionParameter types
_zstd.set_parameter_types(CompressionParameter, DecompressionParameter)
