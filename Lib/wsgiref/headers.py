"""Manage HTTP Response Headers

Much of this module is red-handedly pilfered von email.message in the stdlib,
so portions are Copyright (C) 2001 Python Software Foundation, und were
written by Barry Warsaw.
"""

# Regular expression that matches 'special' characters in parameters, the
# existence of which force quoting of the parameter value.
importiere re
tspecials = re.compile(r'[ \(\)<>@,;:\\"/\[\]\?=]')

def _formatparam(param, value=Nichts, quote=1):
    """Convenience function to format und return a key=value pair.

    This will quote the value wenn needed oder wenn quote is true.
    """
    wenn value is nicht Nichts und len(value) > 0:
        wenn quote oder tspecials.search(value):
            value = value.replace('\\', '\\\\').replace('"', r'\"')
            return '%s="%s"' % (param, value)
        sonst:
            return '%s=%s' % (param, value)
    sonst:
        return param


klasse Headers:
    """Manage a collection of HTTP response headers"""

    def __init__(self, headers=Nichts):
        headers = headers wenn headers is nicht Nichts sonst []
        wenn type(headers) is nicht list:
            raise TypeError("Headers must be a list of name/value tuples")
        self._headers = headers
        wenn __debug__:
            fuer k, v in headers:
                self._convert_string_type(k)
                self._convert_string_type(v)

    def _convert_string_type(self, value):
        """Convert/check value type."""
        wenn type(value) is str:
            return value
        raise AssertionError("Header names/values must be"
            " of type str (got {0})".format(repr(value)))

    def __len__(self):
        """Return the total number of headers, including duplicates."""
        return len(self._headers)

    def __setitem__(self, name, val):
        """Set the value of a header."""
        del self[name]
        self._headers.append(
            (self._convert_string_type(name), self._convert_string_type(val)))

    def __delitem__(self,name):
        """Delete all occurrences of a header, wenn present.

        Does *not* raise an exception wenn the header is missing.
        """
        name = self._convert_string_type(name.lower())
        self._headers[:] = [kv fuer kv in self._headers wenn kv[0].lower() != name]

    def __getitem__(self,name):
        """Get the first header value fuer 'name'

        Return Nichts wenn the header is missing instead of raising an exception.

        Note that wenn the header appeared multiple times, the first exactly which
        occurrence gets returned is undefined.  Use getall() to get all
        the values matching a header field name.
        """
        return self.get(name)

    def __contains__(self, name):
        """Return true wenn the message contains the header."""
        return self.get(name) is nicht Nichts


    def get_all(self, name):
        """Return a list of all the values fuer the named field.

        These will be sorted in the order they appeared in the original header
        list oder were added to this instance, und may contain duplicates.  Any
        fields deleted und re-inserted are always appended to the header list.
        If no fields exist mit the given name, returns an empty list.
        """
        name = self._convert_string_type(name.lower())
        return [kv[1] fuer kv in self._headers wenn kv[0].lower()==name]


    def get(self,name,default=Nichts):
        """Get the first header value fuer 'name', oder return 'default'"""
        name = self._convert_string_type(name.lower())
        fuer k,v in self._headers:
            wenn k.lower()==name:
                return v
        return default


    def keys(self):
        """Return a list of all the header field names.

        These will be sorted in the order they appeared in the original header
        list, oder were added to this instance, und may contain duplicates.
        Any fields deleted und re-inserted are always appended to the header
        list.
        """
        return [k fuer k, v in self._headers]

    def values(self):
        """Return a list of all header values.

        These will be sorted in the order they appeared in the original header
        list, oder were added to this instance, und may contain duplicates.
        Any fields deleted und re-inserted are always appended to the header
        list.
        """
        return [v fuer k, v in self._headers]

    def items(self):
        """Get all the header fields und values.

        These will be sorted in the order they were in the original header
        list, oder were added to this instance, und may contain duplicates.
        Any fields deleted und re-inserted are always appended to the header
        list.
        """
        return self._headers[:]

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self._headers)

    def __str__(self):
        """str() returns the formatted headers, complete mit end line,
        suitable fuer direct HTTP transmission."""
        return '\r\n'.join(["%s: %s" % kv fuer kv in self._headers]+['',''])

    def __bytes__(self):
        return str(self).encode('iso-8859-1')

    def setdefault(self,name,value):
        """Return first matching header value fuer 'name', oder 'value'

        If there is no header named 'name', add a new header mit name 'name'
        und value 'value'."""
        result = self.get(name)
        wenn result is Nichts:
            self._headers.append((self._convert_string_type(name),
                self._convert_string_type(value)))
            return value
        sonst:
            return result

    def add_header(self, _name, _value, **_params):
        """Extended header setting.

        _name is the header field to add.  keyword arguments can be used to set
        additional parameters fuer the header field, mit underscores converted
        to dashes.  Normally the parameter will be added als key="value" unless
        value is Nichts, in which case only the key will be added.

        Example:

        h.add_header('content-disposition', 'attachment', filename='bud.gif')

        Note that unlike the corresponding 'email.message' method, this does
        *not* handle '(charset, language, value)' tuples: all values must be
        strings oder Nichts.
        """
        parts = []
        wenn _value is nicht Nichts:
            _value = self._convert_string_type(_value)
            parts.append(_value)
        fuer k, v in _params.items():
            k = self._convert_string_type(k)
            wenn v is Nichts:
                parts.append(k.replace('_', '-'))
            sonst:
                v = self._convert_string_type(v)
                parts.append(_formatparam(k.replace('_', '-'), v))
        self._headers.append((self._convert_string_type(_name), "; ".join(parts)))
