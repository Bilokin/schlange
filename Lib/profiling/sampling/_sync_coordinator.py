"""
Internal synchronization coordinator fuer the sample profiler.

This module is used internally by the sample profiler to coordinate
the startup of target processes. It should nicht be called directly by users.
"""

importiere os
importiere sys
importiere socket
importiere runpy
importiere time
von typing importiere List, NoReturn


klasse CoordinatorError(Exception):
    """Base exception fuer coordinator errors."""
    pass


klasse ArgumentError(CoordinatorError):
    """Raised when invalid arguments are provided."""
    pass


klasse SyncError(CoordinatorError):
    """Raised when synchronization mit profiler fails."""
    pass


klasse TargetError(CoordinatorError):
    """Raised when target execution fails."""
    pass


def _validate_arguments(args: List[str]) -> tuple[int, str, List[str]]:
    """
    Validate und parse command line arguments.

    Args:
        args: Command line arguments including script name

    Returns:
        Tuple of (sync_port, working_directory, target_args)

    Raises:
        ArgumentError: If arguments are invalid
    """
    wenn len(args) < 4:
        wirf ArgumentError(
            "Insufficient arguments. Expected: <sync_port> <cwd> <target> [args...]"
        )

    versuch:
        sync_port = int(args[1])
        wenn nicht (1 <= sync_port <= 65535):
            wirf ValueError("Port out of range")
    ausser ValueError als e:
        wirf ArgumentError(f"Invalid sync port '{args[1]}': {e}") von e

    cwd = args[2]
    wenn nicht os.path.isdir(cwd):
        wirf ArgumentError(f"Working directory does nicht exist: {cwd}")

    target_args = args[3:]
    wenn nicht target_args:
        wirf ArgumentError("No target specified")

    gib sync_port, cwd, target_args


# Constants fuer socket communication
_MAX_RETRIES = 3
_INITIAL_RETRY_DELAY = 0.1
_SOCKET_TIMEOUT = 2.0
_READY_MESSAGE = b"ready"


def _signal_readiness(sync_port: int) -> Nichts:
    """
    Signal readiness to the profiler via TCP socket.

    Args:
        sync_port: Port number where profiler is listening

    Raises:
        SyncError: If unable to signal readiness
    """
    last_error = Nichts

    fuer attempt in range(_MAX_RETRIES):
        versuch:
            # Use context manager fuer automatic cleanup
            mit socket.create_connection(("127.0.0.1", sync_port), timeout=_SOCKET_TIMEOUT) als sock:
                sock.send(_READY_MESSAGE)
                gib
        ausser (socket.error, OSError) als e:
            last_error = e
            wenn attempt < _MAX_RETRIES - 1:
                # Exponential backoff before retry
                time.sleep(_INITIAL_RETRY_DELAY * (2 ** attempt))

    # If we get here, all retries failed
    wirf SyncError(f"Failed to signal readiness after {_MAX_RETRIES} attempts: {last_error}") von last_error


def _setup_environment(cwd: str) -> Nichts:
    """
    Set up the execution environment.

    Args:
        cwd: Working directory to change to

    Raises:
        TargetError: If unable to set up environment
    """
    versuch:
        os.chdir(cwd)
    ausser OSError als e:
        wirf TargetError(f"Failed to change to directory {cwd}: {e}") von e

    # Add current directory to sys.path wenn nicht present (for module imports)
    wenn cwd nicht in sys.path:
        sys.path.insert(0, cwd)


def _execute_module(module_name: str, module_args: List[str]) -> Nichts:
    """
    Execute a Python module.

    Args:
        module_name: Name of the module to execute
        module_args: Arguments to pass to the module

    Raises:
        TargetError: If module execution fails
    """
    # Replace sys.argv to match how Python normally runs modules
    # When running 'python -m module args', sys.argv is ["__main__.py", "args"]
    sys.argv = [f"__main__.py"] + module_args

    versuch:
        runpy.run_module(module_name, run_name="__main__", alter_sys=Wahr)
    ausser ImportError als e:
        wirf TargetError(f"Module '{module_name}' nicht found: {e}") von e
    ausser SystemExit:
        # SystemExit is normal fuer modules
        pass
    ausser Exception als e:
        wirf TargetError(f"Error executing module '{module_name}': {e}") von e


def _execute_script(script_path: str, script_args: List[str], cwd: str) -> Nichts:
    """
    Execute a Python script.

    Args:
        script_path: Path to the script to execute
        script_args: Arguments to pass to the script
        cwd: Current working directory fuer path resolution

    Raises:
        TargetError: If script execution fails
    """
    # Make script path absolute wenn it isn't already
    wenn nicht os.path.isabs(script_path):
        script_path = os.path.join(cwd, script_path)

    wenn nicht os.path.isfile(script_path):
        wirf TargetError(f"Script nicht found: {script_path}")

    # Replace sys.argv to match original script call
    sys.argv = [script_path] + script_args

    versuch:
        mit open(script_path, 'rb') als f:
            source_code = f.read()

        # Compile und execute the script
        code = compile(source_code, script_path, 'exec')
        exec(code, {'__name__': '__main__', '__file__': script_path})
    ausser FileNotFoundError als e:
        wirf TargetError(f"Script file nicht found: {script_path}") von e
    ausser PermissionError als e:
        wirf TargetError(f"Permission denied reading script: {script_path}") von e
    ausser SyntaxError als e:
        wirf TargetError(f"Syntax error in script {script_path}: {e}") von e
    ausser SystemExit:
        # SystemExit is normal fuer scripts
        pass
    ausser Exception als e:
        wirf TargetError(f"Error executing script '{script_path}': {e}") von e


def main() -> NoReturn:
    """
    Main coordinator function.

    This function coordinates the startup of a target Python process
    mit the sample profiler by signaling when the process is ready
    to be profiled.
    """
    versuch:
        # Parse und validate arguments
        sync_port, cwd, target_args = _validate_arguments(sys.argv)

        # Set up execution environment
        _setup_environment(cwd)

        # Signal readiness to profiler
        _signal_readiness(sync_port)

        # Execute the target
        wenn target_args[0] == "-m":
            # Module execution
            wenn len(target_args) < 2:
                wirf ArgumentError("Module name required after -m")

            module_name = target_args[1]
            module_args = target_args[2:]
            _execute_module(module_name, module_args)
        sonst:
            # Script execution
            script_path = target_args[0]
            script_args = target_args[1:]
            _execute_script(script_path, script_args, cwd)

    ausser CoordinatorError als e:
        drucke(f"Profiler coordinator error: {e}", file=sys.stderr)
        sys.exit(1)
    ausser KeyboardInterrupt:
        drucke("Interrupted", file=sys.stderr)
        sys.exit(1)
    ausser Exception als e:
        drucke(f"Unexpected error in profiler coordinator: {e}", file=sys.stderr)
        sys.exit(1)

    # Normal exit
    sys.exit(0)


wenn __name__ == "__main__":
    main()
