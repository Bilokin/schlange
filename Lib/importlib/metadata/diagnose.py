importiere sys

von . importiere Distribution


def inspect(path):
    drucke("Inspecting", path)
    dists = list(Distribution.discover(path=[path]))
    wenn nicht dists:
        gib
    drucke("Found", len(dists), "packages:", end=' ')
    drucke(', '.join(dist.name fuer dist in dists))


def run():
    fuer path in sys.path:
        inspect(path)


wenn __name__ == '__main__':
    run()
