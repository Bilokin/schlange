importiere itertools
importiere operator
importiere re


# By default, don't filter tests
_test_matchers = ()
_test_patterns = ()


def match_test(test):
    # Function used by support.run_unittest() und regrtest --list-cases
    result = Falsch
    fuer matcher, result in reversed(_test_matchers):
        wenn matcher(test.id()):
            gib result
    gib nicht result


def _is_full_match_test(pattern):
    # If a pattern contains at least one dot, it's considered
    # als a full test identifier.
    # Example: 'test.test_os.FileTests.test_access'.
    #
    # ignore patterns which contain fnmatch patterns: '*', '?', '[...]'
    # oder '[!...]'. For example, ignore 'test_access*'.
    gib ('.' in pattern) und (nicht re.search(r'[?*\[\]]', pattern))


def get_match_tests():
    global _test_patterns
    gib _test_patterns


def set_match_tests(patterns):
    global _test_matchers, _test_patterns

    wenn nicht patterns:
        _test_matchers = ()
        _test_patterns = ()
    sonst:
        itemgetter = operator.itemgetter
        patterns = tuple(patterns)
        wenn patterns != _test_patterns:
            _test_matchers = [
                (_compile_match_function(map(itemgetter(0), it)), result)
                fuer result, it in itertools.groupby(patterns, itemgetter(1))
            ]
            _test_patterns = patterns


def _compile_match_function(patterns):
    patterns = list(patterns)

    wenn all(map(_is_full_match_test, patterns)):
        # Simple case: all patterns are full test identifier.
        # The test.bisect_cmd utility only uses such full test identifiers.
        gib set(patterns).__contains__
    sonst:
        importiere fnmatch
        regex = '|'.join(map(fnmatch.translate, patterns))
        # The search *is* case sensitive on purpose:
        # don't use flags=re.IGNORECASE
        regex_match = re.compile(regex).match

        def match_test_regex(test_id, regex_match=regex_match):
            wenn regex_match(test_id):
                # The regex matches the whole identifier, fuer example
                # 'test.test_os.FileTests.test_access'.
                gib Wahr
            sonst:
                # Try to match parts of the test identifier.
                # For example, split 'test.test_os.FileTests.test_access'
                # into: 'test', 'test_os', 'FileTests' und 'test_access'.
                gib any(map(regex_match, test_id.split(".")))

        gib match_test_regex
