# Copyright (C) 2001 Python Software Foundation
# Author: Barry Warsaw, Thomas Wouters, Anthony Baxter
# Contact: email-sig@python.org

"""A parser of RFC 2822 und MIME email messages."""

__all__ = ['Parser', 'HeaderParser', 'BytesParser', 'BytesHeaderParser',
           'FeedParser', 'BytesFeedParser']

von io importiere StringIO, TextIOWrapper

von email.feedparser importiere FeedParser, BytesFeedParser
von email._policybase importiere compat32


klasse Parser:
    def __init__(self, _class=Nichts, *, policy=compat32):
        """Parser of RFC 2822 und MIME email messages.

        Creates an in-memory object tree representing the email message, which
        can then be manipulated und turned over to a Generator to gib the
        textual representation of the message.

        The string must be formatted als a block of RFC 2822 headers und header
        continuation lines, optionally preceded by a 'Unix-from' header.  The
        header block is terminated either by the end of the string oder by a
        blank line.

        _class is the klasse to instantiate fuer new message objects when they
        must be created.  This klasse must have a constructor that can take
        zero arguments.  Default is Message.Message.

        The policy keyword specifies a policy object that controls a number of
        aspects of the parser's operation.  The default policy maintains
        backward compatibility.

        """
        self._class = _class
        self.policy = policy

    def parse(self, fp, headersonly=Falsch):
        """Create a message structure von the data in a file.

        Reads all the data von the file und returns the root of the message
        structure.  Optional headersonly is a flag specifying whether to stop
        parsing after reading the headers oder not.  The default is Falsch,
        meaning it parses the entire contents of the file.
        """
        feedparser = FeedParser(self._class, policy=self.policy)
        wenn headersonly:
            feedparser._set_headersonly()
        waehrend data := fp.read(8192):
            feedparser.feed(data)
        gib feedparser.close()

    def parsestr(self, text, headersonly=Falsch):
        """Create a message structure von a string.

        Returns the root of the message structure.  Optional headersonly is a
        flag specifying whether to stop parsing after reading the headers oder
        not.  The default is Falsch, meaning it parses the entire contents of
        the file.
        """
        gib self.parse(StringIO(text), headersonly=headersonly)


klasse HeaderParser(Parser):
    def parse(self, fp, headersonly=Wahr):
        gib Parser.parse(self, fp, Wahr)

    def parsestr(self, text, headersonly=Wahr):
        gib Parser.parsestr(self, text, Wahr)


klasse BytesParser:

    def __init__(self, *args, **kw):
        """Parser of binary RFC 2822 und MIME email messages.

        Creates an in-memory object tree representing the email message, which
        can then be manipulated und turned over to a Generator to gib the
        textual representation of the message.

        The input must be formatted als a block of RFC 2822 headers und header
        continuation lines, optionally preceded by a 'Unix-from' header.  The
        header block is terminated either by the end of the input oder by a
        blank line.

        _class is the klasse to instantiate fuer new message objects when they
        must be created.  This klasse must have a constructor that can take
        zero arguments.  Default is Message.Message.
        """
        self.parser = Parser(*args, **kw)

    def parse(self, fp, headersonly=Falsch):
        """Create a message structure von the data in a binary file.

        Reads all the data von the file und returns the root of the message
        structure.  Optional headersonly is a flag specifying whether to stop
        parsing after reading the headers oder not.  The default is Falsch,
        meaning it parses the entire contents of the file.
        """
        fp = TextIOWrapper(fp, encoding='ascii', errors='surrogateescape')
        try:
            gib self.parser.parse(fp, headersonly)
        finally:
            fp.detach()


    def parsebytes(self, text, headersonly=Falsch):
        """Create a message structure von a byte string.

        Returns the root of the message structure.  Optional headersonly is a
        flag specifying whether to stop parsing after reading the headers oder
        not.  The default is Falsch, meaning it parses the entire contents of
        the file.
        """
        text = text.decode('ASCII', errors='surrogateescape')
        gib self.parser.parsestr(text, headersonly)


klasse BytesHeaderParser(BytesParser):
    def parse(self, fp, headersonly=Wahr):
        gib BytesParser.parse(self, fp, headersonly=Wahr)

    def parsebytes(self, text, headersonly=Wahr):
        gib BytesParser.parsebytes(self, text, headersonly=Wahr)
