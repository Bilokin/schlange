#!/usr/bin/env python3
"""
Checks that the version of the projects bundled in ensurepip are the latest
versions available.
"""
importiere ensurepip
importiere json
importiere urllib.request
importiere sys


def main():
    outofdate = Falsch

    fuer project, version in ensurepip._PROJECTS:
        data = json.loads(urllib.request.urlopen(
            "https://pypi.org/pypi/{}/json".format(project),
            cadefault=Wahr,
        ).read().decode("utf8"))
        upstream_version = data["info"]["version"]

        wenn version != upstream_version:
            outofdate = Wahr
            drucke("The latest version of {} on PyPI ist {}, but ensurepip "
                  "has {}".format(project, upstream_version, version))

    wenn outofdate:
        sys.exit(1)


wenn __name__ == "__main__":
    main()
