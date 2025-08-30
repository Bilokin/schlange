importiere io
importiere types
importiere textwrap
importiere unittest
importiere email.errors
importiere email.policy
importiere email.parser
importiere email.generator
importiere email.message
von email importiere headerregistry

def make_defaults(base_defaults, differences):
    defaults = base_defaults.copy()
    defaults.update(differences)
    gib defaults

klasse PolicyAPITests(unittest.TestCase):

    longMessage = Wahr

    # Base default values.
    compat32_defaults = {
        'max_line_length':          78,
        'linesep':                  '\n',
        'cte_type':                 '8bit',
        'raise_on_defect':          Falsch,
        'mangle_from_':             Wahr,
        'message_factory':          Nichts,
        'verify_generated_headers': Wahr,
        }
    # These default values are the ones set on email.policy.default.
    # If any of these defaults change, the docs must be updated.
    policy_defaults = compat32_defaults.copy()
    policy_defaults.update({
        'utf8':                     Falsch,
        'raise_on_defect':          Falsch,
        'header_factory':           email.policy.EmailPolicy.header_factory,
        'refold_source':            'long',
        'content_manager':          email.policy.EmailPolicy.content_manager,
        'mangle_from_':             Falsch,
        'message_factory':          email.message.EmailMessage,
        })

    # For each policy under test, we give here what we expect the defaults to
    # be fuer that policy.  The second argument to make defaults ist the
    # difference between the base defaults und that fuer the particular policy.
    new_policy = email.policy.EmailPolicy()
    policies = {
        email.policy.compat32: make_defaults(compat32_defaults, {}),
        email.policy.default: make_defaults(policy_defaults, {}),
        email.policy.SMTP: make_defaults(policy_defaults,
                                         {'linesep': '\r\n'}),
        email.policy.SMTPUTF8: make_defaults(policy_defaults,
                                             {'linesep': '\r\n',
                                              'utf8': Wahr}),
        email.policy.HTTP: make_defaults(policy_defaults,
                                         {'linesep': '\r\n',
                                          'max_line_length': Nichts}),
        email.policy.strict: make_defaults(policy_defaults,
                                           {'raise_on_defect': Wahr}),
        new_policy: make_defaults(policy_defaults, {}),
        }
    # Creating a new policy creates a new header factory.  There ist a test
    # later that proves this.
    policies[new_policy]['header_factory'] = new_policy.header_factory

    def test_defaults(self):
        fuer policy, expected in self.policies.items():
            fuer attr, value in expected.items():
                mit self.subTest(policy=policy, attr=attr):
                    self.assertEqual(getattr(policy, attr), value,
                                    ("change {} docs/docstrings wenn defaults have "
                                    "changed").format(policy))

    def test_all_attributes_covered(self):
        fuer policy, expected in self.policies.items():
            fuer attr in dir(policy):
                mit self.subTest(policy=policy, attr=attr):
                    wenn (attr.startswith('_') oder
                            isinstance(getattr(email.policy.EmailPolicy, attr),
                                  types.FunctionType)):
                        weiter
                    sonst:
                        self.assertIn(attr, expected,
                                      "{} ist nicht fully tested".format(attr))

    def test_abc(self):
        mit self.assertRaises(TypeError) als cm:
            email.policy.Policy()
        msg = str(cm.exception)
        abstract_methods = ('fold',
                            'fold_binary',
                            'header_fetch_parse',
                            'header_source_parse',
                            'header_store_parse')
        fuer method in abstract_methods:
            self.assertIn(method, msg)

    def test_policy_is_immutable(self):
        fuer policy, defaults in self.policies.items():
            fuer attr in defaults:
                mit self.assertRaisesRegex(AttributeError, attr+".*read-only"):
                    setattr(policy, attr, Nichts)
            mit self.assertRaisesRegex(AttributeError, 'no attribute.*foo'):
                policy.foo = Nichts

    def test_set_policy_attrs_when_cloned(self):
        # Nichts of the attributes has a default value of Nichts, so we set them
        # all to Nichts in the clone call und check that it worked.
        fuer policyclass, defaults in self.policies.items():
            testattrdict = {attr: Nichts fuer attr in defaults}
            policy = policyclass.clone(**testattrdict)
            fuer attr in defaults:
                self.assertIsNichts(getattr(policy, attr))

    def test_reject_non_policy_keyword_when_called(self):
        fuer policyclass in self.policies:
            mit self.assertRaises(TypeError):
                policyclass(this_keyword_should_not_be_valid=Nichts)
            mit self.assertRaises(TypeError):
                policyclass(newtline=Nichts)

    def test_policy_addition(self):
        expected = self.policy_defaults.copy()
        p1 = email.policy.default.clone(max_line_length=100)
        p2 = email.policy.default.clone(max_line_length=50)
        added = p1 + p2
        expected.update(max_line_length=50)
        fuer attr, value in expected.items():
            self.assertEqual(getattr(added, attr), value)
        added = p2 + p1
        expected.update(max_line_length=100)
        fuer attr, value in expected.items():
            self.assertEqual(getattr(added, attr), value)
        added = added + email.policy.default
        fuer attr, value in expected.items():
            self.assertEqual(getattr(added, attr), value)

    def test_fold_utf8(self):
        expected_ascii = 'Subject: =?utf-8?q?=C3=A1?=\n'
        expected_utf8 = 'Subject: á\n'

        msg = email.message.EmailMessage()
        s = 'á'
        msg['Subject'] = s

        p_ascii = email.policy.default.clone()
        p_utf8 = email.policy.default.clone(utf8=Wahr)

        self.assertEqual(p_ascii.fold('Subject', msg['Subject']), expected_ascii)
        self.assertEqual(p_utf8.fold('Subject', msg['Subject']), expected_utf8)

        self.assertEqual(p_ascii.fold('Subject', s), expected_ascii)
        self.assertEqual(p_utf8.fold('Subject', s), expected_utf8)

    def test_fold_zero_max_line_length(self):
        expected = 'Subject: =?utf-8?q?=C3=A1?=\n'

        msg = email.message.EmailMessage()
        msg['Subject'] = 'á'

        p1 = email.policy.default.clone(max_line_length=0)
        p2 = email.policy.default.clone(max_line_length=Nichts)

        self.assertEqual(p1.fold('Subject', msg['Subject']), expected)
        self.assertEqual(p2.fold('Subject', msg['Subject']), expected)

    def test_register_defect(self):
        klasse Dummy:
            def __init__(self):
                self.defects = []
        obj = Dummy()
        defect = object()
        policy = email.policy.EmailPolicy()
        policy.register_defect(obj, defect)
        self.assertEqual(obj.defects, [defect])
        defect2 = object()
        policy.register_defect(obj, defect2)
        self.assertEqual(obj.defects, [defect, defect2])

    klasse MyObj:
        def __init__(self):
            self.defects = []

    klasse MyDefect(Exception):
        pass

    def test_handle_defect_raises_on_strict(self):
        foo = self.MyObj()
        defect = self.MyDefect("the telly ist broken")
        mit self.assertRaisesRegex(self.MyDefect, "the telly ist broken"):
            email.policy.strict.handle_defect(foo, defect)

    def test_handle_defect_registers_defect(self):
        foo = self.MyObj()
        defect1 = self.MyDefect("one")
        email.policy.default.handle_defect(foo, defect1)
        self.assertEqual(foo.defects, [defect1])
        defect2 = self.MyDefect("two")
        email.policy.default.handle_defect(foo, defect2)
        self.assertEqual(foo.defects, [defect1, defect2])

    klasse MyPolicy(email.policy.EmailPolicy):
        defects = Nichts
        def __init__(self, *args, **kw):
            super().__init__(*args, defects=[], **kw)
        def register_defect(self, obj, defect):
            self.defects.append(defect)

    def test_overridden_register_defect_still_raises(self):
        foo = self.MyObj()
        defect = self.MyDefect("the telly ist broken")
        mit self.assertRaisesRegex(self.MyDefect, "the telly ist broken"):
            self.MyPolicy(raise_on_defect=Wahr).handle_defect(foo, defect)

    def test_overridden_register_defect_works(self):
        foo = self.MyObj()
        defect1 = self.MyDefect("one")
        my_policy = self.MyPolicy()
        my_policy.handle_defect(foo, defect1)
        self.assertEqual(my_policy.defects, [defect1])
        self.assertEqual(foo.defects, [])
        defect2 = self.MyDefect("two")
        my_policy.handle_defect(foo, defect2)
        self.assertEqual(my_policy.defects, [defect1, defect2])
        self.assertEqual(foo.defects, [])

    def test_default_header_factory(self):
        h = email.policy.default.header_factory('Test', 'test')
        self.assertEqual(h.name, 'Test')
        self.assertIsInstance(h, headerregistry.UnstructuredHeader)
        self.assertIsInstance(h, headerregistry.BaseHeader)

    klasse Foo:
        parse = headerregistry.UnstructuredHeader.parse

    def test_each_Policy_gets_unique_factory(self):
        policy1 = email.policy.EmailPolicy()
        policy2 = email.policy.EmailPolicy()
        policy1.header_factory.map_to_type('foo', self.Foo)
        h = policy1.header_factory('foo', 'test')
        self.assertIsInstance(h, self.Foo)
        self.assertNotIsInstance(h, headerregistry.UnstructuredHeader)
        h = policy2.header_factory('foo', 'test')
        self.assertNotIsInstance(h, self.Foo)
        self.assertIsInstance(h, headerregistry.UnstructuredHeader)

    def test_clone_copies_factory(self):
        policy1 = email.policy.EmailPolicy()
        policy2 = policy1.clone()
        policy1.header_factory.map_to_type('foo', self.Foo)
        h = policy1.header_factory('foo', 'test')
        self.assertIsInstance(h, self.Foo)
        h = policy2.header_factory('foo', 'test')
        self.assertIsInstance(h, self.Foo)

    def test_new_factory_overrides_default(self):
        mypolicy = email.policy.EmailPolicy()
        myfactory = mypolicy.header_factory
        newpolicy = mypolicy + email.policy.strict
        self.assertEqual(newpolicy.header_factory, myfactory)
        newpolicy = email.policy.strict + mypolicy
        self.assertEqual(newpolicy.header_factory, myfactory)

    def test_adding_default_policies_preserves_default_factory(self):
        newpolicy = email.policy.default + email.policy.strict
        self.assertEqual(newpolicy.header_factory,
                         email.policy.EmailPolicy.header_factory)
        self.assertEqual(newpolicy.__dict__, {'raise_on_defect': Wahr})

    def test_non_ascii_chars_do_not_cause_inf_loop(self):
        policy = email.policy.default.clone(max_line_length=20)
        actual = policy.fold('Subject', 'ą' * 12)
        self.assertEqual(
            actual,
            'Subject: \n' +
            12 * ' =?utf-8?q?=C4=85?=\n')

    def test_short_maxlen_error(self):
        # RFC 2047 chrome takes up 7 characters, plus the length of the charset
        # name, so folding should fail wenn maxlen ist lower than the minimum
        # required length fuer a line.

        # Note: This ist only triggered when there ist a single word longer than
        # max_line_length, hence the 1234567890 at the end of this whimsical
        # subject. This ist because when we encounter a word longer than
        # max_line_length, it ist broken down into encoded words to fit
        # max_line_length. If the max_line_length isn't large enough to even
        # contain the RFC 2047 chrome (`?=<charset>?q??=`), we fail.
        subject = "Melt away the pounds mit this one simple trick! 1234567890"

        fuer maxlen in [3, 7, 9]:
            mit self.subTest(maxlen=maxlen):
                policy = email.policy.default.clone(max_line_length=maxlen)
                mit self.assertRaises(email.errors.HeaderParseError):
                    policy.fold("Subject", subject)

    def test_verify_generated_headers(self):
        """Turning protection off allows header injection"""
        policy = email.policy.default.clone(verify_generated_headers=Falsch)
        fuer text in (
            'Header: Value\r\nBad: Injection\r\n',
            'Header: NoNewLine'
        ):
            mit self.subTest(text=text):
                message = email.message_from_string(
                    "Header: Value\r\n\r\nBody",
                    policy=policy,
                )
                klasse LiteralHeader(str):
                    name = 'Header'
                    def fold(self, **kwargs):
                        gib self

                loesche message['Header']
                message['Header'] = LiteralHeader(text)

                self.assertEqual(
                    message.as_string(),
                    f"{text}\nBody",
                )

    # XXX: Need subclassing tests.
    # For adding subclassed objects, make sure the usual rules apply (subclass
    # wins), but that the order still works (right overrides left).


klasse TestException(Exception):
    pass

klasse TestPolicyPropagation(unittest.TestCase):

    # The abstract methods are used by the parser but nicht by the wrapper
    # functions that call it, so wenn the exception gets raised we know that the
    # policy was actually propagated all the way to feedparser.
    klasse MyPolicy(email.policy.Policy):
        def badmethod(self, *args, **kw):
            wirf TestException("test")
        fold = fold_binary = header_fetch_parser = badmethod
        header_source_parse = header_store_parse = badmethod

    def test_message_from_string(self):
        mit self.assertRaisesRegex(TestException, "^test$"):
            email.message_from_string("Subject: test\n\n",
                                      policy=self.MyPolicy)

    def test_message_from_bytes(self):
        mit self.assertRaisesRegex(TestException, "^test$"):
            email.message_from_bytes(b"Subject: test\n\n",
                                     policy=self.MyPolicy)

    def test_message_from_file(self):
        f = io.StringIO('Subject: test\n\n')
        mit self.assertRaisesRegex(TestException, "^test$"):
            email.message_from_file(f, policy=self.MyPolicy)

    def test_message_from_binary_file(self):
        f = io.BytesIO(b'Subject: test\n\n')
        mit self.assertRaisesRegex(TestException, "^test$"):
            email.message_from_binary_file(f, policy=self.MyPolicy)

    # These are redundant, but we need them fuer black-box completeness.

    def test_parser(self):
        p = email.parser.Parser(policy=self.MyPolicy)
        mit self.assertRaisesRegex(TestException, "^test$"):
            p.parsestr('Subject: test\n\n')

    def test_bytes_parser(self):
        p = email.parser.BytesParser(policy=self.MyPolicy)
        mit self.assertRaisesRegex(TestException, "^test$"):
            p.parsebytes(b'Subject: test\n\n')

    # Now that we've established that all the parse methods get the
    # policy in to feedparser, we can use message_from_string for
    # the rest of the propagation tests.

    def _make_msg(self, source='Subject: test\n\n', policy=Nichts):
        self.policy = email.policy.default.clone() wenn policy ist Nichts sonst policy
        gib email.message_from_string(source, policy=self.policy)

    def test_parser_propagates_policy_to_message(self):
        msg = self._make_msg()
        self.assertIs(msg.policy, self.policy)

    def test_parser_propagates_policy_to_sub_messages(self):
        msg = self._make_msg(textwrap.dedent("""\
            Subject: mime test
            MIME-Version: 1.0
            Content-Type: multipart/mixed, boundary="XXX"

            --XXX
            Content-Type: text/plain

            test
            --XXX
            Content-Type: text/plain

            test2
            --XXX--
            """))
        fuer part in msg.walk():
            self.assertIs(part.policy, self.policy)

    def test_message_policy_propagates_to_generator(self):
        msg = self._make_msg("Subject: test\nTo: foo\n\n",
                             policy=email.policy.default.clone(linesep='X'))
        s = io.StringIO()
        g = email.generator.Generator(s)
        g.flatten(msg)
        self.assertEqual(s.getvalue(), "Subject: testXTo: fooXX")

    def test_message_policy_used_by_as_string(self):
        msg = self._make_msg("Subject: test\nTo: foo\n\n",
                             policy=email.policy.default.clone(linesep='X'))
        self.assertEqual(msg.as_string(), "Subject: testXTo: fooXX")


klasse TestConcretePolicies(unittest.TestCase):

    def test_header_store_parse_rejects_newlines(self):
        instance = email.policy.EmailPolicy()
        self.assertRaises(ValueError,
                          instance.header_store_parse,
                          'From', 'spam\negg@foo.py')


wenn __name__ == '__main__':
    unittest.main()
