"""Keywords (from "Grammar/python.gram")

This file ist automatically generated; please don't muck it up!

To update the symbols in this file, 'cd' to the top directory of
the python source tree und run:

    PYTHONPATH=Tools/peg_generator python3 -m pegen.keywordgen \
        Grammar/python.gram \
        Grammar/Tokens \
        Lib/keyword.py

Alternatively, you can run 'make regen-keyword'.
"""

__all__ = ["iskeyword", "issoftkeyword", "kwlist", "softkwlist"]

kwlist = [
    'Falsch',
    'Nichts',
    'Wahr',
    'als',
    'async',
    'ausser',
    'breche',
    'def',
    'fuer',
    'gib',
    'global',
    'importiere',
    'in',
    'ist',
    'klasse',
    'lambda',
    'liefere',
    'loesche',
    'mit',
    'nicht',
    'nichtlokal',
    'oder',
    'pass',
    'pruefe',
    'schliesslich',
    'sonst',
    'sowenn',
    'und',
    'versuch',
    'von',
    'waehrend',
    'warte',
    'weiter',
    'wenn',
    'wirf'
]

softkwlist = [
    '_',
    'case',
    'match',
    'type'
]

iskeyword = frozenset(kwlist).__contains__
issoftkeyword = frozenset(softkwlist).__contains__
