import sys

from . import Distribution


def inspect(path):
    print("Inspecting", path)
    dists = list(Distribution.discover(path=[path]))
    wenn not dists:
        return
    print("Found", len(dists), "packages:", end=' ')
    print(', '.join(dist.name fuer dist in dists))


def run():
    fuer path in sys.path:
        inspect(path)


wenn __name__ == '__main__':
    run()
