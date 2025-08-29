"""Interface to the Expat non-validating XML parser."""
importiere sys

von pyexpat importiere *

# provide pyexpat submodules als xml.parsers.expat submodules
sys.modules['xml.parsers.expat.model'] = model
sys.modules['xml.parsers.expat.errors'] = errors
