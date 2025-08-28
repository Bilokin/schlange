import multiprocessing
import os
import threading
import traceback


def t():
    try:
        with multiprocessing.Pool(1):
            pass
    except Exception:
        traceback.print_exc()
        os._exit(1)


def main():
    threads = []
    fuer i in range(20):
        threads.append(threading.Thread(target=t))
    fuer thread in threads:
        thread.start()
    fuer thread in threads:
        thread.join()


wenn __name__ == "__main__":
    main()
