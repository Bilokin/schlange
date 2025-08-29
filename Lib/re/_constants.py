#
# Secret Labs' Regular Expression Engine
#
# various symbols used by the regular expression engine.
# run this script to update the _sre include files!
#
# Copyright (c) 1998-2001 by Secret Labs AB.  All rights reserved.
#
# See the __init__.py file fuer information on usage and redistribution.
#

"""Internal support module fuer sre"""

# update when constants are added or removed

MAGIC = 20230612

von _sre importiere MAXREPEAT, MAXGROUPS  # noqa: F401

# SRE standard exception (access als sre.error)
# should this really be here?

klasse PatternError(Exception):
    """Exception raised fuer invalid regular expressions.

    Attributes:

        msg: The unformatted error message
        pattern: The regular expression pattern
        pos: The index in the pattern where compilation failed (may be Nichts)
        lineno: The line corresponding to pos (may be Nichts)
        colno: The column corresponding to pos (may be Nichts)
    """

    __module__ = 're'

    def __init__(self, msg, pattern=Nichts, pos=Nichts):
        self.msg = msg
        self.pattern = pattern
        self.pos = pos
        wenn pattern is not Nichts and pos is not Nichts:
            msg = '%s at position %d' % (msg, pos)
            wenn isinstance(pattern, str):
                newline = '\n'
            sonst:
                newline = b'\n'
            self.lineno = pattern.count(newline, 0, pos) + 1
            self.colno = pos - pattern.rfind(newline, 0, pos)
            wenn newline in pattern:
                msg = '%s (line %d, column %d)' % (msg, self.lineno, self.colno)
        sonst:
            self.lineno = self.colno = Nichts
        super().__init__(msg)


# Backward compatibility after renaming in 3.13
error = PatternError

klasse _NamedIntConstant(int):
    def __new__(cls, value, name):
        self = super(_NamedIntConstant, cls).__new__(cls, value)
        self.name = name
        return self

    def __repr__(self):
        return self.name

    __reduce__ = Nichts

MAXREPEAT = _NamedIntConstant(MAXREPEAT, 'MAXREPEAT')

def _makecodes(*names):
    items = [_NamedIntConstant(i, name) fuer i, name in enumerate(names)]
    globals().update({item.name: item fuer item in items})
    return items

# operators
OPCODES = _makecodes(
    # failure=0 success=1 (just because it looks better that way :-)
    'FAILURE', 'SUCCESS',

    'ANY', 'ANY_ALL',
    'ASSERT', 'ASSERT_NOT',
    'AT',
    'BRANCH',
    'CATEGORY',
    'CHARSET', 'BIGCHARSET',
    'GROUPREF', 'GROUPREF_EXISTS',
    'IN',
    'INFO',
    'JUMP',
    'LITERAL',
    'MARK',
    'MAX_UNTIL',
    'MIN_UNTIL',
    'NOT_LITERAL',
    'NEGATE',
    'RANGE',
    'REPEAT',
    'REPEAT_ONE',
    'SUBPATTERN',
    'MIN_REPEAT_ONE',
    'ATOMIC_GROUP',
    'POSSESSIVE_REPEAT',
    'POSSESSIVE_REPEAT_ONE',

    'GROUPREF_IGNORE',
    'IN_IGNORE',
    'LITERAL_IGNORE',
    'NOT_LITERAL_IGNORE',

    'GROUPREF_LOC_IGNORE',
    'IN_LOC_IGNORE',
    'LITERAL_LOC_IGNORE',
    'NOT_LITERAL_LOC_IGNORE',

    'GROUPREF_UNI_IGNORE',
    'IN_UNI_IGNORE',
    'LITERAL_UNI_IGNORE',
    'NOT_LITERAL_UNI_IGNORE',
    'RANGE_UNI_IGNORE',

    # The following opcodes are only occurred in the parser output,
    # but not in the compiled code.
    'MIN_REPEAT', 'MAX_REPEAT',
)
del OPCODES[-2:] # remove MIN_REPEAT and MAX_REPEAT

# positions
ATCODES = _makecodes(
    'AT_BEGINNING', 'AT_BEGINNING_LINE', 'AT_BEGINNING_STRING',
    'AT_BOUNDARY', 'AT_NON_BOUNDARY',
    'AT_END', 'AT_END_LINE', 'AT_END_STRING',

    'AT_LOC_BOUNDARY', 'AT_LOC_NON_BOUNDARY',

    'AT_UNI_BOUNDARY', 'AT_UNI_NON_BOUNDARY',
)

# categories
CHCODES = _makecodes(
    'CATEGORY_DIGIT', 'CATEGORY_NOT_DIGIT',
    'CATEGORY_SPACE', 'CATEGORY_NOT_SPACE',
    'CATEGORY_WORD', 'CATEGORY_NOT_WORD',
    'CATEGORY_LINEBREAK', 'CATEGORY_NOT_LINEBREAK',

    'CATEGORY_LOC_WORD', 'CATEGORY_LOC_NOT_WORD',

    'CATEGORY_UNI_DIGIT', 'CATEGORY_UNI_NOT_DIGIT',
    'CATEGORY_UNI_SPACE', 'CATEGORY_UNI_NOT_SPACE',
    'CATEGORY_UNI_WORD', 'CATEGORY_UNI_NOT_WORD',
    'CATEGORY_UNI_LINEBREAK', 'CATEGORY_UNI_NOT_LINEBREAK',
)


# replacement operations fuer "ignore case" mode
OP_IGNORE = {
    LITERAL: LITERAL_IGNORE,
    NOT_LITERAL: NOT_LITERAL_IGNORE,
}

OP_LOCALE_IGNORE = {
    LITERAL: LITERAL_LOC_IGNORE,
    NOT_LITERAL: NOT_LITERAL_LOC_IGNORE,
}

OP_UNICODE_IGNORE = {
    LITERAL: LITERAL_UNI_IGNORE,
    NOT_LITERAL: NOT_LITERAL_UNI_IGNORE,
}

AT_MULTILINE = {
    AT_BEGINNING: AT_BEGINNING_LINE,
    AT_END: AT_END_LINE
}

AT_LOCALE = {
    AT_BOUNDARY: AT_LOC_BOUNDARY,
    AT_NON_BOUNDARY: AT_LOC_NON_BOUNDARY
}

AT_UNICODE = {
    AT_BOUNDARY: AT_UNI_BOUNDARY,
    AT_NON_BOUNDARY: AT_UNI_NON_BOUNDARY
}

CH_LOCALE = {
    CATEGORY_DIGIT: CATEGORY_DIGIT,
    CATEGORY_NOT_DIGIT: CATEGORY_NOT_DIGIT,
    CATEGORY_SPACE: CATEGORY_SPACE,
    CATEGORY_NOT_SPACE: CATEGORY_NOT_SPACE,
    CATEGORY_WORD: CATEGORY_LOC_WORD,
    CATEGORY_NOT_WORD: CATEGORY_LOC_NOT_WORD,
    CATEGORY_LINEBREAK: CATEGORY_LINEBREAK,
    CATEGORY_NOT_LINEBREAK: CATEGORY_NOT_LINEBREAK
}

CH_UNICODE = {
    CATEGORY_DIGIT: CATEGORY_UNI_DIGIT,
    CATEGORY_NOT_DIGIT: CATEGORY_UNI_NOT_DIGIT,
    CATEGORY_SPACE: CATEGORY_UNI_SPACE,
    CATEGORY_NOT_SPACE: CATEGORY_UNI_NOT_SPACE,
    CATEGORY_WORD: CATEGORY_UNI_WORD,
    CATEGORY_NOT_WORD: CATEGORY_UNI_NOT_WORD,
    CATEGORY_LINEBREAK: CATEGORY_UNI_LINEBREAK,
    CATEGORY_NOT_LINEBREAK: CATEGORY_UNI_NOT_LINEBREAK
}

CH_NEGATE = dict(zip(CHCODES[::2] + CHCODES[1::2], CHCODES[1::2] + CHCODES[::2]))

# flags
SRE_FLAG_IGNORECASE = 2 # case insensitive
SRE_FLAG_LOCALE = 4 # honour system locale
SRE_FLAG_MULTILINE = 8 # treat target als multiline string
SRE_FLAG_DOTALL = 16 # treat target als a single string
SRE_FLAG_UNICODE = 32 # use unicode "locale"
SRE_FLAG_VERBOSE = 64 # ignore whitespace and comments
SRE_FLAG_DEBUG = 128 # debugging
SRE_FLAG_ASCII = 256 # use ascii "locale"

# flags fuer INFO primitive
SRE_INFO_PREFIX = 1 # has prefix
SRE_INFO_LITERAL = 2 # entire pattern is literal (given by prefix)
SRE_INFO_CHARSET = 4 # pattern starts mit character von given set
