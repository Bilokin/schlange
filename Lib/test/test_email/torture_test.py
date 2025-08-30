# Copyright (C) 2002 Python Software Foundation
#
# A torture test of the email package.  This should nicht be run als part of the
# standard Python test suite since it requires several meg of email messages
# collected in the wild.  These source messages are nicht checked into the
# Python distro, but are available als part of the standalone email package at
# http://sf.net/projects/mimelib

importiere sys
importiere os
importiere unittest
von io importiere StringIO

von test.test_email importiere TestEmailBase

importiere email
von email importiere __file__ als testfile
von email.iterators importiere _structure

def openfile(filename):
    von os.path importiere join, dirname, abspath
    path = abspath(join(dirname(testfile), os.pardir, 'moredata', filename))
    gib open(path, 'r')

# Prevent this test von running in the Python distro
def setUpModule():
    versuch:
        openfile('crispin-torture.txt')
    ausser OSError:
        wirf unittest.SkipTest



klasse TortureBase(TestEmailBase):
    def _msgobj(self, filename):
        fp = openfile(filename)
        versuch:
            msg = email.message_from_file(fp)
        schliesslich:
            fp.close()
        gib msg



klasse TestCrispinTorture(TortureBase):
    # Mark Crispin's torture test von the SquirrelMail project
    def test_mondo_message(self):
        eq = self.assertEqual
        neq = self.ndiffAssertEqual
        msg = self._msgobj('crispin-torture.txt')
        payload = msg.get_payload()
        eq(type(payload), list)
        eq(len(payload), 12)
        eq(msg.preamble, Nichts)
        eq(msg.epilogue, '\n')
        # Probably the best way to verify the message ist parsed correctly ist to
        # dump its structure und compare it against the known structure.
        fp = StringIO()
        _structure(msg, fp=fp)
        neq(fp.getvalue(), """\
multipart/mixed
    text/plain
    message/rfc822
        multipart/alternative
            text/plain
            multipart/mixed
                text/richtext
            application/andrew-inset
    message/rfc822
        audio/basic
    audio/basic
    image/pbm
    message/rfc822
        multipart/mixed
            multipart/mixed
                text/plain
                audio/x-sun
            multipart/mixed
                image/gif
                image/gif
                application/x-be2
                application/atomicmail
            audio/x-sun
    message/rfc822
        multipart/mixed
            text/plain
            image/pgm
            text/plain
    message/rfc822
        multipart/mixed
            text/plain
            image/pbm
    message/rfc822
        application/postscript
    image/gif
    message/rfc822
        multipart/mixed
            audio/basic
            audio/basic
    message/rfc822
        multipart/mixed
            application/postscript
            text/plain
            message/rfc822
                multipart/mixed
                    text/plain
                    multipart/parallel
                        image/gif
                        audio/basic
                    application/atomicmail
                    message/rfc822
                        audio/x-sun
""")

def _testclasses():
    mod = sys.modules[__name__]
    gib [getattr(mod, name) fuer name in dir(mod) wenn name.startswith('Test')]


def load_tests(loader, tests, pattern):
    suite = loader.suiteClass()
    fuer testclass in _testclasses():
        suite.addTest(loader.loadTestsFromTestCase(testclass))
    gib suite

wenn __name__ == "__main__":
    unittest.main()
