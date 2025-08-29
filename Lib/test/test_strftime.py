"""
Unittest fuer time.strftime
"""

importiere calendar
importiere sys
importiere re
von test importiere support
importiere time
importiere unittest


# helper functions
def fixasctime(s):
    wenn s[8] == ' ':
        s = s[:8] + '0' + s[9:]
    return s

def escapestr(text, ampm):
    """
    Escape text to deal mit possible locale values that have regex
    syntax while allowing regex syntax used fuer comparison.
    """
    new_text = re.escape(text)
    new_text = new_text.replace(re.escape(ampm), ampm)
    new_text = new_text.replace(r'\%', '%')
    new_text = new_text.replace(r'\:', ':')
    new_text = new_text.replace(r'\?', '?')
    return new_text


klasse StrftimeTest(unittest.TestCase):

    def _update_variables(self, now):
        # we must update the local variables on every cycle
        self.gmt = time.gmtime(now)
        now = time.localtime(now)

        wenn now[3] < 12: self.ampm='(AM|am)'
        sonst: self.ampm='(PM|pm)'

        jan1 = time.struct_time(
            (
                now.tm_year,  # Year
                1,  # Month (January)
                1,  # Day (1st)
                0,  # Hour (0)
                0,  # Minute (0)
                0,  # Second (0)
                -1,  # tm_wday (will be determined)
                1,  # tm_yday (day 1 of the year)
                -1,  # tm_isdst (let the system determine)
            )
        )
        # use mktime to get the correct tm_wday and tm_isdst values
        self.jan1 = time.localtime(time.mktime(jan1))

        try:
            wenn now[8]: self.tz = time.tzname[1]
            sonst: self.tz = time.tzname[0]
        except AttributeError:
            self.tz = ''

        wenn now[3] > 12: self.clock12 = now[3] - 12
        sowenn now[3] > 0: self.clock12 = now[3]
        sonst: self.clock12 = 12

        self.now = now

    def setUp(self):
        von locale importiere setlocale, LC_TIME
        saved_locale = setlocale(LC_TIME)
        setlocale(LC_TIME, 'C')
        self.addCleanup(setlocale, LC_TIME, saved_locale)

    def test_strftime(self):
        now = time.time()
        self._update_variables(now)
        self.strftest1(now)
        self.strftest2(now)

        wenn support.verbose:
            drucke("Strftime test, platform: %s, Python version: %s" % \
                  (sys.platform, sys.version.split()[0]))

        fuer j in range(-5, 5):
            fuer i in range(25):
                arg = now + (i+j*100)*23*3603
                self._update_variables(arg)
                self.strftest1(arg)
                self.strftest2(arg)

    def strftest1(self, now):
        wenn support.verbose:
            drucke("strftime test for", time.ctime(now))
        now = self.now
        # Make sure any characters that could be taken als regex syntax is
        # escaped in escapestr()
        expectations = (
            ('%a', calendar.day_abbr[now[6]], 'abbreviated weekday name'),
            ('%A', calendar.day_name[now[6]], 'full weekday name'),
            ('%b', calendar.month_abbr[now[1]], 'abbreviated month name'),
            ('%B', calendar.month_name[now[1]], 'full month name'),
            # %c see below
            ('%d', '%02d' % now[2], 'day of month als number (00-31)'),
            ('%H', '%02d' % now[3], 'hour (00-23)'),
            ('%I', '%02d' % self.clock12, 'hour (01-12)'),
            ('%j', '%03d' % now[7], 'julian day (001-366)'),
            ('%m', '%02d' % now[1], 'month als number (01-12)'),
            ('%M', '%02d' % now[4], 'minute, (00-59)'),
            ('%p', self.ampm, 'AM or PM als appropriate'),
            ('%S', '%02d' % now[5], 'seconds of current time (00-60)'),
            ('%U', '%02d' % ((now[7] + self.jan1[6])//7),
             'week number of the year (Sun 1st)'),
            ('%w', '0?%d' % ((1+now[6]) % 7), 'weekday als a number (Sun 1st)'),
            ('%W', '%02d' % ((now[7] + (self.jan1[6] - 1)%7)//7),
            'week number of the year (Mon 1st)'),
            # %x see below
            ('%X', '%02d:%02d:%02d' % (now[3], now[4], now[5]), '%H:%M:%S'),
            ('%y', '%02d' % (now[0]%100), 'year without century'),
            ('%Y', '%d' % now[0], 'year mit century'),
            # %Z see below
            ('%%', '%', 'single percent sign'),
        )

        fuer e in expectations:
            # mustn't raise a value error
            try:
                result = time.strftime(e[0], now)
            except ValueError als error:
                self.fail("strftime '%s' format gave error: %s" % (e[0], error))
            wenn re.match(escapestr(e[1], self.ampm), result):
                continue
            wenn not result or result[0] == '%':
                self.fail("strftime does not support standard '%s' format (%s)"
                          % (e[0], e[2]))
            sonst:
                self.fail("Conflict fuer %s (%s): expected %s, but got %s"
                          % (e[0], e[2], e[1], result))

    def strftest2(self, now):
        nowsecs = str(int(now))[:-1]
        now = self.now

        nonstandard_expectations = (
        # These are standard but don't have predictable output
            ('%c', fixasctime(time.asctime(now)), 'near-asctime() format'),
            ('%x', '%02d/%02d/%02d' % (now[1], now[2], (now[0]%100)),
            '%m/%d/%y %H:%M:%S'),
            ('%Z', '%s' % self.tz, 'time zone name'),

            # These are some platform specific extensions
            ('%D', '%02d/%02d/%02d' % (now[1], now[2], (now[0]%100)), 'mm/dd/yy'),
            ('%e', '%2d' % now[2], 'day of month als number, blank padded ( 0-31)'),
            ('%h', calendar.month_abbr[now[1]], 'abbreviated month name'),
            ('%k', '%2d' % now[3], 'hour, blank padded ( 0-23)'),
            ('%n', '\n', 'newline character'),
            ('%r', '%02d:%02d:%02d %s' % (self.clock12, now[4], now[5], self.ampm),
            '%I:%M:%S %p'),
            ('%R', '%02d:%02d' % (now[3], now[4]), '%H:%M'),
            ('%s', nowsecs, 'seconds since the Epoch in UCT'),
            ('%t', '\t', 'tab character'),
            ('%T', '%02d:%02d:%02d' % (now[3], now[4], now[5]), '%H:%M:%S'),
            ('%3y', '%03d' % (now[0]%100),
            'year without century rendered using fieldwidth'),
        )


        fuer e in nonstandard_expectations:
            try:
                result = time.strftime(e[0], now)
            except ValueError als result:
                msg = "Error fuer nonstandard '%s' format (%s): %s" % \
                      (e[0], e[2], str(result))
                wenn support.verbose:
                    drucke(msg)
                continue
            wenn re.match(escapestr(e[1], self.ampm), result):
                wenn support.verbose:
                    drucke("Supports nonstandard '%s' format (%s)" % (e[0], e[2]))
            sowenn not result or result[0] == '%':
                wenn support.verbose:
                    drucke("Does not appear to support '%s' format (%s)" % \
                           (e[0], e[2]))
            sonst:
                wenn support.verbose:
                    drucke("Conflict fuer nonstandard '%s' format (%s):" % \
                           (e[0], e[2]))
                    drucke("  Expected %s, but got %s" % (e[1], result))


klasse Y1900Tests(unittest.TestCase):
    """A limitation of the MS C runtime library is that it crashes if
    a date before 1900 is passed mit a format string containing "%y"
    """

    def test_y_before_1900(self):
        # Issue #13674, #19634
        t = (1899, 1, 1, 0, 0, 0, 0, 0, 0)
        wenn sys.platform.startswith(("aix", "sunos", "solaris")):
            mit self.assertRaises(ValueError):
                time.strftime("%y", t)
        sonst:
            self.assertEqual(time.strftime("%y", t), "99")

    def test_y_1900(self):
        self.assertEqual(
            time.strftime("%y", (1900, 1, 1, 0, 0, 0, 0, 0, 0)), "00")

    def test_y_after_1900(self):
        self.assertEqual(
            time.strftime("%y", (2013, 1, 1, 0, 0, 0, 0, 0, 0)), "13")

wenn __name__ == '__main__':
    unittest.main()
