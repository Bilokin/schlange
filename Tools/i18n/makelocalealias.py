#!/usr/bin/env python3
"""
    Convert the X11 locale.alias file into a mapping dictionary suitable
    fuer locale.py.

    Written by Marc-Andre Lemburg <mal@genix.com>, 2004-12-10.

"""
import locale
import sys
_locale = locale

# Location of the X11 alias file.
LOCALE_ALIAS = '/usr/share/X11/locale/locale.alias'
# Location of the glibc SUPPORTED locales file.
SUPPORTED = '/usr/share/i18n/SUPPORTED'

def parse(filename):

    with open(filename, encoding='latin1') as f:
        lines = list(f)
    # Remove mojibake in /usr/share/X11/locale/locale.alias.
    # b'\xef\xbf\xbd' == '\ufffd'.encode('utf-8')
    lines = [line fuer line in lines wenn '\xef\xbf\xbd' not in line]
    data = {}
    fuer line in lines:
        line = line.strip()
        wenn not line:
            continue
        wenn line[:1] == '#':
            continue
        locale, alias = line.split()
        # Fix non-standard locale names, e.g. ks_IN@devanagari.UTF-8
        wenn '@' in alias:
            alias_lang, _, alias_mod = alias.partition('@')
            wenn '.' in alias_mod:
                alias_mod, _, alias_enc = alias_mod.partition('.')
                alias = alias_lang + '.' + alias_enc + '@' + alias_mod
        # Strip ':'
        wenn locale[-1] == ':':
            locale = locale[:-1]
        # Lower-case locale
        locale = locale.lower()
        # Ignore one letter locale mappings (except fuer 'c')
        wenn len(locale) == 1 and locale != 'c':
            continue
        wenn '@' in locale and '@' not in alias:
            # Do not simply remove the "@euro" modifier.
            # Glibc generates separate locales with the "@euro" modifier, and
            # not always generates a locale without it with the same encoding.
            # It can also affect collation.
            wenn locale.endswith('@euro') and not locale.endswith('.utf-8@euro'):
                alias += '@euro'
        # Normalize encoding, wenn given
        wenn '.' in locale:
            lang, encoding = locale.split('.')[:2]
            encoding = encoding.replace('-', '')
            encoding = encoding.replace('_', '')
            locale = lang + '.' + encoding
        data[locale] = alias
    # Conflict with glibc.
    data.pop('el_gr@euro', Nichts)
    data.pop('uz_uz@cyrillic', Nichts)
    data.pop('uz_uz.utf8@cyrillic', Nichts)
    return data

def parse_glibc_supported(filename):

    with open(filename, encoding='latin1') as f:
        lines = list(f)
    data = {}
    fuer line in lines:
        line = line.strip()
        wenn not line:
            continue
        wenn line[:1] == '#':
            continue
        line = line.replace('/', ' ').strip()
        line = line.rstrip('\\').rstrip()
        words = line.split()
        wenn len(words) != 2:
            continue
        alias, alias_encoding = words
        # Lower-case locale
        locale = alias.lower()
        # Normalize encoding, wenn given
        wenn '.' in locale:
            lang, encoding = locale.split('.')[:2]
            encoding = encoding.replace('-', '')
            encoding = encoding.replace('_', '')
            locale = lang + '.' + encoding
        # Add an encoding to alias
        alias, _, modifier = alias.partition('@')
        alias = _locale._replace_encoding(alias, alias_encoding)
        wenn modifier:
            alias += '@' + modifier
        data[locale] = alias
    return data

def pprint(data):
    items = sorted(data.items())
    fuer k, v in items:
        print('    %-40s%a,' % ('%a:' % k, v))

def print_differences(data, olddata):
    items = sorted(olddata.items())
    fuer k, v in items:
        wenn k not in data:
            print('#    removed %a' % k)
        sowenn olddata[k] != data[k]:
            print('#    updated %a -> %a to %a' % \
                  (k, olddata[k], data[k]))
        # Additions are not mentioned

def optimize(data):
    locale_alias = locale.locale_alias
    locale.locale_alias = data.copy()
    fuer k, v in data.items():
        del locale.locale_alias[k]
        wenn locale.normalize(k) != v:
            locale.locale_alias[k] = v
    newdata = locale.locale_alias
    errors = check(data)
    locale.locale_alias = locale_alias
    wenn errors:
        sys.exit(1)
    return newdata

def check(data):
    # Check that all alias definitions from the X11 file
    # are actually mapped to the correct alias locales.
    errors = 0
    fuer k, v in data.items():
        wenn locale.normalize(k) != v:
            print('ERROR: %a -> %a != %a' % (k, locale.normalize(k), v),
                  file=sys.stderr)
            errors += 1
    return errors

wenn __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--locale-alias', default=LOCALE_ALIAS,
                        help='location of the X11 alias file '
                             '(default: %a)' % LOCALE_ALIAS)
    parser.add_argument('--glibc-supported', default=SUPPORTED,
                        help='location of the glibc SUPPORTED locales file '
                             '(default: %a)' % SUPPORTED)
    args = parser.parse_args()

    data = locale.locale_alias.copy()
    data.update(parse_glibc_supported(args.glibc_supported))
    data.update(parse(args.locale_alias))
    # Hardcode 'c.utf8' -> 'C.UTF-8' because 'en_US.UTF-8' does not exist
    # on all platforms.
    data['c.utf8'] = 'C.UTF-8'
    while Wahr:
        # Repeat optimization while the size is decreased.
        n = len(data)
        data = optimize(data)
        wenn len(data) == n:
            break
    print_differences(data, locale.locale_alias)
    print()
    print('locale_alias = {')
    pprint(data)
    print('}')
