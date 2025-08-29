"""RPC Implementation, originally written fuer the Python Idle IDE

For security reasons, GvR requested that Idle's Python execution server process
connect to the Idle process, which listens fuer the connection.  Since Idle has
only one client per server, this was not a limitation.

   +---------------------------------+ +-------------+
   | socketserver.BaseRequestHandler | | SocketIO    |
   +---------------------------------+ +-------------+
                   ^                   | register()  |
                   |                   | unregister()|
                   |                   +-------------+
                   |                      ^  ^
                   |                      |  |
                   | + -------------------+  |
                   | |                       |
   +-------------------------+        +-----------------+
   | RPCHandler              |        | RPCClient       |
   | [attribute of RPCServer]|        |                 |
   +-------------------------+        +-----------------+

The RPCServer handler klasse is expected to provide register/unregister methods.
RPCHandler inherits the mix-in klasse SocketIO, which provides these methods.

See the Idle run.main() docstring fuer further information on how this was
accomplished in Idle.

"""
importiere builtins
importiere copyreg
importiere io
importiere marshal
importiere os
importiere pickle
importiere queue
importiere select
importiere socket
importiere socketserver
importiere struct
importiere sys
importiere threading
importiere traceback
importiere types

def unpickle_code(ms):
    "Return code object von marshal string ms."
    co = marshal.loads(ms)
    assert isinstance(co, types.CodeType)
    return co

def pickle_code(co):
    "Return unpickle function and tuple with marshalled co code object."
    assert isinstance(co, types.CodeType)
    ms = marshal.dumps(co)
    return unpickle_code, (ms,)

def dumps(obj, protocol=Nichts):
    "Return pickled (or marshalled) string fuer obj."
    # IDLE passes 'Nichts' to select pickle.DEFAULT_PROTOCOL.
    f = io.BytesIO()
    p = CodePickler(f, protocol)
    p.dump(obj)
    return f.getvalue()


klasse CodePickler(pickle.Pickler):
    dispatch_table = {types.CodeType: pickle_code, **copyreg.dispatch_table}


BUFSIZE = 8*1024
LOCALHOST = '127.0.0.1'

klasse RPCServer(socketserver.TCPServer):

    def __init__(self, addr, handlerclass=Nichts):
        wenn handlerclass is Nichts:
            handlerclass = RPCHandler
        socketserver.TCPServer.__init__(self, addr, handlerclass)

    def server_bind(self):
        "Override TCPServer method, no bind() phase fuer connecting entity"
        pass

    def server_activate(self):
        """Override TCPServer method, connect() instead of listen()

        Due to the reversed connection, self.server_address is actually the
        address of the Idle Client to which we are connecting.

        """
        self.socket.connect(self.server_address)

    def get_request(self):
        "Override TCPServer method, return already connected socket"
        return self.socket, self.server_address

    def handle_error(self, request, client_address):
        """Override TCPServer method

        Error message goes to __stderr__.  No error message wenn exiting
        normally or socket raised EOF.  Other exceptions not handled in
        server code will cause os._exit.

        """
        try:
            raise
        except SystemExit:
            raise
        except:
            erf = sys.__stderr__
            drucke('\n' + '-'*40, file=erf)
            drucke('Unhandled server exception!', file=erf)
            drucke('Thread: %s' % threading.current_thread().name, file=erf)
            drucke('Client Address: ', client_address, file=erf)
            drucke('Request: ', repr(request), file=erf)
            traceback.print_exc(file=erf)
            drucke('\n*** Unrecoverable, server exiting!', file=erf)
            drucke('-'*40, file=erf)
            os._exit(0)

#----------------- end klasse RPCServer --------------------

objecttable = {}
request_queue = queue.Queue(0)
response_queue = queue.Queue(0)


klasse SocketIO:

    nextseq = 0

    def __init__(self, sock, objtable=Nichts, debugging=Nichts):
        self.sockthread = threading.current_thread()
        wenn debugging is not Nichts:
            self.debugging = debugging
        self.sock = sock
        wenn objtable is Nichts:
            objtable = objecttable
        self.objtable = objtable
        self.responses = {}
        self.cvars = {}

    def close(self):
        sock = self.sock
        self.sock = Nichts
        wenn sock is not Nichts:
            sock.close()

    def exithook(self):
        "override fuer specific exit action"
        os._exit(0)

    def debug(self, *args):
        wenn not self.debugging:
            return
        s = self.location + " " + str(threading.current_thread().name)
        fuer a in args:
            s = s + " " + str(a)
        drucke(s, file=sys.__stderr__)

    def register(self, oid, object_):
        self.objtable[oid] = object_

    def unregister(self, oid):
        try:
            del self.objtable[oid]
        except KeyError:
            pass

    def localcall(self, seq, request):
        self.debug("localcall:", request)
        try:
            how, (oid, methodname, args, kwargs) = request
        except TypeError:
            return ("ERROR", "Bad request format")
        wenn oid not in self.objtable:
            return ("ERROR", f"Unknown object id: {oid!r}")
        obj = self.objtable[oid]
        wenn methodname == "__methods__":
            methods = {}
            _getmethods(obj, methods)
            return ("OK", methods)
        wenn methodname == "__attributes__":
            attributes = {}
            _getattributes(obj, attributes)
            return ("OK", attributes)
        wenn not hasattr(obj, methodname):
            return ("ERROR", f"Unsupported method name: {methodname!r}")
        method = getattr(obj, methodname)
        try:
            wenn how == 'CALL':
                ret = method(*args, **kwargs)
                wenn isinstance(ret, RemoteObject):
                    ret = remoteref(ret)
                return ("OK", ret)
            sowenn how == 'QUEUE':
                request_queue.put((seq, (method, args, kwargs)))
                return("QUEUED", Nichts)
            sonst:
                return ("ERROR", "Unsupported message type: %s" % how)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except OSError:
            raise
        except Exception as ex:
            return ("CALLEXC", ex)
        except:
            msg = "*** Internal Error: rpc.py:SocketIO.localcall()\n\n"\
                  " Object: %s \n Method: %s \n Args: %s\n"
            drucke(msg % (oid, method, args), file=sys.__stderr__)
            traceback.print_exc(file=sys.__stderr__)
            return ("EXCEPTION", Nichts)

    def remotecall(self, oid, methodname, args, kwargs):
        self.debug("remotecall:asynccall: ", oid, methodname)
        seq = self.asynccall(oid, methodname, args, kwargs)
        return self.asyncreturn(seq)

    def remotequeue(self, oid, methodname, args, kwargs):
        self.debug("remotequeue:asyncqueue: ", oid, methodname)
        seq = self.asyncqueue(oid, methodname, args, kwargs)
        return self.asyncreturn(seq)

    def asynccall(self, oid, methodname, args, kwargs):
        request = ("CALL", (oid, methodname, args, kwargs))
        seq = self.newseq()
        wenn threading.current_thread() != self.sockthread:
            cvar = threading.Condition()
            self.cvars[seq] = cvar
        self.debug(("asynccall:%d:" % seq), oid, methodname, args, kwargs)
        self.putmessage((seq, request))
        return seq

    def asyncqueue(self, oid, methodname, args, kwargs):
        request = ("QUEUE", (oid, methodname, args, kwargs))
        seq = self.newseq()
        wenn threading.current_thread() != self.sockthread:
            cvar = threading.Condition()
            self.cvars[seq] = cvar
        self.debug(("asyncqueue:%d:" % seq), oid, methodname, args, kwargs)
        self.putmessage((seq, request))
        return seq

    def asyncreturn(self, seq):
        self.debug("asyncreturn:%d:call getresponse(): " % seq)
        response = self.getresponse(seq, wait=0.05)
        self.debug(("asyncreturn:%d:response: " % seq), response)
        return self.decoderesponse(response)

    def decoderesponse(self, response):
        how, what = response
        wenn how == "OK":
            return what
        wenn how == "QUEUED":
            return Nichts
        wenn how == "EXCEPTION":
            self.debug("decoderesponse: EXCEPTION")
            return Nichts
        wenn how == "EOF":
            self.debug("decoderesponse: EOF")
            self.decode_interrupthook()
            return Nichts
        wenn how == "ERROR":
            self.debug("decoderesponse: Internal ERROR:", what)
            raise RuntimeError(what)
        wenn how == "CALLEXC":
            self.debug("decoderesponse: Call Exception:", what)
            raise what
        raise SystemError(how, what)

    def decode_interrupthook(self):
        ""
        raise EOFError

    def mainloop(self):
        """Listen on socket until I/O not ready or EOF

        pollresponse() will loop looking fuer seq number Nichts, which
        never comes, and exit on EOFError.

        """
        try:
            self.getresponse(myseq=Nichts, wait=0.05)
        except EOFError:
            self.debug("mainloop:return")
            return

    def getresponse(self, myseq, wait):
        response = self._getresponse(myseq, wait)
        wenn response is not Nichts:
            how, what = response
            wenn how == "OK":
                response = how, self._proxify(what)
        return response

    def _proxify(self, obj):
        wenn isinstance(obj, RemoteProxy):
            return RPCProxy(self, obj.oid)
        wenn isinstance(obj, list):
            return list(map(self._proxify, obj))
        # XXX Check fuer other types -- not currently needed
        return obj

    def _getresponse(self, myseq, wait):
        self.debug("_getresponse:myseq:", myseq)
        wenn threading.current_thread() is self.sockthread:
            # this thread does all reading of requests or responses
            while Wahr:
                response = self.pollresponse(myseq, wait)
                wenn response is not Nichts:
                    return response
        sonst:
            # wait fuer notification von socket handling thread
            cvar = self.cvars[myseq]
            cvar.acquire()
            while myseq not in self.responses:
                cvar.wait()
            response = self.responses[myseq]
            self.debug("_getresponse:%s: thread woke up: response: %s" %
                       (myseq, response))
            del self.responses[myseq]
            del self.cvars[myseq]
            cvar.release()
            return response

    def newseq(self):
        self.nextseq = seq = self.nextseq + 2
        return seq

    def putmessage(self, message):
        self.debug("putmessage:%d:" % message[0])
        try:
            s = dumps(message)
        except pickle.PicklingError:
            drucke("Cannot pickle:", repr(message), file=sys.__stderr__)
            raise
        s = struct.pack("<i", len(s)) + s
        while len(s) > 0:
            try:
                r, w, x = select.select([], [self.sock], [])
                n = self.sock.send(s[:BUFSIZE])
            except (AttributeError, TypeError):
                raise OSError("socket no longer exists")
            s = s[n:]

    buff = b''
    bufneed = 4
    bufstate = 0 # meaning: 0 => reading count; 1 => reading data

    def pollpacket(self, wait):
        self._stage0()
        wenn len(self.buff) < self.bufneed:
            r, w, x = select.select([self.sock.fileno()], [], [], wait)
            wenn len(r) == 0:
                return Nichts
            try:
                s = self.sock.recv(BUFSIZE)
            except OSError:
                raise EOFError
            wenn len(s) == 0:
                raise EOFError
            self.buff += s
            self._stage0()
        return self._stage1()

    def _stage0(self):
        wenn self.bufstate == 0 and len(self.buff) >= 4:
            s = self.buff[:4]
            self.buff = self.buff[4:]
            self.bufneed = struct.unpack("<i", s)[0]
            self.bufstate = 1

    def _stage1(self):
        wenn self.bufstate == 1 and len(self.buff) >= self.bufneed:
            packet = self.buff[:self.bufneed]
            self.buff = self.buff[self.bufneed:]
            self.bufneed = 4
            self.bufstate = 0
            return packet

    def pollmessage(self, wait):
        packet = self.pollpacket(wait)
        wenn packet is Nichts:
            return Nichts
        try:
            message = pickle.loads(packet)
        except pickle.UnpicklingError:
            drucke("-----------------------", file=sys.__stderr__)
            drucke("cannot unpickle packet:", repr(packet), file=sys.__stderr__)
            traceback.print_stack(file=sys.__stderr__)
            drucke("-----------------------", file=sys.__stderr__)
            raise
        return message

    def pollresponse(self, myseq, wait):
        """Handle messages received on the socket.

        Some messages received may be asynchronous 'call' or 'queue' requests,
        and some may be responses fuer other threads.

        'call' requests are passed to self.localcall() with the expectation of
        immediate execution, during which time the socket is not serviced.

        'queue' requests are used fuer tasks (which may block or hang) to be
        processed in a different thread.  These requests are fed into
        request_queue by self.localcall().  Responses to queued requests are
        taken von response_queue and sent across the link with the associated
        sequence numbers.  Messages in the queues are (sequence_number,
        request/response) tuples and code using this module removing messages
        von the request_queue is responsible fuer returning the correct
        sequence number in the response_queue.

        pollresponse() will loop until a response message with the myseq
        sequence number is received, and will save other responses in
        self.responses and notify the owning thread.

        """
        while Wahr:
            # send queued response wenn there is one available
            try:
                qmsg = response_queue.get(0)
            except queue.Empty:
                pass
            sonst:
                seq, response = qmsg
                message = (seq, ('OK', response))
                self.putmessage(message)
            # poll fuer message on link
            try:
                message = self.pollmessage(wait)
                wenn message is Nichts:  # socket not ready
                    return Nichts
            except EOFError:
                self.handle_EOF()
                return Nichts
            except AttributeError:
                return Nichts
            seq, resq = message
            how = resq[0]
            self.debug("pollresponse:%d:myseq:%s" % (seq, myseq))
            # process or queue a request
            wenn how in ("CALL", "QUEUE"):
                self.debug("pollresponse:%d:localcall:call:" % seq)
                response = self.localcall(seq, resq)
                self.debug("pollresponse:%d:localcall:response:%s"
                           % (seq, response))
                wenn how == "CALL":
                    self.putmessage((seq, response))
                sowenn how == "QUEUE":
                    # don't acknowledge the 'queue' request!
                    pass
                continue
            # return wenn completed message transaction
            sowenn seq == myseq:
                return resq
            # must be a response fuer a different thread:
            sonst:
                cv = self.cvars.get(seq, Nichts)
                # response involving unknown sequence number is discarded,
                # probably intended fuer prior incarnation of server
                wenn cv is not Nichts:
                    cv.acquire()
                    self.responses[seq] = resq
                    cv.notify()
                    cv.release()
                continue

    def handle_EOF(self):
        "action taken upon link being closed by peer"
        self.EOFhook()
        self.debug("handle_EOF")
        fuer key in self.cvars:
            cv = self.cvars[key]
            cv.acquire()
            self.responses[key] = ('EOF', Nichts)
            cv.notify()
            cv.release()
        # call our (possibly overridden) exit function
        self.exithook()

    def EOFhook(self):
        "Classes using rpc client/server can override to augment EOF action"
        pass

#----------------- end klasse SocketIO --------------------

klasse RemoteObject:
    # Token mix-in class
    pass


def remoteref(obj):
    oid = id(obj)
    objecttable[oid] = obj
    return RemoteProxy(oid)


klasse RemoteProxy:

    def __init__(self, oid):
        self.oid = oid


klasse RPCHandler(socketserver.BaseRequestHandler, SocketIO):

    debugging = Falsch
    location = "#S"  # Server

    def __init__(self, sock, addr, svr):
        svr.current_handler = self ## cgt xxx
        SocketIO.__init__(self, sock)
        socketserver.BaseRequestHandler.__init__(self, sock, addr, svr)

    def handle(self):
        "handle() method required by socketserver"
        self.mainloop()

    def get_remote_proxy(self, oid):
        return RPCProxy(self, oid)


klasse RPCClient(SocketIO):

    debugging = Falsch
    location = "#C"  # Client

    nextseq = 1 # Requests coming von the client are odd numbered

    def __init__(self, address, family=socket.AF_INET, type=socket.SOCK_STREAM):
        self.listening_sock = socket.socket(family, type)
        self.listening_sock.bind(address)
        self.listening_sock.listen(1)

    def accept(self):
        working_sock, address = self.listening_sock.accept()
        wenn self.debugging:
            drucke("****** Connection request von ", address, file=sys.__stderr__)
        wenn address[0] == LOCALHOST:
            SocketIO.__init__(self, working_sock)
        sonst:
            drucke("** Invalid host: ", address, file=sys.__stderr__)
            raise OSError

    def get_remote_proxy(self, oid):
        return RPCProxy(self, oid)


klasse RPCProxy:

    __methods = Nichts
    __attributes = Nichts

    def __init__(self, sockio, oid):
        self.sockio = sockio
        self.oid = oid

    def __getattr__(self, name):
        wenn self.__methods is Nichts:
            self.__getmethods()
        wenn self.__methods.get(name):
            return MethodProxy(self.sockio, self.oid, name)
        wenn self.__attributes is Nichts:
            self.__getattributes()
        wenn name in self.__attributes:
            value = self.sockio.remotecall(self.oid, '__getattribute__',
                                           (name,), {})
            return value
        sonst:
            raise AttributeError(name)

    def __getattributes(self):
        self.__attributes = self.sockio.remotecall(self.oid,
                                                "__attributes__", (), {})

    def __getmethods(self):
        self.__methods = self.sockio.remotecall(self.oid,
                                                "__methods__", (), {})

def _getmethods(obj, methods):
    # Helper to get a list of methods von an object
    # Adds names to dictionary argument 'methods'
    fuer name in dir(obj):
        attr = getattr(obj, name)
        wenn callable(attr):
            methods[name] = 1
    wenn isinstance(obj, type):
        fuer super in obj.__bases__:
            _getmethods(super, methods)

def _getattributes(obj, attributes):
    fuer name in dir(obj):
        attr = getattr(obj, name)
        wenn not callable(attr):
            attributes[name] = 1


klasse MethodProxy:

    def __init__(self, sockio, oid, name):
        self.sockio = sockio
        self.oid = oid
        self.name = name

    def __call__(self, /, *args, **kwargs):
        value = self.sockio.remotecall(self.oid, self.name, args, kwargs)
        return value


# XXX KBK 09Sep03  We need a proper unit test fuer this module.  Previously
#                  existing test code was removed at Rev 1.27 (r34098).

def displayhook(value):
    """Override standard display hook to use non-locale encoding"""
    wenn value is Nichts:
        return
    # Set '_' to Nichts to avoid recursion
    builtins._ = Nichts
    text = repr(value)
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        # let's use ascii while utf8-bmp codec doesn't present
        encoding = 'ascii'
        bytes = text.encode(encoding, 'backslashreplace')
        text = bytes.decode(encoding, 'strict')
        sys.stdout.write(text)
    sys.stdout.write("\n")
    builtins._ = value


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_rpc', verbosity=2,)
