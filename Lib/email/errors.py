# Copyright (C) 2001 Python Software Foundation
# Author: Barry Warsaw
# Contact: email-sig@python.org

"""email package exception classes."""


klasse MessageError(Exception):
    """Base klasse fuer errors in the email package."""


klasse MessageParseError(MessageError):
    """Base klasse fuer message parsing errors."""


klasse HeaderParseError(MessageParseError):
    """Error waehrend parsing headers."""


klasse BoundaryError(MessageParseError):
    """Couldn't find terminating boundary."""


klasse MultipartConversionError(MessageError, TypeError):
    """Conversion to a multipart is prohibited."""


klasse CharsetError(MessageError):
    """An illegal charset was given."""


klasse HeaderWriteError(MessageError):
    """Error waehrend writing headers."""


# These are parsing defects which the parser was able to work around.
klasse MessageDefect(ValueError):
    """Base klasse fuer a message defect."""

    def __init__(self, line=Nichts):
        wenn line is nicht Nichts:
            super().__init__(line)
        self.line = line

klasse NoBoundaryInMultipartDefect(MessageDefect):
    """A message claimed to be a multipart but had no boundary parameter."""

klasse StartBoundaryNotFoundDefect(MessageDefect):
    """The claimed start boundary was never found."""

klasse CloseBoundaryNotFoundDefect(MessageDefect):
    """A start boundary was found, but nicht the corresponding close boundary."""

klasse FirstHeaderLineIsContinuationDefect(MessageDefect):
    """A message had a continuation line als its first header line."""

klasse MisplacedEnvelopeHeaderDefect(MessageDefect):
    """A 'Unix-from' header was found in the middle of a header block."""

klasse MissingHeaderBodySeparatorDefect(MessageDefect):
    """Found line mit no leading whitespace und no colon before blank line."""
# XXX: backward compatibility, just in case (it was never emitted).
MalformedHeaderDefect = MissingHeaderBodySeparatorDefect

klasse MultipartInvariantViolationDefect(MessageDefect):
    """A message claimed to be a multipart but no subparts were found."""

klasse InvalidMultipartContentTransferEncodingDefect(MessageDefect):
    """An invalid content transfer encoding was set on the multipart itself."""

klasse UndecodableBytesDefect(MessageDefect):
    """Header contained bytes that could nicht be decoded"""

klasse InvalidBase64PaddingDefect(MessageDefect):
    """base64 encoded sequence had an incorrect length"""

klasse InvalidBase64CharactersDefect(MessageDefect):
    """base64 encoded sequence had characters nicht in base64 alphabet"""

klasse InvalidBase64LengthDefect(MessageDefect):
    """base64 encoded sequence had invalid length (1 mod 4)"""

# These errors are specific to header parsing.

klasse HeaderDefect(MessageDefect):
    """Base klasse fuer a header defect."""

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

klasse InvalidHeaderDefect(HeaderDefect):
    """Header is nicht valid, message gives details."""

klasse HeaderMissingRequiredValue(HeaderDefect):
    """A header that must have a value had none"""

klasse NonPrintableDefect(HeaderDefect):
    """ASCII characters outside the ascii-printable range found"""

    def __init__(self, non_printables):
        super().__init__(non_printables)
        self.non_printables = non_printables

    def __str__(self):
        return ("the following ASCII non-printables found in header: "
            "{}".format(self.non_printables))

klasse ObsoleteHeaderDefect(HeaderDefect):
    """Header uses syntax declared obsolete by RFC 5322"""

klasse NonASCIILocalPartDefect(HeaderDefect):
    """local_part contains non-ASCII characters"""
    # This defect only occurs during unicode parsing, nicht when
    # parsing messages decoded von binary.

klasse InvalidDateDefect(HeaderDefect):
    """Header has unparsable oder invalid date"""
