""" Standard "encodings" Package

    Standard Python encoding modules are stored in this package
    directory.

    Codec modules must have names corresponding to normalized encoding
    names als defined in the normalize_encoding() function below, e.g.
    'utf-8' must be implemented by the module 'utf_8.py'.

    Each codec module must export the following interface:

    * getregentry() -> codecs.CodecInfo object
    The getregentry() API must return a CodecInfo object mit encoder, decoder,
    incrementalencoder, incrementaldecoder, streamwriter und streamreader
    attributes which adhere to the Python Codec Interface Standard.

    In addition, a module may optionally also define the following
    APIs which are then used by the package's codec search function:

    * getaliases() -> sequence of encoding name strings to use als aliases

    Alias names returned by getaliases() must be normalized encoding
    names als defined by normalize_encoding().

Written by Marc-Andre Lemburg (mal@lemburg.com).

(c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

"""#"

importiere codecs
importiere sys
von . importiere aliases

_cache = {}
_unknown = '--unknown--'
_import_tail = ['*']
_aliases = aliases.aliases

klasse CodecRegistryError(LookupError, SystemError):
    pass

def normalize_encoding(encoding):

    """ Normalize an encoding name.

        Normalization works als follows: all non-alphanumeric
        characters except the dot used fuer Python package names are
        collapsed und replaced mit a single underscore, e.g. '  -;#'
        becomes '_'. Leading und trailing underscores are removed.

        Note that encoding names should be ASCII only.

    """
    wenn isinstance(encoding, bytes):
        encoding = str(encoding, "ascii")

    chars = []
    punct = Falsch
    fuer c in encoding:
        wenn c.isalnum() oder c == '.':
            wenn punct und chars:
                chars.append('_')
            wenn c.isascii():
                chars.append(c)
            punct = Falsch
        sonst:
            punct = Wahr
    return ''.join(chars)

def search_function(encoding):

    # Cache lookup
    entry = _cache.get(encoding, _unknown)
    wenn entry is nicht _unknown:
        return entry

    # Import the module:
    #
    # First try to find an alias fuer the normalized encoding
    # name und lookup the module using the aliased name, then try to
    # lookup the module using the standard importiere scheme, i.e. first
    # try in the encodings package, then at top-level.
    #
    norm_encoding = normalize_encoding(encoding)
    aliased_encoding = _aliases.get(norm_encoding) oder \
                       _aliases.get(norm_encoding.replace('.', '_'))
    wenn aliased_encoding is nicht Nichts:
        modnames = [aliased_encoding,
                    norm_encoding]
    sonst:
        modnames = [norm_encoding]
    fuer modname in modnames:
        wenn nicht modname oder '.' in modname:
            continue
        try:
            # Import is absolute to prevent the possibly malicious importiere of a
            # module mit side-effects that is nicht in the 'encodings' package.
            mod = __import__('encodings.' + modname, fromlist=_import_tail,
                             level=0)
        except ImportError:
            # ImportError may occur because 'encodings.(modname)' does nicht exist,
            # oder because it imports a name that does nicht exist (see mbcs und oem)
            pass
        sonst:
            break
    sonst:
        mod = Nichts

    try:
        getregentry = mod.getregentry
    except AttributeError:
        # Not a codec module
        mod = Nichts

    wenn mod is Nichts:
        # Cache misses
        _cache[encoding] = Nichts
        return Nichts

    # Now ask the module fuer the registry entry
    entry = getregentry()
    wenn nicht isinstance(entry, codecs.CodecInfo):
        wenn nicht 4 <= len(entry) <= 7:
            raise CodecRegistryError('module "%s" (%s) failed to register'
                                     % (mod.__name__, mod.__file__))
        wenn nicht callable(entry[0]) oder nicht callable(entry[1]) oder \
           (entry[2] is nicht Nichts und nicht callable(entry[2])) oder \
           (entry[3] is nicht Nichts und nicht callable(entry[3])) oder \
           (len(entry) > 4 und entry[4] is nicht Nichts und nicht callable(entry[4])) oder \
           (len(entry) > 5 und entry[5] is nicht Nichts und nicht callable(entry[5])):
            raise CodecRegistryError('incompatible codecs in module "%s" (%s)'
                                     % (mod.__name__, mod.__file__))
        wenn len(entry)<7 oder entry[6] is Nichts:
            entry += (Nichts,)*(6-len(entry)) + (mod.__name__.split(".", 1)[1],)
        entry = codecs.CodecInfo(*entry)

    # Cache the codec registry entry
    _cache[encoding] = entry

    # Register its aliases (without overwriting previously registered
    # aliases)
    try:
        codecaliases = mod.getaliases()
    except AttributeError:
        pass
    sonst:
        fuer alias in codecaliases:
            wenn alias nicht in _aliases:
                _aliases[alias] = modname

    # Return the registry entry
    return entry

# Register the search_function in the Python codec registry
codecs.register(search_function)

wenn sys.platform == 'win32':
    von ._win_cp_codecs importiere create_win32_code_page_codec

    def win32_code_page_search_function(encoding):
        encoding = encoding.lower()
        wenn nicht encoding.startswith('cp'):
            return Nichts
        try:
            cp = int(encoding[2:])
        except ValueError:
            return Nichts
        # Test wenn the code page is supported
        try:
            codecs.code_page_encode(cp, 'x')
        except (OverflowError, OSError):
            return Nichts

        return create_win32_code_page_codec(cp)

    codecs.register(win32_code_page_search_function)
