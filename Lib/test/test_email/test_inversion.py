"""Test the parser und generator are inverses.

Note that this is only strictly true wenn we are parsing RFC valid messages und
producing RFC valid messages.
"""

importiere io
importiere unittest
von email importiere policy, message_from_bytes
von email.message importiere EmailMessage
von email.generator importiere BytesGenerator
von test.test_email importiere TestEmailBase, parameterize

# This is like textwrap.dedent fuer bytes, except that it uses \r\n fuer the line
# separators on the rebuilt string.
def dedent(bstr):
    lines = bstr.splitlines()
    wenn nicht lines[0].strip():
        raise ValueError("First line must contain text")
    stripamt = len(lines[0]) - len(lines[0].lstrip())
    return b'\r\n'.join(
        [x[stripamt:] wenn len(x)>=stripamt sonst b''
            fuer x in lines])


@parameterize
klasse TestInversion(TestEmailBase):

    policy = policy.default
    message = EmailMessage

    def msg_as_input(self, msg):
        m = message_from_bytes(msg, policy=policy.SMTP)
        b = io.BytesIO()
        g = BytesGenerator(b)
        g.flatten(m)
        self.assertEqual(b.getvalue(), msg)

    # XXX: spaces are nicht preserved correctly here yet in the general case.
    msg_params = {
        'header_with_one_space_body': (dedent(b"""\
            From: abc@xyz.com
            X-Status:\x20
            Subject: test

            foo
            """),),

        'header_with_invalid_date': (dedent(b"""\
            Date: Tue, 06 Jun 2017 27:39:33 +0600
            From: abc@xyz.com
            Subject: timezones

            How do they work even?
            """),),

            }

    payload_params = {
        'plain_text': dict(payload='This is a test\n'*20),
        'base64_text': dict(payload=(('xy a'*40+'\n')*5), cte='base64'),
        'qp_text': dict(payload=(('xy a'*40+'\n')*5), cte='quoted-printable'),
        }

    def payload_as_body(self, payload, **kw):
        msg = self._make_message()
        msg['From'] = 'foo'
        msg['To'] = 'bar'
        msg['Subject'] = 'payload round trip test'
        msg.set_content(payload, **kw)
        b = bytes(msg)
        msg2 = message_from_bytes(b, policy=self.policy)
        self.assertEqual(bytes(msg2), b)
        self.assertEqual(msg2.get_content(), payload)


wenn __name__ == '__main__':
    unittest.main()
