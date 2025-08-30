"""Tests fuer http/cookiejar.py."""

importiere os
importiere stat
importiere sys
importiere re
von test importiere support
von test.support importiere os_helper
von test.support importiere warnings_helper
importiere time
importiere unittest
importiere urllib.request

von http.cookiejar importiere (time2isoz, http2time, iso2time, time2netscape,
     parse_ns_headers, join_header_words, split_header_words, Cookie,
     CookieJar, DefaultCookiePolicy, LWPCookieJar, MozillaCookieJar,
     LoadError, lwp_cookie_str, DEFAULT_HTTP_PORT, escape_path,
     reach, is_HDN, domain_match, user_domain_match, request_path,
     request_port, request_host)

mswindows = (sys.platform == "win32")

klasse DateTimeTests(unittest.TestCase):

    def test_time2isoz(self):
        base = 1019227000
        day = 24*3600
        self.assertEqual(time2isoz(base), "2002-04-19 14:36:40Z")
        self.assertEqual(time2isoz(base+day), "2002-04-20 14:36:40Z")
        self.assertEqual(time2isoz(base+2*day), "2002-04-21 14:36:40Z")
        self.assertEqual(time2isoz(base+3*day), "2002-04-22 14:36:40Z")

        az = time2isoz()
        bz = time2isoz(500000)
        fuer text in (az, bz):
            self.assertRegex(text, r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\dZ$",
                             "bad time2isoz format: %s %s" % (az, bz))

    def test_time2netscape(self):
        base = 1019227000
        day = 24*3600
        self.assertEqual(time2netscape(base), "Fri, 19-Apr-2002 14:36:40 GMT")
        self.assertEqual(time2netscape(base+day),
                         "Sat, 20-Apr-2002 14:36:40 GMT")

        self.assertEqual(time2netscape(base+2*day),
                         "Sun, 21-Apr-2002 14:36:40 GMT")

        self.assertEqual(time2netscape(base+3*day),
                         "Mon, 22-Apr-2002 14:36:40 GMT")

        az = time2netscape()
        bz = time2netscape(500000)
        fuer text in (az, bz):
            # Format "%s, %02d-%s-%04d %02d:%02d:%02d GMT"
            self.assertRegex(
                text,
                r"[a-zA-Z]{3}, \d{2}-[a-zA-Z]{3}-\d{4} \d{2}:\d{2}:\d{2} GMT$",
                "bad time2netscape format: %s %s" % (az, bz))

    def test_http2time(self):
        def parse_date(text):
            gib time.gmtime(http2time(text))[:6]

        self.assertEqual(parse_date("01 Jan 2001"), (2001, 1, 1, 0, 0, 0.0))

        # this test will breche around year 2070
        self.assertEqual(parse_date("03-Feb-20"), (2020, 2, 3, 0, 0, 0.0))

        # this test will breche around year 2048
        self.assertEqual(parse_date("03-Feb-98"), (1998, 2, 3, 0, 0, 0.0))

    def test_http2time_formats(self):
        # test http2time fuer supported dates.  Test cases mit 2 digit year
        # will probably breche in year 2044.
        tests = [
         'Thu, 03 Feb 1994 00:00:00 GMT',  # proposed new HTTP format
         'Thursday, 03-Feb-94 00:00:00 GMT',  # old rfc850 HTTP format
         'Thursday, 03-Feb-1994 00:00:00 GMT',  # broken rfc850 HTTP format

         '03 Feb 1994 00:00:00 GMT',  # HTTP format (no weekday)
         '03-Feb-94 00:00:00 GMT',  # old rfc850 (no weekday)
         '03-Feb-1994 00:00:00 GMT',  # broken rfc850 (no weekday)
         '03-Feb-1994 00:00 GMT',  # broken rfc850 (no weekday, no seconds)
         '03-Feb-1994 00:00',  # broken rfc850 (no weekday, no seconds, no tz)
         '02-Feb-1994 24:00',  # broken rfc850 (no weekday, no seconds,
                               # no tz) using hour 24 mit yesterday date

         '03-Feb-94',  # old rfc850 HTTP format (no weekday, no time)
         '03-Feb-1994',  # broken rfc850 HTTP format (no weekday, no time)
         '03 Feb 1994',  # proposed new HTTP format (no weekday, no time)

         # A few tests mit extra space at various places
         '  03   Feb   1994  0:00  ',
         '  03-Feb-1994  ',
        ]

        test_t = 760233600  # assume broken POSIX counting of seconds
        result = time2isoz(test_t)
        expected = "1994-02-03 00:00:00Z"
        self.assertEqual(result, expected,
                         "%s  =>  '%s' (%s)" % (test_t, result, expected))

        fuer s in tests:
            self.assertEqual(http2time(s), test_t, s)
            self.assertEqual(http2time(s.lower()), test_t, s.lower())
            self.assertEqual(http2time(s.upper()), test_t, s.upper())

    @support.subTests('test', [
            '',
            'Garbage',
            'Mandag 16. September 1996',
            '01-00-1980',
            '01-13-1980',
            '00-01-1980',
            '32-01-1980',
            '01-01-1980 25:00:00',
            '01-01-1980 00:61:00',
            '01-01-1980 00:00:62',
            '08-Oct-3697739',
            '08-01-3697739',
            '09 Feb 19942632 22:23:32 GMT',
            'Wed, 09 Feb 1994834 22:23:32 GMT',
        ])
    def test_http2time_garbage(self, test):
        self.assertIsNichts(http2time(test))

    def test_http2time_redos_regression_actually_completes(self):
        # LOOSE_HTTP_DATE_RE was vulnerable to malicious input which caused catastrophic backtracking (REDoS).
        # If we regress to cubic complexity, this test will take a very long time to succeed.
        # If fixed, it should complete within a fraction of a second.
        http2time("01 Jan 1970{}00:00:00 GMT!".format(" " * 10 ** 5))
        http2time("01 Jan 1970 00:00:00{}GMT!".format(" " * 10 ** 5))

    def test_iso2time(self):
        def parse_date(text):
            gib time.gmtime(iso2time(text))[:6]

        # ISO 8601 compact format
        self.assertEqual(parse_date("19940203T141529Z"),
                         (1994, 2, 3, 14, 15, 29))

        # ISO 8601 mit time behind UTC
        self.assertEqual(parse_date("1994-02-03 07:15:29 -0700"),
                         (1994, 2, 3, 14, 15, 29))

        # ISO 8601 mit time ahead of UTC
        self.assertEqual(parse_date("1994-02-03 19:45:29 +0530"),
                         (1994, 2, 3, 14, 15, 29))

    @support.subTests('s', [
            '1994-02-03 00:00:00 -0000', # ISO 8601 format
            '1994-02-03 00:00:00 +0000', # ISO 8601 format
            '1994-02-03 00:00:00',       # zone is optional
            '1994-02-03',                # only date
            '1994-02-03T00:00:00',       # Use T als separator
            '19940203',                  # only date
            '1994-02-02 24:00:00',       # using hour-24 yesterday date
            '19940203T000000Z',          # ISO 8601 compact format

            # A few tests mit extra space at various places
            '  1994-02-03 ',
            '  1994-02-03T00:00:00  ',
        ])
    def test_iso2time_formats(self, s):
        # test iso2time fuer supported dates.
        test_t = 760233600  # assume broken POSIX counting of seconds
        self.assertEqual(iso2time(s), test_t, s)
        self.assertEqual(iso2time(s.lower()), test_t, s.lower())
        self.assertEqual(iso2time(s.upper()), test_t, s.upper())

    @support.subTests('test', [
            '',
            'Garbage',
            'Thursday, 03-Feb-94 00:00:00 GMT',
            '1980-00-01',
            '1980-13-01',
            '1980-01-00',
            '1980-01-32',
            '1980-01-01 25:00:00',
            '1980-01-01 00:61:00',
            '01-01-1980 00:00:62',
            '01-01-1980T00:00:62',
            '19800101T250000Z',
        ])
    def test_iso2time_garbage(self, test):
        self.assertIsNichts(iso2time(test))

    def test_iso2time_performance_regression(self):
        # If ISO_DATE_RE regresses to quadratic complexity, this test will take a very long time to succeed.
        # If fixed, it should complete within a fraction of a second.
        iso2time('1994-02-03{}14:15:29 -0100!'.format(' '*10**6))
        iso2time('1994-02-03 14:15:29{}-0100!'.format(' '*10**6))


klasse HeaderTests(unittest.TestCase):

    @support.subTests('hdr', [
            'foo=bar; expires=01 Jan 2040 22:23:32 GMT',
            'foo=bar; expires="01 Jan 2040 22:23:32 GMT"',
        ])
    def test_parse_ns_headers(self, hdr):
        # quotes should be stripped
        expected = [[('foo', 'bar'), ('expires', 2209069412), ('version', '0')]]
        self.assertEqual(parse_ns_headers([hdr]), expected)

    @support.subTests('hdr', [
            'foo=bar; version="1"',
            'foo=bar; Version="1"',
        ])
    def test_parse_ns_headers_version(self, hdr):
        # quotes should be stripped
        expected = [[('foo', 'bar'), ('version', '1')]]
        self.assertEqual(parse_ns_headers([hdr]), expected)

    def test_parse_ns_headers_special_names(self):
        # names such als 'expires' are nicht special in first name=value pair
        # of Set-Cookie: header
        # Cookie mit name 'expires'
        hdr = 'expires=01 Jan 2040 22:23:32 GMT'
        expected = [[("expires", "01 Jan 2040 22:23:32 GMT"), ("version", "0")]]
        self.assertEqual(parse_ns_headers([hdr]), expected)

    @support.subTests('src,expected', [
            ([[("foo", Nichts), ("bar", "baz")]], "foo; bar=baz"),
            (([]), ""),
            (([[]]), ""),
            (([[("a", "_")]]), "a=_"),
            (([[("a", ";")]]), 'a=";"'),
            ([[("n", Nichts), ("foo", "foo;_")], [("bar", "foo_bar")]],
             'n; foo="foo;_", bar=foo_bar'),
            ([[("n", "m"), ("foo", Nichts)], [("bar", "foo_bar")]],
             'n=m; foo, bar=foo_bar'),
        ])
    def test_join_header_words(self, src, expected):
        self.assertEqual(join_header_words(src), expected)

    @support.subTests('arg,expect', [
            ("foo", [[("foo", Nichts)]]),
            ("foo=bar", [[("foo", "bar")]]),
            ("   foo   ", [[("foo", Nichts)]]),
            ("   foo=   ", [[("foo", "")]]),
            ("   foo=", [[("foo", "")]]),
            ("   foo=   ; ", [[("foo", "")]]),
            ("   foo=   ; bar= baz ", [[("foo", ""), ("bar", "baz")]]),
            ("foo=bar bar=baz", [[("foo", "bar"), ("bar", "baz")]]),
            # doesn't really matter wenn this next fails, but it works ATM
            ("foo= bar=baz", [[("foo", "bar=baz")]]),
            ("foo=bar;bar=baz", [[("foo", "bar"), ("bar", "baz")]]),
            ('foo bar baz', [[("foo", Nichts), ("bar", Nichts), ("baz", Nichts)]]),
            ("a, b, c", [[("a", Nichts)], [("b", Nichts)], [("c", Nichts)]]),
            (r'foo; bar=baz, spam=, foo="\,\;\"", bar= ',
             [[("foo", Nichts), ("bar", "baz")],
              [("spam", "")], [("foo", ',;"')], [("bar", "")]]),
        ])
    def test_split_header_words(self, arg, expect):
        versuch:
            result = split_header_words([arg])
        ausser:
            importiere traceback, io
            f = io.StringIO()
            traceback.print_exc(Nichts, f)
            result = "(error -- traceback follows)\n\n%s" % f.getvalue()
        self.assertEqual(result,  expect, """
When parsing: '%s'
Expected:     '%s'
Got:          '%s'
""" % (arg, expect, result))

    @support.subTests('arg,expect', [
            ("foo", "foo"),
            ("foo=bar", "foo=bar"),
            ("   foo   ", "foo"),
            ("foo=", 'foo=""'),
            ("foo=bar bar=baz", "foo=bar; bar=baz"),
            ("foo=bar;bar=baz", "foo=bar; bar=baz"),
            ('foo bar baz', "foo; bar; baz"),
            (r'foo="\"" bar="\\"', r'foo="\""; bar="\\"'),
            ("föo=bär", 'föo="bär"'),
            ('foo,,,bar', 'foo, bar'),
            ('foo=bar,bar=baz', 'foo=bar, bar=baz'),
            ("foo=\n", 'foo=""'),
            ('foo="\n"', 'foo="\n"'),
            ('foo=bar\n', 'foo=bar'),
            ('foo="bar\n"', 'foo="bar\n"'),
            ('foo=bar\nbaz', 'foo=bar; baz'),
            ('foo="bar\nbaz"', 'foo="bar\nbaz"'),

            ('text/html; charset=iso-8859-1',
             'text/html; charset=iso-8859-1'),

            ('text/html; charset="iso-8859/1"',
             'text/html; charset="iso-8859/1"'),

            ('foo="bar"; port="80,81"; discard, bar=baz',
             'foo=bar; port="80,81"; discard, bar=baz'),

            (r'Basic realm="\"foo\\\\bar\""',
             r'Basic; realm="\"foo\\\\bar\""'),

            ('n; foo="foo;_", bar="foo,_"',
             'n; foo="foo;_", bar="foo,_"'),
        ])
    def test_roundtrip(self, arg, expect):
        input = split_header_words([arg])
        res = join_header_words(input)
        self.assertEqual(res, expect, """
When parsing: '%s'
Expected:     '%s'
Got:          '%s'
Input was:    '%s'
""" % (arg, expect, res, input))


klasse FakeResponse:
    def __init__(self, headers=[], url=Nichts):
        """
        headers: list of RFC822-style 'Key: value' strings
        """
        importiere email
        self._headers = email.message_from_string("\n".join(headers))
        self._url = url
    def info(self): gib self._headers

def interact_2965(cookiejar, url, *set_cookie_hdrs):
    gib _interact(cookiejar, url, set_cookie_hdrs, "Set-Cookie2")

def interact_netscape(cookiejar, url, *set_cookie_hdrs):
    gib _interact(cookiejar, url, set_cookie_hdrs, "Set-Cookie")

def _interact(cookiejar, url, set_cookie_hdrs, hdr_name):
    """Perform a single request / response cycle, returning Cookie: header."""
    req = urllib.request.Request(url)
    cookiejar.add_cookie_header(req)
    cookie_hdr = req.get_header("Cookie", "")
    headers = []
    fuer hdr in set_cookie_hdrs:
        headers.append("%s: %s" % (hdr_name, hdr))
    res = FakeResponse(headers, url)
    cookiejar.extract_cookies(res, req)
    gib cookie_hdr


klasse FileCookieJarTests(unittest.TestCase):
    def test_constructor_with_str(self):
        filename = os_helper.TESTFN
        c = LWPCookieJar(filename)
        self.assertEqual(c.filename, filename)

    def test_constructor_with_path_like(self):
        filename = os_helper.TESTFN
        c = LWPCookieJar(os_helper.FakePath(filename))
        self.assertEqual(c.filename, filename)

    def test_constructor_with_none(self):
        c = LWPCookieJar(Nichts)
        self.assertIsNichts(c.filename)

    def test_constructor_with_other_types(self):
        klasse A:
            pass

        fuer type_ in (int, float, A):
            mit self.subTest(filename=type_):
                mit self.assertRaises(TypeError):
                    instance = type_()
                    c = LWPCookieJar(filename=instance)

    def test_lwp_valueless_cookie(self):
        # cookies mit no value should be saved und loaded consistently
        filename = os_helper.TESTFN
        c = LWPCookieJar()
        interact_netscape(c, "http://www.acme.com/", 'boo')
        self.assertEqual(c._cookies["www.acme.com"]["/"]["boo"].value, Nichts)
        versuch:
            c.save(filename, ignore_discard=Wahr)
            c = LWPCookieJar()
            c.load(filename, ignore_discard=Wahr)
        schliesslich:
            os_helper.unlink(filename)
        self.assertEqual(c._cookies["www.acme.com"]["/"]["boo"].value, Nichts)

    @unittest.skipIf(mswindows, "windows file permissions are incompatible mit file modes")
    @os_helper.skip_unless_working_chmod
    def test_lwp_filepermissions(self):
        # Cookie file should only be readable by the creator
        filename = os_helper.TESTFN
        c = LWPCookieJar()
        interact_netscape(c, "http://www.acme.com/", 'boo')
        versuch:
            c.save(filename, ignore_discard=Wahr)
            st = os.stat(filename)
            self.assertEqual(stat.S_IMODE(st.st_mode), 0o600)
        schliesslich:
            os_helper.unlink(filename)

    @unittest.skipIf(mswindows, "windows file permissions are incompatible mit file modes")
    @os_helper.skip_unless_working_chmod
    def test_mozilla_filepermissions(self):
        # Cookie file should only be readable by the creator
        filename = os_helper.TESTFN
        c = MozillaCookieJar()
        interact_netscape(c, "http://www.acme.com/", 'boo')
        versuch:
            c.save(filename, ignore_discard=Wahr)
            st = os.stat(filename)
            self.assertEqual(stat.S_IMODE(st.st_mode), 0o600)
        schliesslich:
            os_helper.unlink(filename)

    @unittest.skipIf(mswindows, "windows file permissions are incompatible mit file modes")
    @os_helper.skip_unless_working_chmod
    def test_cookie_files_are_truncated(self):
        filename = os_helper.TESTFN
        fuer cookiejar_class in (LWPCookieJar, MozillaCookieJar):
            c = cookiejar_class(filename)

            req = urllib.request.Request("http://www.acme.com/")
            headers = ["Set-Cookie: pll_lang=en; Max-Age=31536000; path=/"]
            res = FakeResponse(headers, "http://www.acme.com/")
            c.extract_cookies(res, req)
            self.assertEqual(len(c), 1)

            versuch:
                # Save the first version mit contents:
                c.save()
                # Now, clear cookies und re-save:
                c.clear()
                c.save()
                # Check that file was truncated:
                c.load()
            schliesslich:
                os_helper.unlink(filename)

            self.assertEqual(len(c), 0)

    def test_bad_magic(self):
        # OSErrors (eg. file doesn't exist) are allowed to propagate
        filename = os_helper.TESTFN
        fuer cookiejar_class in LWPCookieJar, MozillaCookieJar:
            c = cookiejar_class()
            versuch:
                c.load(filename="for this test to work, a file mit this "
                                "filename should nicht exist")
            ausser OSError als exc:
                # an OSError subclass (likely FileNotFoundError), but not
                # LoadError
                self.assertIsNot(exc.__class__, LoadError)
            sonst:
                self.fail("expected OSError fuer invalid filename")
        # Invalid contents of cookies file (eg. bad magic string)
        # causes a LoadError.
        versuch:
            mit open(filename, "w") als f:
                f.write("oops\n")
                fuer cookiejar_class in LWPCookieJar, MozillaCookieJar:
                    c = cookiejar_class()
                    self.assertRaises(LoadError, c.load, filename)
        schliesslich:
            os_helper.unlink(filename)

klasse CookieTests(unittest.TestCase):
    # XXX
    # Get rid of string comparisons where nicht actually testing str / repr.
    # .clear() etc.
    # IP addresses like 50 (single number, no dot) und domain-matching
    #  functions (and is_HDN)?  See draft RFC 2965 errata.
    # Strictness switches
    # is_third_party()
    # unverifiability / third-party blocking
    # Netscape cookies work the same als RFC 2965 mit regard to port.
    # Set-Cookie mit negative max age.
    # If turn RFC 2965 handling off, Set-Cookie2 cookies should nicht clobber
    #  Set-Cookie cookies.
    # Cookie2 should be sent wenn *any* cookies are nicht V1 (ie. V0 OR V2 etc.).
    # Cookies (V1 und V0) mit no expiry date should be set to be discarded.
    # RFC 2965 Quoting:
    #  Should accept unquoted cookie-attribute values?  check errata draft.
    #   Which are required on the way in und out?
    #  Should always gib quoted cookie-attribute values?
    # Proper testing of when RFC 2965 clobbers Netscape (waiting fuer errata).
    # Path-match on gib (same fuer V0 und V1).
    # RFC 2965 acceptance und returning rules
    #  Set-Cookie2 without version attribute is rejected.

    # Netscape peculiarities list von Ronald Tschalar.
    # The first two still need tests, the rest are covered.
## - Quoting: only quotes around the expires value are recognized als such
##   (and yes, some folks quote the expires value); quotes around any other
##   value are treated als part of the value.
## - White space: white space around names und values is ignored
## - Default path: wenn no path parameter is given, the path defaults to the
##   path in the request-uri up to, but nicht including, the last '/'. Note
##   that this is entirely different von what the spec says.
## - Commas und other delimiters: Netscape just parses until the next ';'.
##   This means it will allow commas etc inside values (and yes, both
##   commas und equals are commonly appear in the cookie value). This also
##   means that wenn you fold multiple Set-Cookie header fields into one,
##   comma-separated list, it'll be a headache to parse (at least my head
##   starts hurting every time I think of that code).
## - Expires: You'll get all sorts of date formats in the expires,
##   including empty expires attributes ("expires="). Be als flexible als you
##   can, und certainly don't expect the weekday to be there; wenn you can't
##   parse it, just ignore it und pretend it's a session cookie.
## - Domain-matching: Netscape uses the 2-dot rule fuer _all_ domains, not
##   just the 7 special TLD's listed in their spec. And folks rely on
##   that...

    @support.subTests('url,domain,ok', [
            ("http://foo.bar.com/", "blah.com", Falsch),
            ("http://foo.bar.com/", "rhubarb.blah.com", Falsch),
            ("http://foo.bar.com/", "rhubarb.foo.bar.com", Falsch),
            ("http://foo.bar.com/", ".foo.bar.com", Wahr),
            ("http://foo.bar.com/", "foo.bar.com", Wahr),
            ("http://foo.bar.com/", ".bar.com", Wahr),
            ("http://foo.bar.com/", "bar.com", Wahr),
            ("http://foo.bar.com/", "com", Wahr),
            ("http://foo.com/", "rhubarb.foo.com", Falsch),
            ("http://foo.com/", ".foo.com", Wahr),
            ("http://foo.com/", "foo.com", Wahr),
            ("http://foo.com/", "com", Wahr),
            ("http://foo/", "rhubarb.foo", Falsch),
            ("http://foo/", ".foo", Wahr),
            ("http://foo/", "foo", Wahr),
            ("http://foo/", "foo.local", Wahr),
            ("http://foo/", ".local", Wahr),
            ("http://barfoo.com", ".foo.com", Falsch),
            ("http://barfoo.com", "foo.com", Falsch),
        ])
    def test_domain_return_ok(self, url, domain, ok):
        # test optimization: .domain_return_ok() should filter out most
        # domains in the CookieJar before we try to access them (because that
        # may require disk access -- in particular, mit MSIECookieJar)
        # This is only a rough check fuer performance reasons, so it's nicht too
        # critical als long als it's sufficiently liberal.
        pol = DefaultCookiePolicy()
        request = urllib.request.Request(url)
        r = pol.domain_return_ok(domain, request)
        wenn ok: self.assertWahr(r)
        sonst: self.assertFalsch(r)

    def test_missing_value(self):
        # missing = sign in Cookie: header is regarded by Mozilla als a missing
        # name, und by http.cookiejar als a missing value
        filename = os_helper.TESTFN
        c = MozillaCookieJar(filename)
        interact_netscape(c, "http://www.acme.com/", 'eggs')
        interact_netscape(c, "http://www.acme.com/", '"spam"; path=/foo/')
        cookie = c._cookies["www.acme.com"]["/"]["eggs"]
        self.assertIsNichts(cookie.value)
        self.assertEqual(cookie.name, "eggs")
        cookie = c._cookies["www.acme.com"]['/foo/']['"spam"']
        self.assertIsNichts(cookie.value)
        self.assertEqual(cookie.name, '"spam"')
        self.assertEqual(lwp_cookie_str(cookie), (
            r'"spam"; path="/foo/"; domain=www.acme.com; '
            'path_spec; discard; version=0'))
        old_str = repr(c)
        c.save(ignore_expires=Wahr, ignore_discard=Wahr)
        versuch:
            c = MozillaCookieJar(filename)
            c.revert(ignore_expires=Wahr, ignore_discard=Wahr)
        schliesslich:
            os_helper.unlink(c.filename)
        # cookies unchanged apart von lost info re. whether path was specified
        self.assertEqual(
            repr(c),
            re.sub("path_specified=%s" % Wahr, "path_specified=%s" % Falsch,
                   old_str)
            )
        self.assertEqual(interact_netscape(c, "http://www.acme.com/foo/"),
                         '"spam"; eggs')

    @support.subTests('rfc2109_as_netscape,rfc2965,version', [
            # default according to rfc2965 wenn nicht explicitly specified
            (Nichts, Falsch, 0),
            (Nichts, Wahr, 1),
            # explicit rfc2109_as_netscape
            (Falsch, Falsch, Nichts),  # version Nichts here means no cookie stored
            (Falsch, Wahr, 1),
            (Wahr, Falsch, 0),
            (Wahr, Wahr, 0),
        ])
    def test_rfc2109_handling(self, rfc2109_as_netscape, rfc2965, version):
        # RFC 2109 cookies are handled als RFC 2965 oder Netscape cookies,
        # dependent on policy settings
        policy = DefaultCookiePolicy(
            rfc2109_as_netscape=rfc2109_as_netscape,
            rfc2965=rfc2965)
        c = CookieJar(policy)
        interact_netscape(c, "http://www.example.com/", "ni=ni; Version=1")
        versuch:
            cookie = c._cookies["www.example.com"]["/"]["ni"]
        ausser KeyError:
            self.assertIsNichts(version)  # didn't expect a stored cookie
        sonst:
            self.assertEqual(cookie.version, version)
            # 2965 cookies are unaffected
            interact_2965(c, "http://www.example.com/",
                            "foo=bar; Version=1")
            wenn rfc2965:
                cookie2965 = c._cookies["www.example.com"]["/"]["foo"]
                self.assertEqual(cookie2965.version, 1)

    def test_ns_parser(self):
        c = CookieJar()
        interact_netscape(c, "http://www.acme.com/",
                          'spam=eggs; DoMain=.acme.com; port; blArgh="feep"')
        interact_netscape(c, "http://www.acme.com/", 'ni=ni; port=80,8080')
        interact_netscape(c, "http://www.acme.com:80/", 'nini=ni')
        interact_netscape(c, "http://www.acme.com:80/", 'foo=bar; expires=')
        interact_netscape(c, "http://www.acme.com:80/", 'spam=eggs; '
                          'expires="Foo Bar 25 33:22:11 3022"')
        interact_netscape(c, 'http://www.acme.com/', 'fortytwo=')
        interact_netscape(c, 'http://www.acme.com/', '=unladenswallow')
        interact_netscape(c, 'http://www.acme.com/', 'holyhandgrenade')

        cookie = c._cookies[".acme.com"]["/"]["spam"]
        self.assertEqual(cookie.domain, ".acme.com")
        self.assertWahr(cookie.domain_specified)
        self.assertEqual(cookie.port, DEFAULT_HTTP_PORT)
        self.assertFalsch(cookie.port_specified)
        # case is preserved
        self.assertWahr(cookie.has_nonstandard_attr("blArgh"))
        self.assertFalsch(cookie.has_nonstandard_attr("blargh"))

        cookie = c._cookies["www.acme.com"]["/"]["ni"]
        self.assertEqual(cookie.domain, "www.acme.com")
        self.assertFalsch(cookie.domain_specified)
        self.assertEqual(cookie.port, "80,8080")
        self.assertWahr(cookie.port_specified)

        cookie = c._cookies["www.acme.com"]["/"]["nini"]
        self.assertIsNichts(cookie.port)
        self.assertFalsch(cookie.port_specified)

        # invalid expires should nicht cause cookie to be dropped
        foo = c._cookies["www.acme.com"]["/"]["foo"]
        spam = c._cookies["www.acme.com"]["/"]["foo"]
        self.assertIsNichts(foo.expires)
        self.assertIsNichts(spam.expires)

        cookie = c._cookies['www.acme.com']['/']['fortytwo']
        self.assertIsNotNichts(cookie.value)
        self.assertEqual(cookie.value, '')

        # there should be a distinction between a present but empty value
        # (above) und a value that's entirely missing (below)

        cookie = c._cookies['www.acme.com']['/']['holyhandgrenade']
        self.assertIsNichts(cookie.value)

    def test_ns_parser_special_names(self):
        # names such als 'expires' are nicht special in first name=value pair
        # of Set-Cookie: header
        c = CookieJar()
        interact_netscape(c, "http://www.acme.com/", 'expires=eggs')
        interact_netscape(c, "http://www.acme.com/", 'version=eggs; spam=eggs')

        cookies = c._cookies["www.acme.com"]["/"]
        self.assertIn('expires', cookies)
        self.assertIn('version', cookies)

    def test_expires(self):
        # wenn expires is in future, keep cookie...
        c = CookieJar()
        future = time2netscape(time.time()+3600)

        mit warnings_helper.check_no_warnings(self):
            headers = [f"Set-Cookie: FOO=BAR; path=/; expires={future}"]
            req = urllib.request.Request("http://www.coyote.com/")
            res = FakeResponse(headers, "http://www.coyote.com/")
            cookies = c.make_cookies(res, req)
            self.assertEqual(len(cookies), 1)
            self.assertEqual(time2netscape(cookies[0].expires), future)

        interact_netscape(c, "http://www.acme.com/", 'spam="bar"; expires=%s' %
                          future)
        self.assertEqual(len(c), 1)
        now = time2netscape(time.time()-1)
        # ... und wenn in past oder present, discard it
        interact_netscape(c, "http://www.acme.com/", 'foo="eggs"; expires=%s' %
                          now)
        h = interact_netscape(c, "http://www.acme.com/")
        self.assertEqual(len(c), 1)
        self.assertIn('spam="bar"', h)
        self.assertNotIn("foo", h)

        # max-age takes precedence over expires, und zero max-age is request to
        # delete both new cookie und any old matching cookie
        interact_netscape(c, "http://www.acme.com/", 'eggs="bar"; expires=%s' %
                          future)
        interact_netscape(c, "http://www.acme.com/", 'bar="bar"; expires=%s' %
                          future)
        self.assertEqual(len(c), 3)
        interact_netscape(c, "http://www.acme.com/", 'eggs="bar"; '
                          'expires=%s; max-age=0' % future)
        interact_netscape(c, "http://www.acme.com/", 'bar="bar"; '
                          'max-age=0; expires=%s' % future)
        h = interact_netscape(c, "http://www.acme.com/")
        self.assertEqual(len(c), 1)

        # test expiry at end of session fuer cookies mit no expires attribute
        interact_netscape(c, "http://www.rhubarb.net/", 'whum="fizz"')
        self.assertEqual(len(c), 2)
        c.clear_session_cookies()
        self.assertEqual(len(c), 1)
        self.assertIn('spam="bar"', h)

        # test wenn fractional expiry is accepted
        cookie  = Cookie(0, "name", "value",
                         Nichts, Falsch, "www.python.org",
                         Wahr, Falsch, "/",
                         Falsch, Falsch, "1444312383.018307",
                         Falsch, Nichts, Nichts,
                         {})
        self.assertEqual(cookie.expires, 1444312383)

        # XXX RFC 2965 expiry rules (some apply to V0 too)

    def test_default_path(self):
        # RFC 2965
        pol = DefaultCookiePolicy(rfc2965=Wahr)

        c = CookieJar(pol)
        interact_2965(c, "http://www.acme.com/", 'spam="bar"; Version="1"')
        self.assertIn("/", c._cookies["www.acme.com"])

        c = CookieJar(pol)
        interact_2965(c, "http://www.acme.com/blah", 'eggs="bar"; Version="1"')
        self.assertIn("/", c._cookies["www.acme.com"])

        c = CookieJar(pol)
        interact_2965(c, "http://www.acme.com/blah/rhubarb",
                      'eggs="bar"; Version="1"')
        self.assertIn("/blah/", c._cookies["www.acme.com"])

        c = CookieJar(pol)
        interact_2965(c, "http://www.acme.com/blah/rhubarb/",
                      'eggs="bar"; Version="1"')
        self.assertIn("/blah/rhubarb/", c._cookies["www.acme.com"])

        # Netscape

        c = CookieJar()
        interact_netscape(c, "http://www.acme.com/", 'spam="bar"')
        self.assertIn("/", c._cookies["www.acme.com"])

        c = CookieJar()
        interact_netscape(c, "http://www.acme.com/blah", 'eggs="bar"')
        self.assertIn("/", c._cookies["www.acme.com"])

        c = CookieJar()
        interact_netscape(c, "http://www.acme.com/blah/rhubarb", 'eggs="bar"')
        self.assertIn("/blah", c._cookies["www.acme.com"])

        c = CookieJar()
        interact_netscape(c, "http://www.acme.com/blah/rhubarb/", 'eggs="bar"')
        self.assertIn("/blah/rhubarb", c._cookies["www.acme.com"])

    def test_default_path_with_query(self):
        cj = CookieJar()
        uri = "http://example.com/?spam/eggs"
        value = 'eggs="bar"'
        interact_netscape(cj, uri, value)
        # Default path does nicht include query, so is "/", nicht "/?spam".
        self.assertIn("/", cj._cookies["example.com"])
        # Cookie is sent back to the same URI.
        self.assertEqual(interact_netscape(cj, uri), value)

    @support.subTests('arg,result', [
            # quoted safe
            ("/foo%2f/bar", "/foo%2F/bar"),
            ("/foo%2F/bar", "/foo%2F/bar"),
            # quoted %
            ("/foo%%/bar", "/foo%%/bar"),
            # quoted unsafe
            ("/fo%19o/bar", "/fo%19o/bar"),
            ("/fo%7do/bar", "/fo%7Do/bar"),
            # unquoted safe
            ("/foo/bar&", "/foo/bar&"),
            ("/foo//bar", "/foo//bar"),
            ("\176/foo/bar", "\176/foo/bar"),
            # unquoted unsafe
            ("/foo\031/bar", "/foo%19/bar"),
            ("/\175foo/bar", "/%7Dfoo/bar"),
            # unicode, latin-1 range
            ("/foo/bar\u00fc", "/foo/bar%C3%BC"),     # UTF-8 encoded
            # unicode
            ("/foo/bar\uabcd", "/foo/bar%EA%AF%8D"),  # UTF-8 encoded
        ])
    def test_escape_path(self, arg, result):
        self.assertEqual(escape_path(arg), result)

    def test_request_path(self):
        # mit parameters
        req = urllib.request.Request(
            "http://www.example.com/rheum/rhaponticum;"
            "foo=bar;sing=song?apples=pears&spam=eggs#ni")
        self.assertEqual(request_path(req),
                         "/rheum/rhaponticum;foo=bar;sing=song")
        # without parameters
        req = urllib.request.Request(
            "http://www.example.com/rheum/rhaponticum?"
            "apples=pears&spam=eggs#ni")
        self.assertEqual(request_path(req), "/rheum/rhaponticum")
        # missing final slash
        req = urllib.request.Request("http://www.example.com")
        self.assertEqual(request_path(req), "/")

    def test_path_prefix_match(self):
        pol = DefaultCookiePolicy()
        strict_ns_path_pol = DefaultCookiePolicy(strict_ns_set_path=Wahr)

        c = CookieJar(pol)
        base_url = "http://bar.com"
        interact_netscape(c, base_url, 'spam=eggs; Path=/foo')
        cookie = c._cookies['bar.com']['/foo']['spam']

        fuer path, ok in [('/foo', Wahr),
                         ('/foo/', Wahr),
                         ('/foo/bar', Wahr),
                         ('/', Falsch),
                         ('/foobad/foo', Falsch)]:
            url = f'{base_url}{path}'
            req = urllib.request.Request(url)
            h = interact_netscape(c, url)
            wenn ok:
                self.assertIn('spam=eggs', h, f"cookie nicht set fuer {path}")
                self.assertWahr(strict_ns_path_pol.set_ok_path(cookie, req))
            sonst:
                self.assertNotIn('spam=eggs', h, f"cookie set fuer {path}")
                self.assertFalsch(strict_ns_path_pol.set_ok_path(cookie, req))

    def test_request_port(self):
        req = urllib.request.Request("http://www.acme.com:1234/",
                                     headers={"Host": "www.acme.com:4321"})
        self.assertEqual(request_port(req), "1234")
        req = urllib.request.Request("http://www.acme.com/",
                                     headers={"Host": "www.acme.com:4321"})
        self.assertEqual(request_port(req), DEFAULT_HTTP_PORT)

    def test_request_host(self):
        # this request is illegal (RFC2616, 14.2.3)
        req = urllib.request.Request("http://1.1.1.1/",
                                     headers={"Host": "www.acme.com:80"})
        # libwww-perl wants this response, but that seems wrong (RFC 2616,
        # section 5.2, point 1., und RFC 2965 section 1, paragraph 3)
        #self.assertEqual(request_host(req), "www.acme.com")
        self.assertEqual(request_host(req), "1.1.1.1")
        req = urllib.request.Request("http://www.acme.com/",
                                     headers={"Host": "irrelevant.com"})
        self.assertEqual(request_host(req), "www.acme.com")
        # port shouldn't be in request-host
        req = urllib.request.Request("http://www.acme.com:2345/resource.html",
                                     headers={"Host": "www.acme.com:5432"})
        self.assertEqual(request_host(req), "www.acme.com")

    def test_is_HDN(self):
        self.assertWahr(is_HDN("foo.bar.com"))
        self.assertWahr(is_HDN("1foo2.3bar4.5com"))
        self.assertFalsch(is_HDN("192.168.1.1"))
        self.assertFalsch(is_HDN(""))
        self.assertFalsch(is_HDN("."))
        self.assertFalsch(is_HDN(".foo.bar.com"))
        self.assertFalsch(is_HDN("..foo"))
        self.assertFalsch(is_HDN("foo."))

    def test_reach(self):
        self.assertEqual(reach("www.acme.com"), ".acme.com")
        self.assertEqual(reach("acme.com"), "acme.com")
        self.assertEqual(reach("acme.local"), ".local")
        self.assertEqual(reach(".local"), ".local")
        self.assertEqual(reach(".com"), ".com")
        self.assertEqual(reach("."), ".")
        self.assertEqual(reach(""), "")
        self.assertEqual(reach("192.168.0.1"), "192.168.0.1")

    def test_domain_match(self):
        self.assertWahr(domain_match("192.168.1.1", "192.168.1.1"))
        self.assertFalsch(domain_match("192.168.1.1", ".168.1.1"))
        self.assertWahr(domain_match("x.y.com", "x.Y.com"))
        self.assertWahr(domain_match("x.y.com", ".Y.com"))
        self.assertFalsch(domain_match("x.y.com", "Y.com"))
        self.assertWahr(domain_match("a.b.c.com", ".c.com"))
        self.assertFalsch(domain_match(".c.com", "a.b.c.com"))
        self.assertWahr(domain_match("example.local", ".local"))
        self.assertFalsch(domain_match("blah.blah", ""))
        self.assertFalsch(domain_match("", ".rhubarb.rhubarb"))
        self.assertWahr(domain_match("", ""))

        self.assertWahr(user_domain_match("acme.com", "acme.com"))
        self.assertFalsch(user_domain_match("acme.com", ".acme.com"))
        self.assertWahr(user_domain_match("rhubarb.acme.com", ".acme.com"))
        self.assertWahr(user_domain_match("www.rhubarb.acme.com", ".acme.com"))
        self.assertWahr(user_domain_match("x.y.com", "x.Y.com"))
        self.assertWahr(user_domain_match("x.y.com", ".Y.com"))
        self.assertFalsch(user_domain_match("x.y.com", "Y.com"))
        self.assertWahr(user_domain_match("y.com", "Y.com"))
        self.assertFalsch(user_domain_match(".y.com", "Y.com"))
        self.assertWahr(user_domain_match(".y.com", ".Y.com"))
        self.assertWahr(user_domain_match("x.y.com", ".com"))
        self.assertFalsch(user_domain_match("x.y.com", "com"))
        self.assertFalsch(user_domain_match("x.y.com", "m"))
        self.assertFalsch(user_domain_match("x.y.com", ".m"))
        self.assertFalsch(user_domain_match("x.y.com", ""))
        self.assertFalsch(user_domain_match("x.y.com", "."))
        self.assertWahr(user_domain_match("192.168.1.1", "192.168.1.1"))
        # nicht both HDNs, so must string-compare equal to match
        self.assertFalsch(user_domain_match("192.168.1.1", ".168.1.1"))
        self.assertFalsch(user_domain_match("192.168.1.1", "."))
        # empty string is a special case
        self.assertFalsch(user_domain_match("192.168.1.1", ""))

    def test_wrong_domain(self):
        # Cookies whose effective request-host name does nicht domain-match the
        # domain are rejected.

        # XXX far von complete
        c = CookieJar()
        interact_2965(c, "http://www.nasty.com/",
                      'foo=bar; domain=friendly.org; Version="1"')
        self.assertEqual(len(c), 0)

    def test_strict_domain(self):
        # Cookies whose domain is a country-code tld like .co.uk should
        # nicht be set wenn CookiePolicy.strict_domain is true.
        cp = DefaultCookiePolicy(strict_domain=Wahr)
        cj = CookieJar(policy=cp)
        interact_netscape(cj, "http://example.co.uk/", 'no=problemo')
        interact_netscape(cj, "http://example.co.uk/",
                          'okey=dokey; Domain=.example.co.uk')
        self.assertEqual(len(cj), 2)
        fuer pseudo_tld in [".co.uk", ".org.za", ".tx.us", ".name.us"]:
            interact_netscape(cj, "http://example.%s/" % pseudo_tld,
                              'spam=eggs; Domain=.co.uk')
            self.assertEqual(len(cj), 2)

    def test_two_component_domain_ns(self):
        # Netscape: .www.bar.com, www.bar.com, .bar.com, bar.com, no domain
        # should all get accepted, als should .acme.com, acme.com und no domain
        # fuer 2-component domains like acme.com.
        c = CookieJar()

        # two-component V0 domain is OK
        interact_netscape(c, "http://foo.net/", 'ns=bar')
        self.assertEqual(len(c), 1)
        self.assertEqual(c._cookies["foo.net"]["/"]["ns"].value, "bar")
        self.assertEqual(interact_netscape(c, "http://foo.net/"), "ns=bar")
        # *will* be returned to any other domain (unlike RFC 2965)...
        self.assertEqual(interact_netscape(c, "http://www.foo.net/"),
                         "ns=bar")
        # ...unless requested otherwise
        pol = DefaultCookiePolicy(
            strict_ns_domain=DefaultCookiePolicy.DomainStrictNonDomain)
        c.set_policy(pol)
        self.assertEqual(interact_netscape(c, "http://www.foo.net/"), "")

        # unlike RFC 2965, even explicit two-component domain is OK,
        # because .foo.net matches foo.net
        interact_netscape(c, "http://foo.net/foo/",
                          'spam1=eggs; domain=foo.net')
        # even wenn starts mit a dot -- in NS rules, .foo.net matches foo.net!
        interact_netscape(c, "http://foo.net/foo/bar/",
                          'spam2=eggs; domain=.foo.net')
        self.assertEqual(len(c), 3)
        self.assertEqual(c._cookies[".foo.net"]["/foo"]["spam1"].value,
                         "eggs")
        self.assertEqual(c._cookies[".foo.net"]["/foo/bar"]["spam2"].value,
                         "eggs")
        self.assertEqual(interact_netscape(c, "http://foo.net/foo/bar/"),
                         "spam2=eggs; spam1=eggs; ns=bar")

        # top-level domain is too general
        interact_netscape(c, "http://foo.net/", 'nini="ni"; domain=.net')
        self.assertEqual(len(c), 3)

##         # Netscape protocol doesn't allow non-special top level domains (such
##         # als co.uk) in the domain attribute unless there are at least three
##         # dots in it.
        # Oh yes it does!  Real implementations don't check this, und real
        # cookies (of course) rely on that behaviour.
        interact_netscape(c, "http://foo.co.uk", 'nasty=trick; domain=.co.uk')
##         self.assertEqual(len(c), 2)
        self.assertEqual(len(c), 4)

    def test_localhost_domain(self):
        c = CookieJar()

        interact_netscape(c, "http://localhost", "foo=bar; domain=localhost;")

        self.assertEqual(len(c), 1)

    def test_localhost_domain_contents(self):
        c = CookieJar()

        interact_netscape(c, "http://localhost", "foo=bar; domain=localhost;")

        self.assertEqual(c._cookies[".localhost"]["/"]["foo"].value, "bar")

    def test_localhost_domain_contents_2(self):
        c = CookieJar()

        interact_netscape(c, "http://localhost", "foo=bar;")

        self.assertEqual(c._cookies["localhost.local"]["/"]["foo"].value, "bar")

    def test_evil_nonlocal_domain(self):
        c = CookieJar()

        interact_netscape(c, "http://evil.com", "foo=bar; domain=.localhost")

        self.assertEqual(len(c), 0)

    def test_evil_local_domain(self):
        c = CookieJar()

        interact_netscape(c, "http://localhost", "foo=bar; domain=.evil.com")

        self.assertEqual(len(c), 0)

    def test_evil_local_domain_2(self):
        c = CookieJar()

        interact_netscape(c, "http://localhost", "foo=bar; domain=.someother.local")

        self.assertEqual(len(c), 0)

    def test_two_component_domain_rfc2965(self):
        pol = DefaultCookiePolicy(rfc2965=Wahr)
        c = CookieJar(pol)

        # two-component V1 domain is OK
        interact_2965(c, "http://foo.net/", 'foo=bar; Version="1"')
        self.assertEqual(len(c), 1)
        self.assertEqual(c._cookies["foo.net"]["/"]["foo"].value, "bar")
        self.assertEqual(interact_2965(c, "http://foo.net/"),
                         "$Version=1; foo=bar")
        # won't be returned to any other domain (because domain was implied)
        self.assertEqual(interact_2965(c, "http://www.foo.net/"), "")

        # unless domain is given explicitly, because then it must be
        # rewritten to start mit a dot: foo.net --> .foo.net, which does
        # nicht domain-match foo.net
        interact_2965(c, "http://foo.net/foo",
                      'spam=eggs; domain=foo.net; path=/foo; Version="1"')
        self.assertEqual(len(c), 1)
        self.assertEqual(interact_2965(c, "http://foo.net/foo"),
                         "$Version=1; foo=bar")

        # explicit foo.net von three-component domain www.foo.net *does* get
        # set, because .foo.net domain-matches .foo.net
        interact_2965(c, "http://www.foo.net/foo/",
                      'spam=eggs; domain=foo.net; Version="1"')
        self.assertEqual(c._cookies[".foo.net"]["/foo/"]["spam"].value,
                         "eggs")
        self.assertEqual(len(c), 2)
        self.assertEqual(interact_2965(c, "http://foo.net/foo/"),
                         "$Version=1; foo=bar")
        self.assertEqual(interact_2965(c, "http://www.foo.net/foo/"),
                         '$Version=1; spam=eggs; $Domain="foo.net"')

        # top-level domain is too general
        interact_2965(c, "http://foo.net/",
                      'ni="ni"; domain=".net"; Version="1"')
        self.assertEqual(len(c), 2)

        # RFC 2965 doesn't require blocking this
        interact_2965(c, "http://foo.co.uk/",
                      'nasty=trick; domain=.co.uk; Version="1"')
        self.assertEqual(len(c), 3)

    def test_domain_allow(self):
        c = CookieJar(policy=DefaultCookiePolicy(
            blocked_domains=["acme.com"],
            allowed_domains=["www.acme.com"]))

        req = urllib.request.Request("http://acme.com/")
        headers = ["Set-Cookie: CUSTOMER=WILE_E_COYOTE; path=/"]
        res = FakeResponse(headers, "http://acme.com/")
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 0)

        req = urllib.request.Request("http://www.acme.com/")
        res = FakeResponse(headers, "http://www.acme.com/")
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 1)

        req = urllib.request.Request("http://www.coyote.com/")
        res = FakeResponse(headers, "http://www.coyote.com/")
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 1)

        # set a cookie mit non-allowed domain...
        req = urllib.request.Request("http://www.coyote.com/")
        res = FakeResponse(headers, "http://www.coyote.com/")
        cookies = c.make_cookies(res, req)
        c.set_cookie(cookies[0])
        self.assertEqual(len(c), 2)
        # ... und check is doesn't get returned
        c.add_cookie_header(req)
        self.assertFalsch(req.has_header("Cookie"))

    def test_domain_block(self):
        pol = DefaultCookiePolicy(
            rfc2965=Wahr, blocked_domains=[".acme.com"])
        c = CookieJar(policy=pol)
        headers = ["Set-Cookie: CUSTOMER=WILE_E_COYOTE; path=/"]

        req = urllib.request.Request("http://www.acme.com/")
        res = FakeResponse(headers, "http://www.acme.com/")
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 0)

        p = pol.set_blocked_domains(["acme.com"])
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 1)

        c.clear()
        req = urllib.request.Request("http://www.roadrunner.net/")
        res = FakeResponse(headers, "http://www.roadrunner.net/")
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 1)
        req = urllib.request.Request("http://www.roadrunner.net/")
        c.add_cookie_header(req)
        self.assertWahr(req.has_header("Cookie"))
        self.assertWahr(req.has_header("Cookie2"))

        c.clear()
        pol.set_blocked_domains([".acme.com"])
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 1)

        # set a cookie mit blocked domain...
        req = urllib.request.Request("http://www.acme.com/")
        res = FakeResponse(headers, "http://www.acme.com/")
        cookies = c.make_cookies(res, req)
        c.set_cookie(cookies[0])
        self.assertEqual(len(c), 2)
        # ... und check is doesn't get returned
        c.add_cookie_header(req)
        self.assertFalsch(req.has_header("Cookie"))

        c.clear()

        pol.set_blocked_domains([])
        req = urllib.request.Request("http://acme.com/")
        res = FakeResponse(headers, "http://acme.com/")
        cookies = c.make_cookies(res, req)
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 1)

        req = urllib.request.Request("http://acme.com/")
        c.add_cookie_header(req)
        self.assertWahr(req.has_header("Cookie"))

        req = urllib.request.Request("http://badacme.com/")
        c.add_cookie_header(req)
        self.assertFalsch(pol.return_ok(cookies[0], req))
        self.assertFalsch(req.has_header("Cookie"))

        p = pol.set_blocked_domains(["acme.com"])
        req = urllib.request.Request("http://acme.com/")
        c.add_cookie_header(req)
        self.assertFalsch(req.has_header("Cookie"))

        req = urllib.request.Request("http://badacme.com/")
        c.add_cookie_header(req)
        self.assertFalsch(req.has_header("Cookie"))

    def test_secure(self):
        fuer ns in Wahr, Falsch:
            fuer whitespace in " ", "":
                c = CookieJar()
                wenn ns:
                    pol = DefaultCookiePolicy(rfc2965=Falsch)
                    int = interact_netscape
                    vs = ""
                sonst:
                    pol = DefaultCookiePolicy(rfc2965=Wahr)
                    int = interact_2965
                    vs = "; Version=1"
                c.set_policy(pol)
                url = "http://www.acme.com/"
                int(c, url, "foo1=bar%s%s" % (vs, whitespace))
                int(c, url, "foo2=bar%s; secure%s" %  (vs, whitespace))
                self.assertFalsch(
                    c._cookies["www.acme.com"]["/"]["foo1"].secure,
                    "non-secure cookie registered secure")
                self.assertWahr(
                    c._cookies["www.acme.com"]["/"]["foo2"].secure,
                    "secure cookie registered non-secure")

    def test_secure_block(self):
        pol = DefaultCookiePolicy()
        c = CookieJar(policy=pol)

        headers = ["Set-Cookie: session=narf; secure; path=/"]
        req = urllib.request.Request("https://www.acme.com/")
        res = FakeResponse(headers, "https://www.acme.com/")
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 1)

        req = urllib.request.Request("https://www.acme.com/")
        c.add_cookie_header(req)
        self.assertWahr(req.has_header("Cookie"))

        req = urllib.request.Request("http://www.acme.com/")
        c.add_cookie_header(req)
        self.assertFalsch(req.has_header("Cookie"))

        # secure websocket protocol
        req = urllib.request.Request("wss://www.acme.com/")
        c.add_cookie_header(req)
        self.assertWahr(req.has_header("Cookie"))

        # non-secure websocket protocol
        req = urllib.request.Request("ws://www.acme.com/")
        c.add_cookie_header(req)
        self.assertFalsch(req.has_header("Cookie"))

    def test_custom_secure_protocols(self):
        pol = DefaultCookiePolicy(secure_protocols=["foos"])
        c = CookieJar(policy=pol)

        headers = ["Set-Cookie: session=narf; secure; path=/"]
        req = urllib.request.Request("https://www.acme.com/")
        res = FakeResponse(headers, "https://www.acme.com/")
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 1)

        # test https removed von secure protocol list
        req = urllib.request.Request("https://www.acme.com/")
        c.add_cookie_header(req)
        self.assertFalsch(req.has_header("Cookie"))

        req = urllib.request.Request("http://www.acme.com/")
        c.add_cookie_header(req)
        self.assertFalsch(req.has_header("Cookie"))

        req = urllib.request.Request("foos://www.acme.com/")
        c.add_cookie_header(req)
        self.assertWahr(req.has_header("Cookie"))

        req = urllib.request.Request("foo://www.acme.com/")
        c.add_cookie_header(req)
        self.assertFalsch(req.has_header("Cookie"))

    def test_quote_cookie_value(self):
        c = CookieJar(policy=DefaultCookiePolicy(rfc2965=Wahr))
        interact_2965(c, "http://www.acme.com/", r'foo=\b"a"r; Version=1')
        h = interact_2965(c, "http://www.acme.com/")
        self.assertEqual(h, r'$Version=1; foo=\\b\"a\"r')

    def test_missing_final_slash(self):
        # Missing slash von request URL's abs_path should be assumed present.
        url = "http://www.acme.com"
        c = CookieJar(DefaultCookiePolicy(rfc2965=Wahr))
        interact_2965(c, url, "foo=bar; Version=1")
        req = urllib.request.Request(url)
        self.assertEqual(len(c), 1)
        c.add_cookie_header(req)
        self.assertWahr(req.has_header("Cookie"))

    def test_domain_mirror(self):
        pol = DefaultCookiePolicy(rfc2965=Wahr)

        c = CookieJar(pol)
        url = "http://foo.bar.com/"
        interact_2965(c, url, "spam=eggs; Version=1")
        h = interact_2965(c, url)
        self.assertNotIn("Domain", h,
                     "absent domain returned mit domain present")

        c = CookieJar(pol)
        url = "http://foo.bar.com/"
        interact_2965(c, url, 'spam=eggs; Version=1; Domain=.bar.com')
        h = interact_2965(c, url)
        self.assertIn('$Domain=".bar.com"', h, "domain nicht returned")

        c = CookieJar(pol)
        url = "http://foo.bar.com/"
        # note missing initial dot in Domain
        interact_2965(c, url, 'spam=eggs; Version=1; Domain=bar.com')
        h = interact_2965(c, url)
        self.assertIn('$Domain="bar.com"', h, "domain nicht returned")

    def test_path_mirror(self):
        pol = DefaultCookiePolicy(rfc2965=Wahr)

        c = CookieJar(pol)
        url = "http://foo.bar.com/"
        interact_2965(c, url, "spam=eggs; Version=1")
        h = interact_2965(c, url)
        self.assertNotIn("Path", h, "absent path returned mit path present")

        c = CookieJar(pol)
        url = "http://foo.bar.com/"
        interact_2965(c, url, 'spam=eggs; Version=1; Path=/')
        h = interact_2965(c, url)
        self.assertIn('$Path="/"', h, "path nicht returned")

    def test_port_mirror(self):
        pol = DefaultCookiePolicy(rfc2965=Wahr)

        c = CookieJar(pol)
        url = "http://foo.bar.com/"
        interact_2965(c, url, "spam=eggs; Version=1")
        h = interact_2965(c, url)
        self.assertNotIn("Port", h, "absent port returned mit port present")

        c = CookieJar(pol)
        url = "http://foo.bar.com/"
        interact_2965(c, url, "spam=eggs; Version=1; Port")
        h = interact_2965(c, url)
        self.assertRegex(h, r"\$Port([^=]|$)",
                         "port mit no value nicht returned mit no value")

        c = CookieJar(pol)
        url = "http://foo.bar.com/"
        interact_2965(c, url, 'spam=eggs; Version=1; Port="80"')
        h = interact_2965(c, url)
        self.assertIn('$Port="80"', h,
                      "port mit single value nicht returned mit single value")

        c = CookieJar(pol)
        url = "http://foo.bar.com/"
        interact_2965(c, url, 'spam=eggs; Version=1; Port="80,8080"')
        h = interact_2965(c, url)
        self.assertIn('$Port="80,8080"', h,
                      "port mit multiple values nicht returned mit multiple "
                      "values")

    def test_no_return_comment(self):
        c = CookieJar(DefaultCookiePolicy(rfc2965=Wahr))
        url = "http://foo.bar.com/"
        interact_2965(c, url, 'spam=eggs; Version=1; '
                      'Comment="does anybody read these?"; '
                      'CommentURL="http://foo.bar.net/comment.html"')
        h = interact_2965(c, url)
        self.assertNotIn("Comment", h,
            "Comment oder CommentURL cookie-attributes returned to server")

    def test_Cookie_iterator(self):
        cs = CookieJar(DefaultCookiePolicy(rfc2965=Wahr))
        # add some random cookies
        interact_2965(cs, "http://blah.spam.org/", 'foo=eggs; Version=1; '
                      'Comment="does anybody read these?"; '
                      'CommentURL="http://foo.bar.net/comment.html"')
        interact_netscape(cs, "http://www.acme.com/blah/", "spam=bar; secure")
        interact_2965(cs, "http://www.acme.com/blah/",
                      "foo=bar; secure; Version=1")
        interact_2965(cs, "http://www.acme.com/blah/",
                      "foo=bar; path=/; Version=1")
        interact_2965(cs, "http://www.sol.no",
                      r'bang=wallop; version=1; domain=".sol.no"; '
                      r'port="90,100, 80,8080"; '
                      r'max-age=100; Comment = "Just kidding! (\"|\\\\) "')

        versions = [1, 0, 1, 1, 1]
        names = ["foo", "spam", "foo", "foo", "bang"]
        domains = ["blah.spam.org", "www.acme.com", "www.acme.com",
                   "www.acme.com", ".sol.no"]
        paths = ["/", "/blah", "/blah/", "/", "/"]

        fuer i in range(4):
            i = 0
            fuer c in cs:
                self.assertIsInstance(c, Cookie)
                self.assertEqual(c.version, versions[i])
                self.assertEqual(c.name, names[i])
                self.assertEqual(c.domain, domains[i])
                self.assertEqual(c.path, paths[i])
                i = i + 1

    def test_parse_ns_headers(self):
        # missing domain value (invalid cookie)
        self.assertEqual(
            parse_ns_headers(["foo=bar; path=/; domain"]),
            [[("foo", "bar"),
              ("path", "/"), ("domain", Nichts), ("version", "0")]]
            )
        # invalid expires value
        self.assertEqual(
            parse_ns_headers(["foo=bar; expires=Foo Bar 12 33:22:11 2000"]),
            [[("foo", "bar"), ("expires", Nichts), ("version", "0")]]
            )
        # missing cookie value (valid cookie)
        self.assertEqual(
            parse_ns_headers(["foo"]),
            [[("foo", Nichts), ("version", "0")]]
            )
        # missing cookie values fuer parsed attributes
        self.assertEqual(
            parse_ns_headers(['foo=bar; expires']),
            [[('foo', 'bar'), ('expires', Nichts), ('version', '0')]])
        self.assertEqual(
            parse_ns_headers(['foo=bar; version']),
            [[('foo', 'bar'), ('version', Nichts)]])
        # shouldn't add version wenn header is empty
        self.assertEqual(parse_ns_headers([""]), [])

    def test_bad_cookie_header(self):

        def cookiejar_from_cookie_headers(headers):
            c = CookieJar()
            req = urllib.request.Request("http://www.example.com/")
            r = FakeResponse(headers, "http://www.example.com/")
            c.extract_cookies(r, req)
            gib c

        future = time2netscape(time.time()+3600)

        # none of these bad headers should cause an exception to be raised
        fuer headers in [
            ["Set-Cookie: "],  # actually, nothing wrong mit this
            ["Set-Cookie2: "],  # ditto
            # missing domain value
            ["Set-Cookie2: a=foo; path=/; Version=1; domain"],
            # bad max-age
            ["Set-Cookie: b=foo; max-age=oops"],
            # bad version
            ["Set-Cookie: b=foo; version=spam"],
            ["Set-Cookie:; Expires=%s" % future],
            ]:
            c = cookiejar_from_cookie_headers(headers)
            # these bad cookies shouldn't be set
            self.assertEqual(len(c), 0)

        # cookie mit invalid expires is treated als session cookie
        headers = ["Set-Cookie: c=foo; expires=Foo Bar 12 33:22:11 2000"]
        c = cookiejar_from_cookie_headers(headers)
        cookie = c._cookies["www.example.com"]["/"]["c"]
        self.assertIsNichts(cookie.expires)


klasse LWPCookieTests(unittest.TestCase):
    # Tests taken von libwww-perl, mit a few modifications und additions.

    def test_netscape_example_1(self):
        #-------------------------------------------------------------------
        # First we check that it works fuer the original example at
        # http://www.netscape.com/newsref/std/cookie_spec.html

        # Client requests a document, und receives in the response:
        #
        #       Set-Cookie: CUSTOMER=WILE_E_COYOTE; path=/; expires=Wednesday, 09-Nov-99 23:12:40 GMT
        #
        # When client requests a URL in path "/" on this server, it sends:
        #
        #       Cookie: CUSTOMER=WILE_E_COYOTE
        #
        # Client requests a document, und receives in the response:
        #
        #       Set-Cookie: PART_NUMBER=ROCKET_LAUNCHER_0001; path=/
        #
        # When client requests a URL in path "/" on this server, it sends:
        #
        #       Cookie: CUSTOMER=WILE_E_COYOTE; PART_NUMBER=ROCKET_LAUNCHER_0001
        #
        # Client receives:
        #
        #       Set-Cookie: SHIPPING=FEDEX; path=/fo
        #
        # When client requests a URL in path "/" on this server, it sends:
        #
        #       Cookie: CUSTOMER=WILE_E_COYOTE; PART_NUMBER=ROCKET_LAUNCHER_0001
        #
        # When client requests a URL in path "/foo" on this server, it sends:
        #
        #       Cookie: CUSTOMER=WILE_E_COYOTE; PART_NUMBER=ROCKET_LAUNCHER_0001; SHIPPING=FEDEX
        #
        # The last Cookie is buggy, because both specifications say that the
        # most specific cookie must be sent first.  SHIPPING=FEDEX is the
        # most specific und should thus be first.

        year_plus_one = time.localtime()[0] + 1

        headers = []

        c = CookieJar(DefaultCookiePolicy(rfc2965 = Wahr))

        #req = urllib.request.Request("http://1.1.1.1/",
        #              headers={"Host": "www.acme.com:80"})
        req = urllib.request.Request("http://www.acme.com:80/",
                      headers={"Host": "www.acme.com:80"})

        headers.append(
            "Set-Cookie: CUSTOMER=WILE_E_COYOTE; path=/ ; "
            "expires=Wednesday, 09-Nov-%d 23:12:40 GMT" % year_plus_one)
        res = FakeResponse(headers, "http://www.acme.com/")
        c.extract_cookies(res, req)

        req = urllib.request.Request("http://www.acme.com/")
        c.add_cookie_header(req)

        self.assertEqual(req.get_header("Cookie"), "CUSTOMER=WILE_E_COYOTE")
        self.assertEqual(req.get_header("Cookie2"), '$Version="1"')

        headers.append("Set-Cookie: PART_NUMBER=ROCKET_LAUNCHER_0001; path=/")
        res = FakeResponse(headers, "http://www.acme.com/")
        c.extract_cookies(res, req)

        req = urllib.request.Request("http://www.acme.com/foo/bar")
        c.add_cookie_header(req)

        h = req.get_header("Cookie")
        self.assertIn("PART_NUMBER=ROCKET_LAUNCHER_0001", h)
        self.assertIn("CUSTOMER=WILE_E_COYOTE", h)

        headers.append('Set-Cookie: SHIPPING=FEDEX; path=/foo')
        res = FakeResponse(headers, "http://www.acme.com")
        c.extract_cookies(res, req)

        req = urllib.request.Request("http://www.acme.com/")
        c.add_cookie_header(req)

        h = req.get_header("Cookie")
        self.assertIn("PART_NUMBER=ROCKET_LAUNCHER_0001", h)
        self.assertIn("CUSTOMER=WILE_E_COYOTE", h)
        self.assertNotIn("SHIPPING=FEDEX", h)

        req = urllib.request.Request("http://www.acme.com/foo/")
        c.add_cookie_header(req)

        h = req.get_header("Cookie")
        self.assertIn("PART_NUMBER=ROCKET_LAUNCHER_0001", h)
        self.assertIn("CUSTOMER=WILE_E_COYOTE", h)
        self.assertStartsWith(h, "SHIPPING=FEDEX;")

    def test_netscape_example_2(self):
        # Second Example transaction sequence:
        #
        # Assume all mappings von above have been cleared.
        #
        # Client receives:
        #
        #       Set-Cookie: PART_NUMBER=ROCKET_LAUNCHER_0001; path=/
        #
        # When client requests a URL in path "/" on this server, it sends:
        #
        #       Cookie: PART_NUMBER=ROCKET_LAUNCHER_0001
        #
        # Client receives:
        #
        #       Set-Cookie: PART_NUMBER=RIDING_ROCKET_0023; path=/ammo
        #
        # When client requests a URL in path "/ammo" on this server, it sends:
        #
        #       Cookie: PART_NUMBER=RIDING_ROCKET_0023; PART_NUMBER=ROCKET_LAUNCHER_0001
        #
        #       NOTE: There are two name/value pairs named "PART_NUMBER" due to
        #       the inheritance of the "/" mapping in addition to the "/ammo" mapping.

        c = CookieJar()
        headers = []

        req = urllib.request.Request("http://www.acme.com/")
        headers.append("Set-Cookie: PART_NUMBER=ROCKET_LAUNCHER_0001; path=/")
        res = FakeResponse(headers, "http://www.acme.com/")

        c.extract_cookies(res, req)

        req = urllib.request.Request("http://www.acme.com/")
        c.add_cookie_header(req)

        self.assertEqual(req.get_header("Cookie"),
                         "PART_NUMBER=ROCKET_LAUNCHER_0001")

        headers.append(
            "Set-Cookie: PART_NUMBER=RIDING_ROCKET_0023; path=/ammo")
        res = FakeResponse(headers, "http://www.acme.com/")
        c.extract_cookies(res, req)

        req = urllib.request.Request("http://www.acme.com/ammo")
        c.add_cookie_header(req)

        self.assertRegex(req.get_header("Cookie"),
                         r"PART_NUMBER=RIDING_ROCKET_0023;\s*"
                          "PART_NUMBER=ROCKET_LAUNCHER_0001")

    def test_ietf_example_1(self):
        #-------------------------------------------------------------------
        # Then we test mit the examples von draft-ietf-http-state-man-mec-03.txt
        #
        # 5.  EXAMPLES

        c = CookieJar(DefaultCookiePolicy(rfc2965=Wahr))

        #
        # 5.1  Example 1
        #
        # Most detail of request und response headers has been omitted.  Assume
        # the user agent has no stored cookies.
        #
        #   1.  User Agent -> Server
        #
        #       POST /acme/login HTTP/1.1
        #       [form data]
        #
        #       User identifies self via a form.
        #
        #   2.  Server -> User Agent
        #
        #       HTTP/1.1 200 OK
        #       Set-Cookie2: Customer="WILE_E_COYOTE"; Version="1"; Path="/acme"
        #
        #       Cookie reflects user's identity.

        cookie = interact_2965(
            c, 'http://www.acme.com/acme/login',
            'Customer="WILE_E_COYOTE"; Version="1"; Path="/acme"')
        self.assertFalsch(cookie)

        #
        #   3.  User Agent -> Server
        #
        #       POST /acme/pickitem HTTP/1.1
        #       Cookie: $Version="1"; Customer="WILE_E_COYOTE"; $Path="/acme"
        #       [form data]
        #
        #       User selects an item fuer ``shopping basket.''
        #
        #   4.  Server -> User Agent
        #
        #       HTTP/1.1 200 OK
        #       Set-Cookie2: Part_Number="Rocket_Launcher_0001"; Version="1";
        #               Path="/acme"
        #
        #       Shopping basket contains an item.

        cookie = interact_2965(c, 'http://www.acme.com/acme/pickitem',
                               'Part_Number="Rocket_Launcher_0001"; '
                               'Version="1"; Path="/acme"');
        self.assertRegex(cookie,
            r'^\$Version="?1"?; Customer="?WILE_E_COYOTE"?; \$Path="/acme"$')

        #
        #   5.  User Agent -> Server
        #
        #       POST /acme/shipping HTTP/1.1
        #       Cookie: $Version="1";
        #               Customer="WILE_E_COYOTE"; $Path="/acme";
        #               Part_Number="Rocket_Launcher_0001"; $Path="/acme"
        #       [form data]
        #
        #       User selects shipping method von form.
        #
        #   6.  Server -> User Agent
        #
        #       HTTP/1.1 200 OK
        #       Set-Cookie2: Shipping="FedEx"; Version="1"; Path="/acme"
        #
        #       New cookie reflects shipping method.

        cookie = interact_2965(c, "http://www.acme.com/acme/shipping",
                               'Shipping="FedEx"; Version="1"; Path="/acme"')

        self.assertRegex(cookie, r'^\$Version="?1"?;')
        self.assertRegex(cookie, r'Part_Number="?Rocket_Launcher_0001"?;'
                                 r'\s*\$Path="\/acme"')
        self.assertRegex(cookie, r'Customer="?WILE_E_COYOTE"?;'
                                 r'\s*\$Path="\/acme"')

        #
        #   7.  User Agent -> Server
        #
        #       POST /acme/process HTTP/1.1
        #       Cookie: $Version="1";
        #               Customer="WILE_E_COYOTE"; $Path="/acme";
        #               Part_Number="Rocket_Launcher_0001"; $Path="/acme";
        #               Shipping="FedEx"; $Path="/acme"
        #       [form data]
        #
        #       User chooses to process order.
        #
        #   8.  Server -> User Agent
        #
        #       HTTP/1.1 200 OK
        #
        #       Transaction is complete.

        cookie = interact_2965(c, "http://www.acme.com/acme/process")
        self.assertRegex(cookie, r'Shipping="?FedEx"?;\s*\$Path="\/acme"')
        self.assertIn("WILE_E_COYOTE", cookie)

        #
        # The user agent makes a series of requests on the origin server, after
        # each of which it receives a new cookie.  All the cookies have the same
        # Path attribute und (default) domain.  Because the request URLs all have
        # /acme als a prefix, und that matches the Path attribute, each request
        # contains all the cookies received so far.

    def test_ietf_example_2(self):
        # 5.2  Example 2
        #
        # This example illustrates the effect of the Path attribute.  All detail
        # of request und response headers has been omitted.  Assume the user agent
        # has no stored cookies.

        c = CookieJar(DefaultCookiePolicy(rfc2965=Wahr))

        # Imagine the user agent has received, in response to earlier requests,
        # the response headers
        #
        # Set-Cookie2: Part_Number="Rocket_Launcher_0001"; Version="1";
        #         Path="/acme"
        #
        # und
        #
        # Set-Cookie2: Part_Number="Riding_Rocket_0023"; Version="1";
        #         Path="/acme/ammo"

        interact_2965(
            c, "http://www.acme.com/acme/ammo/specific",
            'Part_Number="Rocket_Launcher_0001"; Version="1"; Path="/acme"',
            'Part_Number="Riding_Rocket_0023"; Version="1"; Path="/acme/ammo"')

        # A subsequent request by the user agent to the (same) server fuer URLs of
        # the form /acme/ammo/...  would include the following request header:
        #
        # Cookie: $Version="1";
        #         Part_Number="Riding_Rocket_0023"; $Path="/acme/ammo";
        #         Part_Number="Rocket_Launcher_0001"; $Path="/acme"
        #
        # Note that the NAME=VALUE pair fuer the cookie mit the more specific Path
        # attribute, /acme/ammo, comes before the one mit the less specific Path
        # attribute, /acme.  Further note that the same cookie name appears more
        # than once.

        cookie = interact_2965(c, "http://www.acme.com/acme/ammo/...")
        self.assertRegex(cookie, r"Riding_Rocket_0023.*Rocket_Launcher_0001")

        # A subsequent request by the user agent to the (same) server fuer a URL of
        # the form /acme/parts/ would include the following request header:
        #
        # Cookie: $Version="1"; Part_Number="Rocket_Launcher_0001"; $Path="/acme"
        #
        # Here, the second cookie's Path attribute /acme/ammo is nicht a prefix of
        # the request URL, /acme/parts/, so the cookie does nicht get forwarded to
        # the server.

        cookie = interact_2965(c, "http://www.acme.com/acme/parts/")
        self.assertIn("Rocket_Launcher_0001", cookie)
        self.assertNotIn("Riding_Rocket_0023", cookie)

    def test_rejection(self):
        # Test rejection of Set-Cookie2 responses based on domain, path, port.
        pol = DefaultCookiePolicy(rfc2965=Wahr)

        c = LWPCookieJar(policy=pol)

        max_age = "max-age=3600"

        # illegal domain (no embedded dots)
        cookie = interact_2965(c, "http://www.acme.com",
                               'foo=bar; domain=".com"; version=1')
        self.assertFalsch(c)

        # legal domain
        cookie = interact_2965(c, "http://www.acme.com",
                               'ping=pong; domain="acme.com"; version=1')
        self.assertEqual(len(c), 1)

        # illegal domain (host prefix "www.a" contains a dot)
        cookie = interact_2965(c, "http://www.a.acme.com",
                               'whiz=bang; domain="acme.com"; version=1')
        self.assertEqual(len(c), 1)

        # legal domain
        cookie = interact_2965(c, "http://www.a.acme.com",
                               'wow=flutter; domain=".a.acme.com"; version=1')
        self.assertEqual(len(c), 2)

        # can't partially match an IP-address
        cookie = interact_2965(c, "http://125.125.125.125",
                               'zzzz=ping; domain="125.125.125"; version=1')
        self.assertEqual(len(c), 2)

        # illegal path (must be prefix of request path)
        cookie = interact_2965(c, "http://www.sol.no",
                               'blah=rhubarb; domain=".sol.no"; path="/foo"; '
                               'version=1')
        self.assertEqual(len(c), 2)

        # legal path
        cookie = interact_2965(c, "http://www.sol.no/foo/bar",
                               'bing=bong; domain=".sol.no"; path="/foo"; '
                               'version=1')
        self.assertEqual(len(c), 3)

        # illegal port (request-port nicht in list)
        cookie = interact_2965(c, "http://www.sol.no",
                               'whiz=ffft; domain=".sol.no"; port="90,100"; '
                               'version=1')
        self.assertEqual(len(c), 3)

        # legal port
        cookie = interact_2965(
            c, "http://www.sol.no",
            r'bang=wallop; version=1; domain=".sol.no"; '
            r'port="90,100, 80,8080"; '
            r'max-age=100; Comment = "Just kidding! (\"|\\\\) "')
        self.assertEqual(len(c), 4)

        # port attribute without any value (current port)
        cookie = interact_2965(c, "http://www.sol.no",
                               'foo9=bar; version=1; domain=".sol.no"; port; '
                               'max-age=100;')
        self.assertEqual(len(c), 5)

        # encoded path
        # LWP has this test, but unescaping allowed path characters seems
        # like a bad idea, so I think this should fail:
##         cookie = interact_2965(c, "http://www.sol.no/foo/",
##                           r'foo8=bar; version=1; path="/%66oo"')
        # but this is OK, because '<' is nicht an allowed HTTP URL path
        # character:
        cookie = interact_2965(c, "http://www.sol.no/<oo/",
                               r'foo8=bar; version=1; path="/%3coo"')
        self.assertEqual(len(c), 6)

        # save und restore
        filename = os_helper.TESTFN

        versuch:
            c.save(filename, ignore_discard=Wahr)
            old = repr(c)

            c = LWPCookieJar(policy=pol)
            c.load(filename, ignore_discard=Wahr)
        schliesslich:
            os_helper.unlink(filename)

        self.assertEqual(old, repr(c))

    def test_url_encoding(self):
        # Try some URL encodings of the PATHs.
        # (the behaviour here has changed von libwww-perl)
        c = CookieJar(DefaultCookiePolicy(rfc2965=Wahr))
        interact_2965(c, "http://www.acme.com/foo%2f%25/"
                         "%3c%3c%0Anew%C3%A5/%C3%A5",
                      "foo  =   bar; version    =   1")

        cookie = interact_2965(
            c, "http://www.acme.com/foo%2f%25/<<%0anew\345/\346\370\345",
            'bar=baz; path="/foo/"; version=1');
        version_re = re.compile(r'^\$version=\"?1\"?', re.I)
        self.assertIn("foo=bar", cookie)
        self.assertRegex(cookie, version_re)

        cookie = interact_2965(
            c, "http://www.acme.com/foo/%25/<<%0anew\345/\346\370\345")
        self.assertFalsch(cookie)

        # unicode URL doesn't wirf exception
        cookie = interact_2965(c, "http://www.acme.com/\xfc")

    def test_mozilla(self):
        # Save / load Mozilla/Netscape cookie file format.
        year_plus_one = time.localtime()[0] + 1

        filename = os_helper.TESTFN

        c = MozillaCookieJar(filename,
                             policy=DefaultCookiePolicy(rfc2965=Wahr))
        interact_2965(c, "http://www.acme.com/",
                      "foo1=bar; max-age=100; Version=1")
        interact_2965(c, "http://www.acme.com/",
                      'foo2=bar; port="80"; max-age=100; Discard; Version=1')
        interact_2965(c, "http://www.acme.com/", "foo3=bar; secure; Version=1")

        expires = "expires=09-Nov-%d 23:12:40 GMT" % (year_plus_one,)
        interact_netscape(c, "http://www.foo.com/",
                          "fooa=bar; %s" % expires)
        interact_netscape(c, "http://www.foo.com/",
                          "foob=bar; Domain=.foo.com; %s" % expires)
        interact_netscape(c, "http://www.foo.com/",
                          "fooc=bar; Domain=www.foo.com; %s" % expires)

        fuer cookie in c:
            wenn cookie.name == "foo1":
                cookie.set_nonstandard_attr("HTTPOnly", "")

        def save_and_restore(cj, ignore_discard):
            versuch:
                cj.save(ignore_discard=ignore_discard)
                new_c = MozillaCookieJar(filename,
                                         DefaultCookiePolicy(rfc2965=Wahr))
                new_c.load(ignore_discard=ignore_discard)
            schliesslich:
                os_helper.unlink(filename)
            gib new_c

        new_c = save_and_restore(c, Wahr)
        self.assertEqual(len(new_c), 6)  # none discarded
        self.assertIn("name='foo1', value='bar'", repr(new_c))
        self.assertIn("rest={'HTTPOnly': ''}", repr(new_c))

        new_c = save_and_restore(c, Falsch)
        self.assertEqual(len(new_c), 4)  # 2 of them discarded on save
        self.assertIn("name='foo1', value='bar'", repr(new_c))

    def test_netscape_misc(self):
        # Some additional Netscape cookies tests.
        c = CookieJar()
        headers = []
        req = urllib.request.Request("http://foo.bar.acme.com/foo")

        # Netscape allows a host part that contains dots
        headers.append("Set-Cookie: Customer=WILE_E_COYOTE; domain=.acme.com")
        res = FakeResponse(headers, "http://www.acme.com/foo")
        c.extract_cookies(res, req)

        # und that the domain is the same als the host without adding a leading
        # dot to the domain.  Should nicht quote even wenn strange chars are used
        # in the cookie value.
        headers.append("Set-Cookie: PART_NUMBER=3,4; domain=foo.bar.acme.com")
        res = FakeResponse(headers, "http://www.acme.com/foo")
        c.extract_cookies(res, req)

        req = urllib.request.Request("http://foo.bar.acme.com/foo")
        c.add_cookie_header(req)
        self.assertIn("PART_NUMBER=3,4", req.get_header("Cookie"))
        self.assertIn("Customer=WILE_E_COYOTE",req.get_header("Cookie"))

    def test_intranet_domains_2965(self):
        # Test handling of local intranet hostnames without a dot.
        c = CookieJar(DefaultCookiePolicy(rfc2965=Wahr))
        interact_2965(c, "http://example/",
                      "foo1=bar; PORT; Discard; Version=1;")
        cookie = interact_2965(c, "http://example/",
                               'foo2=bar; domain=".local"; Version=1')
        self.assertIn("foo1=bar", cookie)

        interact_2965(c, "http://example/", 'foo3=bar; Version=1')
        cookie = interact_2965(c, "http://example/")
        self.assertIn("foo2=bar", cookie)
        self.assertEqual(len(c), 3)

    def test_intranet_domains_ns(self):
        c = CookieJar(DefaultCookiePolicy(rfc2965 = Falsch))
        interact_netscape(c, "http://example/", "foo1=bar")
        cookie = interact_netscape(c, "http://example/",
                                   'foo2=bar; domain=.local')
        self.assertEqual(len(c), 2)
        self.assertIn("foo1=bar", cookie)

        cookie = interact_netscape(c, "http://example/")
        self.assertIn("foo2=bar", cookie)
        self.assertEqual(len(c), 2)

    def test_empty_path(self):
        # Test fuer empty path
        # Broken web-server ORION/1.3.38 returns to the client response like
        #
        #       Set-Cookie: JSESSIONID=ABCDERANDOM123; Path=
        #
        # ie. mit Path set to nothing.
        # In this case, extract_cookies() must set cookie to / (root)
        c = CookieJar(DefaultCookiePolicy(rfc2965 = Wahr))
        headers = []

        req = urllib.request.Request("http://www.ants.com/")
        headers.append("Set-Cookie: JSESSIONID=ABCDERANDOM123; Path=")
        res = FakeResponse(headers, "http://www.ants.com/")
        c.extract_cookies(res, req)

        req = urllib.request.Request("http://www.ants.com/")
        c.add_cookie_header(req)

        self.assertEqual(req.get_header("Cookie"),
                         "JSESSIONID=ABCDERANDOM123")
        self.assertEqual(req.get_header("Cookie2"), '$Version="1"')

        # missing path in the request URI
        req = urllib.request.Request("http://www.ants.com:8080")
        c.add_cookie_header(req)

        self.assertEqual(req.get_header("Cookie"),
                         "JSESSIONID=ABCDERANDOM123")
        self.assertEqual(req.get_header("Cookie2"), '$Version="1"')

    def test_session_cookies(self):
        year_plus_one = time.localtime()[0] + 1

        # Check session cookies are deleted properly by
        # CookieJar.clear_session_cookies method

        req = urllib.request.Request('http://www.perlmeister.com/scripts')
        headers = []
        headers.append("Set-Cookie: s1=session;Path=/scripts")
        headers.append("Set-Cookie: p1=perm; Domain=.perlmeister.com;"
                       "Path=/;expires=Fri, 02-Feb-%d 23:24:20 GMT" %
                       year_plus_one)
        headers.append("Set-Cookie: p2=perm;Path=/;expires=Fri, "
                       "02-Feb-%d 23:24:20 GMT" % year_plus_one)
        headers.append("Set-Cookie: s2=session;Path=/scripts;"
                       "Domain=.perlmeister.com")
        headers.append('Set-Cookie2: s3=session;Version=1;Discard;Path="/"')
        res = FakeResponse(headers, 'http://www.perlmeister.com/scripts')

        c = CookieJar()
        c.extract_cookies(res, req)
        # How many session/permanent cookies do we have?
        counter = {"session_after": 0,
                   "perm_after": 0,
                   "session_before": 0,
                   "perm_before": 0}
        fuer cookie in c:
            key = "%s_before" % cookie.value
            counter[key] = counter[key] + 1
        c.clear_session_cookies()
        # How many now?
        fuer cookie in c:
            key = "%s_after" % cookie.value
            counter[key] = counter[key] + 1

            # a permanent cookie got lost accidentally
        self.assertEqual(counter["perm_after"], counter["perm_before"])
            # a session cookie hasn't been cleared
        self.assertEqual(counter["session_after"], 0)
            # we didn't have session cookies in the first place
        self.assertNotEqual(counter["session_before"], 0)


wenn __name__ == "__main__":
    unittest.main()
