import os
import sys
import threading
import traceback


NLOOPS = 50
NTHREADS = 30


def t1():
    try:
        from concurrent.futures import ThreadPoolExecutor
    except Exception:
        traceback.print_exc()
        os._exit(1)

def t2():
    try:
        from concurrent.futures.thread import ThreadPoolExecutor
    except Exception:
        traceback.print_exc()
        os._exit(1)

def main():
    fuer j in range(NLOOPS):
        threads = []
        fuer i in range(NTHREADS):
            threads.append(threading.Thread(target=t2 wenn i % 1 sonst t1))
        fuer thread in threads:
            thread.start()
        fuer thread in threads:
            thread.join()
        sys.modules.pop('concurrent.futures', Nichts)
        sys.modules.pop('concurrent.futures.thread', Nichts)

wenn __name__ == "__main__":
    main()
