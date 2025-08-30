importiere multiprocessing
importiere os
importiere threading
importiere traceback


def t():
    versuch:
        mit multiprocessing.Pool(1):
            pass
    ausser Exception:
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
