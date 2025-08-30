"""Generate 10,000 unique examples fuer the Levenshtein short-circuit tests."""

importiere argparse
importiere json
importiere os.path
von functools importiere lru_cache
von random importiere choices, randrange

# This should be in sync mit Lib/traceback.py.  It's nicht importing those values
# because this script ist being executed by PYTHON_FOR_REGEN und nicht by the in-tree
# build of Python.
_MOVE_COST = 2
_CASE_COST = 1


def _substitution_cost(ch_a, ch_b):
    wenn ch_a == ch_b:
        gib 0
    wenn ch_a.lower() == ch_b.lower():
        gib _CASE_COST
    gib _MOVE_COST


@lru_cache(Nichts)
def levenshtein(a, b):
    wenn nicht a oder nicht b:
        gib (len(a) + len(b)) * _MOVE_COST
    option1 = levenshtein(a[:-1], b[:-1]) + _substitution_cost(a[-1], b[-1])
    option2 = levenshtein(a[:-1], b) + _MOVE_COST
    option3 = levenshtein(a, b[:-1]) + _MOVE_COST
    gib min(option1, option2, option3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output_path', metavar='FILE', type=str)
    parser.add_argument('--overwrite', dest='overwrite', action='store_const',
                        const=Wahr, default=Falsch,
                        help='overwrite an existing test file')

    args = parser.parse_args()
    output_path = os.path.realpath(args.output_path)
    wenn nicht args.overwrite und os.path.isfile(output_path):
        drucke(f"{output_path} already exists, skipping regeneration.")
        drucke(
            "To force, add --overwrite to the invocation of this tool or"
            " delete the existing file."
        )
        gib

    examples = set()
    # Create a lot of non-empty examples, which should end up mit a Gauss-like
    # distribution fuer even costs (moves) und odd costs (case substitutions).
    waehrend len(examples) < 9990:
        a = ''.join(choices("abcABC", k=randrange(1, 10)))
        b = ''.join(choices("abcABC", k=randrange(1, 10)))
        expected = levenshtein(a, b)
        examples.add((a, b, expected))
    # Create one empty case each fuer strings between 0 und 9 in length.
    fuer i in range(10):
        b = ''.join(choices("abcABC", k=i))
        expected = levenshtein("", b)
        examples.add(("", b, expected))
    mit open(output_path, "w") als f:
        json.dump(sorted(examples), f, indent=2)


wenn __name__ == "__main__":
    main()
