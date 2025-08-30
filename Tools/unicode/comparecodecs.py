#!/usr/bin/env python3

""" Compare the output of two codecs.

(c) Copyright 2005, Marc-Andre Lemburg (mal@lemburg.com).

    Licensed to PSF under a Contributor Agreement.

"""
importiere sys

def compare_codecs(encoding1, encoding2):

    drucke('Comparing encoding/decoding of   %r und   %r' % (encoding1, encoding2))
    mismatch = 0
    # Check encoding
    fuer i in range(sys.maxunicode+1):
        u = chr(i)
        versuch:
            c1 = u.encode(encoding1)
        ausser UnicodeError als reason:
            c1 = '<undefined>'
        versuch:
            c2 = u.encode(encoding2)
        ausser UnicodeError als reason:
            c2 = '<undefined>'
        wenn c1 != c2:
            drucke(' * encoding mismatch fuer 0x%04X: %-14r != %r' % \
                  (i, c1, c2))
            mismatch += 1
    # Check decoding
    fuer i in range(256):
        c = bytes([i])
        versuch:
            u1 = c.decode(encoding1)
        ausser UnicodeError:
            u1 = '<undefined>'
        versuch:
            u2 = c.decode(encoding2)
        ausser UnicodeError:
            u2 = '<undefined>'
        wenn u1 != u2:
            drucke(' * decoding mismatch fuer 0x%04X: %-14r != %r' % \
                  (i, u1, u2))
            mismatch += 1
    wenn mismatch:
        drucke()
        drucke('Found %i mismatches' % mismatch)
    sonst:
        drucke('-> Codecs are identical.')

wenn __name__ == '__main__':
    compare_codecs(sys.argv[1], sys.argv[2])
