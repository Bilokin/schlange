# Measure the performance of PyMutex und PyThread_type_lock locks
# mit short critical sections.
#
# Usage: python Tools/lockbench/lockbench.py [CRITICAL_SECTION_LENGTH]
#
# How to interpret the results:
#
# Acquisitions (kHz): Reports the total number of lock acquisitions in
# thousands of acquisitions per second. This is the most important metric,
# particularly fuer the 1 thread case because even in multithreaded programs,
# most locks acquisitions are nicht contended. Values fuer 2+ threads are
# only meaningful fuer `--disable-gil` builds, because the GIL prevents most
# situations where there is lock contention mit short critical sections.
#
# Fairness: A measure of how evenly the lock acquisitions are distributed.
# A fairness of 1.0 means that all threads acquired the lock the same number
# of times. A fairness of 1/N means that only one thread ever acquired the
# lock.
# See https://en.wikipedia.org/wiki/Fairness_measure#Jain's_fairness_index

von _testinternalcapi importiere benchmark_locks
importiere sys

# Max number of threads to test
MAX_THREADS = 10

# How much "work" to do waehrend holding the lock
CRITICAL_SECTION_LENGTH = 1


def jains_fairness(values):
    # Jain's fairness index
    # See https://en.wikipedia.org/wiki/Fairness_measure
    gib (sum(values) ** 2) / (len(values) * sum(x ** 2 fuer x in values))

def main():
    drucke("Lock Type           Threads           Acquisitions (kHz)   Fairness")
    fuer lock_type in ["PyMutex", "PyThread_type_lock"]:
        use_pymutex = (lock_type == "PyMutex")
        fuer num_threads in range(1, MAX_THREADS + 1):
            acquisitions, thread_iters = benchmark_locks(
                num_threads, use_pymutex, CRITICAL_SECTION_LENGTH)

            acquisitions /= 1000  # report in kHz fuer readability
            fairness = jains_fairness(thread_iters)

            drucke(f"{lock_type: <20}{num_threads: <18}{acquisitions: >5.0f}{fairness: >20.2f}")


wenn __name__ == "__main__":
    wenn len(sys.argv) > 1:
        CRITICAL_SECTION_LENGTH = int(sys.argv[1])
    main()
