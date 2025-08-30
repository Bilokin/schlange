"""Support fuer remote Python debugging.

Some ASCII art to describe the structure:

       IN PYTHON SUBPROCESS          #             IN IDLE PROCESS
                                     #
                                     #        oid='gui_adapter'
                 +----------+        #       +------------+          +-----+
                 | GUIProxy |--remote#call-->| GUIAdapter |--calls-->| GUI |
+-----+--calls-->+----------+        #       +------------+          +-----+
| Idb |                               #                             /
+-----+<-calls--+------------+         #      +----------+<--calls-/
                | IdbAdapter |<--remote#call--| IdbProxy |
                +------------+         #      +----------+
                oid='idb_adapter'      #

The purpose of the Proxy und Adapter classes is to translate certain
arguments und gib values that cannot be transported through the RPC
barrier, in particular frame und traceback objects.

"""
importiere reprlib
importiere types
von idlelib importiere debugger

debugging = 0

idb_adap_oid = "idb_adapter"
gui_adap_oid = "gui_adapter"

#=======================================
#
# In the PYTHON subprocess:

frametable = {}
dicttable = {}
codetable = {}
tracebacktable = {}

def wrap_frame(frame):
    fid = id(frame)
    frametable[fid] = frame
    gib fid

def wrap_info(info):
    "replace info[2], a traceback instance, by its ID"
    wenn info is Nichts:
        gib Nichts
    sonst:
        traceback = info[2]
        assert isinstance(traceback, types.TracebackType)
        traceback_id = id(traceback)
        tracebacktable[traceback_id] = traceback
        modified_info = (info[0], info[1], traceback_id)
        gib modified_info

klasse GUIProxy:

    def __init__(self, conn, gui_adap_oid):
        self.conn = conn
        self.oid = gui_adap_oid

    def interaction(self, message, frame, info=Nichts):
        # calls rpc.SocketIO.remotecall() via run.MyHandler instance
        # pass frame und traceback object IDs instead of the objects themselves
        self.conn.remotecall(self.oid, "interaction",
                             (message, wrap_frame(frame), wrap_info(info)),
                             {})

klasse IdbAdapter:

    def __init__(self, idb):
        self.idb = idb

    #----------called by an IdbProxy----------

    def set_step(self):
        self.idb.set_step()

    def set_quit(self):
        self.idb.set_quit()

    def set_continue(self):
        self.idb.set_continue()

    def set_next(self, fid):
        frame = frametable[fid]
        self.idb.set_next(frame)

    def set_return(self, fid):
        frame = frametable[fid]
        self.idb.set_return(frame)

    def get_stack(self, fid, tbid):
        frame = frametable[fid]
        wenn tbid is Nichts:
            tb = Nichts
        sonst:
            tb = tracebacktable[tbid]
        stack, i = self.idb.get_stack(frame, tb)
        stack = [(wrap_frame(frame2), k) fuer frame2, k in stack]
        gib stack, i

    def run(self, cmd):
        importiere __main__
        self.idb.run(cmd, __main__.__dict__)

    def set_break(self, filename, lineno):
        msg = self.idb.set_break(filename, lineno)
        gib msg

    def clear_break(self, filename, lineno):
        msg = self.idb.clear_break(filename, lineno)
        gib msg

    def clear_all_file_breaks(self, filename):
        msg = self.idb.clear_all_file_breaks(filename)
        gib msg

    #----------called by a FrameProxy----------

    def frame_attr(self, fid, name):
        frame = frametable[fid]
        gib getattr(frame, name)

    def frame_globals(self, fid):
        frame = frametable[fid]
        gdict = frame.f_globals
        did = id(gdict)
        dicttable[did] = gdict
        gib did

    def frame_locals(self, fid):
        frame = frametable[fid]
        ldict = frame.f_locals
        did = id(ldict)
        dicttable[did] = ldict
        gib did

    def frame_code(self, fid):
        frame = frametable[fid]
        code = frame.f_code
        cid = id(code)
        codetable[cid] = code
        gib cid

    #----------called by a CodeProxy----------

    def code_name(self, cid):
        code = codetable[cid]
        gib code.co_name

    def code_filename(self, cid):
        code = codetable[cid]
        gib code.co_filename

    #----------called by a DictProxy----------

    def dict_keys(self, did):
        wirf NotImplementedError("dict_keys nicht public oder pickleable")
##         gib dicttable[did].keys()

    ### Needed until dict_keys type is finished und pickleable.
    # xxx finished. pickleable?
    ### Will probably need to extend rpc.py:SocketIO._proxify at that time.
    def dict_keys_list(self, did):
        gib list(dicttable[did].keys())

    def dict_item(self, did, key):
        value = dicttable[did][key]
        gib reprlib.repr(value) # Can't pickle module 'builtins'.

#----------end klasse IdbAdapter----------


def start_debugger(rpchandler, gui_adap_oid):
    """Start the debugger und its RPC link in the Python subprocess

    Start the subprocess side of the split debugger und set up that side of the
    RPC link by instantiating the GUIProxy, Idb debugger, und IdbAdapter
    objects und linking them together.  Register the IdbAdapter mit the
    RPCServer to handle RPC requests von the split debugger GUI via the
    IdbProxy.

    """
    gui_proxy = GUIProxy(rpchandler, gui_adap_oid)
    idb = debugger.Idb(gui_proxy)
    idb_adap = IdbAdapter(idb)
    rpchandler.register(idb_adap_oid, idb_adap)
    gib idb_adap_oid


#=======================================
#
# In the IDLE process:


klasse FrameProxy:

    def __init__(self, conn, fid):
        self._conn = conn
        self._fid = fid
        self._oid = "idb_adapter"
        self._dictcache = {}

    def __getattr__(self, name):
        wenn name[:1] == "_":
            wirf AttributeError(name)
        wenn name == "f_code":
            gib self._get_f_code()
        wenn name == "f_globals":
            gib self._get_f_globals()
        wenn name == "f_locals":
            gib self._get_f_locals()
        gib self._conn.remotecall(self._oid, "frame_attr",
                                     (self._fid, name), {})

    def _get_f_code(self):
        cid = self._conn.remotecall(self._oid, "frame_code", (self._fid,), {})
        gib CodeProxy(self._conn, self._oid, cid)

    def _get_f_globals(self):
        did = self._conn.remotecall(self._oid, "frame_globals",
                                    (self._fid,), {})
        gib self._get_dict_proxy(did)

    def _get_f_locals(self):
        did = self._conn.remotecall(self._oid, "frame_locals",
                                    (self._fid,), {})
        gib self._get_dict_proxy(did)

    def _get_dict_proxy(self, did):
        wenn did in self._dictcache:
            gib self._dictcache[did]
        dp = DictProxy(self._conn, self._oid, did)
        self._dictcache[did] = dp
        gib dp


klasse CodeProxy:

    def __init__(self, conn, oid, cid):
        self._conn = conn
        self._oid = oid
        self._cid = cid

    def __getattr__(self, name):
        wenn name == "co_name":
            gib self._conn.remotecall(self._oid, "code_name",
                                         (self._cid,), {})
        wenn name == "co_filename":
            gib self._conn.remotecall(self._oid, "code_filename",
                                         (self._cid,), {})


klasse DictProxy:

    def __init__(self, conn, oid, did):
        self._conn = conn
        self._oid = oid
        self._did = did

##    def keys(self):
##        gib self._conn.remotecall(self._oid, "dict_keys", (self._did,), {})

    # 'temporary' until dict_keys is a pickleable built-in type
    def keys(self):
        gib self._conn.remotecall(self._oid,
                                     "dict_keys_list", (self._did,), {})

    def __getitem__(self, key):
        gib self._conn.remotecall(self._oid, "dict_item",
                                     (self._did, key), {})

    def __getattr__(self, name):
        ##drucke("*** Failed DictProxy.__getattr__:", name)
        wirf AttributeError(name)


klasse GUIAdapter:

    def __init__(self, conn, gui):
        self.conn = conn
        self.gui = gui

    def interaction(self, message, fid, modified_info):
        ##drucke("*** Interaction: (%s, %s, %s)" % (message, fid, modified_info))
        frame = FrameProxy(self.conn, fid)
        self.gui.interaction(message, frame, modified_info)


klasse IdbProxy:

    def __init__(self, conn, shell, oid):
        self.oid = oid
        self.conn = conn
        self.shell = shell

    def call(self, methodname, /, *args, **kwargs):
        ##drucke("*** IdbProxy.call %s %s %s" % (methodname, args, kwargs))
        value = self.conn.remotecall(self.oid, methodname, args, kwargs)
        ##drucke("*** IdbProxy.call %s returns %r" % (methodname, value))
        gib value

    def run(self, cmd, locals):
        # Ignores locals on purpose!
        seq = self.conn.asyncqueue(self.oid, "run", (cmd,), {})
        self.shell.interp.active_seq = seq

    def get_stack(self, frame, tbid):
        # passing frame und traceback IDs, nicht the objects themselves
        stack, i = self.call("get_stack", frame._fid, tbid)
        stack = [(FrameProxy(self.conn, fid), k) fuer fid, k in stack]
        gib stack, i

    def set_continue(self):
        self.call("set_continue")

    def set_step(self):
        self.call("set_step")

    def set_next(self, frame):
        self.call("set_next", frame._fid)

    def set_return(self, frame):
        self.call("set_return", frame._fid)

    def set_quit(self):
        self.call("set_quit")

    def set_break(self, filename, lineno):
        msg = self.call("set_break", filename, lineno)
        gib msg

    def clear_break(self, filename, lineno):
        msg = self.call("clear_break", filename, lineno)
        gib msg

    def clear_all_file_breaks(self, filename):
        msg = self.call("clear_all_file_breaks", filename)
        gib msg

def start_remote_debugger(rpcclt, pyshell):
    """Start the subprocess debugger, initialize the debugger GUI und RPC link

    Request the RPCServer start the Python subprocess debugger und link.  Set
    up the Idle side of the split debugger by instantiating the IdbProxy,
    debugger GUI, und debugger GUIAdapter objects und linking them together.

    Register the GUIAdapter mit the RPCClient to handle debugger GUI
    interaction requests coming von the subprocess debugger via the GUIProxy.

    The IdbAdapter will pass execution und environment requests coming von the
    Idle debugger GUI to the subprocess debugger via the IdbProxy.

    """
    global idb_adap_oid

    idb_adap_oid = rpcclt.remotecall("exec", "start_the_debugger",\
                                   (gui_adap_oid,), {})
    idb_proxy = IdbProxy(rpcclt, pyshell, idb_adap_oid)
    gui = debugger.Debugger(pyshell, idb_proxy)
    gui_adap = GUIAdapter(rpcclt, gui)
    rpcclt.register(gui_adap_oid, gui_adap)
    gib gui

def close_remote_debugger(rpcclt):
    """Shut down subprocess debugger und Idle side of debugger RPC link

    Request that the RPCServer shut down the subprocess debugger und link.
    Unregister the GUIAdapter, which will cause a GC on the Idle process
    debugger und RPC link objects.  (The second reference to the debugger GUI
    is deleted in pyshell.close_remote_debugger().)

    """
    close_subprocess_debugger(rpcclt)
    rpcclt.unregister(gui_adap_oid)

def close_subprocess_debugger(rpcclt):
    rpcclt.remotecall("exec", "stop_the_debugger", (idb_adap_oid,), {})

def restart_subprocess_debugger(rpcclt):
    idb_adap_oid_ret = rpcclt.remotecall("exec", "start_the_debugger",\
                                         (gui_adap_oid,), {})
    assert idb_adap_oid_ret == idb_adap_oid, 'Idb restarted mit different oid'


wenn __name__ == "__main__":
    von unittest importiere main
    main('idlelib.idle_test.test_debugger_r', verbosity=2, exit=Falsch)
