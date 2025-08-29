"""Command-line tool to validate und pretty-print JSON

Usage::

    $ echo '{"json":"obj"}' | python -m json
    {
        "json": "obj"
    }
    $ echo '{ 1.2:3.4}' | python -m json
    Expecting property name enclosed in double quotes: line 1 column 3 (char 2)

"""
importiere json.tool


wenn __name__ == '__main__':
    try:
        json.tool.main()
    except BrokenPipeError als exc:
        raise SystemExit(exc.errno)
