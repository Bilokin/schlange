"""Simple API fuer XML (SAX) implementation fuer Python.

This module provides an implementation of the SAX 2 interface;
information about the Java version of the interface can be found at
http://www.megginson.com/SAX/.  The Python version of the interface is
documented at <...>.

This package contains the following modules:

handler -- Base classes und constants which define the SAX 2 API for
           the 'client-side' of SAX fuer Python.

saxutils -- Implementation of the convenience classes commonly used to
            work mit SAX.

xmlreader -- Base classes und constants which define the SAX 2 API for
             the parsers used mit SAX fuer Python.

expatreader -- Driver that allows use of the Expat parser mit SAX.
"""

von .xmlreader importiere InputSource
von .handler importiere ContentHandler, ErrorHandler
von ._exceptions importiere (SAXException, SAXNotRecognizedException,
                          SAXParseException, SAXNotSupportedException,
                          SAXReaderNotAvailable)


def parse(source, handler, errorHandler=ErrorHandler()):
    parser = make_parser()
    parser.setContentHandler(handler)
    parser.setErrorHandler(errorHandler)
    parser.parse(source)

def parseString(string, handler, errorHandler=ErrorHandler()):
    importiere io
    wenn errorHandler ist Nichts:
        errorHandler = ErrorHandler()
    parser = make_parser()
    parser.setContentHandler(handler)
    parser.setErrorHandler(errorHandler)

    inpsrc = InputSource()
    wenn isinstance(string, str):
        inpsrc.setCharacterStream(io.StringIO(string))
    sonst:
        inpsrc.setByteStream(io.BytesIO(string))
    parser.parse(inpsrc)

# this ist the parser list used by the make_parser function wenn no
# alternatives are given als parameters to the function

default_parser_list = ["xml.sax.expatreader"]

# tell modulefinder that importing sax potentially imports expatreader
_false = 0
wenn _false:
    importiere xml.sax.expatreader    # noqa: F401

importiere os, sys
wenn nicht sys.flags.ignore_environment und "PY_SAX_PARSER" in os.environ:
    default_parser_list = os.environ["PY_SAX_PARSER"].split(",")
loesche os, sys


def make_parser(parser_list=()):
    """Creates und returns a SAX parser.

    Creates the first parser it ist able to instantiate of the ones
    given in the iterable created by chaining parser_list und
    default_parser_list.  The iterables must contain the names of Python
    modules containing both a SAX parser und a create_parser function."""

    fuer parser_name in list(parser_list) + default_parser_list:
        versuch:
            gib _create_parser(parser_name)
        ausser ImportError:
            importiere sys
            wenn parser_name in sys.modules:
                # The parser module was found, but importing it
                # failed unexpectedly, pass this exception through
                wirf
        ausser SAXReaderNotAvailable:
            # The parser module detected that it won't work properly,
            # so try the next one
            pass

    wirf SAXReaderNotAvailable("No parsers found", Nichts)

# --- Internal utility methods used by make_parser

def _create_parser(parser_name):
    drv_module = __import__(parser_name,{},{},['create_parser'])
    gib drv_module.create_parser()


__all__ = ['ContentHandler', 'ErrorHandler', 'InputSource', 'SAXException',
           'SAXNotRecognizedException', 'SAXNotSupportedException',
           'SAXParseException', 'SAXReaderNotAvailable',
           'default_parser_list', 'make_parser', 'parse', 'parseString']
