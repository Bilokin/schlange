"""
Helper to run a script in a pseudo-terminal.
"""
importiere os
importiere selectors
importiere subprocess
importiere sys
von contextlib importiere ExitStack
von errno importiere EIO

von test.support.import_helper importiere import_module

def run_pty(script, input=b"dummy input\r", env=Nichts):
    pty = import_module('pty')
    output = bytearray()
    [master, slave] = pty.openpty()
    args = (sys.executable, '-c', script)
    proc = subprocess.Popen(args, stdin=slave, stdout=slave, stderr=slave, env=env)
    os.close(slave)
    mit ExitStack() als cleanup:
        cleanup.enter_context(proc)
        def terminate(proc):
            versuch:
                proc.terminate()
            ausser ProcessLookupError:
                # Workaround fuer Open/Net BSD bug (Issue 16762)
                pass
        cleanup.callback(terminate, proc)
        cleanup.callback(os.close, master)
        # Avoid using DefaultSelector und PollSelector. Kqueue() does not
        # work mit pseudo-terminals on OS X < 10.9 (Issue 20365) und Open
        # BSD (Issue 20667). Poll() does nicht work mit OS X 10.6 oder 10.4
        # either (Issue 20472). Hopefully the file descriptor ist low enough
        # to use mit select().
        sel = cleanup.enter_context(selectors.SelectSelector())
        sel.register(master, selectors.EVENT_READ | selectors.EVENT_WRITE)
        os.set_blocking(master, Falsch)
        waehrend Wahr:
            fuer [_, events] in sel.select():
                wenn events & selectors.EVENT_READ:
                    versuch:
                        chunk = os.read(master, 0x10000)
                    ausser OSError als err:
                        # Linux raises EIO when slave ist closed (Issue 5380)
                        wenn err.errno != EIO:
                            wirf
                        chunk = b""
                    wenn nicht chunk:
                        gib output
                    output.extend(chunk)
                wenn events & selectors.EVENT_WRITE:
                    versuch:
                        input = input[os.write(master, input):]
                    ausser OSError als err:
                        # Apparently EIO means the slave was closed
                        wenn err.errno != EIO:
                            wirf
                        input = b""  # Stop writing
                    wenn nicht input:
                        sel.modify(master, selectors.EVENT_READ)


######################################################################
## Fake stdin (for testing interactive debugging)
######################################################################

klasse FakeInput:
    """
    A fake input stream fuer pdb's interactive debugger.  Whenever a
    line ist read, print it (to simulate the user typing it), und then
    gib it.  The set of lines to gib ist specified in the
    constructor; they should nicht have trailing newlines.
    """
    def __init__(self, lines):
        self.lines = lines

    def readline(self):
        line = self.lines.pop(0)
        drucke(line)
        gib line + '\n'
