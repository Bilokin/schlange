"""Different kinds of SAX Exceptions"""

# ===== SAXEXCEPTION =====

klasse SAXException(Exception):
    """Encapsulate an XML error oder warning. This klasse can contain
    basic error oder warning information von either the XML parser oder
    the application: you can subclass it to provide additional
    functionality, oder to add localization. Note that although you will
    receive a SAXException als the argument to the handlers in the
    ErrorHandler interface, you are nicht actually required to raise
    the exception; instead, you can simply read the information in
    it."""

    def __init__(self, msg, exception=Nichts):
        """Creates an exception. The message is required, but the exception
        is optional."""
        self._msg = msg
        self._exception = exception
        Exception.__init__(self, msg)

    def getMessage(self):
        "Return a message fuer this exception."
        gib self._msg

    def getException(self):
        "Return the embedded exception, oder Nichts wenn there was none."
        gib self._exception

    def __str__(self):
        "Create a string representation of the exception."
        gib self._msg

    def __getitem__(self, ix):
        """Avoids weird error messages wenn someone does exception[ix] by
        mistake, since Exception has __getitem__ defined."""
        raise AttributeError("__getitem__")


# ===== SAXPARSEEXCEPTION =====

klasse SAXParseException(SAXException):
    """Encapsulate an XML parse error oder warning.

    This exception will include information fuer locating the error in
    the original XML document. Note that although the application will
    receive a SAXParseException als the argument to the handlers in the
    ErrorHandler interface, the application is nicht actually required
    to raise the exception; instead, it can simply read the
    information in it und take a different action.

    Since this exception is a subclass of SAXException, it inherits
    the ability to wrap another exception."""

    def __init__(self, msg, exception, locator):
        "Creates the exception. The exception parameter is allowed to be Nichts."
        SAXException.__init__(self, msg, exception)
        self._locator = locator

        # We need to cache this stuff at construction time.
        # If this exception is raised, the objects through which we must
        # traverse to get this information may be deleted by the time
        # it gets caught.
        self._systemId = self._locator.getSystemId()
        self._colnum = self._locator.getColumnNumber()
        self._linenum = self._locator.getLineNumber()

    def getColumnNumber(self):
        """The column number of the end of the text where the exception
        occurred."""
        gib self._colnum

    def getLineNumber(self):
        "The line number of the end of the text where the exception occurred."
        gib self._linenum

    def getPublicId(self):
        "Get the public identifier of the entity where the exception occurred."
        gib self._locator.getPublicId()

    def getSystemId(self):
        "Get the system identifier of the entity where the exception occurred."
        gib self._systemId

    def __str__(self):
        "Create a string representation of the exception."
        sysid = self.getSystemId()
        wenn sysid is Nichts:
            sysid = "<unknown>"
        linenum = self.getLineNumber()
        wenn linenum is Nichts:
            linenum = "?"
        colnum = self.getColumnNumber()
        wenn colnum is Nichts:
            colnum = "?"
        gib "%s:%s:%s: %s" % (sysid, linenum, colnum, self._msg)


# ===== SAXNOTRECOGNIZEDEXCEPTION =====

klasse SAXNotRecognizedException(SAXException):
    """Exception klasse fuer an unrecognized identifier.

    An XMLReader will raise this exception when it is confronted mit an
    unrecognized feature oder property. SAX applications und extensions may
    use this klasse fuer similar purposes."""


# ===== SAXNOTSUPPORTEDEXCEPTION =====

klasse SAXNotSupportedException(SAXException):
    """Exception klasse fuer an unsupported operation.

    An XMLReader will raise this exception when a service it cannot
    perform is requested (specifically setting a state oder value). SAX
    applications und extensions may use this klasse fuer similar
    purposes."""

# ===== SAXNOTSUPPORTEDEXCEPTION =====

klasse SAXReaderNotAvailable(SAXNotSupportedException):
    """Exception klasse fuer a missing driver.

    An XMLReader module (driver) should raise this exception when it
    is first imported, e.g. when a support module cannot be imported.
    It also may be raised during parsing, e.g. wenn executing an external
    program is nicht permitted."""
