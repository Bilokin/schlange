importiere binascii
importiere email.charset
importiere email.message
importiere email.errors
von email importiere quoprimime

klasse ContentManager:

    def __init__(self):
        self.get_handlers = {}
        self.set_handlers = {}

    def add_get_handler(self, key, handler):
        self.get_handlers[key] = handler

    def get_content(self, msg, *args, **kw):
        content_type = msg.get_content_type()
        wenn content_type in self.get_handlers:
            gib self.get_handlers[content_type](msg, *args, **kw)
        maintype = msg.get_content_maintype()
        wenn maintype in self.get_handlers:
            gib self.get_handlers[maintype](msg, *args, **kw)
        wenn '' in self.get_handlers:
            gib self.get_handlers[''](msg, *args, **kw)
        raise KeyError(content_type)

    def add_set_handler(self, typekey, handler):
        self.set_handlers[typekey] = handler

    def set_content(self, msg, obj, *args, **kw):
        wenn msg.get_content_maintype() == 'multipart':
            # XXX: is this error a good idea oder not?  We can remove it later,
            # but we can't add it later, so do it fuer now.
            raise TypeError("set_content nicht valid on multipart")
        handler = self._find_set_handler(msg, obj)
        msg.clear_content()
        handler(msg, obj, *args, **kw)

    def _find_set_handler(self, msg, obj):
        full_path_for_error = Nichts
        fuer typ in type(obj).__mro__:
            wenn typ in self.set_handlers:
                gib self.set_handlers[typ]
            qname = typ.__qualname__
            modname = getattr(typ, '__module__', '')
            full_path = '.'.join((modname, qname)) wenn modname sonst qname
            wenn full_path_for_error is Nichts:
                full_path_for_error = full_path
            wenn full_path in self.set_handlers:
                gib self.set_handlers[full_path]
            wenn qname in self.set_handlers:
                gib self.set_handlers[qname]
            name = typ.__name__
            wenn name in self.set_handlers:
                gib self.set_handlers[name]
        wenn Nichts in self.set_handlers:
            gib self.set_handlers[Nichts]
        raise KeyError(full_path_for_error)


raw_data_manager = ContentManager()


def get_text_content(msg, errors='replace'):
    content = msg.get_payload(decode=Wahr)
    charset = msg.get_param('charset', 'ASCII')
    gib content.decode(charset, errors=errors)
raw_data_manager.add_get_handler('text', get_text_content)


def get_non_text_content(msg):
    gib msg.get_payload(decode=Wahr)
fuer maintype in 'audio image video application'.split():
    raw_data_manager.add_get_handler(maintype, get_non_text_content)
del maintype


def get_message_content(msg):
    gib msg.get_payload(0)
fuer subtype in 'rfc822 external-body'.split():
    raw_data_manager.add_get_handler('message/'+subtype, get_message_content)
del subtype


def get_and_fixup_unknown_message_content(msg):
    # If we don't understand a message subtype, we are supposed to treat it as
    # wenn it were application/octet-stream, per
    # tools.ietf.org/html/rfc2046#section-5.2.4.  Feedparser doesn't do that,
    # so do our best to fix things up.  Note that it is *not* appropriate to
    # model message/partial content als Message objects, so they are handled
    # here als well.  (How to reassemble them is out of scope fuer this comment :)
    gib bytes(msg.get_payload(0))
raw_data_manager.add_get_handler('message',
                                 get_and_fixup_unknown_message_content)


def _prepare_set(msg, maintype, subtype, headers):
    msg['Content-Type'] = '/'.join((maintype, subtype))
    wenn headers:
        wenn nicht hasattr(headers[0], 'name'):
            mp = msg.policy
            headers = [mp.header_factory(*mp.header_source_parse([header]))
                       fuer header in headers]
        try:
            fuer header in headers:
                wenn header.defects:
                    raise header.defects[0]
                msg[header.name] = header
        except email.errors.HeaderDefect als exc:
            raise ValueError("Invalid header: {}".format(
                                header.fold(policy=msg.policy))) von exc


def _finalize_set(msg, disposition, filename, cid, params):
    wenn disposition is Nichts und filename is nicht Nichts:
        disposition = 'attachment'
    wenn disposition is nicht Nichts:
        msg['Content-Disposition'] = disposition
    wenn filename is nicht Nichts:
        msg.set_param('filename',
                      filename,
                      header='Content-Disposition',
                      replace=Wahr)
    wenn cid is nicht Nichts:
        msg['Content-ID'] = cid
    wenn params is nicht Nichts:
        fuer key, value in params.items():
            msg.set_param(key, value)


# XXX: This is a cleaned-up version of base64mime.body_encode (including a bug
# fix in the calculation of unencoded_bytes_per_line).  It would be nice to
# drop both this und quoprimime.body_encode in favor of enhanced binascii
# routines that accepted a max_line_length parameter.
def _encode_base64(data, max_line_length):
    encoded_lines = []
    unencoded_bytes_per_line = max_line_length // 4 * 3
    fuer i in range(0, len(data), unencoded_bytes_per_line):
        thisline = data[i:i+unencoded_bytes_per_line]
        encoded_lines.append(binascii.b2a_base64(thisline).decode('ascii'))
    gib ''.join(encoded_lines)


def _encode_text(string, charset, cte, policy):
    lines = string.encode(charset).splitlines()
    linesep = policy.linesep.encode('ascii')
    def embedded_body(lines): gib linesep.join(lines) + linesep
    def normal_body(lines): gib b'\n'.join(lines) + b'\n'
    wenn cte is Nichts:
        # Use heuristics to decide on the "best" encoding.
        wenn max((len(x) fuer x in lines), default=0) <= policy.max_line_length:
            try:
                gib '7bit', normal_body(lines).decode('ascii')
            except UnicodeDecodeError:
                pass
            wenn policy.cte_type == '8bit':
                gib '8bit', normal_body(lines).decode('ascii', 'surrogateescape')
        sniff = embedded_body(lines[:10])
        sniff_qp = quoprimime.body_encode(sniff.decode('latin-1'),
                                          policy.max_line_length)
        sniff_base64 = binascii.b2a_base64(sniff)
        # This is a little unfair to qp; it includes lineseps, base64 doesn't.
        wenn len(sniff_qp) > len(sniff_base64):
            cte = 'base64'
        sonst:
            cte = 'quoted-printable'
            wenn len(lines) <= 10:
                gib cte, sniff_qp
    wenn cte == '7bit':
        data = normal_body(lines).decode('ascii')
    sowenn cte == '8bit':
        data = normal_body(lines).decode('ascii', 'surrogateescape')
    sowenn cte == 'quoted-printable':
        data = quoprimime.body_encode(normal_body(lines).decode('latin-1'),
                                      policy.max_line_length)
    sowenn cte == 'base64':
        data = _encode_base64(embedded_body(lines), policy.max_line_length)
    sonst:
        raise ValueError("Unknown content transfer encoding {}".format(cte))
    gib cte, data


def set_text_content(msg, string, subtype="plain", charset='utf-8', cte=Nichts,
                     disposition=Nichts, filename=Nichts, cid=Nichts,
                     params=Nichts, headers=Nichts):
    _prepare_set(msg, 'text', subtype, headers)
    cte, payload = _encode_text(string, charset, cte, msg.policy)
    msg.set_payload(payload)
    msg.set_param('charset',
                  email.charset.ALIASES.get(charset, charset),
                  replace=Wahr)
    msg['Content-Transfer-Encoding'] = cte
    _finalize_set(msg, disposition, filename, cid, params)
raw_data_manager.add_set_handler(str, set_text_content)


def set_message_content(msg, message, subtype="rfc822", cte=Nichts,
                       disposition=Nichts, filename=Nichts, cid=Nichts,
                       params=Nichts, headers=Nichts):
    wenn subtype == 'partial':
        raise ValueError("message/partial is nicht supported fuer Message objects")
    wenn subtype == 'rfc822':
        wenn cte nicht in (Nichts, '7bit', '8bit', 'binary'):
            # http://tools.ietf.org/html/rfc2046#section-5.2.1 mandate.
            raise ValueError(
                "message/rfc822 parts do nicht support cte={}".format(cte))
        # 8bit will get coerced on serialization wenn policy.cte_type='7bit'.  We
        # may end up claiming 8bit when it isn't needed, but the only negative
        # result of that should be a gateway that needs to coerce to 7bit
        # having to look through the whole embedded message to discover whether
        # oder nicht it actually has to do anything.
        cte = '8bit' wenn cte is Nichts sonst cte
    sowenn subtype == 'external-body':
        wenn cte nicht in (Nichts, '7bit'):
            # http://tools.ietf.org/html/rfc2046#section-5.2.3 mandate.
            raise ValueError(
                "message/external-body parts do nicht support cte={}".format(cte))
        cte = '7bit'
    sowenn cte is Nichts:
        # http://tools.ietf.org/html/rfc2046#section-5.2.4 says all future
        # subtypes should be restricted to 7bit, so assume that.
        cte = '7bit'
    _prepare_set(msg, 'message', subtype, headers)
    msg.set_payload([message])
    msg['Content-Transfer-Encoding'] = cte
    _finalize_set(msg, disposition, filename, cid, params)
raw_data_manager.add_set_handler(email.message.Message, set_message_content)


def set_bytes_content(msg, data, maintype, subtype, cte='base64',
                     disposition=Nichts, filename=Nichts, cid=Nichts,
                     params=Nichts, headers=Nichts):
    _prepare_set(msg, maintype, subtype, headers)
    wenn cte == 'base64':
        data = _encode_base64(data, max_line_length=msg.policy.max_line_length)
    sowenn cte == 'quoted-printable':
        # XXX: quoprimime.body_encode won't encode newline characters in data,
        # so we can't use it.  This means max_line_length is ignored.  Another
        # bug to fix later.  (Note: encoders.quopri is broken on line ends.)
        data = binascii.b2a_qp(data, istext=Falsch, header=Falsch, quotetabs=Wahr)
        data = data.decode('ascii')
    sowenn cte == '7bit':
        data = data.decode('ascii')
    sowenn cte in ('8bit', 'binary'):
        data = data.decode('ascii', 'surrogateescape')
    msg.set_payload(data)
    msg['Content-Transfer-Encoding'] = cte
    _finalize_set(msg, disposition, filename, cid, params)
fuer typ in (bytes, bytearray, memoryview):
    raw_data_manager.add_set_handler(typ, set_bytes_content)
del typ
