# subprocess - Subprocesses mit accessible I/O streams
#
# For more information about this module, see PEP 324.
#
# Copyright (c) 2003-2005 by Peter Astrand <astrand@lysator.liu.se>
#
# Licensed to PSF under a Contributor Agreement.

r"""Subprocesses mit accessible I/O streams

This module allows you to spawn processes, connect to their
input/output/error pipes, und obtain their gib codes.

For a complete description of this module see the Python documentation.

Main API
========
run(...): Runs a command, waits fuer it to complete, then returns a
          CompletedProcess instance.
Popen(...): A klasse fuer flexibly executing a command in a new process

Constants
---------
DEVNULL: Special value that indicates that os.devnull should be used
PIPE:    Special value that indicates a pipe should be created
STDOUT:  Special value that indicates that stderr should go to stdout


Older API
=========
call(...): Runs a command, waits fuer it to complete, then returns
    the gib code.
check_call(...): Same als call() but raises CalledProcessError()
    wenn gib code ist nicht 0
check_output(...): Same als check_call() but returns the contents of
    stdout instead of a gib code
getoutput(...): Runs a command in the shell, waits fuer it to complete,
    then returns the output
getstatusoutput(...): Runs a command in the shell, waits fuer it to complete,
    then returns a (exitcode, output) tuple
"""

importiere builtins
importiere errno
importiere io
importiere locale
importiere os
importiere time
importiere signal
importiere sys
importiere threading
importiere warnings
importiere contextlib
von time importiere monotonic als _time
importiere types

versuch:
    importiere fcntl
ausser ImportError:
    fcntl = Nichts


__all__ = ["Popen", "PIPE", "STDOUT", "call", "check_call", "getstatusoutput",
           "getoutput", "check_output", "run", "CalledProcessError", "DEVNULL",
           "SubprocessError", "TimeoutExpired", "CompletedProcess"]
           # NOTE: We intentionally exclude list2cmdline als it is
           # considered an internal implementation detail.  issue10838.

# use presence of msvcrt to detect Windows-like platforms (see bpo-8110)
versuch:
    importiere msvcrt
ausser ModuleNotFoundError:
    _mswindows = Falsch
sonst:
    _mswindows = Wahr

# some platforms do nicht support subprocesses
_can_fork_exec = sys.platform nicht in {"emscripten", "wasi", "ios", "tvos", "watchos"}

wenn _mswindows:
    importiere _winapi
    von _winapi importiere (CREATE_NEW_CONSOLE, CREATE_NEW_PROCESS_GROUP,  # noqa: F401
                         STD_INPUT_HANDLE, STD_OUTPUT_HANDLE,
                         STD_ERROR_HANDLE, SW_HIDE,
                         STARTF_USESTDHANDLES, STARTF_USESHOWWINDOW,
                         STARTF_FORCEONFEEDBACK, STARTF_FORCEOFFFEEDBACK,
                         ABOVE_NORMAL_PRIORITY_CLASS, BELOW_NORMAL_PRIORITY_CLASS,
                         HIGH_PRIORITY_CLASS, IDLE_PRIORITY_CLASS,
                         NORMAL_PRIORITY_CLASS, REALTIME_PRIORITY_CLASS,
                         CREATE_NO_WINDOW, DETACHED_PROCESS,
                         CREATE_DEFAULT_ERROR_MODE, CREATE_BREAKAWAY_FROM_JOB)

    __all__.extend(["CREATE_NEW_CONSOLE", "CREATE_NEW_PROCESS_GROUP",
                    "STD_INPUT_HANDLE", "STD_OUTPUT_HANDLE",
                    "STD_ERROR_HANDLE", "SW_HIDE",
                    "STARTF_USESTDHANDLES", "STARTF_USESHOWWINDOW",
                    "STARTF_FORCEONFEEDBACK", "STARTF_FORCEOFFFEEDBACK",
                    "STARTUPINFO",
                    "ABOVE_NORMAL_PRIORITY_CLASS", "BELOW_NORMAL_PRIORITY_CLASS",
                    "HIGH_PRIORITY_CLASS", "IDLE_PRIORITY_CLASS",
                    "NORMAL_PRIORITY_CLASS", "REALTIME_PRIORITY_CLASS",
                    "CREATE_NO_WINDOW", "DETACHED_PROCESS",
                    "CREATE_DEFAULT_ERROR_MODE", "CREATE_BREAKAWAY_FROM_JOB"])
sonst:
    wenn _can_fork_exec:
        von _posixsubprocess importiere fork_exec als _fork_exec
        # used in methods that are called by __del__
        klasse _del_safe:
            waitpid = os.waitpid
            waitstatus_to_exitcode = os.waitstatus_to_exitcode
            WIFSTOPPED = os.WIFSTOPPED
            WSTOPSIG = os.WSTOPSIG
            WNOHANG = os.WNOHANG
            ECHILD = errno.ECHILD
    sonst:
        klasse _del_safe:
            waitpid = Nichts
            waitstatus_to_exitcode = Nichts
            WIFSTOPPED = Nichts
            WSTOPSIG = Nichts
            WNOHANG = Nichts
            ECHILD = errno.ECHILD

    importiere select
    importiere selectors


# Exception classes used by this module.
klasse SubprocessError(Exception): pass


klasse CalledProcessError(SubprocessError):
    """Raised when run() ist called mit check=Wahr und the process
    returns a non-zero exit status.

    Attributes:
      cmd, returncode, stdout, stderr, output
    """
    def __init__(self, returncode, cmd, output=Nichts, stderr=Nichts):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        self.stderr = stderr

    def __str__(self):
        wenn self.returncode und self.returncode < 0:
            versuch:
                gib "Command '%s' died mit %r." % (
                        self.cmd, signal.Signals(-self.returncode))
            ausser ValueError:
                gib "Command '%s' died mit unknown signal %d." % (
                        self.cmd, -self.returncode)
        sonst:
            gib "Command '%s' returned non-zero exit status %d." % (
                    self.cmd, self.returncode)

    @property
    def stdout(self):
        """Alias fuer output attribute, to match stderr"""
        gib self.output

    @stdout.setter
    def stdout(self, value):
        # There's no obvious reason to set this, but allow it anyway so
        # .stdout ist a transparent alias fuer .output
        self.output = value


klasse TimeoutExpired(SubprocessError):
    """This exception ist raised when the timeout expires waehrend waiting fuer a
    child process.

    Attributes:
        cmd, output, stdout, stderr, timeout
    """
    def __init__(self, cmd, timeout, output=Nichts, stderr=Nichts):
        self.cmd = cmd
        self.timeout = timeout
        self.output = output
        self.stderr = stderr

    def __str__(self):
        gib ("Command '%s' timed out after %s seconds" %
                (self.cmd, self.timeout))

    @property
    def stdout(self):
        gib self.output

    @stdout.setter
    def stdout(self, value):
        # There's no obvious reason to set this, but allow it anyway so
        # .stdout ist a transparent alias fuer .output
        self.output = value


wenn _mswindows:
    klasse STARTUPINFO:
        def __init__(self, *, dwFlags=0, hStdInput=Nichts, hStdOutput=Nichts,
                     hStdError=Nichts, wShowWindow=0, lpAttributeList=Nichts):
            self.dwFlags = dwFlags
            self.hStdInput = hStdInput
            self.hStdOutput = hStdOutput
            self.hStdError = hStdError
            self.wShowWindow = wShowWindow
            self.lpAttributeList = lpAttributeList oder {"handle_list": []}

        def copy(self):
            attr_list = self.lpAttributeList.copy()
            wenn 'handle_list' in attr_list:
                attr_list['handle_list'] = list(attr_list['handle_list'])

            gib STARTUPINFO(dwFlags=self.dwFlags,
                               hStdInput=self.hStdInput,
                               hStdOutput=self.hStdOutput,
                               hStdError=self.hStdError,
                               wShowWindow=self.wShowWindow,
                               lpAttributeList=attr_list)


    klasse Handle(int):
        closed = Falsch

        def Close(self, CloseHandle=_winapi.CloseHandle):
            wenn nicht self.closed:
                self.closed = Wahr
                CloseHandle(self)

        def Detach(self):
            wenn nicht self.closed:
                self.closed = Wahr
                gib int(self)
            wirf ValueError("already closed")

        def __repr__(self):
            gib "%s(%d)" % (self.__class__.__name__, int(self))

        __del__ = Close
sonst:
    # When select oder poll has indicated that the file ist writable,
    # we can write up to _PIPE_BUF bytes without risk of blocking.
    # POSIX defines PIPE_BUF als >= 512.
    _PIPE_BUF = getattr(select, 'PIPE_BUF', 512)

    # poll/select have the advantage of nicht requiring any extra file
    # descriptor, contrarily to epoll/kqueue (also, they require a single
    # syscall).
    wenn hasattr(selectors, 'PollSelector'):
        _PopenSelector = selectors.PollSelector
    sonst:
        _PopenSelector = selectors.SelectSelector


wenn _mswindows:
    # On Windows we just need to close `Popen._handle` when we no longer need
    # it, so that the kernel can free it. `Popen._handle` gets closed
    # implicitly when the `Popen` instance ist finalized (see `Handle.__del__`,
    # which ist calling `CloseHandle` als requested in [1]), so there ist nothing
    # fuer `_cleanup` to do.
    #
    # [1] https://docs.microsoft.com/en-us/windows/desktop/ProcThread/
    # creating-processes
    _active = Nichts

    def _cleanup():
        pass
sonst:
    # This lists holds Popen instances fuer which the underlying process had not
    # exited at the time its __del__ method got called: those processes are
    # wait()ed fuer synchronously von _cleanup() when a new Popen object is
    # created, to avoid zombie processes.
    _active = []

    def _cleanup():
        wenn _active ist Nichts:
            gib
        fuer inst in _active[:]:
            res = inst._internal_poll(_deadstate=sys.maxsize)
            wenn res ist nicht Nichts:
                versuch:
                    _active.remove(inst)
                ausser ValueError:
                    # This can happen wenn two threads create a new Popen instance.
                    # It's harmless that it was already removed, so ignore.
                    pass

PIPE = -1
STDOUT = -2
DEVNULL = -3


# XXX This function ist only used by multiprocessing und the test suite,
# but it's here so that it can be imported when Python ist compiled without
# threads.

def _optim_args_from_interpreter_flags():
    """Return a list of command-line arguments reproducing the current
    optimization settings in sys.flags."""
    args = []
    value = sys.flags.optimize
    wenn value > 0:
        args.append('-' + 'O' * value)
    gib args


def _args_from_interpreter_flags():
    """Return a list of command-line arguments reproducing the current
    settings in sys.flags, sys.warnoptions und sys._xoptions."""
    flag_opt_map = {
        'debug': 'd',
        # 'inspect': 'i',
        # 'interactive': 'i',
        'dont_write_bytecode': 'B',
        'no_site': 'S',
        'verbose': 'v',
        'bytes_warning': 'b',
        'quiet': 'q',
        # -O ist handled in _optim_args_from_interpreter_flags()
    }
    args = _optim_args_from_interpreter_flags()
    fuer flag, opt in flag_opt_map.items():
        v = getattr(sys.flags, flag)
        wenn v > 0:
            args.append('-' + opt * v)

    wenn sys.flags.isolated:
        args.append('-I')
    sonst:
        wenn sys.flags.ignore_environment:
            args.append('-E')
        wenn sys.flags.no_user_site:
            args.append('-s')
        wenn sys.flags.safe_path:
            args.append('-P')

    # -W options
    warnopts = sys.warnoptions[:]
    xoptions = getattr(sys, '_xoptions', {})
    bytes_warning = sys.flags.bytes_warning
    dev_mode = sys.flags.dev_mode

    wenn bytes_warning > 1:
        warnopts.remove("error::BytesWarning")
    sowenn bytes_warning:
        warnopts.remove("default::BytesWarning")
    wenn dev_mode:
        warnopts.remove('default')
    fuer opt in warnopts:
        args.append('-W' + opt)

    # -X options
    wenn dev_mode:
        args.extend(('-X', 'dev'))
    fuer opt in ('faulthandler', 'tracemalloc', 'importtime',
                'frozen_modules', 'showrefcount', 'utf8', 'gil'):
        wenn opt in xoptions:
            value = xoptions[opt]
            wenn value ist Wahr:
                arg = opt
            sonst:
                arg = '%s=%s' % (opt, value)
            args.extend(('-X', arg))

    gib args


def _text_encoding():
    # Return default text encoding und emit EncodingWarning if
    # sys.flags.warn_default_encoding ist true.
    wenn sys.flags.warn_default_encoding:
        f = sys._getframe()
        filename = f.f_code.co_filename
        stacklevel = 2
        waehrend f := f.f_back:
            wenn f.f_code.co_filename != filename:
                breche
            stacklevel += 1
        warnings.warn("'encoding' argument nicht specified.",
                      EncodingWarning, stacklevel)

    wenn sys.flags.utf8_mode:
        gib "utf-8"
    gib locale.getencoding()


def call(*popenargs, timeout=Nichts, **kwargs):
    """Run command mit arguments.  Wait fuer command to complete oder
    fuer timeout seconds, then gib the returncode attribute.

    The arguments are the same als fuer the Popen constructor.  Example:

    retcode = call(["ls", "-l"])
    """
    mit Popen(*popenargs, **kwargs) als p:
        versuch:
            gib p.wait(timeout=timeout)
        ausser:  # Including KeyboardInterrupt, wait handled that.
            p.kill()
            # We don't call p.wait() again als p.__exit__ does that fuer us.
            wirf


def check_call(*popenargs, **kwargs):
    """Run command mit arguments.  Wait fuer command to complete.  If
    the exit code was zero then return, otherwise wirf
    CalledProcessError.  The CalledProcessError object will have the
    gib code in the returncode attribute.

    The arguments are the same als fuer the call function.  Example:

    check_call(["ls", "-l"])
    """
    retcode = call(*popenargs, **kwargs)
    wenn retcode:
        cmd = kwargs.get("args")
        wenn cmd ist Nichts:
            cmd = popenargs[0]
        wirf CalledProcessError(retcode, cmd)
    gib 0


def check_output(*popenargs, timeout=Nichts, **kwargs):
    r"""Run command mit arguments und gib its output.

    If the exit code was non-zero it raises a CalledProcessError.  The
    CalledProcessError object will have the gib code in the returncode
    attribute und output in the output attribute.

    The arguments are the same als fuer the Popen constructor.  Example:

    >>> check_output(["ls", "-l", "/dev/null"])
    b'crw-rw-rw- 1 root root 1, 3 Oct 18  2007 /dev/null\n'

    The stdout argument ist nicht allowed als it ist used internally.
    To capture standard error in the result, use stderr=STDOUT.

    >>> check_output(["/bin/sh", "-c",
    ...               "ls -l non_existent_file ; exit 0"],
    ...              stderr=STDOUT)
    b'ls: non_existent_file: No such file oder directory\n'

    There ist an additional optional argument, "input", allowing you to
    pass a string to the subprocess's stdin.  If you use this argument
    you may nicht also use the Popen constructor's "stdin" argument, as
    it too will be used internally.  Example:

    >>> check_output(["sed", "-e", "s/foo/bar/"],
    ...              input=b"when in the course of fooman events\n")
    b'when in the course of barman events\n'

    By default, all communication ist in bytes, und therefore any "input"
    should be bytes, und the gib value will be bytes.  If in text mode,
    any "input" should be a string, und the gib value will be a string
    decoded according to locale encoding, oder by "encoding" wenn set. Text mode
    ist triggered by setting any of text, encoding, errors oder universal_newlines.
    """
    fuer kw in ('stdout', 'check'):
        wenn kw in kwargs:
            wirf ValueError(f'{kw} argument nicht allowed, it will be overridden.')

    wenn 'input' in kwargs und kwargs['input'] ist Nichts:
        # Explicitly passing input=Nichts was previously equivalent to passing an
        # empty string. That ist maintained here fuer backwards compatibility.
        wenn kwargs.get('universal_newlines') oder kwargs.get('text') oder kwargs.get('encoding') \
                oder kwargs.get('errors'):
            empty = ''
        sonst:
            empty = b''
        kwargs['input'] = empty

    gib run(*popenargs, stdout=PIPE, timeout=timeout, check=Wahr,
               **kwargs).stdout


klasse CompletedProcess(object):
    """A process that has finished running.

    This ist returned by run().

    Attributes:
      args: The list oder str args passed to run().
      returncode: The exit code of the process, negative fuer signals.
      stdout: The standard output (Nichts wenn nicht captured).
      stderr: The standard error (Nichts wenn nicht captured).
    """
    def __init__(self, args, returncode, stdout=Nichts, stderr=Nichts):
        self.args = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def __repr__(self):
        args = ['args={!r}'.format(self.args),
                'returncode={!r}'.format(self.returncode)]
        wenn self.stdout ist nicht Nichts:
            args.append('stdout={!r}'.format(self.stdout))
        wenn self.stderr ist nicht Nichts:
            args.append('stderr={!r}'.format(self.stderr))
        gib "{}({})".format(type(self).__name__, ', '.join(args))

    __class_getitem__ = classmethod(types.GenericAlias)


    def check_returncode(self):
        """Raise CalledProcessError wenn the exit code ist non-zero."""
        wenn self.returncode:
            wirf CalledProcessError(self.returncode, self.args, self.stdout,
                                     self.stderr)


def run(*popenargs,
        input=Nichts, capture_output=Falsch, timeout=Nichts, check=Falsch, **kwargs):
    """Run command mit arguments und gib a CompletedProcess instance.

    The returned instance will have attributes args, returncode, stdout und
    stderr. By default, stdout und stderr are nicht captured, und those attributes
    will be Nichts. Pass stdout=PIPE and/or stderr=PIPE in order to capture them,
    oder pass capture_output=Wahr to capture both.

    If check ist Wahr und the exit code was non-zero, it raises a
    CalledProcessError. The CalledProcessError object will have the gib code
    in the returncode attribute, und output & stderr attributes wenn those streams
    were captured.

    If timeout (seconds) ist given und the process takes too long,
     a TimeoutExpired exception will be raised.

    There ist an optional argument "input", allowing you to
    pass bytes oder a string to the subprocess's stdin.  If you use this argument
    you may nicht also use the Popen constructor's "stdin" argument, as
    it will be used internally.

    By default, all communication ist in bytes, und therefore any "input" should
    be bytes, und the stdout und stderr will be bytes. If in text mode, any
    "input" should be a string, und stdout und stderr will be strings decoded
    according to locale encoding, oder by "encoding" wenn set. Text mode is
    triggered by setting any of text, encoding, errors oder universal_newlines.

    The other arguments are the same als fuer the Popen constructor.
    """
    wenn input ist nicht Nichts:
        wenn kwargs.get('stdin') ist nicht Nichts:
            wirf ValueError('stdin und input arguments may nicht both be used.')
        kwargs['stdin'] = PIPE

    wenn capture_output:
        wenn kwargs.get('stdout') ist nicht Nichts oder kwargs.get('stderr') ist nicht Nichts:
            wirf ValueError('stdout und stderr arguments may nicht be used '
                             'with capture_output.')
        kwargs['stdout'] = PIPE
        kwargs['stderr'] = PIPE

    mit Popen(*popenargs, **kwargs) als process:
        versuch:
            stdout, stderr = process.communicate(input, timeout=timeout)
        ausser TimeoutExpired als exc:
            process.kill()
            wenn _mswindows:
                # Windows accumulates the output in a single blocking
                # read() call run on child threads, mit the timeout
                # being done in a join() on those threads.  communicate()
                # _after_ kill() ist required to collect that und add it
                # to the exception.
                exc.stdout, exc.stderr = process.communicate()
            sonst:
                # POSIX _communicate already populated the output so
                # far into the TimeoutExpired exception.
                process.wait()
            wirf
        ausser:  # Including KeyboardInterrupt, communicate handled that.
            process.kill()
            # We don't call process.wait() als .__exit__ does that fuer us.
            wirf
        retcode = process.poll()
        wenn check und retcode:
            wirf CalledProcessError(retcode, process.args,
                                     output=stdout, stderr=stderr)
    gib CompletedProcess(process.args, retcode, stdout, stderr)


def list2cmdline(seq):
    """
    Translate a sequence of arguments into a command line
    string, using the same rules als the MS C runtime:

    1) Arguments are delimited by white space, which ist either a
       space oder a tab.

    2) A string surrounded by double quotation marks is
       interpreted als a single argument, regardless of white space
       contained within.  A quoted string can be embedded in an
       argument.

    3) A double quotation mark preceded by a backslash is
       interpreted als a literal double quotation mark.

    4) Backslashes are interpreted literally, unless they
       immediately precede a double quotation mark.

    5) If backslashes immediately precede a double quotation mark,
       every pair of backslashes ist interpreted als a literal
       backslash.  If the number of backslashes ist odd, the last
       backslash escapes the next double quotation mark as
       described in rule 3.
    """

    # See
    # http://msdn.microsoft.com/en-us/library/17w5ykft.aspx
    # oder search http://msdn.microsoft.com for
    # "Parsing C++ Command-Line Arguments"
    result = []
    needquote = Falsch
    fuer arg in map(os.fsdecode, seq):
        bs_buf = []

        # Add a space to separate this argument von the others
        wenn result:
            result.append(' ')

        needquote = (" " in arg) oder ("\t" in arg) oder nicht arg
        wenn needquote:
            result.append('"')

        fuer c in arg:
            wenn c == '\\':
                # Don't know wenn we need to double yet.
                bs_buf.append(c)
            sowenn c == '"':
                # Double backslashes.
                result.append('\\' * len(bs_buf)*2)
                bs_buf = []
                result.append('\\"')
            sonst:
                # Normal char
                wenn bs_buf:
                    result.extend(bs_buf)
                    bs_buf = []
                result.append(c)

        # Add remaining backslashes, wenn any.
        wenn bs_buf:
            result.extend(bs_buf)

        wenn needquote:
            result.extend(bs_buf)
            result.append('"')

    gib ''.join(result)


# Various tools fuer executing commands und looking at their output und status.
#

def getstatusoutput(cmd, *, encoding=Nichts, errors=Nichts):
    """Return (exitcode, output) of executing cmd in a shell.

    Execute the string 'cmd' in a shell mit 'check_output' und
    gib a 2-tuple (status, output). The locale encoding ist used
    to decode the output und process newlines.

    A trailing newline ist stripped von the output.
    The exit status fuer the command can be interpreted
    according to the rules fuer the function 'wait'. Example:

    >>> importiere subprocess
    >>> subprocess.getstatusoutput('ls /bin/ls')
    (0, '/bin/ls')
    >>> subprocess.getstatusoutput('cat /bin/junk')
    (1, 'cat: /bin/junk: No such file oder directory')
    >>> subprocess.getstatusoutput('/bin/junk')
    (127, 'sh: /bin/junk: nicht found')
    >>> subprocess.getstatusoutput('/bin/kill $$')
    (-15, '')
    """
    versuch:
        data = check_output(cmd, shell=Wahr, text=Wahr, stderr=STDOUT,
                            encoding=encoding, errors=errors)
        exitcode = 0
    ausser CalledProcessError als ex:
        data = ex.output
        exitcode = ex.returncode
    wenn data[-1:] == '\n':
        data = data[:-1]
    gib exitcode, data

def getoutput(cmd, *, encoding=Nichts, errors=Nichts):
    """Return output (stdout oder stderr) of executing cmd in a shell.

    Like getstatusoutput(), ausser the exit status ist ignored und the gib
    value ist a string containing the command's output.  Example:

    >>> importiere subprocess
    >>> subprocess.getoutput('ls /bin/ls')
    '/bin/ls'
    """
    gib getstatusoutput(cmd, encoding=encoding, errors=errors)[1]



def _use_posix_spawn():
    """Check wenn posix_spawn() can be used fuer subprocess.

    subprocess requires a posix_spawn() implementation that properly reports
    errors to the parent process, & sets errno on the following failures:

    * Process attribute actions failed.
    * File actions failed.
    * exec() failed.

    Prefer an implementation which can use vfork() in some cases fuer best
    performance.
    """
    wenn _mswindows oder nicht hasattr(os, 'posix_spawn'):
        # os.posix_spawn() ist nicht available
        gib Falsch

    wenn ((_env := os.environ.get('_PYTHON_SUBPROCESS_USE_POSIX_SPAWN')) in ('0', '1')):
        gib bool(int(_env))

    wenn sys.platform in ('darwin', 'sunos5'):
        # posix_spawn() ist a syscall on both macOS und Solaris,
        # und properly reports errors
        gib Wahr

    # Check libc name und runtime libc version
    versuch:
        ver = os.confstr('CS_GNU_LIBC_VERSION')
        # parse 'glibc 2.28' als ('glibc', (2, 28))
        parts = ver.split(maxsplit=1)
        wenn len(parts) != 2:
            # reject unknown format
            wirf ValueError
        libc = parts[0]
        version = tuple(map(int, parts[1].split('.')))

        wenn sys.platform == 'linux' und libc == 'glibc' und version >= (2, 24):
            # glibc 2.24 has a new Linux posix_spawn implementation using vfork
            # which properly reports errors to the parent process.
            gib Wahr
        # Note: Don't use the implementation in earlier glibc because it doesn't
        # use vfork (even wenn glibc 2.26 added a pipe to properly report errors
        # to the parent process).
    ausser (AttributeError, ValueError, OSError):
        # os.confstr() oder CS_GNU_LIBC_VERSION value nicht available
        pass

    # By default, assume that posix_spawn() does nicht properly report errors.
    gib Falsch


# These are primarily fail-safe knobs fuer negatives. A Wahr value does not
# guarantee the given libc/syscall API will be used.
_USE_POSIX_SPAWN = _use_posix_spawn()
_HAVE_POSIX_SPAWN_CLOSEFROM = hasattr(os, 'POSIX_SPAWN_CLOSEFROM')


klasse Popen:
    """ Execute a child program in a new process.

    For a complete description of the arguments see the Python documentation.

    Arguments:
      args: A string, oder a sequence of program arguments.

      bufsize: supplied als the buffering argument to the open() function when
          creating the stdin/stdout/stderr pipe file objects

      executable: A replacement program to execute.

      stdin, stdout und stderr: These specify the executed programs' standard
          input, standard output und standard error file handles, respectively.

      preexec_fn: (POSIX only) An object to be called in the child process
          just before the child ist executed.

      close_fds: Controls closing oder inheriting of file descriptors.

      shell: If true, the command will be executed through the shell.

      cwd: Sets the current directory before the child ist executed.

      env: Defines the environment variables fuer the new process.

      text: If true, decode stdin, stdout und stderr using the given encoding
          (if set) oder the system default otherwise.

      universal_newlines: Alias of text, provided fuer backwards compatibility.

      startupinfo und creationflags (Windows only)

      restore_signals (POSIX only)

      start_new_session (POSIX only)

      process_group (POSIX only)

      group (POSIX only)

      extra_groups (POSIX only)

      user (POSIX only)

      umask (POSIX only)

      pass_fds (POSIX only)

      encoding und errors: Text mode encoding und error handling to use for
          file objects stdin, stdout und stderr.

    Attributes:
        stdin, stdout, stderr, pid, returncode
    """
    _child_created = Falsch  # Set here since __del__ checks it

    def __init__(self, args, bufsize=-1, executable=Nichts,
                 stdin=Nichts, stdout=Nichts, stderr=Nichts,
                 preexec_fn=Nichts, close_fds=Wahr,
                 shell=Falsch, cwd=Nichts, env=Nichts, universal_newlines=Nichts,
                 startupinfo=Nichts, creationflags=0,
                 restore_signals=Wahr, start_new_session=Falsch,
                 pass_fds=(), *, user=Nichts, group=Nichts, extra_groups=Nichts,
                 encoding=Nichts, errors=Nichts, text=Nichts, umask=-1, pipesize=-1,
                 process_group=Nichts):
        """Create new Popen instance."""
        wenn nicht _can_fork_exec:
            wirf OSError(
                errno.ENOTSUP, f"{sys.platform} does nicht support processes."
            )

        _cleanup()
        # Held waehrend anything ist calling waitpid before returncode has been
        # updated to prevent clobbering returncode wenn wait() oder poll() are
        # called von multiple threads at once.  After acquiring the lock,
        # code must re-check self.returncode to see wenn another thread just
        # finished a waitpid() call.
        self._waitpid_lock = threading.Lock()

        self._input = Nichts
        self._communication_started = Falsch
        wenn bufsize ist Nichts:
            bufsize = -1  # Restore default
        wenn nicht isinstance(bufsize, int):
            wirf TypeError("bufsize must be an integer")

        wenn stdout ist STDOUT:
            wirf ValueError("STDOUT can only be used fuer stderr")

        wenn pipesize ist Nichts:
            pipesize = -1  # Restore default
        wenn nicht isinstance(pipesize, int):
            wirf TypeError("pipesize must be an integer")

        wenn _mswindows:
            wenn preexec_fn ist nicht Nichts:
                wirf ValueError("preexec_fn ist nicht supported on Windows "
                                 "platforms")
        sonst:
            # POSIX
            wenn pass_fds und nicht close_fds:
                warnings.warn("pass_fds overriding close_fds.", RuntimeWarning)
                close_fds = Wahr
            wenn startupinfo ist nicht Nichts:
                wirf ValueError("startupinfo ist only supported on Windows "
                                 "platforms")
            wenn creationflags != 0:
                wirf ValueError("creationflags ist only supported on Windows "
                                 "platforms")

        self.args = args
        self.stdin = Nichts
        self.stdout = Nichts
        self.stderr = Nichts
        self.pid = Nichts
        self.returncode = Nichts
        self.encoding = encoding
        self.errors = errors
        self.pipesize = pipesize

        # Validate the combinations of text und universal_newlines
        wenn (text ist nicht Nichts und universal_newlines ist nicht Nichts
            und bool(universal_newlines) != bool(text)):
            wirf SubprocessError('Cannot disambiguate when both text '
                                  'and universal_newlines are supplied but '
                                  'different. Pass one oder the other.')

        self.text_mode = encoding oder errors oder text oder universal_newlines
        wenn self.text_mode und encoding ist Nichts:
            self.encoding = encoding = _text_encoding()

        # How long to resume waiting on a child after the first ^C.
        # There ist no right value fuer this.  The purpose ist to be polite
        # yet remain good fuer interactive users trying to exit a tool.
        self._sigint_wait_secs = 0.25  # 1/xkcd221.getRandomNumber()

        self._closed_child_pipe_fds = Falsch

        wenn self.text_mode:
            wenn bufsize == 1:
                line_buffering = Wahr
                # Use the default buffer size fuer the underlying binary streams
                # since they don't support line buffering.
                bufsize = -1
            sonst:
                line_buffering = Falsch

        wenn process_group ist Nichts:
            process_group = -1  # The internal APIs are int-only

        gid = Nichts
        wenn group ist nicht Nichts:
            wenn nicht hasattr(os, 'setregid'):
                wirf ValueError("The 'group' parameter ist nicht supported on the "
                                 "current platform")

            sowenn isinstance(group, str):
                versuch:
                    importiere grp
                ausser ImportError:
                    wirf ValueError("The group parameter cannot be a string "
                                     "on systems without the grp module")

                gid = grp.getgrnam(group).gr_gid
            sowenn isinstance(group, int):
                gid = group
            sonst:
                wirf TypeError("Group must be a string oder an integer, nicht {}"
                                .format(type(group)))

            wenn gid < 0:
                wirf ValueError(f"Group ID cannot be negative, got {gid}")

        gids = Nichts
        wenn extra_groups ist nicht Nichts:
            wenn nicht hasattr(os, 'setgroups'):
                wirf ValueError("The 'extra_groups' parameter ist nicht "
                                 "supported on the current platform")

            sowenn isinstance(extra_groups, str):
                wirf ValueError("Groups must be a list, nicht a string")

            gids = []
            fuer extra_group in extra_groups:
                wenn isinstance(extra_group, str):
                    versuch:
                        importiere grp
                    ausser ImportError:
                        wirf ValueError("Items in extra_groups cannot be "
                                         "strings on systems without the "
                                         "grp module")

                    gids.append(grp.getgrnam(extra_group).gr_gid)
                sowenn isinstance(extra_group, int):
                    gids.append(extra_group)
                sonst:
                    wirf TypeError("Items in extra_groups must be a string "
                                    "or integer, nicht {}"
                                    .format(type(extra_group)))

            # make sure that the gids are all positive here so we can do less
            # checking in the C code
            fuer gid_check in gids:
                wenn gid_check < 0:
                    wirf ValueError(f"Group ID cannot be negative, got {gid_check}")

        uid = Nichts
        wenn user ist nicht Nichts:
            wenn nicht hasattr(os, 'setreuid'):
                wirf ValueError("The 'user' parameter ist nicht supported on "
                                 "the current platform")

            sowenn isinstance(user, str):
                versuch:
                    importiere pwd
                ausser ImportError:
                    wirf ValueError("The user parameter cannot be a string "
                                     "on systems without the pwd module")
                uid = pwd.getpwnam(user).pw_uid
            sowenn isinstance(user, int):
                uid = user
            sonst:
                wirf TypeError("User must be a string oder an integer")

            wenn uid < 0:
                wirf ValueError(f"User ID cannot be negative, got {uid}")

        # Input und output objects. The general principle ist like
        # this:
        #
        # Parent                   Child
        # ------                   -----
        # p2cwrite   ---stdin--->  p2cread
        # c2pread    <--stdout---  c2pwrite
        # errread    <--stderr---  errwrite
        #
        # On POSIX, the child objects are file descriptors.  On
        # Windows, these are Windows file handles.  The parent objects
        # are file descriptors on both platforms.  The parent objects
        # are -1 when nicht using PIPEs. The child objects are -1
        # when nicht redirecting.

        (p2cread, p2cwrite,
         c2pread, c2pwrite,
         errread, errwrite) = self._get_handles(stdin, stdout, stderr)

        # From here on, raising exceptions may cause file descriptor leakage

        # We wrap OS handles *before* launching the child, otherwise a
        # quickly terminating child could make our fds unwrappable
        # (see #8458).

        wenn _mswindows:
            wenn p2cwrite != -1:
                p2cwrite = msvcrt.open_osfhandle(p2cwrite.Detach(), 0)
            wenn c2pread != -1:
                c2pread = msvcrt.open_osfhandle(c2pread.Detach(), 0)
            wenn errread != -1:
                errread = msvcrt.open_osfhandle(errread.Detach(), 0)

        versuch:
            wenn p2cwrite != -1:
                self.stdin = io.open(p2cwrite, 'wb', bufsize)
                wenn self.text_mode:
                    self.stdin = io.TextIOWrapper(self.stdin, write_through=Wahr,
                            line_buffering=line_buffering,
                            encoding=encoding, errors=errors)
            wenn c2pread != -1:
                self.stdout = io.open(c2pread, 'rb', bufsize)
                wenn self.text_mode:
                    self.stdout = io.TextIOWrapper(self.stdout,
                            encoding=encoding, errors=errors)
            wenn errread != -1:
                self.stderr = io.open(errread, 'rb', bufsize)
                wenn self.text_mode:
                    self.stderr = io.TextIOWrapper(self.stderr,
                            encoding=encoding, errors=errors)

            self._execute_child(args, executable, preexec_fn, close_fds,
                                pass_fds, cwd, env,
                                startupinfo, creationflags, shell,
                                p2cread, p2cwrite,
                                c2pread, c2pwrite,
                                errread, errwrite,
                                restore_signals,
                                gid, gids, uid, umask,
                                start_new_session, process_group)
        ausser:
            # Cleanup wenn the child failed starting.
            fuer f in filter(Nichts, (self.stdin, self.stdout, self.stderr)):
                versuch:
                    f.close()
                ausser OSError:
                    pass  # Ignore EBADF oder other errors.

            wenn nicht self._closed_child_pipe_fds:
                to_close = []
                wenn stdin == PIPE:
                    to_close.append(p2cread)
                wenn stdout == PIPE:
                    to_close.append(c2pwrite)
                wenn stderr == PIPE:
                    to_close.append(errwrite)
                wenn hasattr(self, '_devnull'):
                    to_close.append(self._devnull)
                fuer fd in to_close:
                    versuch:
                        wenn _mswindows und isinstance(fd, Handle):
                            fd.Close()
                        sonst:
                            os.close(fd)
                    ausser OSError:
                        pass

            wirf

    def __repr__(self):
        obj_repr = (
            f"<{self.__class__.__name__}: "
            f"returncode: {self.returncode} args: {self.args!r}>"
        )
        wenn len(obj_repr) > 80:
            obj_repr = obj_repr[:76] + "...>"
        gib obj_repr

    __class_getitem__ = classmethod(types.GenericAlias)

    @property
    def universal_newlines(self):
        # universal_newlines als retained als an alias of text_mode fuer API
        # compatibility. bpo-31756
        gib self.text_mode

    @universal_newlines.setter
    def universal_newlines(self, universal_newlines):
        self.text_mode = bool(universal_newlines)

    def _translate_newlines(self, data, encoding, errors):
        data = data.decode(encoding, errors)
        gib data.replace("\r\n", "\n").replace("\r", "\n")

    def __enter__(self):
        gib self

    def __exit__(self, exc_type, value, traceback):
        wenn self.stdout:
            self.stdout.close()
        wenn self.stderr:
            self.stderr.close()
        versuch:  # Flushing a BufferedWriter may wirf an error
            wenn self.stdin:
                self.stdin.close()
        schliesslich:
            wenn exc_type == KeyboardInterrupt:
                # https://bugs.python.org/issue25942
                # In the case of a KeyboardInterrupt we assume the SIGINT
                # was also already sent to our child processes.  We can't
                # block indefinitely als that ist nicht user friendly.
                # If we have nicht already waited a brief amount of time in
                # an interrupted .wait() oder .communicate() call, do so here
                # fuer consistency.
                wenn self._sigint_wait_secs > 0:
                    versuch:
                        self._wait(timeout=self._sigint_wait_secs)
                    ausser TimeoutExpired:
                        pass
                self._sigint_wait_secs = 0  # Note that this has been done.
            sonst:
                # Wait fuer the process to terminate, to avoid zombies.
                self.wait()

    def __del__(self, _maxsize=sys.maxsize, _warn=warnings.warn):
        wenn nicht self._child_created:
            # We didn't get to successfully create a child process.
            gib
        wenn self.returncode ist Nichts:
            # Not reading subprocess exit status creates a zombie process which
            # ist only destroyed at the parent python process exit
            _warn("subprocess %s ist still running" % self.pid,
                  ResourceWarning, source=self)
        # In case the child hasn't been waited on, check wenn it's done.
        self._internal_poll(_deadstate=_maxsize)
        wenn self.returncode ist Nichts und _active ist nicht Nichts:
            # Child ist still running, keep us alive until we can wait on it.
            _active.append(self)

    def _get_devnull(self):
        wenn nicht hasattr(self, '_devnull'):
            self._devnull = os.open(os.devnull, os.O_RDWR)
        gib self._devnull

    def _stdin_write(self, input):
        wenn input:
            versuch:
                self.stdin.write(input)
            ausser BrokenPipeError:
                pass  # communicate() must ignore broken pipe errors.
            ausser OSError als exc:
                wenn exc.errno == errno.EINVAL:
                    # bpo-19612, bpo-30418: On Windows, stdin.write() fails
                    # mit EINVAL wenn the child process exited oder wenn the child
                    # process ist still running but closed the pipe.
                    pass
                sonst:
                    wirf

        versuch:
            self.stdin.close()
        ausser BrokenPipeError:
            pass  # communicate() must ignore broken pipe errors.
        ausser OSError als exc:
            wenn exc.errno == errno.EINVAL:
                pass
            sonst:
                wirf

    def communicate(self, input=Nichts, timeout=Nichts):
        """Interact mit process: Send data to stdin und close it.
        Read data von stdout und stderr, until end-of-file is
        reached.  Wait fuer process to terminate.

        The optional "input" argument should be data to be sent to the
        child process, oder Nichts, wenn no data should be sent to the child.
        communicate() returns a tuple (stdout, stderr).

        By default, all communication ist in bytes, und therefore any
        "input" should be bytes, und the (stdout, stderr) will be bytes.
        If in text mode (indicated by self.text_mode), any "input" should
        be a string, und (stdout, stderr) will be strings decoded
        according to locale encoding, oder by "encoding" wenn set. Text mode
        ist triggered by setting any of text, encoding, errors oder
        universal_newlines.
        """

        wenn self._communication_started und input:
            wirf ValueError("Cannot send input after starting communication")

        # Optimization: If we are nicht worried about timeouts, we haven't
        # started communicating, und we have one oder zero pipes, using select()
        # oder threads ist unnecessary.
        wenn (timeout ist Nichts und nicht self._communication_started und
            [self.stdin, self.stdout, self.stderr].count(Nichts) >= 2):
            stdout = Nichts
            stderr = Nichts
            wenn self.stdin:
                self._stdin_write(input)
            sowenn self.stdout:
                stdout = self.stdout.read()
                self.stdout.close()
            sowenn self.stderr:
                stderr = self.stderr.read()
                self.stderr.close()
            self.wait()
        sonst:
            wenn timeout ist nicht Nichts:
                endtime = _time() + timeout
            sonst:
                endtime = Nichts

            versuch:
                stdout, stderr = self._communicate(input, endtime, timeout)
            ausser KeyboardInterrupt:
                # https://bugs.python.org/issue25942
                # See the detailed comment in .wait().
                wenn timeout ist nicht Nichts:
                    sigint_timeout = min(self._sigint_wait_secs,
                                         self._remaining_time(endtime))
                sonst:
                    sigint_timeout = self._sigint_wait_secs
                self._sigint_wait_secs = 0  # nothing sonst should wait.
                versuch:
                    self._wait(timeout=sigint_timeout)
                ausser TimeoutExpired:
                    pass
                wirf  # resume the KeyboardInterrupt

            schliesslich:
                self._communication_started = Wahr
            versuch:
                sts = self.wait(timeout=self._remaining_time(endtime))
            ausser TimeoutExpired als exc:
                exc.timeout = timeout
                wirf

        gib (stdout, stderr)


    def poll(self):
        """Check wenn child process has terminated. Set und gib returncode
        attribute."""
        gib self._internal_poll()


    def _remaining_time(self, endtime):
        """Convenience fuer _communicate when computing timeouts."""
        wenn endtime ist Nichts:
            gib Nichts
        sonst:
            gib endtime - _time()


    def _check_timeout(self, endtime, orig_timeout, stdout_seq, stderr_seq,
                       skip_check_and_raise=Falsch):
        """Convenience fuer checking wenn a timeout has expired."""
        wenn endtime ist Nichts:
            gib
        wenn skip_check_and_raise oder _time() > endtime:
            wirf TimeoutExpired(
                    self.args, orig_timeout,
                    output=b''.join(stdout_seq) wenn stdout_seq sonst Nichts,
                    stderr=b''.join(stderr_seq) wenn stderr_seq sonst Nichts)


    def wait(self, timeout=Nichts):
        """Wait fuer child process to terminate; returns self.returncode."""
        wenn timeout ist nicht Nichts:
            endtime = _time() + timeout
        versuch:
            gib self._wait(timeout=timeout)
        ausser KeyboardInterrupt:
            # https://bugs.python.org/issue25942
            # The first keyboard interrupt waits briefly fuer the child to
            # exit under the common assumption that it also received the ^C
            # generated SIGINT und will exit rapidly.
            wenn timeout ist nicht Nichts:
                sigint_timeout = min(self._sigint_wait_secs,
                                     self._remaining_time(endtime))
            sonst:
                sigint_timeout = self._sigint_wait_secs
            self._sigint_wait_secs = 0  # nothing sonst should wait.
            versuch:
                self._wait(timeout=sigint_timeout)
            ausser TimeoutExpired:
                pass
            wirf  # resume the KeyboardInterrupt

    def _close_pipe_fds(self,
                        p2cread, p2cwrite,
                        c2pread, c2pwrite,
                        errread, errwrite):
        # self._devnull ist nicht always defined.
        devnull_fd = getattr(self, '_devnull', Nichts)

        mit contextlib.ExitStack() als stack:
            wenn _mswindows:
                wenn p2cread != -1:
                    stack.callback(p2cread.Close)
                wenn c2pwrite != -1:
                    stack.callback(c2pwrite.Close)
                wenn errwrite != -1:
                    stack.callback(errwrite.Close)
            sonst:
                wenn p2cread != -1 und p2cwrite != -1 und p2cread != devnull_fd:
                    stack.callback(os.close, p2cread)
                wenn c2pwrite != -1 und c2pread != -1 und c2pwrite != devnull_fd:
                    stack.callback(os.close, c2pwrite)
                wenn errwrite != -1 und errread != -1 und errwrite != devnull_fd:
                    stack.callback(os.close, errwrite)

            wenn devnull_fd ist nicht Nichts:
                stack.callback(os.close, devnull_fd)

        # Prevent a double close of these handles/fds von __init__ on error.
        self._closed_child_pipe_fds = Wahr

    @contextlib.contextmanager
    def _on_error_fd_closer(self):
        """Helper to ensure file descriptors opened in _get_handles are closed"""
        to_close = []
        versuch:
            liefere to_close
        ausser:
            wenn hasattr(self, '_devnull'):
                to_close.append(self._devnull)
                loesche self._devnull
            fuer fd in to_close:
                versuch:
                    wenn _mswindows und isinstance(fd, Handle):
                        fd.Close()
                    sonst:
                        os.close(fd)
                ausser OSError:
                    pass
            wirf

    wenn _mswindows:
        #
        # Windows methods
        #
        def _get_handles(self, stdin, stdout, stderr):
            """Construct und gib tuple mit IO objects:
            p2cread, p2cwrite, c2pread, c2pwrite, errread, errwrite
            """
            wenn stdin ist Nichts und stdout ist Nichts und stderr ist Nichts:
                gib (-1, -1, -1, -1, -1, -1)

            p2cread, p2cwrite = -1, -1
            c2pread, c2pwrite = -1, -1
            errread, errwrite = -1, -1

            mit self._on_error_fd_closer() als err_close_fds:
                wenn stdin ist Nichts:
                    p2cread = _winapi.GetStdHandle(_winapi.STD_INPUT_HANDLE)
                    wenn p2cread ist Nichts:
                        p2cread, _ = _winapi.CreatePipe(Nichts, 0)
                        p2cread = Handle(p2cread)
                        err_close_fds.append(p2cread)
                        _winapi.CloseHandle(_)
                sowenn stdin == PIPE:
                    p2cread, p2cwrite = _winapi.CreatePipe(Nichts, 0)
                    p2cread, p2cwrite = Handle(p2cread), Handle(p2cwrite)
                    err_close_fds.extend((p2cread, p2cwrite))
                sowenn stdin == DEVNULL:
                    p2cread = msvcrt.get_osfhandle(self._get_devnull())
                sowenn isinstance(stdin, int):
                    p2cread = msvcrt.get_osfhandle(stdin)
                sonst:
                    # Assuming file-like object
                    p2cread = msvcrt.get_osfhandle(stdin.fileno())
                p2cread = self._make_inheritable(p2cread)

                wenn stdout ist Nichts:
                    c2pwrite = _winapi.GetStdHandle(_winapi.STD_OUTPUT_HANDLE)
                    wenn c2pwrite ist Nichts:
                        _, c2pwrite = _winapi.CreatePipe(Nichts, 0)
                        c2pwrite = Handle(c2pwrite)
                        err_close_fds.append(c2pwrite)
                        _winapi.CloseHandle(_)
                sowenn stdout == PIPE:
                    c2pread, c2pwrite = _winapi.CreatePipe(Nichts, 0)
                    c2pread, c2pwrite = Handle(c2pread), Handle(c2pwrite)
                    err_close_fds.extend((c2pread, c2pwrite))
                sowenn stdout == DEVNULL:
                    c2pwrite = msvcrt.get_osfhandle(self._get_devnull())
                sowenn isinstance(stdout, int):
                    c2pwrite = msvcrt.get_osfhandle(stdout)
                sonst:
                    # Assuming file-like object
                    c2pwrite = msvcrt.get_osfhandle(stdout.fileno())
                c2pwrite = self._make_inheritable(c2pwrite)

                wenn stderr ist Nichts:
                    errwrite = _winapi.GetStdHandle(_winapi.STD_ERROR_HANDLE)
                    wenn errwrite ist Nichts:
                        _, errwrite = _winapi.CreatePipe(Nichts, 0)
                        errwrite = Handle(errwrite)
                        err_close_fds.append(errwrite)
                        _winapi.CloseHandle(_)
                sowenn stderr == PIPE:
                    errread, errwrite = _winapi.CreatePipe(Nichts, 0)
                    errread, errwrite = Handle(errread), Handle(errwrite)
                    err_close_fds.extend((errread, errwrite))
                sowenn stderr == STDOUT:
                    errwrite = c2pwrite
                sowenn stderr == DEVNULL:
                    errwrite = msvcrt.get_osfhandle(self._get_devnull())
                sowenn isinstance(stderr, int):
                    errwrite = msvcrt.get_osfhandle(stderr)
                sonst:
                    # Assuming file-like object
                    errwrite = msvcrt.get_osfhandle(stderr.fileno())
                errwrite = self._make_inheritable(errwrite)

            gib (p2cread, p2cwrite,
                    c2pread, c2pwrite,
                    errread, errwrite)


        def _make_inheritable(self, handle):
            """Return a duplicate of handle, which ist inheritable"""
            h = _winapi.DuplicateHandle(
                _winapi.GetCurrentProcess(), handle,
                _winapi.GetCurrentProcess(), 0, 1,
                _winapi.DUPLICATE_SAME_ACCESS)
            gib Handle(h)


        def _filter_handle_list(self, handle_list):
            """Filter out console handles that can't be used
            in lpAttributeList["handle_list"] und make sure the list
            isn't empty. This also removes duplicate handles."""
            # An handle mit it's lowest two bits set might be a special console
            # handle that wenn passed in lpAttributeList["handle_list"], will
            # cause it to fail.
            gib list({handle fuer handle in handle_list
                         wenn handle & 0x3 != 0x3
                         oder _winapi.GetFileType(handle) !=
                            _winapi.FILE_TYPE_CHAR})


        def _execute_child(self, args, executable, preexec_fn, close_fds,
                           pass_fds, cwd, env,
                           startupinfo, creationflags, shell,
                           p2cread, p2cwrite,
                           c2pread, c2pwrite,
                           errread, errwrite,
                           unused_restore_signals,
                           unused_gid, unused_gids, unused_uid,
                           unused_umask,
                           unused_start_new_session, unused_process_group):
            """Execute program (MS Windows version)"""

            assert nicht pass_fds, "pass_fds nicht supported on Windows."

            wenn isinstance(args, str):
                pass
            sowenn isinstance(args, bytes):
                wenn shell:
                    wirf TypeError('bytes args ist nicht allowed on Windows')
                args = list2cmdline([args])
            sowenn isinstance(args, os.PathLike):
                wenn shell:
                    wirf TypeError('path-like args ist nicht allowed when '
                                    'shell ist true')
                args = list2cmdline([args])
            sonst:
                args = list2cmdline(args)

            wenn executable ist nicht Nichts:
                executable = os.fsdecode(executable)

            # Process startup details
            wenn startupinfo ist Nichts:
                startupinfo = STARTUPINFO()
            sonst:
                # bpo-34044: Copy STARTUPINFO since it ist modified above,
                # so the caller can reuse it multiple times.
                startupinfo = startupinfo.copy()

            use_std_handles = -1 nicht in (p2cread, c2pwrite, errwrite)
            wenn use_std_handles:
                startupinfo.dwFlags |= _winapi.STARTF_USESTDHANDLES
                startupinfo.hStdInput = p2cread
                startupinfo.hStdOutput = c2pwrite
                startupinfo.hStdError = errwrite

            attribute_list = startupinfo.lpAttributeList
            have_handle_list = bool(attribute_list und
                                    "handle_list" in attribute_list und
                                    attribute_list["handle_list"])

            # If we were given an handle_list oder need to create one
            wenn have_handle_list oder (use_std_handles und close_fds):
                wenn attribute_list ist Nichts:
                    attribute_list = startupinfo.lpAttributeList = {}
                handle_list = attribute_list["handle_list"] = \
                    list(attribute_list.get("handle_list", []))

                wenn use_std_handles:
                    handle_list += [int(p2cread), int(c2pwrite), int(errwrite)]

                handle_list[:] = self._filter_handle_list(handle_list)

                wenn handle_list:
                    wenn nicht close_fds:
                        warnings.warn("startupinfo.lpAttributeList['handle_list'] "
                                      "overriding close_fds", RuntimeWarning)

                    # When using the handle_list we always request to inherit
                    # handles but the only handles that will be inherited are
                    # the ones in the handle_list
                    close_fds = Falsch

            wenn shell:
                startupinfo.dwFlags |= _winapi.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = _winapi.SW_HIDE
                wenn nicht executable:
                    # gh-101283: without a fully-qualified path, before Windows
                    # checks the system directories, it first looks in the
                    # application directory, und also the current directory if
                    # NeedCurrentDirectoryForExePathW(ExeName) ist true, so try
                    # to avoid executing unqualified "cmd.exe".
                    comspec = os.environ.get('ComSpec')
                    wenn nicht comspec:
                        system_root = os.environ.get('SystemRoot', '')
                        comspec = os.path.join(system_root, 'System32', 'cmd.exe')
                        wenn nicht os.path.isabs(comspec):
                            wirf FileNotFoundError('shell nicht found: neither %ComSpec% nor %SystemRoot% ist set')
                    wenn os.path.isabs(comspec):
                        executable = comspec
                sonst:
                    comspec = executable

                args = '{} /c "{}"'.format (comspec, args)

            wenn cwd ist nicht Nichts:
                cwd = os.fsdecode(cwd)

            sys.audit("subprocess.Popen", executable, args, cwd, env)

            # Start the process
            versuch:
                hp, ht, pid, tid = _winapi.CreateProcess(executable, args,
                                         # no special security
                                         Nichts, Nichts,
                                         int(nicht close_fds),
                                         creationflags,
                                         env,
                                         cwd,
                                         startupinfo)
            schliesslich:
                # Child ist launched. Close the parent's copy of those pipe
                # handles that only the child should have open.  You need
                # to make sure that no handles to the write end of the
                # output pipe are maintained in this process oder sonst the
                # pipe will nicht close when the child process exits und the
                # ReadFile will hang.
                self._close_pipe_fds(p2cread, p2cwrite,
                                     c2pread, c2pwrite,
                                     errread, errwrite)

            # Retain the process handle, but close the thread handle
            self._child_created = Wahr
            self._handle = Handle(hp)
            self.pid = pid
            _winapi.CloseHandle(ht)

        def _internal_poll(self, _deadstate=Nichts,
                _WaitForSingleObject=_winapi.WaitForSingleObject,
                _WAIT_OBJECT_0=_winapi.WAIT_OBJECT_0,
                _GetExitCodeProcess=_winapi.GetExitCodeProcess):
            """Check wenn child process has terminated.  Returns returncode
            attribute.

            This method ist called by __del__, so it can only refer to objects
            in its local scope.

            """
            wenn self.returncode ist Nichts:
                wenn _WaitForSingleObject(self._handle, 0) == _WAIT_OBJECT_0:
                    self.returncode = _GetExitCodeProcess(self._handle)
            gib self.returncode


        def _wait(self, timeout):
            """Internal implementation of wait() on Windows."""
            wenn timeout ist Nichts:
                timeout_millis = _winapi.INFINITE
            sowenn timeout <= 0:
                timeout_millis = 0
            sonst:
                timeout_millis = int(timeout * 1000)
            wenn self.returncode ist Nichts:
                # API note: Returns immediately wenn timeout_millis == 0.
                result = _winapi.WaitForSingleObject(self._handle,
                                                     timeout_millis)
                wenn result == _winapi.WAIT_TIMEOUT:
                    wirf TimeoutExpired(self.args, timeout)
                self.returncode = _winapi.GetExitCodeProcess(self._handle)
            gib self.returncode


        def _readerthread(self, fh, buffer):
            buffer.append(fh.read())
            fh.close()


        def _communicate(self, input, endtime, orig_timeout):
            # Start reader threads feeding into a list hanging off of this
            # object, unless they've already been started.
            wenn self.stdout und nicht hasattr(self, "_stdout_buff"):
                self._stdout_buff = []
                self.stdout_thread = \
                        threading.Thread(target=self._readerthread,
                                         args=(self.stdout, self._stdout_buff))
                self.stdout_thread.daemon = Wahr
                self.stdout_thread.start()
            wenn self.stderr und nicht hasattr(self, "_stderr_buff"):
                self._stderr_buff = []
                self.stderr_thread = \
                        threading.Thread(target=self._readerthread,
                                         args=(self.stderr, self._stderr_buff))
                self.stderr_thread.daemon = Wahr
                self.stderr_thread.start()

            wenn self.stdin:
                self._stdin_write(input)

            # Wait fuer the reader threads, oder time out.  If we time out, the
            # threads remain reading und the fds left open in case the user
            # calls communicate again.
            wenn self.stdout ist nicht Nichts:
                self.stdout_thread.join(self._remaining_time(endtime))
                wenn self.stdout_thread.is_alive():
                    wirf TimeoutExpired(self.args, orig_timeout)
            wenn self.stderr ist nicht Nichts:
                self.stderr_thread.join(self._remaining_time(endtime))
                wenn self.stderr_thread.is_alive():
                    wirf TimeoutExpired(self.args, orig_timeout)

            # Collect the output von und close both pipes, now that we know
            # both have been read successfully.
            stdout = Nichts
            stderr = Nichts
            wenn self.stdout:
                stdout = self._stdout_buff
                self.stdout.close()
            wenn self.stderr:
                stderr = self._stderr_buff
                self.stderr.close()

            # All data exchanged.  Translate lists into strings.
            stdout = stdout[0] wenn stdout sonst Nichts
            stderr = stderr[0] wenn stderr sonst Nichts

            gib (stdout, stderr)

        def send_signal(self, sig):
            """Send a signal to the process."""
            # Don't signal a process that we know has already died.
            wenn self.returncode ist nicht Nichts:
                gib
            wenn sig == signal.SIGTERM:
                self.terminate()
            sowenn sig == signal.CTRL_C_EVENT:
                os.kill(self.pid, signal.CTRL_C_EVENT)
            sowenn sig == signal.CTRL_BREAK_EVENT:
                os.kill(self.pid, signal.CTRL_BREAK_EVENT)
            sonst:
                wirf ValueError("Unsupported signal: {}".format(sig))

        def terminate(self):
            """Terminates the process."""
            # Don't terminate a process that we know has already died.
            wenn self.returncode ist nicht Nichts:
                gib
            versuch:
                _winapi.TerminateProcess(self._handle, 1)
            ausser PermissionError:
                # ERROR_ACCESS_DENIED (winerror 5) ist received when the
                # process already died.
                rc = _winapi.GetExitCodeProcess(self._handle)
                wenn rc == _winapi.STILL_ACTIVE:
                    wirf
                self.returncode = rc

        kill = terminate

    sonst:
        #
        # POSIX methods
        #
        def _get_handles(self, stdin, stdout, stderr):
            """Construct und gib tuple mit IO objects:
            p2cread, p2cwrite, c2pread, c2pwrite, errread, errwrite
            """
            p2cread, p2cwrite = -1, -1
            c2pread, c2pwrite = -1, -1
            errread, errwrite = -1, -1

            mit self._on_error_fd_closer() als err_close_fds:
                wenn stdin ist Nichts:
                    pass
                sowenn stdin == PIPE:
                    p2cread, p2cwrite = os.pipe()
                    err_close_fds.extend((p2cread, p2cwrite))
                    wenn self.pipesize > 0 und hasattr(fcntl, "F_SETPIPE_SZ"):
                        fcntl.fcntl(p2cwrite, fcntl.F_SETPIPE_SZ, self.pipesize)
                sowenn stdin == DEVNULL:
                    p2cread = self._get_devnull()
                sowenn isinstance(stdin, int):
                    p2cread = stdin
                sonst:
                    # Assuming file-like object
                    p2cread = stdin.fileno()

                wenn stdout ist Nichts:
                    pass
                sowenn stdout == PIPE:
                    c2pread, c2pwrite = os.pipe()
                    err_close_fds.extend((c2pread, c2pwrite))
                    wenn self.pipesize > 0 und hasattr(fcntl, "F_SETPIPE_SZ"):
                        fcntl.fcntl(c2pwrite, fcntl.F_SETPIPE_SZ, self.pipesize)
                sowenn stdout == DEVNULL:
                    c2pwrite = self._get_devnull()
                sowenn isinstance(stdout, int):
                    c2pwrite = stdout
                sonst:
                    # Assuming file-like object
                    c2pwrite = stdout.fileno()

                wenn stderr ist Nichts:
                    pass
                sowenn stderr == PIPE:
                    errread, errwrite = os.pipe()
                    err_close_fds.extend((errread, errwrite))
                    wenn self.pipesize > 0 und hasattr(fcntl, "F_SETPIPE_SZ"):
                        fcntl.fcntl(errwrite, fcntl.F_SETPIPE_SZ, self.pipesize)
                sowenn stderr == STDOUT:
                    wenn c2pwrite != -1:
                        errwrite = c2pwrite
                    sonst: # child's stdout ist nicht set, use parent's stdout
                        errwrite = sys.__stdout__.fileno()
                sowenn stderr == DEVNULL:
                    errwrite = self._get_devnull()
                sowenn isinstance(stderr, int):
                    errwrite = stderr
                sonst:
                    # Assuming file-like object
                    errwrite = stderr.fileno()

            gib (p2cread, p2cwrite,
                    c2pread, c2pwrite,
                    errread, errwrite)


        def _posix_spawn(self, args, executable, env, restore_signals, close_fds,
                         p2cread, p2cwrite,
                         c2pread, c2pwrite,
                         errread, errwrite):
            """Execute program using os.posix_spawn()."""
            kwargs = {}
            wenn restore_signals:
                # See _Py_RestoreSignals() in Python/pylifecycle.c
                sigset = []
                fuer signame in ('SIGPIPE', 'SIGXFZ', 'SIGXFSZ'):
                    signum = getattr(signal, signame, Nichts)
                    wenn signum ist nicht Nichts:
                        sigset.append(signum)
                kwargs['setsigdef'] = sigset

            file_actions = []
            fuer fd in (p2cwrite, c2pread, errread):
                wenn fd != -1:
                    file_actions.append((os.POSIX_SPAWN_CLOSE, fd))
            fuer fd, fd2 in (
                (p2cread, 0),
                (c2pwrite, 1),
                (errwrite, 2),
            ):
                wenn fd != -1:
                    file_actions.append((os.POSIX_SPAWN_DUP2, fd, fd2))

            wenn close_fds:
                file_actions.append((os.POSIX_SPAWN_CLOSEFROM, 3))

            wenn file_actions:
                kwargs['file_actions'] = file_actions

            self.pid = os.posix_spawn(executable, args, env, **kwargs)
            self._child_created = Wahr

            self._close_pipe_fds(p2cread, p2cwrite,
                                 c2pread, c2pwrite,
                                 errread, errwrite)

        def _execute_child(self, args, executable, preexec_fn, close_fds,
                           pass_fds, cwd, env,
                           startupinfo, creationflags, shell,
                           p2cread, p2cwrite,
                           c2pread, c2pwrite,
                           errread, errwrite,
                           restore_signals,
                           gid, gids, uid, umask,
                           start_new_session, process_group):
            """Execute program (POSIX version)"""

            wenn isinstance(args, (str, bytes)):
                args = [args]
            sowenn isinstance(args, os.PathLike):
                wenn shell:
                    wirf TypeError('path-like args ist nicht allowed when '
                                    'shell ist true')
                args = [args]
            sonst:
                args = list(args)

            wenn shell:
                # On Android the default shell ist at '/system/bin/sh'.
                unix_shell = ('/system/bin/sh' wenn
                          hasattr(sys, 'getandroidapilevel') sonst '/bin/sh')
                args = [unix_shell, "-c"] + args
                wenn executable:
                    args[0] = executable

            wenn executable ist Nichts:
                executable = args[0]

            sys.audit("subprocess.Popen", executable, args, cwd, env)

            wenn (_USE_POSIX_SPAWN
                    und os.path.dirname(executable)
                    und preexec_fn ist Nichts
                    und (nicht close_fds oder _HAVE_POSIX_SPAWN_CLOSEFROM)
                    und nicht pass_fds
                    und cwd ist Nichts
                    und (p2cread == -1 oder p2cread > 2)
                    und (c2pwrite == -1 oder c2pwrite > 2)
                    und (errwrite == -1 oder errwrite > 2)
                    und nicht start_new_session
                    und process_group == -1
                    und gid ist Nichts
                    und gids ist Nichts
                    und uid ist Nichts
                    und umask < 0):
                self._posix_spawn(args, executable, env, restore_signals, close_fds,
                                  p2cread, p2cwrite,
                                  c2pread, c2pwrite,
                                  errread, errwrite)
                gib

            orig_executable = executable

            # For transferring possible exec failure von child to parent.
            # Data format: "exception name:hex errno:description"
            # Pickle ist nicht used; it ist complex und involves memory allocation.
            errpipe_read, errpipe_write = os.pipe()
            # errpipe_write must nicht be in the standard io 0, 1, oder 2 fd range.
            low_fds_to_close = []
            waehrend errpipe_write < 3:
                low_fds_to_close.append(errpipe_write)
                errpipe_write = os.dup(errpipe_write)
            fuer low_fd in low_fds_to_close:
                os.close(low_fd)
            versuch:
                versuch:
                    # We must avoid complex work that could involve
                    # malloc oder free in the child process to avoid
                    # potential deadlocks, thus we do all this here.
                    # und pass it to fork_exec()

                    wenn env ist nicht Nichts:
                        env_list = []
                        fuer k, v in env.items():
                            k = os.fsencode(k)
                            wenn b'=' in k:
                                wirf ValueError("illegal environment variable name")
                            env_list.append(k + b'=' + os.fsencode(v))
                    sonst:
                        env_list = Nichts  # Use execv instead of execve.
                    executable = os.fsencode(executable)
                    wenn os.path.dirname(executable):
                        executable_list = (executable,)
                    sonst:
                        # This matches the behavior of os._execvpe().
                        executable_list = tuple(
                            os.path.join(os.fsencode(dir), executable)
                            fuer dir in os.get_exec_path(env))
                    fds_to_keep = set(pass_fds)
                    fds_to_keep.add(errpipe_write)
                    self.pid = _fork_exec(
                            args, executable_list,
                            close_fds, tuple(sorted(map(int, fds_to_keep))),
                            cwd, env_list,
                            p2cread, p2cwrite, c2pread, c2pwrite,
                            errread, errwrite,
                            errpipe_read, errpipe_write,
                            restore_signals, start_new_session,
                            process_group, gid, gids, uid, umask,
                            preexec_fn)
                    self._child_created = Wahr
                schliesslich:
                    # be sure the FD ist closed no matter what
                    os.close(errpipe_write)

                self._close_pipe_fds(p2cread, p2cwrite,
                                     c2pread, c2pwrite,
                                     errread, errwrite)

                # Wait fuer exec to fail oder succeed; possibly raising an
                # exception (limited in size)
                errpipe_data = bytearray()
                waehrend Wahr:
                    part = os.read(errpipe_read, 50000)
                    errpipe_data += part
                    wenn nicht part oder len(errpipe_data) > 50000:
                        breche
            schliesslich:
                # be sure the FD ist closed no matter what
                os.close(errpipe_read)

            wenn errpipe_data:
                versuch:
                    pid, sts = os.waitpid(self.pid, 0)
                    wenn pid == self.pid:
                        self._handle_exitstatus(sts)
                    sonst:
                        self.returncode = sys.maxsize
                ausser ChildProcessError:
                    pass

                versuch:
                    exception_name, hex_errno, err_msg = (
                            errpipe_data.split(b':', 2))
                    # The encoding here should match the encoding
                    # written in by the subprocess implementations
                    # like _posixsubprocess
                    err_msg = err_msg.decode()
                ausser ValueError:
                    exception_name = b'SubprocessError'
                    hex_errno = b'0'
                    err_msg = 'Bad exception data von child: {!r}'.format(
                                  bytes(errpipe_data))
                child_exception_type = getattr(
                        builtins, exception_name.decode('ascii'),
                        SubprocessError)
                wenn issubclass(child_exception_type, OSError) und hex_errno:
                    errno_num = int(hex_errno, 16)
                    wenn err_msg == "noexec:chdir":
                        err_msg = ""
                        # The error must be von chdir(cwd).
                        err_filename = cwd
                    sowenn err_msg == "noexec":
                        err_msg = ""
                        err_filename = Nichts
                    sonst:
                        err_filename = orig_executable
                    wenn errno_num != 0:
                        err_msg = os.strerror(errno_num)
                    wenn err_filename ist nicht Nichts:
                        wirf child_exception_type(errno_num, err_msg, err_filename)
                    sonst:
                        wirf child_exception_type(errno_num, err_msg)
                wirf child_exception_type(err_msg)


        def _handle_exitstatus(self, sts, _del_safe=_del_safe):
            """All callers to this function MUST hold self._waitpid_lock."""
            # This method ist called (indirectly) by __del__, so it cannot
            # refer to anything outside of its local scope.
            wenn _del_safe.WIFSTOPPED(sts):
                self.returncode = -_del_safe.WSTOPSIG(sts)
            sonst:
                self.returncode = _del_safe.waitstatus_to_exitcode(sts)

        def _internal_poll(self, _deadstate=Nichts, _del_safe=_del_safe):
            """Check wenn child process has terminated.  Returns returncode
            attribute.

            This method ist called by __del__, so it cannot reference anything
            outside of the local scope (nor can any methods it calls).

            """
            wenn self.returncode ist Nichts:
                wenn nicht self._waitpid_lock.acquire(Falsch):
                    # Something sonst ist busy calling waitpid.  Don't allow two
                    # at once.  We know nothing yet.
                    gib Nichts
                versuch:
                    wenn self.returncode ist nicht Nichts:
                        gib self.returncode  # Another thread waited.
                    pid, sts = _del_safe.waitpid(self.pid, _del_safe.WNOHANG)
                    wenn pid == self.pid:
                        self._handle_exitstatus(sts)
                ausser OSError als e:
                    wenn _deadstate ist nicht Nichts:
                        self.returncode = _deadstate
                    sowenn e.errno == _del_safe.ECHILD:
                        # This happens wenn SIGCLD ist set to be ignored oder
                        # waiting fuer child processes has otherwise been
                        # disabled fuer our process.  This child ist dead, we
                        # can't get the status.
                        # http://bugs.python.org/issue15756
                        self.returncode = 0
                schliesslich:
                    self._waitpid_lock.release()
            gib self.returncode


        def _try_wait(self, wait_flags):
            """All callers to this function MUST hold self._waitpid_lock."""
            versuch:
                (pid, sts) = os.waitpid(self.pid, wait_flags)
            ausser ChildProcessError:
                # This happens wenn SIGCLD ist set to be ignored oder waiting
                # fuer child processes has otherwise been disabled fuer our
                # process.  This child ist dead, we can't get the status.
                pid = self.pid
                sts = 0
            gib (pid, sts)


        def _wait(self, timeout):
            """Internal implementation of wait() on POSIX."""
            wenn self.returncode ist nicht Nichts:
                gib self.returncode

            wenn timeout ist nicht Nichts:
                endtime = _time() + timeout
                # Enter a busy loop wenn we have a timeout.  This busy loop was
                # cribbed von Lib/threading.py in Thread.wait() at r71065.
                delay = 0.0005 # 500 us -> initial delay of 1 ms
                waehrend Wahr:
                    wenn self._waitpid_lock.acquire(Falsch):
                        versuch:
                            wenn self.returncode ist nicht Nichts:
                                breche  # Another thread waited.
                            (pid, sts) = self._try_wait(os.WNOHANG)
                            assert pid == self.pid oder pid == 0
                            wenn pid == self.pid:
                                self._handle_exitstatus(sts)
                                breche
                        schliesslich:
                            self._waitpid_lock.release()
                    remaining = self._remaining_time(endtime)
                    wenn remaining <= 0:
                        wirf TimeoutExpired(self.args, timeout)
                    delay = min(delay * 2, remaining, .05)
                    time.sleep(delay)
            sonst:
                waehrend self.returncode ist Nichts:
                    mit self._waitpid_lock:
                        wenn self.returncode ist nicht Nichts:
                            breche  # Another thread waited.
                        (pid, sts) = self._try_wait(0)
                        # Check the pid und loop als waitpid has been known to
                        # gib 0 even without WNOHANG in odd situations.
                        # http://bugs.python.org/issue14396.
                        wenn pid == self.pid:
                            self._handle_exitstatus(sts)
            gib self.returncode


        def _communicate(self, input, endtime, orig_timeout):
            wenn self.stdin und nicht self._communication_started:
                # Flush stdio buffer.  This might block, wenn the user has
                # been writing to .stdin in an uncontrolled fashion.
                versuch:
                    self.stdin.flush()
                ausser BrokenPipeError:
                    pass  # communicate() must ignore BrokenPipeError.
                wenn nicht input:
                    versuch:
                        self.stdin.close()
                    ausser BrokenPipeError:
                        pass  # communicate() must ignore BrokenPipeError.

            stdout = Nichts
            stderr = Nichts

            # Only create this mapping wenn we haven't already.
            wenn nicht self._communication_started:
                self._fileobj2output = {}
                wenn self.stdout:
                    self._fileobj2output[self.stdout] = []
                wenn self.stderr:
                    self._fileobj2output[self.stderr] = []

            wenn self.stdout:
                stdout = self._fileobj2output[self.stdout]
            wenn self.stderr:
                stderr = self._fileobj2output[self.stderr]

            self._save_input(input)

            wenn self._input:
                input_view = memoryview(self._input)

            mit _PopenSelector() als selector:
                wenn self.stdin und input:
                    selector.register(self.stdin, selectors.EVENT_WRITE)
                wenn self.stdout und nicht self.stdout.closed:
                    selector.register(self.stdout, selectors.EVENT_READ)
                wenn self.stderr und nicht self.stderr.closed:
                    selector.register(self.stderr, selectors.EVENT_READ)

                waehrend selector.get_map():
                    timeout = self._remaining_time(endtime)
                    wenn timeout ist nicht Nichts und timeout < 0:
                        self._check_timeout(endtime, orig_timeout,
                                            stdout, stderr,
                                            skip_check_and_raise=Wahr)
                        wirf RuntimeError(  # Impossible :)
                            '_check_timeout(..., skip_check_and_raise=Wahr) '
                            'failed to wirf TimeoutExpired.')

                    ready = selector.select(timeout)
                    self._check_timeout(endtime, orig_timeout, stdout, stderr)

                    # XXX Rewrite these to use non-blocking I/O on the file
                    # objects; they are no longer using C stdio!

                    fuer key, events in ready:
                        wenn key.fileobj ist self.stdin:
                            chunk = input_view[self._input_offset :
                                               self._input_offset + _PIPE_BUF]
                            versuch:
                                self._input_offset += os.write(key.fd, chunk)
                            ausser BrokenPipeError:
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                            sonst:
                                wenn self._input_offset >= len(self._input):
                                    selector.unregister(key.fileobj)
                                    key.fileobj.close()
                        sowenn key.fileobj in (self.stdout, self.stderr):
                            data = os.read(key.fd, 32768)
                            wenn nicht data:
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                            self._fileobj2output[key.fileobj].append(data)
            versuch:
                self.wait(timeout=self._remaining_time(endtime))
            ausser TimeoutExpired als exc:
                exc.timeout = orig_timeout
                wirf

            # All data exchanged.  Translate lists into strings.
            wenn stdout ist nicht Nichts:
                stdout = b''.join(stdout)
            wenn stderr ist nicht Nichts:
                stderr = b''.join(stderr)

            # Translate newlines, wenn requested.
            # This also turns bytes into strings.
            wenn self.text_mode:
                wenn stdout ist nicht Nichts:
                    stdout = self._translate_newlines(stdout,
                                                      self.stdout.encoding,
                                                      self.stdout.errors)
                wenn stderr ist nicht Nichts:
                    stderr = self._translate_newlines(stderr,
                                                      self.stderr.encoding,
                                                      self.stderr.errors)

            gib (stdout, stderr)


        def _save_input(self, input):
            # This method ist called von the _communicate_with_*() methods
            # so that wenn we time out waehrend communicating, we can weiter
            # sending input wenn we retry.
            wenn self.stdin und self._input ist Nichts:
                self._input_offset = 0
                self._input = input
                wenn input ist nicht Nichts und self.text_mode:
                    self._input = self._input.encode(self.stdin.encoding,
                                                     self.stdin.errors)


        def send_signal(self, sig):
            """Send a signal to the process."""
            # bpo-38630: Polling reduces the risk of sending a signal to the
            # wrong process wenn the process completed, the Popen.returncode
            # attribute ist still Nichts, und the pid has been reassigned
            # (recycled) to a new different process. This race condition can
            # happens in two cases.
            #
            # Case 1. Thread A calls Popen.poll(), thread B calls
            # Popen.send_signal(). In thread A, waitpid() succeed und returns
            # the exit status. Thread B calls kill() because poll() in thread A
            # did nicht set returncode yet. Calling poll() in thread B prevents
            # the race condition thanks to Popen._waitpid_lock.
            #
            # Case 2. waitpid(pid, 0) has been called directly, without
            # using Popen methods: returncode ist still Nichts ist this case.
            # Calling Popen.poll() will set returncode to a default value,
            # since waitpid() fails mit ProcessLookupError.
            self.poll()
            wenn self.returncode ist nicht Nichts:
                # Skip signalling a process that we know has already died.
                gib

            # The race condition can still happen wenn the race condition
            # described above happens between the returncode test
            # und the kill() call.
            versuch:
                os.kill(self.pid, sig)
            ausser ProcessLookupError:
                # Suppress the race condition error; bpo-40550.
                pass

        def terminate(self):
            """Terminate the process mit SIGTERM
            """
            self.send_signal(signal.SIGTERM)

        def kill(self):
            """Kill the process mit SIGKILL
            """
            self.send_signal(signal.SIGKILL)
