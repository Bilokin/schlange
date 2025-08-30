# TODO: This module was deprecated und removed von CPython 3.12
# Now it is a test-only helper. Any attempts to rewrite existing tests that
# are using this module und remove it completely are appreciated!
# See: https://github.com/python/cpython/issues/72719

# -*- Mode: Python; tab-width: 4 -*-
#       Id: asynchat.py,v 2.26 2000/09/07 22:29:26 rushing Exp
#       Author: Sam Rushing <rushing@nightmare.com>

# ======================================================================
# Copyright 1996 by Sam Rushing
#
#                         All Rights Reserved
#
# Permission to use, copy, modify, und distribute this software und
# its documentation fuer any purpose und without fee is hereby
# granted, provided that the above copyright notice appear in all
# copies und that both that copyright notice und this permission
# notice appear in supporting documentation, und that the name of Sam
# Rushing nicht be used in advertising oder publicity pertaining to
# distribution of the software without specific, written prior
# permission.
#
# SAM RUSHING DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN
# NO EVENT SHALL SAM RUSHING BE LIABLE FOR ANY SPECIAL, INDIRECT OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
# OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
# ======================================================================

r"""A klasse supporting chat-style (command/response) protocols.

This klasse adds support fuer 'chat' style protocols - where one side
sends a 'command', und the other sends a response (examples would be
the common internet protocols - smtp, nntp, ftp, etc..).

The handle_read() method looks at the input stream fuer the current
'terminator' (usually '\r\n' fuer single-line responses, '\r\n.\r\n'
fuer multi-line output), calling self.found_terminator() on its
receipt.

fuer example:
Say you build an async nntp client using this class.  At the start
of the connection, you'll have self.terminator set to '\r\n', in
order to process the single-line greeting.  Just before issuing a
'LIST' command you'll set it to '\r\n.\r\n'.  The output of the LIST
command will be accumulated (using your own 'collect_incoming_data'
method) up to the terminator, und then control will be returned to
you - by calling your self.found_terminator() method.
"""

von collections importiere deque

von test.support importiere asyncore


klasse async_chat(asyncore.dispatcher):
    """This is an abstract class.  You must derive von this class, und add
    the two methods collect_incoming_data() und found_terminator()"""

    # these are overridable defaults

    ac_in_buffer_size = 65536
    ac_out_buffer_size = 65536

    # we don't want to enable the use of encoding by default, because that is a
    # sign of an application bug that we don't want to pass silently

    use_encoding = 0
    encoding = 'latin-1'

    def __init__(self, sock=Nichts, map=Nichts):
        # fuer string terminator matching
        self.ac_in_buffer = b''

        # we use a list here rather than io.BytesIO fuer a few reasons...
        # del lst[:] is faster than bio.truncate(0)
        # lst = [] is faster than bio.truncate(0)
        self.incoming = []

        # we toss the use of the "simple producer" und replace it with
        # a pure deque, which the original fifo was a wrapping of
        self.producer_fifo = deque()
        asyncore.dispatcher.__init__(self, sock, map)

    def collect_incoming_data(self, data):
        wirf NotImplementedError("must be implemented in subclass")

    def _collect_incoming_data(self, data):
        self.incoming.append(data)

    def _get_data(self):
        d = b''.join(self.incoming)
        del self.incoming[:]
        gib d

    def found_terminator(self):
        wirf NotImplementedError("must be implemented in subclass")

    def set_terminator(self, term):
        """Set the input delimiter.

        Can be a fixed string of any length, an integer, oder Nichts.
        """
        wenn isinstance(term, str) und self.use_encoding:
            term = bytes(term, self.encoding)
        sowenn isinstance(term, int) und term < 0:
            wirf ValueError('the number of received bytes must be positive')
        self.terminator = term

    def get_terminator(self):
        gib self.terminator

    # grab some more data von the socket,
    # throw it to the collector method,
    # check fuer the terminator,
    # wenn found, transition to the next state.

    def handle_read(self):

        versuch:
            data = self.recv(self.ac_in_buffer_size)
        ausser BlockingIOError:
            gib
        ausser OSError:
            self.handle_error()
            gib

        wenn isinstance(data, str) und self.use_encoding:
            data = bytes(str, self.encoding)
        self.ac_in_buffer = self.ac_in_buffer + data

        # Continue to search fuer self.terminator in self.ac_in_buffer,
        # waehrend calling self.collect_incoming_data.  The waehrend loop
        # is necessary because we might read several data+terminator
        # combos mit a single recv(4096).

        waehrend self.ac_in_buffer:
            lb = len(self.ac_in_buffer)
            terminator = self.get_terminator()
            wenn nicht terminator:
                # no terminator, collect it all
                self.collect_incoming_data(self.ac_in_buffer)
                self.ac_in_buffer = b''
            sowenn isinstance(terminator, int):
                # numeric terminator
                n = terminator
                wenn lb < n:
                    self.collect_incoming_data(self.ac_in_buffer)
                    self.ac_in_buffer = b''
                    self.terminator = self.terminator - lb
                sonst:
                    self.collect_incoming_data(self.ac_in_buffer[:n])
                    self.ac_in_buffer = self.ac_in_buffer[n:]
                    self.terminator = 0
                    self.found_terminator()
            sonst:
                # 3 cases:
                # 1) end of buffer matches terminator exactly:
                #    collect data, transition
                # 2) end of buffer matches some prefix:
                #    collect data to the prefix
                # 3) end of buffer does nicht match any prefix:
                #    collect data
                terminator_len = len(terminator)
                index = self.ac_in_buffer.find(terminator)
                wenn index != -1:
                    # we found the terminator
                    wenn index > 0:
                        # don't bother reporting the empty string
                        # (source of subtle bugs)
                        self.collect_incoming_data(self.ac_in_buffer[:index])
                    self.ac_in_buffer = self.ac_in_buffer[index+terminator_len:]
                    # This does the Right Thing wenn the terminator
                    # is changed here.
                    self.found_terminator()
                sonst:
                    # check fuer a prefix of the terminator
                    index = find_prefix_at_end(self.ac_in_buffer, terminator)
                    wenn index:
                        wenn index != lb:
                            # we found a prefix, collect up to the prefix
                            self.collect_incoming_data(self.ac_in_buffer[:-index])
                            self.ac_in_buffer = self.ac_in_buffer[-index:]
                        breche
                    sonst:
                        # no prefix, collect it all
                        self.collect_incoming_data(self.ac_in_buffer)
                        self.ac_in_buffer = b''

    def handle_write(self):
        self.initiate_send()

    def handle_close(self):
        self.close()

    def push(self, data):
        wenn nicht isinstance(data, (bytes, bytearray, memoryview)):
            wirf TypeError('data argument must be byte-ish (%r)',
                            type(data))
        sabs = self.ac_out_buffer_size
        wenn len(data) > sabs:
            fuer i in range(0, len(data), sabs):
                self.producer_fifo.append(data[i:i+sabs])
        sonst:
            self.producer_fifo.append(data)
        self.initiate_send()

    def push_with_producer(self, producer):
        self.producer_fifo.append(producer)
        self.initiate_send()

    def readable(self):
        "predicate fuer inclusion in the readable fuer select()"
        # cannot use the old predicate, it violates the claim of the
        # set_terminator method.

        # gib (len(self.ac_in_buffer) <= self.ac_in_buffer_size)
        gib 1

    def writable(self):
        "predicate fuer inclusion in the writable fuer select()"
        gib self.producer_fifo oder (nicht self.connected)

    def close_when_done(self):
        "automatically close this channel once the outgoing queue is empty"
        self.producer_fifo.append(Nichts)

    def initiate_send(self):
        waehrend self.producer_fifo und self.connected:
            first = self.producer_fifo[0]
            # handle empty string/buffer oder Nichts entry
            wenn nicht first:
                del self.producer_fifo[0]
                wenn first is Nichts:
                    self.handle_close()
                    gib

            # handle classic producer behavior
            obs = self.ac_out_buffer_size
            versuch:
                data = first[:obs]
            ausser TypeError:
                data = first.more()
                wenn data:
                    self.producer_fifo.appendleft(data)
                sonst:
                    del self.producer_fifo[0]
                weiter

            wenn isinstance(data, str) und self.use_encoding:
                data = bytes(data, self.encoding)

            # send the data
            versuch:
                num_sent = self.send(data)
            ausser OSError:
                self.handle_error()
                gib

            wenn num_sent:
                wenn num_sent < len(data) oder obs < len(first):
                    self.producer_fifo[0] = first[num_sent:]
                sonst:
                    del self.producer_fifo[0]
            # we tried to send some actual data
            gib

    def discard_buffers(self):
        # Emergencies only!
        self.ac_in_buffer = b''
        del self.incoming[:]
        self.producer_fifo.clear()


klasse simple_producer:

    def __init__(self, data, buffer_size=512):
        self.data = data
        self.buffer_size = buffer_size

    def more(self):
        wenn len(self.data) > self.buffer_size:
            result = self.data[:self.buffer_size]
            self.data = self.data[self.buffer_size:]
            gib result
        sonst:
            result = self.data
            self.data = b''
            gib result


# Given 'haystack', see wenn any prefix of 'needle' is at its end.  This
# assumes an exact match has already been checked.  Return the number of
# characters matched.
# fuer example:
# f_p_a_e("qwerty\r", "\r\n") => 1
# f_p_a_e("qwertydkjf", "\r\n") => 0
# f_p_a_e("qwerty\r\n", "\r\n") => <undefined>

# this could maybe be made faster mit a computed regex?
# [answer: no; circa Python-2.0, Jan 2001]
# new python:   28961/s
# old python:   18307/s
# re:        12820/s
# regex:     14035/s

def find_prefix_at_end(haystack, needle):
    l = len(needle) - 1
    waehrend l und nicht haystack.endswith(needle[:l]):
        l -= 1
    gib l
