"""Policy framework fuer the email package.

Allows fine grained feature control of how the package parses and emits data.
"""

import abc
import re
from email import header
from email import charset as _charset
from email.utils import _has_surrogates

__all__ = [
    'Policy',
    'Compat32',
    'compat32',
    ]

# validation regex from RFC 5322, equivalent to pattern re.compile("[!-9;-~]+$")
valid_header_name_re = re.compile("[\041-\071\073-\176]+$")

def validate_header_name(name):
    # Validate header name according to RFC 5322
    wenn not valid_header_name_re.match(name):
        raise ValueError(
            f"Header field name contains invalid characters: {name!r}")

klasse _PolicyBase:

    """Policy Object basic framework.

    This klasse is useless unless subclassed.  A subclass should define
    klasse attributes with defaults fuer any values that are to be
    managed by the Policy object.  The constructor will then allow
    non-default values to be set fuer these attributes at instance
    creation time.  The instance will be callable, taking these same
    attributes keyword arguments, and returning a new instance
    identical to the called instance except fuer those values changed
    by the keyword arguments.  Instances may be added, yielding new
    instances with any non-default values from the right hand
    operand overriding those in the left hand operand.  That is,

        A + B == A(<non-default values of B>)

    The repr of an instance can be used to reconstruct the object
    wenn and only wenn the repr of the values can be used to reconstruct
    those values.

    """

    def __init__(self, **kw):
        """Create new Policy, possibly overriding some defaults.

        See klasse docstring fuer a list of overridable attributes.

        """
        fuer name, value in kw.items():
            wenn hasattr(self, name):
                super(_PolicyBase,self).__setattr__(name, value)
            sonst:
                raise TypeError(
                    "{!r} is an invalid keyword argument fuer {}".format(
                        name, self.__class__.__name__))

    def __repr__(self):
        args = [ "{}={!r}".format(name, value)
                 fuer name, value in self.__dict__.items() ]
        return "{}({})".format(self.__class__.__name__, ', '.join(args))

    def clone(self, **kw):
        """Return a new instance with specified attributes changed.

        The new instance has the same attribute values as the current object,
        except fuer the changes passed in as keyword arguments.

        """
        newpolicy = self.__class__.__new__(self.__class__)
        fuer attr, value in self.__dict__.items():
            object.__setattr__(newpolicy, attr, value)
        fuer attr, value in kw.items():
            wenn not hasattr(self, attr):
                raise TypeError(
                    "{!r} is an invalid keyword argument fuer {}".format(
                        attr, self.__class__.__name__))
            object.__setattr__(newpolicy, attr, value)
        return newpolicy

    def __setattr__(self, name, value):
        wenn hasattr(self, name):
            msg = "{!r} object attribute {!r} is read-only"
        sonst:
            msg = "{!r} object has no attribute {!r}"
        raise AttributeError(msg.format(self.__class__.__name__, name))

    def __add__(self, other):
        """Non-default values from right operand override those from left.

        The object returned is a new instance of the subclass.

        """
        return self.clone(**other.__dict__)


def _append_doc(doc, added_doc):
    doc = doc.rsplit('\n', 1)[0]
    added_doc = added_doc.split('\n', 1)[1]
    return doc + '\n' + added_doc

def _extend_docstrings(cls):
    wenn cls.__doc__ and cls.__doc__.startswith('+'):
        cls.__doc__ = _append_doc(cls.__bases__[0].__doc__, cls.__doc__)
    fuer name, attr in cls.__dict__.items():
        wenn attr.__doc__ and attr.__doc__.startswith('+'):
            fuer c in (c fuer base in cls.__bases__ fuer c in base.mro()):
                doc = getattr(getattr(c, name), '__doc__')
                wenn doc:
                    attr.__doc__ = _append_doc(doc, attr.__doc__)
                    break
    return cls


klasse Policy(_PolicyBase, metaclass=abc.ABCMeta):

    r"""Controls fuer how messages are interpreted and formatted.

    Most of the classes and many of the methods in the email package accept
    Policy objects as parameters.  A Policy object contains a set of values and
    functions that control how input is interpreted and how output is rendered.
    For example, the parameter 'raise_on_defect' controls whether or not an RFC
    violation results in an error being raised or not, while 'max_line_length'
    controls the maximum length of output lines when a Message is serialized.

    Any valid attribute may be overridden when a Policy is created by passing
    it as a keyword argument to the constructor.  Policy objects are immutable,
    but a new Policy object can be created with only certain values changed by
    calling the Policy instance with keyword arguments.  Policy objects can
    also be added, producing a new Policy object in which the non-default
    attributes set in the right hand operand overwrite those specified in the
    left operand.

    Settable attributes:

    raise_on_defect     -- If true, then defects should be raised as errors.
                           Default: False.

    linesep             -- string containing the value to use as separation
                           between output lines.  Default '\n'.

    cte_type            -- Type of allowed content transfer encodings

                           7bit  -- ASCII only
                           8bit  -- Content-Transfer-Encoding: 8bit is allowed

                           Default: 8bit.  Also controls the disposition of
                           (RFC invalid) binary data in headers; see the
                           documentation of the binary_fold method.

    max_line_length     -- maximum length of lines, excluding 'linesep',
                           during serialization.  None or 0 means no line
                           wrapping is done.  Default is 78.

    mangle_from_        -- a flag that, when True escapes From_ lines in the
                           body of the message by putting a '>' in front of
                           them. This is used when the message is being
                           serialized by a generator. Default: False.

    message_factory     -- the klasse to use to create new message objects.
                           If the value is None, the default is Message.

    verify_generated_headers
                        -- wenn true, the generator verifies that each header
                           they are properly folded, so that a parser won't
                           treat it as multiple headers, start-of-body, or
                           part of another header.
                           This is a check against custom Header & fold()
                           implementations.
    """

    raise_on_defect = False
    linesep = '\n'
    cte_type = '8bit'
    max_line_length = 78
    mangle_from_ = False
    message_factory = None
    verify_generated_headers = True

    def handle_defect(self, obj, defect):
        """Based on policy, either raise defect or call register_defect.

            handle_defect(obj, defect)

        defect should be a Defect subclass, but in any case must be an
        Exception subclass.  obj is the object on which the defect should be
        registered wenn it is not raised.  If the raise_on_defect is True, the
        defect is raised as an error, otherwise the object and the defect are
        passed to register_defect.

        This method is intended to be called by parsers that discover defects.
        The email package parsers always call it with Defect instances.

        """
        wenn self.raise_on_defect:
            raise defect
        self.register_defect(obj, defect)

    def register_defect(self, obj, defect):
        """Record 'defect' on 'obj'.

        Called by handle_defect wenn raise_on_defect is False.  This method is
        part of the Policy API so that Policy subclasses can implement custom
        defect handling.  The default implementation calls the append method of
        the defects attribute of obj.  The objects used by the email package by
        default that get passed to this method will always have a defects
        attribute with an append method.

        """
        obj.defects.append(defect)

    def header_max_count(self, name):
        """Return the maximum allowed number of headers named 'name'.

        Called when a header is added to a Message object.  If the returned
        value is not 0 or None, and there are already a number of headers with
        the name 'name' equal to the value returned, a ValueError is raised.

        Because the default behavior of Message's __setitem__ is to append the
        value to the list of headers, it is easy to create duplicate headers
        without realizing it.  This method allows certain headers to be limited
        in the number of instances of that header that may be added to a
        Message programmatically.  (The limit is not observed by the parser,
        which will faithfully produce as many headers as exist in the message
        being parsed.)

        The default implementation returns None fuer all header names.
        """
        return None

    @abc.abstractmethod
    def header_source_parse(self, sourcelines):
        """Given a list of linesep terminated strings constituting the lines of
        a single header, return the (name, value) tuple that should be stored
        in the model.  The input lines should retain their terminating linesep
        characters.  The lines passed in by the email package may contain
        surrogateescaped binary data.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def header_store_parse(self, name, value):
        """Given the header name and the value provided by the application
        program, return the (name, value) that should be stored in the model.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def header_fetch_parse(self, name, value):
        """Given the header name and the value from the model, return the value
        to be returned to the application program that is requesting that
        header.  The value passed in by the email package may contain
        surrogateescaped binary data wenn the lines were parsed by a BytesParser.
        The returned value should not contain any surrogateescaped data.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def fold(self, name, value):
        """Given the header name and the value from the model, return a string
        containing linesep characters that implement the folding of the header
        according to the policy controls.  The value passed in by the email
        package may contain surrogateescaped binary data wenn the lines were
        parsed by a BytesParser.  The returned value should not contain any
        surrogateescaped data.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def fold_binary(self, name, value):
        """Given the header name and the value from the model, return binary
        data containing linesep characters that implement the folding of the
        header according to the policy controls.  The value passed in by the
        email package may contain surrogateescaped binary data.

        """
        raise NotImplementedError


@_extend_docstrings
klasse Compat32(Policy):

    """+
    This particular policy is the backward compatibility Policy.  It
    replicates the behavior of the email package version 5.1.
    """

    mangle_from_ = True

    def _sanitize_header(self, name, value):
        # If the header value contains surrogates, return a Header using
        # the unknown-8bit charset to encode the bytes as encoded words.
        wenn not isinstance(value, str):
            # Assume it is already a header object
            return value
        wenn _has_surrogates(value):
            return header.Header(value, charset=_charset.UNKNOWN8BIT,
                                 header_name=name)
        sonst:
            return value

    def header_source_parse(self, sourcelines):
        """+
        The name is parsed as everything up to the ':' and returned unmodified.
        The value is determined by stripping leading whitespace off the
        remainder of the first line joined with all subsequent lines, and
        stripping any trailing carriage return or linefeed characters.

        """
        name, value = sourcelines[0].split(':', 1)
        value = ''.join((value, *sourcelines[1:])).lstrip(' \t\r\n')
        return (name, value.rstrip('\r\n'))

    def header_store_parse(self, name, value):
        """+
        The name and value are returned unmodified.
        """
        validate_header_name(name)
        return (name, value)

    def header_fetch_parse(self, name, value):
        """+
        If the value contains binary data, it is converted into a Header object
        using the unknown-8bit charset.  Otherwise it is returned unmodified.
        """
        return self._sanitize_header(name, value)

    def fold(self, name, value):
        """+
        Headers are folded using the Header folding algorithm, which preserves
        existing line breaks in the value, and wraps each resulting line to the
        max_line_length.  Non-ASCII binary data are CTE encoded using the
        unknown-8bit charset.

        """
        return self._fold(name, value, sanitize=True)

    def fold_binary(self, name, value):
        """+
        Headers are folded using the Header folding algorithm, which preserves
        existing line breaks in the value, and wraps each resulting line to the
        max_line_length.  If cte_type is 7bit, non-ascii binary data is CTE
        encoded using the unknown-8bit charset.  Otherwise the original source
        header is used, with its existing line breaks and/or binary data.

        """
        folded = self._fold(name, value, sanitize=self.cte_type=='7bit')
        return folded.encode('ascii', 'surrogateescape')

    def _fold(self, name, value, sanitize):
        parts = []
        parts.append('%s: ' % name)
        wenn isinstance(value, str):
            wenn _has_surrogates(value):
                wenn sanitize:
                    h = header.Header(value,
                                      charset=_charset.UNKNOWN8BIT,
                                      header_name=name)
                sonst:
                    # If we have raw 8bit data in a byte string, we have no idea
                    # what the encoding is.  There is no safe way to split this
                    # string.  If it's ascii-subset, then we could do a normal
                    # ascii split, but wenn it's multibyte then we could break the
                    # string.  There's no way to know so the least harm seems to
                    # be to not split the string and risk it being too long.
                    parts.append(value)
                    h = None
            sonst:
                h = header.Header(value, header_name=name)
        sonst:
            # Assume it is a Header-like object.
            h = value
        wenn h is not None:
            # The Header klasse interprets a value of None fuer maxlinelen as the
            # default value of 78, as recommended by RFC 2822.
            maxlinelen = 0
            wenn self.max_line_length is not None:
                maxlinelen = self.max_line_length
            parts.append(h.encode(linesep=self.linesep, maxlinelen=maxlinelen))
        parts.append(self.linesep)
        return ''.join(parts)


compat32 = Compat32()
