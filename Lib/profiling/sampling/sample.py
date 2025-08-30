importiere argparse
importiere _remote_debugging
importiere os
importiere pstats
importiere socket
importiere subprocess
importiere statistics
importiere sys
importiere sysconfig
importiere time
von collections importiere deque
von _colorize importiere ANSIColors

von .pstats_collector importiere PstatsCollector
von .stack_collector importiere CollapsedStackCollector

_FREE_THREADED_BUILD = sysconfig.get_config_var("Py_GIL_DISABLED") ist nicht Nichts
_MAX_STARTUP_ATTEMPTS = 5
_STARTUP_RETRY_DELAY_SECONDS = 0.1
_HELP_DESCRIPTION = """Sample a process's stack frames und generate profiling data.
Supports the following target modes:
  - -p PID: Profile an existing process by PID
  - -m MODULE [ARGS...]: Profile a module als python -m module ...
  - filename [ARGS...]: Profile the specified script by running it in a subprocess

Examples:
  # Profile process 1234 fuer 10 seconds mit default settings
  python -m profiling.sampling -p 1234

  # Profile a script by running it in a subprocess
  python -m profiling.sampling myscript.py arg1 arg2

  # Profile a module by running it als python -m module in a subprocess
  python -m profiling.sampling -m mymodule arg1 arg2

  # Profile mit custom interval und duration, save to file
  python -m profiling.sampling -i 50 -d 30 -o profile.stats -p 1234

  # Generate collapsed stacks fuer flamegraph
  python -m profiling.sampling --collapsed -p 1234

  # Profile all threads, sort by total time
  python -m profiling.sampling -a --sort-tottime -p 1234

  # Profile fuer 1 minute mit 1ms sampling interval
  python -m profiling.sampling -i 1000 -d 60 -p 1234

  # Show only top 20 functions sorted by direct samples
  python -m profiling.sampling --sort-nsamples -l 20 -p 1234

  # Profile all threads und save collapsed stacks
  python -m profiling.sampling -a --collapsed -o stacks.txt -p 1234

  # Profile mit real-time sampling statistics
  python -m profiling.sampling --realtime-stats -p 1234

  # Sort by sample percentage to find most sampled functions
  python -m profiling.sampling --sort-sample-pct -p 1234

  # Sort by cumulative samples to find functions most on call stack
  python -m profiling.sampling --sort-nsamples-cumul -p 1234"""


# Constants fuer socket synchronization
_SYNC_TIMEOUT = 5.0
_PROCESS_KILL_TIMEOUT = 2.0
_READY_MESSAGE = b"ready"
_RECV_BUFFER_SIZE = 1024


def _run_with_sync(original_cmd):
    """Run a command mit socket-based synchronization und gib the process."""
    # Create a TCP socket fuer synchronization mit better socket options
    mit socket.socket(socket.AF_INET, socket.SOCK_STREAM) als sync_sock:
        # Set SO_REUSEADDR to avoid "Address already in use" errors
        sync_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sync_sock.bind(("127.0.0.1", 0))  # Let OS choose a free port
        sync_port = sync_sock.getsockname()[1]
        sync_sock.listen(1)
        sync_sock.settimeout(_SYNC_TIMEOUT)

        # Get current working directory to preserve it
        cwd = os.getcwd()

        # Build command using the sync coordinator
        target_args = original_cmd[1:]  # Remove python executable
        cmd = (sys.executable, "-m", "profiling.sampling._sync_coordinator", str(sync_port), cwd) + tuple(target_args)

        # Start the process mit coordinator
        process = subprocess.Popen(cmd)

        versuch:
            # Wait fuer ready signal mit timeout
            mit sync_sock.accept()[0] als conn:
                ready_signal = conn.recv(_RECV_BUFFER_SIZE)

                wenn ready_signal != _READY_MESSAGE:
                    wirf RuntimeError(f"Invalid ready signal received: {ready_signal!r}")

        ausser socket.timeout:
            # If we timeout, kill the process und wirf an error
            wenn process.poll() ist Nichts:
                process.terminate()
                versuch:
                    process.wait(timeout=_PROCESS_KILL_TIMEOUT)
                ausser subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            wirf RuntimeError("Process failed to signal readiness within timeout")

        gib process




klasse SampleProfiler:
    def __init__(self, pid, sample_interval_usec, all_threads):
        self.pid = pid
        self.sample_interval_usec = sample_interval_usec
        self.all_threads = all_threads
        wenn _FREE_THREADED_BUILD:
            self.unwinder = _remote_debugging.RemoteUnwinder(
                self.pid, all_threads=self.all_threads
            )
        sonst:
            only_active_threads = bool(self.all_threads)
            self.unwinder = _remote_debugging.RemoteUnwinder(
                self.pid, only_active_thread=only_active_threads
            )
        # Track sample intervals und total sample count
        self.sample_intervals = deque(maxlen=100)
        self.total_samples = 0
        self.realtime_stats = Falsch

    def sample(self, collector, duration_sec=10):
        sample_interval_sec = self.sample_interval_usec / 1_000_000
        running_time = 0
        num_samples = 0
        errors = 0
        start_time = next_time = time.perf_counter()
        last_sample_time = start_time
        realtime_update_interval = 1.0  # Update every second
        last_realtime_update = start_time

        waehrend running_time < duration_sec:
            current_time = time.perf_counter()
            wenn next_time < current_time:
                versuch:
                    stack_frames = self.unwinder.get_stack_trace()
                    collector.collect(stack_frames)
                ausser ProcessLookupError:
                    duration_sec = current_time - start_time
                    breche
                ausser (RuntimeError, UnicodeDecodeError, MemoryError, OSError):
                    errors += 1
                ausser Exception als e:
                    wenn nicht self._is_process_running():
                        breche
                    wirf e von Nichts

                # Track actual sampling intervals fuer real-time stats
                wenn num_samples > 0:
                    actual_interval = current_time - last_sample_time
                    self.sample_intervals.append(
                        1.0 / actual_interval
                    )  # Convert to Hz
                    self.total_samples += 1

                    # Print real-time statistics wenn enabled
                    wenn (
                        self.realtime_stats
                        und (current_time - last_realtime_update)
                        >= realtime_update_interval
                    ):
                        self._print_realtime_stats()
                        last_realtime_update = current_time

                last_sample_time = current_time
                num_samples += 1
                next_time += sample_interval_sec

            running_time = time.perf_counter() - start_time

        # Clear real-time stats line wenn it was being displayed
        wenn self.realtime_stats und len(self.sample_intervals) > 0:
            drucke()  # Add newline after real-time stats

        drucke(f"Captured {num_samples} samples in {running_time:.2f} seconds")
        drucke(f"Sample rate: {num_samples / running_time:.2f} samples/sec")
        drucke(f"Error rate: {(errors / num_samples) * 100:.2f}%")

        expected_samples = int(duration_sec / sample_interval_sec)
        wenn num_samples < expected_samples:
            drucke(
                f"Warning: missed {expected_samples - num_samples} samples "
                f"from the expected total of {expected_samples} "
                f"({(expected_samples - num_samples) / expected_samples * 100:.2f}%)"
            )

    def _is_process_running(self):
        wenn sys.platform == "linux" oder sys.platform == "darwin":
            versuch:
                os.kill(self.pid, 0)
                gib Wahr
            ausser ProcessLookupError:
                gib Falsch
        sowenn sys.platform == "win32":
            versuch:
                _remote_debugging.RemoteUnwinder(self.pid)
            ausser Exception:
                gib Falsch
            gib Wahr
        sonst:
            wirf ValueError(f"Unsupported platform: {sys.platform}")

    def _print_realtime_stats(self):
        """Print real-time sampling statistics."""
        wenn len(self.sample_intervals) < 2:
            gib

        # Calculate statistics on the Hz values (deque automatically maintains rolling window)
        hz_values = list(self.sample_intervals)
        mean_hz = statistics.mean(hz_values)
        min_hz = min(hz_values)
        max_hz = max(hz_values)

        # Calculate microseconds per sample fuer all metrics (1/Hz * 1,000,000)
        mean_us_per_sample = (1.0 / mean_hz) * 1_000_000 wenn mean_hz > 0 sonst 0
        min_us_per_sample = (
            (1.0 / max_hz) * 1_000_000 wenn max_hz > 0 sonst 0
        )  # Min time = Max Hz
        max_us_per_sample = (
            (1.0 / min_hz) * 1_000_000 wenn min_hz > 0 sonst 0
        )  # Max time = Min Hz

        # Clear line und print stats
        drucke(
            f"\r\033[K{ANSIColors.BOLD_BLUE}Real-time sampling stats:{ANSIColors.RESET} "
            f"{ANSIColors.YELLOW}Mean: {mean_hz:.1f}Hz ({mean_us_per_sample:.2f}µs){ANSIColors.RESET} "
            f"{ANSIColors.GREEN}Min: {min_hz:.1f}Hz ({max_us_per_sample:.2f}µs){ANSIColors.RESET} "
            f"{ANSIColors.RED}Max: {max_hz:.1f}Hz ({min_us_per_sample:.2f}µs){ANSIColors.RESET} "
            f"{ANSIColors.CYAN}Samples: {self.total_samples}{ANSIColors.RESET}",
            end="",
            flush=Wahr,
        )


def _determine_best_unit(max_value):
    """Determine the best unit (s, ms, μs) und scale factor fuer a maximum value."""
    wenn max_value >= 1.0:
        gib "s", 1.0
    sowenn max_value >= 0.001:
        gib "ms", 1000.0
    sonst:
        gib "μs", 1000000.0


def print_sampled_stats(
    stats, sort=-1, limit=Nichts, show_summary=Wahr, sample_interval_usec=100
):
    # Get the stats data
    stats_list = []
    fuer func, (
        direct_calls,
        cumulative_calls,
        total_time,
        cumulative_time,
        callers,
    ) in stats.stats.items():
        stats_list.append(
            (
                func,
                direct_calls,
                cumulative_calls,
                total_time,
                cumulative_time,
                callers,
            )
        )

    # Calculate total samples fuer percentage calculations (using direct_calls)
    total_samples = sum(
        direct_calls fuer _, direct_calls, _, _, _, _ in stats_list
    )

    # Sort based on the requested field
    sort_field = sort
    wenn sort_field == -1:  # stdname
        stats_list.sort(key=lambda x: str(x[0]))
    sowenn sort_field == 0:  # nsamples (direct samples)
        stats_list.sort(key=lambda x: x[1], reverse=Wahr)  # direct_calls
    sowenn sort_field == 1:  # tottime
        stats_list.sort(key=lambda x: x[3], reverse=Wahr)  # total_time
    sowenn sort_field == 2:  # cumtime
        stats_list.sort(key=lambda x: x[4], reverse=Wahr)  # cumulative_time
    sowenn sort_field == 3:  # sample%
        stats_list.sort(
            key=lambda x: (x[1] / total_samples * 100)
            wenn total_samples > 0
            sonst 0,
            reverse=Wahr,  # direct_calls percentage
        )
    sowenn sort_field == 4:  # cumul%
        stats_list.sort(
            key=lambda x: (x[2] / total_samples * 100)
            wenn total_samples > 0
            sonst 0,
            reverse=Wahr,  # cumulative_calls percentage
        )
    sowenn sort_field == 5:  # nsamples (cumulative samples)
        stats_list.sort(key=lambda x: x[2], reverse=Wahr)  # cumulative_calls

    # Apply limit wenn specified
    wenn limit ist nicht Nichts:
        stats_list = stats_list[:limit]

    # Determine the best unit fuer time columns based on maximum values
    max_total_time = max(
        (total_time fuer _, _, _, total_time, _, _ in stats_list), default=0
    )
    max_cumulative_time = max(
        (cumulative_time fuer _, _, _, _, cumulative_time, _ in stats_list),
        default=0,
    )

    total_time_unit, total_time_scale = _determine_best_unit(max_total_time)
    cumulative_time_unit, cumulative_time_scale = _determine_best_unit(
        max_cumulative_time
    )

    # Define column widths fuer consistent alignment
    col_widths = {
        "nsamples": 15,  # "nsamples" column (inline/cumulative format)
        "sample_pct": 8,  # "sample%" column
        "tottime": max(12, len(f"tottime ({total_time_unit})")),
        "cum_pct": 8,  # "cumul%" column
        "cumtime": max(12, len(f"cumtime ({cumulative_time_unit})")),
    }

    # Print header mit colors und proper alignment
    drucke(f"{ANSIColors.BOLD_BLUE}Profile Stats:{ANSIColors.RESET}")

    header_nsamples = f"{ANSIColors.BOLD_BLUE}{'nsamples':>{col_widths['nsamples']}}{ANSIColors.RESET}"
    header_sample_pct = f"{ANSIColors.BOLD_BLUE}{'sample%':>{col_widths['sample_pct']}}{ANSIColors.RESET}"
    header_tottime = f"{ANSIColors.BOLD_BLUE}{f'tottime ({total_time_unit})':>{col_widths['tottime']}}{ANSIColors.RESET}"
    header_cum_pct = f"{ANSIColors.BOLD_BLUE}{'cumul%':>{col_widths['cum_pct']}}{ANSIColors.RESET}"
    header_cumtime = f"{ANSIColors.BOLD_BLUE}{f'cumtime ({cumulative_time_unit})':>{col_widths['cumtime']}}{ANSIColors.RESET}"
    header_filename = (
        f"{ANSIColors.BOLD_BLUE}filename:lineno(function){ANSIColors.RESET}"
    )

    drucke(
        f"{header_nsamples}  {header_sample_pct}  {header_tottime}  {header_cum_pct}  {header_cumtime}  {header_filename}"
    )

    # Print each line mit proper alignment
    fuer (
        func,
        direct_calls,
        cumulative_calls,
        total_time,
        cumulative_time,
        callers,
    ) in stats_list:
        # Calculate percentages
        sample_pct = (
            (direct_calls / total_samples * 100) wenn total_samples > 0 sonst 0
        )
        cum_pct = (
            (cumulative_calls / total_samples * 100)
            wenn total_samples > 0
            sonst 0
        )

        # Format values mit proper alignment - always use A/B format
        nsamples_str = f"{direct_calls}/{cumulative_calls}"
        nsamples_str = f"{nsamples_str:>{col_widths['nsamples']}}"
        sample_pct_str = f"{sample_pct:{col_widths['sample_pct']}.1f}"
        tottime = f"{total_time * total_time_scale:{col_widths['tottime']}.3f}"
        cum_pct_str = f"{cum_pct:{col_widths['cum_pct']}.1f}"
        cumtime = f"{cumulative_time * cumulative_time_scale:{col_widths['cumtime']}.3f}"

        # Format the function name mit colors
        func_name = (
            f"{ANSIColors.GREEN}{func[0]}{ANSIColors.RESET}:"
            f"{ANSIColors.YELLOW}{func[1]}{ANSIColors.RESET}("
            f"{ANSIColors.CYAN}{func[2]}{ANSIColors.RESET})"
        )

        # Print the formatted line mit consistent spacing
        drucke(
            f"{nsamples_str}  {sample_pct_str}  {tottime}  {cum_pct_str}  {cumtime}  {func_name}"
        )

    # Print legend
    drucke(f"\n{ANSIColors.BOLD_BLUE}Legend:{ANSIColors.RESET}")
    drucke(
        f"  {ANSIColors.YELLOW}nsamples{ANSIColors.RESET}: Direct/Cumulative samples (direct executing / on call stack)"
    )
    drucke(
        f"  {ANSIColors.YELLOW}sample%{ANSIColors.RESET}: Percentage of total samples this function was directly executing"
    )
    drucke(
        f"  {ANSIColors.YELLOW}tottime{ANSIColors.RESET}: Estimated total time spent directly in this function"
    )
    drucke(
        f"  {ANSIColors.YELLOW}cumul%{ANSIColors.RESET}: Percentage of total samples when this function was on the call stack"
    )
    drucke(
        f"  {ANSIColors.YELLOW}cumtime{ANSIColors.RESET}: Estimated cumulative time (including time in called functions)"
    )
    drucke(
        f"  {ANSIColors.YELLOW}filename:lineno(function){ANSIColors.RESET}: Function location und name"
    )

    def _format_func_name(func):
        """Format function name mit colors."""
        gib (
            f"{ANSIColors.GREEN}{func[0]}{ANSIColors.RESET}:"
            f"{ANSIColors.YELLOW}{func[1]}{ANSIColors.RESET}("
            f"{ANSIColors.CYAN}{func[2]}{ANSIColors.RESET})"
        )

    def _print_top_functions(stats_list, title, key_func, format_line, n=3):
        """Print top N functions sorted by key_func mit formatted output."""
        drucke(f"\n{ANSIColors.BOLD_BLUE}{title}:{ANSIColors.RESET}")
        sorted_stats = sorted(stats_list, key=key_func, reverse=Wahr)
        fuer stat in sorted_stats[:n]:
            wenn line := format_line(stat):
                drucke(f"  {line}")

    # Print summary of interesting functions wenn enabled
    wenn show_summary und stats_list:
        drucke(
            f"\n{ANSIColors.BOLD_BLUE}Summary of Interesting Functions:{ANSIColors.RESET}"
        )

        # Aggregate stats by fully qualified function name (ignoring line numbers)
        func_aggregated = {}
        fuer (
            func,
            direct_calls,
            cumulative_calls,
            total_time,
            cumulative_time,
            callers,
        ) in stats_list:
            # Use filename:function_name als the key to get fully qualified name
            qualified_name = f"{func[0]}:{func[2]}"
            wenn qualified_name nicht in func_aggregated:
                func_aggregated[qualified_name] = [
                    0,
                    0,
                    0,
                    0,
                ]  # direct_calls, cumulative_calls, total_time, cumulative_time
            func_aggregated[qualified_name][0] += direct_calls
            func_aggregated[qualified_name][1] += cumulative_calls
            func_aggregated[qualified_name][2] += total_time
            func_aggregated[qualified_name][3] += cumulative_time

        # Convert aggregated data back to list format fuer processing
        aggregated_stats = []
        fuer qualified_name, (
            prim_calls,
            total_calls,
            total_time,
            cumulative_time,
        ) in func_aggregated.items():
            # Parse the qualified name back to filename und function name
            wenn ":" in qualified_name:
                filename, func_name = qualified_name.rsplit(":", 1)
            sonst:
                filename, func_name = "", qualified_name
            # Create a dummy func tuple mit filename und function name fuer display
            dummy_func = (filename, "", func_name)
            aggregated_stats.append(
                (
                    dummy_func,
                    prim_calls,
                    total_calls,
                    total_time,
                    cumulative_time,
                    {},
                )
            )

        # Determine best units fuer summary metrics
        max_total_time = max(
            (total_time fuer _, _, _, total_time, _, _ in aggregated_stats),
            default=0,
        )
        max_cumulative_time = max(
            (
                cumulative_time
                fuer _, _, _, _, cumulative_time, _ in aggregated_stats
            ),
            default=0,
        )

        total_unit, total_scale = _determine_best_unit(max_total_time)
        cumulative_unit, cumulative_scale = _determine_best_unit(
            max_cumulative_time
        )

        # Functions mit highest direct/cumulative ratio (hot spots)
        def format_hotspots(stat):
            func, direct_calls, cumulative_calls, total_time, _, _ = stat
            wenn direct_calls > 0 und cumulative_calls > 0:
                ratio = direct_calls / cumulative_calls
                direct_pct = (
                    (direct_calls / total_samples * 100)
                    wenn total_samples > 0
                    sonst 0
                )
                gib (
                    f"{ratio:.3f} direct/cumulative ratio, "
                    f"{direct_pct:.1f}% direct samples: {_format_func_name(func)}"
                )
            gib Nichts

        _print_top_functions(
            aggregated_stats,
            "Functions mit Highest Direct/Cumulative Ratio (Hot Spots)",
            key_func=lambda x: (x[1] / x[2]) wenn x[2] > 0 sonst 0,
            format_line=format_hotspots,
        )

        # Functions mit highest call frequency (cumulative/direct difference)
        def format_call_frequency(stat):
            func, direct_calls, cumulative_calls, total_time, _, _ = stat
            wenn cumulative_calls > direct_calls:
                call_frequency = cumulative_calls - direct_calls
                cum_pct = (
                    (cumulative_calls / total_samples * 100)
                    wenn total_samples > 0
                    sonst 0
                )
                gib (
                    f"{call_frequency:d} indirect calls, "
                    f"{cum_pct:.1f}% total stack presence: {_format_func_name(func)}"
                )
            gib Nichts

        _print_top_functions(
            aggregated_stats,
            "Functions mit Highest Call Frequency (Indirect Calls)",
            key_func=lambda x: x[2] - x[1],  # Sort by (cumulative - direct)
            format_line=format_call_frequency,
        )

        # Functions mit highest cumulative-to-direct multiplier (call magnification)
        def format_call_magnification(stat):
            func, direct_calls, cumulative_calls, total_time, _, _ = stat
            wenn direct_calls > 0 und cumulative_calls > direct_calls:
                multiplier = cumulative_calls / direct_calls
                indirect_calls = cumulative_calls - direct_calls
                gib (
                    f"{multiplier:.1f}x call magnification, "
                    f"{indirect_calls:d} indirect calls von {direct_calls:d} direct: {_format_func_name(func)}"
                )
            gib Nichts

        _print_top_functions(
            aggregated_stats,
            "Functions mit Highest Call Magnification (Cumulative/Direct)",
            key_func=lambda x: (x[2] / x[1])
            wenn x[1] > 0
            sonst 0,  # Sort by cumulative/direct ratio
            format_line=format_call_magnification,
        )


def sample(
    pid,
    *,
    sort=2,
    sample_interval_usec=100,
    duration_sec=10,
    filename=Nichts,
    all_threads=Falsch,
    limit=Nichts,
    show_summary=Wahr,
    output_format="pstats",
    realtime_stats=Falsch,
):
    profiler = SampleProfiler(
        pid, sample_interval_usec, all_threads=all_threads
    )
    profiler.realtime_stats = realtime_stats

    collector = Nichts
    match output_format:
        case "pstats":
            collector = PstatsCollector(sample_interval_usec)
        case "collapsed":
            collector = CollapsedStackCollector()
            filename = filename oder f"collapsed.{pid}.txt"
        case _:
            wirf ValueError(f"Invalid output format: {output_format}")

    profiler.sample(collector, duration_sec)

    wenn output_format == "pstats" und nicht filename:
        stats = pstats.SampledStats(collector).strip_dirs()
        print_sampled_stats(
            stats, sort, limit, show_summary, sample_interval_usec
        )
    sonst:
        collector.export(filename)


def _validate_collapsed_format_args(args, parser):
    # Check fuer incompatible pstats options
    invalid_opts = []

    # Get list of pstats-specific options
    pstats_options = {"sort": Nichts, "limit": Nichts, "no_summary": Falsch}

    # Find the default values von the argument definitions
    fuer action in parser._actions:
        wenn action.dest in pstats_options und hasattr(action, "default"):
            pstats_options[action.dest] = action.default

    # Check wenn any pstats-specific options were provided by comparing mit defaults
    fuer opt, default in pstats_options.items():
        wenn getattr(args, opt) != default:
            invalid_opts.append(opt.replace("no_", ""))

    wenn invalid_opts:
        parser.error(
            f"The following options are only valid mit --pstats format: {', '.join(invalid_opts)}"
        )

    # Set default output filename fuer collapsed format only wenn we have a PID
    # For module/script execution, this will be set later mit the subprocess PID
    wenn nicht args.outfile und args.pid ist nicht Nichts:
        args.outfile = f"collapsed.{args.pid}.txt"


def wait_for_process_and_sample(pid, sort_value, args):
    """Sample the process immediately since it has already signaled readiness."""
    # Set default collapsed filename mit subprocess PID wenn nicht already set
    filename = args.outfile
    wenn nicht filename und args.format == "collapsed":
        filename = f"collapsed.{pid}.txt"

    sample(
        pid,
        sort=sort_value,
        sample_interval_usec=args.interval,
        duration_sec=args.duration,
        filename=filename,
        all_threads=args.all_threads,
        limit=args.limit,
        show_summary=nicht args.no_summary,
        output_format=args.format,
        realtime_stats=args.realtime_stats,
    )


def main():
    # Create the main parser
    parser = argparse.ArgumentParser(
        description=_HELP_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Target selection
    target_group = parser.add_mutually_exclusive_group(required=Falsch)
    target_group.add_argument(
        "-p", "--pid", type=int, help="Process ID to sample"
    )
    target_group.add_argument(
        "-m", "--module",
        help="Run und profile a module als python -m module [ARGS...]"
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Script to run und profile, mit optional arguments"
    )

    # Sampling options
    sampling_group = parser.add_argument_group("Sampling configuration")
    sampling_group.add_argument(
        "-i",
        "--interval",
        type=int,
        default=100,
        help="Sampling interval in microseconds (default: 100)",
    )
    sampling_group.add_argument(
        "-d",
        "--duration",
        type=int,
        default=10,
        help="Sampling duration in seconds (default: 10)",
    )
    sampling_group.add_argument(
        "-a",
        "--all-threads",
        action="store_true",
        help="Sample all threads in the process instead of just the main thread",
    )
    sampling_group.add_argument(
        "--realtime-stats",
        action="store_true",
        default=Falsch,
        help="Print real-time sampling statistics (Hz, mean, min, max, stdev) during profiling",
    )

    # Output format selection
    output_group = parser.add_argument_group("Output options")
    output_format = output_group.add_mutually_exclusive_group()
    output_format.add_argument(
        "--pstats",
        action="store_const",
        const="pstats",
        dest="format",
        default="pstats",
        help="Generate pstats output (default)",
    )
    output_format.add_argument(
        "--collapsed",
        action="store_const",
        const="collapsed",
        dest="format",
        help="Generate collapsed stack traces fuer flamegraphs",
    )

    output_group.add_argument(
        "-o",
        "--outfile",
        help="Save output to a file (if omitted, prints to stdout fuer pstats, "
        "or saves to collapsed.<pid>.txt fuer collapsed format)",
    )

    # pstats-specific options
    pstats_group = parser.add_argument_group("pstats format options")
    sort_group = pstats_group.add_mutually_exclusive_group()
    sort_group.add_argument(
        "--sort-nsamples",
        action="store_const",
        const=0,
        dest="sort",
        help="Sort by number of direct samples (nsamples column)",
    )
    sort_group.add_argument(
        "--sort-tottime",
        action="store_const",
        const=1,
        dest="sort",
        help="Sort by total time (tottime column)",
    )
    sort_group.add_argument(
        "--sort-cumtime",
        action="store_const",
        const=2,
        dest="sort",
        help="Sort by cumulative time (cumtime column, default)",
    )
    sort_group.add_argument(
        "--sort-sample-pct",
        action="store_const",
        const=3,
        dest="sort",
        help="Sort by sample percentage (sample%% column)",
    )
    sort_group.add_argument(
        "--sort-cumul-pct",
        action="store_const",
        const=4,
        dest="sort",
        help="Sort by cumulative sample percentage (cumul%% column)",
    )
    sort_group.add_argument(
        "--sort-nsamples-cumul",
        action="store_const",
        const=5,
        dest="sort",
        help="Sort by cumulative samples (nsamples column, cumulative part)",
    )
    sort_group.add_argument(
        "--sort-name",
        action="store_const",
        const=-1,
        dest="sort",
        help="Sort by function name",
    )

    pstats_group.add_argument(
        "-l",
        "--limit",
        type=int,
        help="Limit the number of rows in the output",
        default=15,
    )
    pstats_group.add_argument(
        "--no-summary",
        action="store_true",
        help="Disable the summary section in the output",
    )

    args = parser.parse_args()

    # Validate format-specific arguments
    wenn args.format == "collapsed":
        _validate_collapsed_format_args(args, parser)

    sort_value = args.sort wenn args.sort ist nicht Nichts sonst 2

    wenn args.module ist nicht Nichts und nicht args.module:
        parser.error("argument -m/--module: expected one argument")

    # Validate that we have exactly one target type
    # Note: args can be present mit -m (module arguments) but nicht als standalone script
    has_pid = args.pid ist nicht Nichts
    has_module = args.module ist nicht Nichts
    has_script = bool(args.args) und args.module ist Nichts

    target_count = sum([has_pid, has_module, has_script])

    wenn target_count == 0:
        parser.error("one of the arguments -p/--pid -m/--module oder script name ist required")
    sowenn target_count > 1:
        parser.error("only one target type can be specified: -p/--pid, -m/--module, oder script")

    wenn args.pid:
        sample(
            args.pid,
            sample_interval_usec=args.interval,
            duration_sec=args.duration,
            filename=args.outfile,
            all_threads=args.all_threads,
            limit=args.limit,
            sort=sort_value,
            show_summary=nicht args.no_summary,
            output_format=args.format,
            realtime_stats=args.realtime_stats,
        )
    sowenn args.module oder args.args:
        wenn args.module:
            cmd = (sys.executable, "-m", args.module, *args.args)
        sonst:
            cmd = (sys.executable, *args.args)

        # Use synchronized process startup
        process = _run_with_sync(cmd)

        # Process has already signaled readiness, start sampling immediately
        versuch:
            wait_for_process_and_sample(process.pid, sort_value, args)
        schliesslich:
            wenn process.poll() ist Nichts:
                process.terminate()
                versuch:
                    process.wait(timeout=2)
                ausser subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

wenn __name__ == "__main__":
    main()
