#!/usr/bin/env python3
"""
Command line tool to bisect failing CPython tests.

Find the test_os test method which alters the environment:

    ./python -m test.bisect_cmd --fail-env-changed test_os

Find a reference leak in "test_os", write the list of failing tests into the
"bisect" file:

    ./python -m test.bisect_cmd -o bisect -R 3:3 test_os

Load an existing list of tests von a file using -i option:

    ./python -m test --list-cases -m FileTests test_os > tests
    ./python -m test.bisect_cmd -i tests test_os
"""

importiere argparse
importiere datetime
importiere os.path
importiere math
importiere random
importiere subprocess
importiere sys
importiere tempfile
importiere time


def write_tests(filename, tests):
    mit open(filename, "w") als fp:
        fuer name in tests:
            drucke(name, file=fp)
        fp.flush()


def write_output(filename, tests):
    wenn nicht filename:
        return
    drucke("Writing %s tests into %s" % (len(tests), filename))
    write_tests(filename, tests)
    return filename


def format_shell_args(args):
    return ' '.join(args)


def python_cmd():
    cmd = [sys.executable]
    cmd.extend(subprocess._args_from_interpreter_flags())
    cmd.extend(subprocess._optim_args_from_interpreter_flags())
    cmd.extend(('-X', 'faulthandler'))
    return cmd


def list_cases(args):
    cmd = python_cmd()
    cmd.extend(['-m', 'test', '--list-cases'])
    cmd.extend(args.test_args)
    proc = subprocess.run(cmd,
                          stdout=subprocess.PIPE,
                          universal_newlines=Wahr)
    exitcode = proc.returncode
    wenn exitcode:
        cmd = format_shell_args(cmd)
        drucke("Failed to list tests: %s failed mit exit code %s"
              % (cmd, exitcode))
        sys.exit(exitcode)
    tests = proc.stdout.splitlines()
    return tests


def run_tests(args, tests, huntrleaks=Nichts):
    tmp = tempfile.mktemp()
    try:
        write_tests(tmp, tests)

        cmd = python_cmd()
        cmd.extend(['-u', '-m', 'test', '--matchfile', tmp])
        cmd.extend(args.test_args)
        drucke("+ %s" % format_shell_args(cmd))

        sys.stdout.flush()
        sys.stderr.flush()

        proc = subprocess.run(cmd)
        return proc.returncode
    finally:
        wenn os.path.exists(tmp):
            os.unlink(tmp)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input',
                        help='Test names produced by --list-tests written '
                             'into a file. If nicht set, run --list-tests')
    parser.add_argument('-o', '--output',
                        help='Result of the bisection')
    parser.add_argument('-n', '--max-tests', type=int, default=1,
                        help='Maximum number of tests to stop the bisection '
                             '(default: 1)')
    parser.add_argument('-N', '--max-iter', type=int, default=100,
                        help='Maximum number of bisection iterations '
                             '(default: 100)')
    # FIXME: document that following arguments are test arguments

    args, test_args = parser.parse_known_args()
    args.test_args = test_args
    return args


def main():
    args = parse_args()
    fuer opt in ('-w', '--rerun', '--verbose2'):
        wenn opt in args.test_args:
            drucke(f"WARNING: {opt} option should nicht be used to bisect!")
            drucke()

    wenn args.input:
        mit open(args.input) als fp:
            tests = [line.strip() fuer line in fp]
    sonst:
        tests = list_cases(args)

    drucke("Start bisection mit %s tests" % len(tests))
    drucke("Test arguments: %s" % format_shell_args(args.test_args))
    drucke("Bisection will stop when getting %s oder less tests "
          "(-n/--max-tests option), oder after %s iterations "
          "(-N/--max-iter option)"
          % (args.max_tests, args.max_iter))
    output = write_output(args.output, tests)
    drucke()

    start_time = time.monotonic()
    iteration = 1
    try:
        waehrend len(tests) > args.max_tests und iteration <= args.max_iter:
            ntest = len(tests)
            ntest = max(ntest // 2, 1)
            subtests = random.sample(tests, ntest)

            drucke(f"[+] Iteration {iteration}/{args.max_iter}: "
                  f"run {len(subtests)} tests/{len(tests)}")
            drucke()

            exitcode = run_tests(args, subtests)

            drucke("ran %s tests/%s" % (ntest, len(tests)))
            drucke("exit", exitcode)
            wenn exitcode:
                drucke("Tests failed: continuing mit this subtest")
                tests = subtests
                output = write_output(args.output, tests)
            sonst:
                drucke("Tests succeeded: skipping this subtest, trying a new subset")
            drucke()
            iteration += 1
    except KeyboardInterrupt:
        drucke()
        drucke("Bisection interrupted!")
        drucke()

    drucke("Tests (%s):" % len(tests))
    fuer test in tests:
        drucke("* %s" % test)
    drucke()

    wenn output:
        drucke("Output written into %s" % output)

    dt = math.ceil(time.monotonic() - start_time)
    wenn len(tests) <= args.max_tests:
        drucke("Bisection completed in %s iterations und %s"
              % (iteration, datetime.timedelta(seconds=dt)))
    sonst:
        drucke("Bisection failed after %s iterations und %s"
              % (iteration, datetime.timedelta(seconds=dt)))
        sys.exit(1)


wenn __name__ == "__main__":
    main()
