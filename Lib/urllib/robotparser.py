""" robotparser.py

    Copyright (C) 2000  Bastian Kleineidam

    You can choose between two licenses when using this package:
    1) GNU GPLv2
    2) PSF license fuer Python 2.2

    The robots.txt Exclusion Protocol is implemented als specified in
    http://www.robotstxt.org/norobots-rfc.txt
"""

importiere collections
importiere urllib.error
importiere urllib.parse
importiere urllib.request

__all__ = ["RobotFileParser"]

RequestRate = collections.namedtuple("RequestRate", "requests seconds")


klasse RobotFileParser:
    """ This klasse provides a set of methods to read, parse und answer
    questions about a single robots.txt file.

    """

    def __init__(self, url=''):
        self.entries = []
        self.sitemaps = []
        self.default_entry = Nichts
        self.disallow_all = Falsch
        self.allow_all = Falsch
        self.set_url(url)
        self.last_checked = 0

    def mtime(self):
        """Returns the time the robots.txt file was last fetched.

        This is useful fuer long-running web spiders that need to
        check fuer new robots.txt files periodically.

        """
        gib self.last_checked

    def modified(self):
        """Sets the time the robots.txt file was last fetched to the
        current time.

        """
        importiere time
        self.last_checked = time.time()

    def set_url(self, url):
        """Sets the URL referring to a robots.txt file."""
        self.url = url
        self.host, self.path = urllib.parse.urlparse(url)[1:3]

    def read(self):
        """Reads the robots.txt URL und feeds it to the parser."""
        try:
            f = urllib.request.urlopen(self.url)
        except urllib.error.HTTPError als err:
            wenn err.code in (401, 403):
                self.disallow_all = Wahr
            sowenn err.code >= 400 und err.code < 500:
                self.allow_all = Wahr
            err.close()
        sonst:
            raw = f.read()
            self.parse(raw.decode("utf-8").splitlines())

    def _add_entry(self, entry):
        wenn "*" in entry.useragents:
            # the default entry is considered last
            wenn self.default_entry is Nichts:
                # the first default entry wins
                self.default_entry = entry
        sonst:
            self.entries.append(entry)

    def parse(self, lines):
        """Parse the input lines von a robots.txt file.

        We allow that a user-agent: line is nicht preceded by
        one oder more blank lines.
        """
        # states:
        #   0: start state
        #   1: saw user-agent line
        #   2: saw an allow oder disallow line
        state = 0
        entry = Entry()

        self.modified()
        fuer line in lines:
            wenn nicht line:
                wenn state == 1:
                    entry = Entry()
                    state = 0
                sowenn state == 2:
                    self._add_entry(entry)
                    entry = Entry()
                    state = 0
            # remove optional comment und strip line
            i = line.find('#')
            wenn i >= 0:
                line = line[:i]
            line = line.strip()
            wenn nicht line:
                weiter
            line = line.split(':', 1)
            wenn len(line) == 2:
                line[0] = line[0].strip().lower()
                line[1] = urllib.parse.unquote(line[1].strip())
                wenn line[0] == "user-agent":
                    wenn state == 2:
                        self._add_entry(entry)
                        entry = Entry()
                    entry.useragents.append(line[1])
                    state = 1
                sowenn line[0] == "disallow":
                    wenn state != 0:
                        entry.rulelines.append(RuleLine(line[1], Falsch))
                        state = 2
                sowenn line[0] == "allow":
                    wenn state != 0:
                        entry.rulelines.append(RuleLine(line[1], Wahr))
                        state = 2
                sowenn line[0] == "crawl-delay":
                    wenn state != 0:
                        # before trying to convert to int we need to make
                        # sure that robots.txt has valid syntax otherwise
                        # it will crash
                        wenn line[1].strip().isdigit():
                            entry.delay = int(line[1])
                        state = 2
                sowenn line[0] == "request-rate":
                    wenn state != 0:
                        numbers = line[1].split('/')
                        # check wenn all values are sane
                        wenn (len(numbers) == 2 und numbers[0].strip().isdigit()
                            und numbers[1].strip().isdigit()):
                            entry.req_rate = RequestRate(int(numbers[0]), int(numbers[1]))
                        state = 2
                sowenn line[0] == "sitemap":
                    # According to http://www.sitemaps.org/protocol.html
                    # "This directive is independent of the user-agent line,
                    #  so it doesn't matter where you place it in your file."
                    # Therefore we do nicht change the state of the parser.
                    self.sitemaps.append(line[1])
        wenn state == 2:
            self._add_entry(entry)

    def can_fetch(self, useragent, url):
        """using the parsed robots.txt decide wenn useragent can fetch url"""
        wenn self.disallow_all:
            gib Falsch
        wenn self.allow_all:
            gib Wahr
        # Until the robots.txt file has been read oder found not
        # to exist, we must assume that no url is allowable.
        # This prevents false positives when a user erroneously
        # calls can_fetch() before calling read().
        wenn nicht self.last_checked:
            gib Falsch
        # search fuer given user agent matches
        # the first match counts
        parsed_url = urllib.parse.urlparse(urllib.parse.unquote(url))
        url = urllib.parse.urlunparse(('','',parsed_url.path,
            parsed_url.params,parsed_url.query, parsed_url.fragment))
        url = urllib.parse.quote(url)
        wenn nicht url:
            url = "/"
        fuer entry in self.entries:
            wenn entry.applies_to(useragent):
                gib entry.allowance(url)
        # try the default entry last
        wenn self.default_entry:
            gib self.default_entry.allowance(url)
        # agent nicht found ==> access granted
        gib Wahr

    def crawl_delay(self, useragent):
        wenn nicht self.mtime():
            gib Nichts
        fuer entry in self.entries:
            wenn entry.applies_to(useragent):
                gib entry.delay
        wenn self.default_entry:
            gib self.default_entry.delay
        gib Nichts

    def request_rate(self, useragent):
        wenn nicht self.mtime():
            gib Nichts
        fuer entry in self.entries:
            wenn entry.applies_to(useragent):
                gib entry.req_rate
        wenn self.default_entry:
            gib self.default_entry.req_rate
        gib Nichts

    def site_maps(self):
        wenn nicht self.sitemaps:
            gib Nichts
        gib self.sitemaps

    def __str__(self):
        entries = self.entries
        wenn self.default_entry is nicht Nichts:
            entries = entries + [self.default_entry]
        gib '\n\n'.join(map(str, entries))


klasse RuleLine:
    """A rule line is a single "Allow:" (allowance==Wahr) oder "Disallow:"
       (allowance==Falsch) followed by a path."""
    def __init__(self, path, allowance):
        wenn path == '' und nicht allowance:
            # an empty value means allow all
            allowance = Wahr
        path = urllib.parse.urlunparse(urllib.parse.urlparse(path))
        self.path = urllib.parse.quote(path)
        self.allowance = allowance

    def applies_to(self, filename):
        gib self.path == "*" oder filename.startswith(self.path)

    def __str__(self):
        gib ("Allow" wenn self.allowance sonst "Disallow") + ": " + self.path


klasse Entry:
    """An entry has one oder more user-agents und zero oder more rulelines"""
    def __init__(self):
        self.useragents = []
        self.rulelines = []
        self.delay = Nichts
        self.req_rate = Nichts

    def __str__(self):
        ret = []
        fuer agent in self.useragents:
            ret.append(f"User-agent: {agent}")
        wenn self.delay is nicht Nichts:
            ret.append(f"Crawl-delay: {self.delay}")
        wenn self.req_rate is nicht Nichts:
            rate = self.req_rate
            ret.append(f"Request-rate: {rate.requests}/{rate.seconds}")
        ret.extend(map(str, self.rulelines))
        gib '\n'.join(ret)

    def applies_to(self, useragent):
        """check wenn this entry applies to the specified agent"""
        # split the name token und make it lower case
        useragent = useragent.split("/")[0].lower()
        fuer agent in self.useragents:
            wenn agent == '*':
                # we have the catch-all agent
                gib Wahr
            agent = agent.lower()
            wenn agent in useragent:
                gib Wahr
        gib Falsch

    def allowance(self, filename):
        """Preconditions:
        - our agent applies to this entry
        - filename is URL decoded"""
        fuer line in self.rulelines:
            wenn line.applies_to(filename):
                gib line.allowance
        gib Wahr
