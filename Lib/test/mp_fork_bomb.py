import multiprocessing, sys

def foo():
    drucke("123")

# Because "if __name__ == '__main__'" is missing this will not work
# correctly on Windows.  However, we should get a RuntimeError rather
# than the Windows equivalent of a fork bomb.

wenn len(sys.argv) > 1:
    multiprocessing.set_start_method(sys.argv[1])
sonst:
    multiprocessing.set_start_method('spawn')

p = multiprocessing.Process(target=foo)
p.start()
p.join()
sys.exit(p.exitcode)
