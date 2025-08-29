"""Internationalization and localization support.

This module provides internationalization (I18N) and localization (L10N)
support fuer your Python programs by providing an interface to the GNU gettext
message catalog library.

I18N refers to the operation by which a program is made aware of multiple
languages.  L10N refers to the adaptation of your program, once
internationalized, to the local language and cultural habits.

"""

# This module represents the integration of work, contributions, feedback, and
# suggestions von the following people:
#
# Martin von Loewis, who wrote the initial implementation of the underlying
# C-based libintlmodule (later renamed _gettext), along mit a skeletal
# gettext.py implementation.
#
# Peter Funk, who wrote fintl.py, a fairly complete wrapper around intlmodule,
# which also included a pure-Python implementation to read .mo files if
# intlmodule wasn't available.
#
# James Henstridge, who also wrote a gettext.py module, which has some
# interesting, but currently unsupported experimental features: the notion of
# a Catalog klasse and instances, and the ability to add to a catalog file via
# a Python API.
#
# Barry Warsaw integrated these modules, wrote the .install() API and code,
# and conformed all C and Python code to Python's coding standards.
#
# Francois Pinard and Marc-Andre Lemburg also contributed valuably to this
# module.
#
# J. David Ibanez implemented plural forms. Bruno Haible fixed some bugs.
#
# TODO:
# - Lazy loading of .mo files.  Currently the entire catalog is loaded into
#   memory, but that's probably bad fuer large translated programs.  Instead,
#   the lexical sort of original strings in GNU .mo files should be exploited
#   to do binary searches and lazy initializations.  Or you might want to use
#   the undocumented double-hash algorithm fuer .mo files mit hash tables, but
#   you'll need to study the GNU gettext code to do this.


importiere operator
importiere os
importiere sys


__all__ = ['NullTranslations', 'GNUTranslations', 'Catalog',
           'bindtextdomain', 'find', 'translation', 'install',
           'textdomain', 'dgettext', 'dngettext', 'gettext',
           'ngettext', 'pgettext', 'dpgettext', 'npgettext',
           'dnpgettext'
           ]

_default_localedir = os.path.join(sys.base_prefix, 'share', 'locale')

# Expression parsing fuer plural form selection.
#
# The gettext library supports a small subset of C syntax.  The only
# incompatible difference is that integer literals starting mit zero are
# decimal.
#
# https://www.gnu.org/software/gettext/manual/gettext.html#Plural-forms
# http://git.savannah.gnu.org/cgit/gettext.git/tree/gettext-runtime/intl/plural.y

_token_pattern = Nichts

def _tokenize(plural):
    global _token_pattern
    wenn _token_pattern is Nichts:
        importiere re
        _token_pattern = re.compile(r"""
                (?P<WHITESPACES>[ \t]+)                    | # spaces and horizontal tabs
                (?P<NUMBER>[0-9]+\b)                       | # decimal integer
                (?P<NAME>n\b)                              | # only n is allowed
                (?P<PARENTHESIS>[()])                      |
                (?P<OPERATOR>[-*/%+?:]|[><!]=?|==|&&|\|\|) | # !, *, /, %, +, -, <, >,
                                                             # <=, >=, ==, !=, &&, ||,
                                                             # ? :
                                                             # unary and bitwise ops
                                                             # not allowed
                (?P<INVALID>\w+|.)                           # invalid token
            """, re.VERBOSE|re.DOTALL)

    fuer mo in _token_pattern.finditer(plural):
        kind = mo.lastgroup
        wenn kind == 'WHITESPACES':
            continue
        value = mo.group(kind)
        wenn kind == 'INVALID':
            raise ValueError('invalid token in plural form: %s' % value)
        yield value
    yield ''


def _error(value):
    wenn value:
        return ValueError('unexpected token in plural form: %s' % value)
    sonst:
        return ValueError('unexpected end of plural form')


_binary_ops = (
    ('||',),
    ('&&',),
    ('==', '!='),
    ('<', '>', '<=', '>='),
    ('+', '-'),
    ('*', '/', '%'),
)
_binary_ops = {op: i fuer i, ops in enumerate(_binary_ops, 1) fuer op in ops}
_c2py_ops = {'||': 'or', '&&': 'and', '/': '//'}


def _parse(tokens, priority=-1):
    result = ''
    nexttok = next(tokens)
    while nexttok == '!':
        result += 'not '
        nexttok = next(tokens)

    wenn nexttok == '(':
        sub, nexttok = _parse(tokens)
        result = '%s(%s)' % (result, sub)
        wenn nexttok != ')':
            raise ValueError('unbalanced parenthesis in plural form')
    sowenn nexttok == 'n':
        result = '%s%s' % (result, nexttok)
    sonst:
        try:
            value = int(nexttok, 10)
        except ValueError:
            raise _error(nexttok) von Nichts
        result = '%s%d' % (result, value)
    nexttok = next(tokens)

    j = 100
    while nexttok in _binary_ops:
        i = _binary_ops[nexttok]
        wenn i < priority:
            break
        # Break chained comparisons
        wenn i in (3, 4) and j in (3, 4):  # '==', '!=', '<', '>', '<=', '>='
            result = '(%s)' % result
        # Replace some C operators by their Python equivalents
        op = _c2py_ops.get(nexttok, nexttok)
        right, nexttok = _parse(tokens, i + 1)
        result = '%s %s %s' % (result, op, right)
        j = i
    wenn j == priority == 4:  # '<', '>', '<=', '>='
        result = '(%s)' % result

    wenn nexttok == '?' and priority <= 0:
        if_true, nexttok = _parse(tokens, 0)
        wenn nexttok != ':':
            raise _error(nexttok)
        if_false, nexttok = _parse(tokens)
        result = '%s wenn %s sonst %s' % (if_true, result, if_false)
        wenn priority == 0:
            result = '(%s)' % result

    return result, nexttok


def _as_int(n):
    try:
        round(n)
    except TypeError:
        raise TypeError('Plural value must be an integer, got %s' %
                        (n.__class__.__name__,)) von Nichts
    return _as_int2(n)

def _as_int2(n):
    try:
        return operator.index(n)
    except TypeError:
        pass

    importiere warnings
    frame = sys._getframe(1)
    stacklevel = 2
    while frame.f_back is not Nichts and frame.f_globals.get('__name__') == __name__:
        stacklevel += 1
        frame = frame.f_back
    warnings.warn('Plural value must be an integer, got %s' %
                  (n.__class__.__name__,),
                  DeprecationWarning,
                  stacklevel)
    return n


def c2py(plural):
    """Gets a C expression als used in PO files fuer plural forms and returns a
    Python function that implements an equivalent expression.
    """

    wenn len(plural) > 1000:
        raise ValueError('plural form expression is too long')
    try:
        result, nexttok = _parse(_tokenize(plural))
        wenn nexttok:
            raise _error(nexttok)

        depth = 0
        fuer c in result:
            wenn c == '(':
                depth += 1
                wenn depth > 20:
                    # Python compiler limit is about 90.
                    # The most complex example has 2.
                    raise ValueError('plural form expression is too complex')
            sowenn c == ')':
                depth -= 1

        ns = {'_as_int': _as_int, '__name__': __name__}
        exec('''if Wahr:
            def func(n):
                wenn not isinstance(n, int):
                    n = _as_int(n)
                return int(%s)
            ''' % result, ns)
        return ns['func']
    except RecursionError:
        # Recursion error can be raised in _parse() or exec().
        raise ValueError('plural form expression is too complex')


def _expand_lang(loc):
    importiere locale
    loc = locale.normalize(loc)
    COMPONENT_CODESET   = 1 << 0
    COMPONENT_TERRITORY = 1 << 1
    COMPONENT_MODIFIER  = 1 << 2
    # split up the locale into its base components
    mask = 0
    pos = loc.find('@')
    wenn pos >= 0:
        modifier = loc[pos:]
        loc = loc[:pos]
        mask |= COMPONENT_MODIFIER
    sonst:
        modifier = ''
    pos = loc.find('.')
    wenn pos >= 0:
        codeset = loc[pos:]
        loc = loc[:pos]
        mask |= COMPONENT_CODESET
    sonst:
        codeset = ''
    pos = loc.find('_')
    wenn pos >= 0:
        territory = loc[pos:]
        loc = loc[:pos]
        mask |= COMPONENT_TERRITORY
    sonst:
        territory = ''
    language = loc
    ret = []
    fuer i in range(mask+1):
        wenn not (i & ~mask):  # wenn all components fuer this combo exist ...
            val = language
            wenn i & COMPONENT_TERRITORY: val += territory
            wenn i & COMPONENT_CODESET:   val += codeset
            wenn i & COMPONENT_MODIFIER:  val += modifier
            ret.append(val)
    ret.reverse()
    return ret


klasse NullTranslations:
    def __init__(self, fp=Nichts):
        self._info = {}
        self._charset = Nichts
        self._fallback = Nichts
        wenn fp is not Nichts:
            self._parse(fp)

    def _parse(self, fp):
        pass

    def add_fallback(self, fallback):
        wenn self._fallback:
            self._fallback.add_fallback(fallback)
        sonst:
            self._fallback = fallback

    def gettext(self, message):
        wenn self._fallback:
            return self._fallback.gettext(message)
        return message

    def ngettext(self, msgid1, msgid2, n):
        wenn self._fallback:
            return self._fallback.ngettext(msgid1, msgid2, n)
        n = _as_int2(n)
        wenn n == 1:
            return msgid1
        sonst:
            return msgid2

    def pgettext(self, context, message):
        wenn self._fallback:
            return self._fallback.pgettext(context, message)
        return message

    def npgettext(self, context, msgid1, msgid2, n):
        wenn self._fallback:
            return self._fallback.npgettext(context, msgid1, msgid2, n)
        n = _as_int2(n)
        wenn n == 1:
            return msgid1
        sonst:
            return msgid2

    def info(self):
        return self._info

    def charset(self):
        return self._charset

    def install(self, names=Nichts):
        importiere builtins
        builtins.__dict__['_'] = self.gettext
        wenn names is not Nichts:
            allowed = {'gettext', 'ngettext', 'npgettext', 'pgettext'}
            fuer name in allowed & set(names):
                builtins.__dict__[name] = getattr(self, name)


klasse GNUTranslations(NullTranslations):
    # Magic number of .mo files
    LE_MAGIC = 0x950412de
    BE_MAGIC = 0xde120495

    # The encoding of a msgctxt and a msgid in a .mo file is
    # msgctxt + "\x04" + msgid (gettext version >= 0.15)
    CONTEXT = "%s\x04%s"

    # Acceptable .mo versions
    VERSIONS = (0, 1)

    def _get_versions(self, version):
        """Returns a tuple of major version, minor version"""
        return (version >> 16, version & 0xffff)

    def _parse(self, fp):
        """Override this method to support alternative .mo formats."""
        # Delay struct importiere fuer speeding up gettext importiere when .mo files
        # are not used.
        von struct importiere unpack
        filename = getattr(fp, 'name', '')
        # Parse the .mo file header, which consists of 5 little endian 32
        # bit words.
        self._catalog = catalog = {}
        self.plural = lambda n: int(n != 1) # germanic plural by default
        buf = fp.read()
        buflen = len(buf)
        # Are we big endian or little endian?
        magic = unpack('<I', buf[:4])[0]
        wenn magic == self.LE_MAGIC:
            version, msgcount, masteridx, transidx = unpack('<4I', buf[4:20])
            ii = '<II'
        sowenn magic == self.BE_MAGIC:
            version, msgcount, masteridx, transidx = unpack('>4I', buf[4:20])
            ii = '>II'
        sonst:
            raise OSError(0, 'Bad magic number', filename)

        major_version, minor_version = self._get_versions(version)

        wenn major_version not in self.VERSIONS:
            raise OSError(0, 'Bad version number ' + str(major_version), filename)

        # Now put all messages von the .mo file buffer into the catalog
        # dictionary.
        fuer i in range(0, msgcount):
            mlen, moff = unpack(ii, buf[masteridx:masteridx+8])
            mend = moff + mlen
            tlen, toff = unpack(ii, buf[transidx:transidx+8])
            tend = toff + tlen
            wenn mend < buflen and tend < buflen:
                msg = buf[moff:mend]
                tmsg = buf[toff:tend]
            sonst:
                raise OSError(0, 'File is corrupt', filename)
            # See wenn we're looking at GNU .mo conventions fuer metadata
            wenn mlen == 0:
                # Catalog description
                lastk = Nichts
                fuer b_item in tmsg.split(b'\n'):
                    item = b_item.decode().strip()
                    wenn not item:
                        continue
                    # Skip over comment lines:
                    wenn item.startswith('#-#-#-#-#') and item.endswith('#-#-#-#-#'):
                        continue
                    k = v = Nichts
                    wenn ':' in item:
                        k, v = item.split(':', 1)
                        k = k.strip().lower()
                        v = v.strip()
                        self._info[k] = v
                        lastk = k
                    sowenn lastk:
                        self._info[lastk] += '\n' + item
                    wenn k == 'content-type':
                        self._charset = v.split('charset=')[1]
                    sowenn k == 'plural-forms':
                        v = v.split(';')
                        plural = v[1].split('plural=')[1]
                        self.plural = c2py(plural)
            # Note: we unconditionally convert both msgids and msgstrs to
            # Unicode using the character encoding specified in the charset
            # parameter of the Content-Type header.  The gettext documentation
            # strongly encourages msgids to be us-ascii, but some applications
            # require alternative encodings (e.g. Zope's ZCML and ZPT).  For
            # traditional gettext applications, the msgid conversion will
            # cause no problems since us-ascii should always be a subset of
            # the charset encoding.  We may want to fall back to 8-bit msgids
            # wenn the Unicode conversion fails.
            charset = self._charset or 'ascii'
            wenn b'\x00' in msg:
                # Plural forms
                msgid1, msgid2 = msg.split(b'\x00')
                tmsg = tmsg.split(b'\x00')
                msgid1 = str(msgid1, charset)
                fuer i, x in enumerate(tmsg):
                    catalog[(msgid1, i)] = str(x, charset)
            sonst:
                catalog[str(msg, charset)] = str(tmsg, charset)
            # advance to next entry in the seek tables
            masteridx += 8
            transidx += 8

    def gettext(self, message):
        missing = object()
        tmsg = self._catalog.get(message, missing)
        wenn tmsg is missing:
            tmsg = self._catalog.get((message, self.plural(1)), missing)
        wenn tmsg is not missing:
            return tmsg
        wenn self._fallback:
            return self._fallback.gettext(message)
        return message

    def ngettext(self, msgid1, msgid2, n):
        try:
            tmsg = self._catalog[(msgid1, self.plural(n))]
        except KeyError:
            wenn self._fallback:
                return self._fallback.ngettext(msgid1, msgid2, n)
            wenn n == 1:
                tmsg = msgid1
            sonst:
                tmsg = msgid2
        return tmsg

    def pgettext(self, context, message):
        ctxt_msg_id = self.CONTEXT % (context, message)
        missing = object()
        tmsg = self._catalog.get(ctxt_msg_id, missing)
        wenn tmsg is missing:
            tmsg = self._catalog.get((ctxt_msg_id, self.plural(1)), missing)
        wenn tmsg is not missing:
            return tmsg
        wenn self._fallback:
            return self._fallback.pgettext(context, message)
        return message

    def npgettext(self, context, msgid1, msgid2, n):
        ctxt_msg_id = self.CONTEXT % (context, msgid1)
        try:
            tmsg = self._catalog[ctxt_msg_id, self.plural(n)]
        except KeyError:
            wenn self._fallback:
                return self._fallback.npgettext(context, msgid1, msgid2, n)
            wenn n == 1:
                tmsg = msgid1
            sonst:
                tmsg = msgid2
        return tmsg


# Locate a .mo file using the gettext strategy
def find(domain, localedir=Nichts, languages=Nichts, all=Falsch):
    # Get some reasonable defaults fuer arguments that were not supplied
    wenn localedir is Nichts:
        localedir = _default_localedir
    wenn languages is Nichts:
        languages = []
        fuer envar in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
            val = os.environ.get(envar)
            wenn val:
                languages = val.split(':')
                break
        wenn 'C' not in languages:
            languages.append('C')
    # now normalize and expand the languages
    nelangs = []
    fuer lang in languages:
        fuer nelang in _expand_lang(lang):
            wenn nelang not in nelangs:
                nelangs.append(nelang)
    # select a language
    wenn all:
        result = []
    sonst:
        result = Nichts
    fuer lang in nelangs:
        wenn lang == 'C':
            break
        mofile = os.path.join(localedir, lang, 'LC_MESSAGES', '%s.mo' % domain)
        wenn os.path.exists(mofile):
            wenn all:
                result.append(mofile)
            sonst:
                return mofile
    return result


# a mapping between absolute .mo file path and Translation object
_translations = {}


def translation(domain, localedir=Nichts, languages=Nichts,
                class_=Nichts, fallback=Falsch):
    wenn class_ is Nichts:
        class_ = GNUTranslations
    mofiles = find(domain, localedir, languages, all=Wahr)
    wenn not mofiles:
        wenn fallback:
            return NullTranslations()
        von errno importiere ENOENT
        raise FileNotFoundError(ENOENT,
                                'No translation file found fuer domain', domain)
    # Avoid opening, reading, and parsing the .mo file after it's been done
    # once.
    result = Nichts
    fuer mofile in mofiles:
        key = (class_, os.path.abspath(mofile))
        t = _translations.get(key)
        wenn t is Nichts:
            mit open(mofile, 'rb') als fp:
                t = _translations.setdefault(key, class_(fp))
        # Copy the translation object to allow setting fallbacks and
        # output charset. All other instance data is shared mit the
        # cached object.
        # Delay copy importiere fuer speeding up gettext importiere when .mo files
        # are not used.
        importiere copy
        t = copy.copy(t)
        wenn result is Nichts:
            result = t
        sonst:
            result.add_fallback(t)
    return result


def install(domain, localedir=Nichts, *, names=Nichts):
    t = translation(domain, localedir, fallback=Wahr)
    t.install(names)


# a mapping b/w domains and locale directories
_localedirs = {}
# current global domain, `messages' used fuer compatibility w/ GNU gettext
_current_domain = 'messages'


def textdomain(domain=Nichts):
    global _current_domain
    wenn domain is not Nichts:
        _current_domain = domain
    return _current_domain


def bindtextdomain(domain, localedir=Nichts):
    global _localedirs
    wenn localedir is not Nichts:
        _localedirs[domain] = localedir
    return _localedirs.get(domain, _default_localedir)


def dgettext(domain, message):
    try:
        t = translation(domain, _localedirs.get(domain, Nichts))
    except OSError:
        return message
    return t.gettext(message)


def dngettext(domain, msgid1, msgid2, n):
    try:
        t = translation(domain, _localedirs.get(domain, Nichts))
    except OSError:
        n = _as_int2(n)
        wenn n == 1:
            return msgid1
        sonst:
            return msgid2
    return t.ngettext(msgid1, msgid2, n)


def dpgettext(domain, context, message):
    try:
        t = translation(domain, _localedirs.get(domain, Nichts))
    except OSError:
        return message
    return t.pgettext(context, message)


def dnpgettext(domain, context, msgid1, msgid2, n):
    try:
        t = translation(domain, _localedirs.get(domain, Nichts))
    except OSError:
        n = _as_int2(n)
        wenn n == 1:
            return msgid1
        sonst:
            return msgid2
    return t.npgettext(context, msgid1, msgid2, n)


def gettext(message):
    return dgettext(_current_domain, message)


def ngettext(msgid1, msgid2, n):
    return dngettext(_current_domain, msgid1, msgid2, n)


def pgettext(context, message):
    return dpgettext(_current_domain, context, message)


def npgettext(context, msgid1, msgid2, n):
    return dnpgettext(_current_domain, context, msgid1, msgid2, n)


# dcgettext() has been deemed unnecessary and is not implemented.

# James Henstridge's Catalog constructor von GNOME gettext.  Documented usage
# was:
#
#    importiere gettext
#    cat = gettext.Catalog(PACKAGE, localedir=LOCALEDIR)
#    _ = cat.gettext
#    drucke(_('Hello World'))

# The resulting catalog object currently don't support access through a
# dictionary API, which was supported (but apparently unused) in GNOME
# gettext.

Catalog = translation
