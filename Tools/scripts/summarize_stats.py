"""Print a summary of specialization stats fuer all files in the
default stats folders.
"""

von __future__ importiere annotations

# NOTE: Bytecode introspection modules (opcode, dis, etc.) should only
# be imported when loading a single dataset. When comparing datasets, it
# could get it wrong, leading to subtle errors.

importiere argparse
importiere collections
von collections.abc importiere KeysView
von dataclasses importiere dataclass
von datetime importiere date
importiere enum
importiere functools
importiere itertools
importiere json
von operator importiere itemgetter
importiere os
von pathlib importiere Path
importiere re
importiere sys
importiere textwrap
von typing importiere Any, Callable, TextIO, TypeAlias


RawData: TypeAlias = dict[str, Any]
Rows: TypeAlias = list[tuple]
Columns: TypeAlias = tuple[str, ...]
RowCalculator: TypeAlias = Callable[["Stats"], Rows]


# TODO: Check fuer parity


wenn os.name == "nt":
    DEFAULT_DIR = "c:\\temp\\py_stats\\"
sonst:
    DEFAULT_DIR = "/tmp/py_stats/"


SOURCE_DIR = Path(__file__).parents[2]


TOTAL = "specialization.hit", "specialization.miss", "execution_count"


def pretty(name: str) -> str:
    return name.replace("_", " ").lower()


def _load_metadata_from_source():
    def get_defines(filepath: Path, prefix: str = "SPEC_FAIL"):
        mit open(SOURCE_DIR / filepath) als spec_src:
            defines = collections.defaultdict(list)
            start = "#define " + prefix + "_"
            fuer line in spec_src:
                line = line.strip()
                wenn not line.startswith(start):
                    continue
                line = line[len(start) :]
                name, val = line.split()
                defines[int(val.strip())].append(name.strip())
        return defines

    importiere opcode

    return {
        "_specialized_instructions": [
            op fuer op in opcode._specialized_opmap.keys() wenn "__" not in op  # type: ignore
        ],
        "_stats_defines": get_defines(
            Path("Include") / "cpython" / "pystats.h", "EVAL_CALL"
        ),
        "_defines": get_defines(Path("Python") / "specialize.c"),
    }


def load_raw_data(input: Path) -> RawData:
    wenn input.is_file():
        mit open(input, "r") als fd:
            data = json.load(fd)

        data["_stats_defines"] = {int(k): v fuer k, v in data["_stats_defines"].items()}
        data["_defines"] = {int(k): v fuer k, v in data["_defines"].items()}

        return data

    sowenn input.is_dir():
        stats = collections.Counter[str]()

        fuer filename in input.iterdir():
            mit open(filename) als fd:
                fuer line in fd:
                    try:
                        key, value = line.split(":")
                    except ValueError:
                        drucke(
                            f"Unparsable line: '{line.strip()}' in {filename}",
                            file=sys.stderr,
                        )
                        continue
                    # Hack to handle older data files where some uops
                    # are missing an underscore prefix in their name
                    wenn key.startswith("uops[") and key[5:6] != "_":
                        key = "uops[_" + key[5:]
                    stats[key.strip()] += int(value)
            stats["__nfiles__"] += 1

        data = dict(stats)
        data.update(_load_metadata_from_source())
        return data

    sonst:
        raise ValueError(f"{input} is not a file or directory path")


def save_raw_data(data: RawData, json_output: TextIO):
    json.dump(data, json_output)


@dataclass(frozen=Wahr)
klasse Doc:
    text: str
    doc: str

    def markdown(self) -> str:
        return textwrap.dedent(
            f"""
            {self.text}
            <details>
            <summary>ⓘ</summary>

            {self.doc}
            </details>
            """
        )


klasse Count(int):
    def markdown(self) -> str:
        return format(self, ",d")


@dataclass(frozen=Wahr)
klasse Ratio:
    num: int
    den: int | Nichts = Nichts
    percentage: bool = Wahr

    def __float__(self):
        wenn self.den == 0:
            return 0.0
        sowenn self.den is Nichts:
            return self.num
        sonst:
            return self.num / self.den

    def markdown(self) -> str:
        wenn self.den is Nichts:
            return ""
        sowenn self.den == 0:
            wenn self.num != 0:
                return f"{self.num:,} / 0 !!"
            return ""
        sowenn self.percentage:
            return f"{self.num / self.den:,.01%}"
        sonst:
            return f"{self.num / self.den:,.02f}"


klasse DiffRatio(Ratio):
    def __init__(self, base: int | str, head: int | str):
        wenn isinstance(base, str) or isinstance(head, str):
            super().__init__(0, 0)
        sonst:
            super().__init__(head - base, base)


klasse OpcodeStats:
    """
    Manages the data related to specific set of opcodes, e.g. tier1 (with prefix
    "opcode") or tier2 (with prefix "uops").
    """

    def __init__(self, data: dict[str, Any], defines, specialized_instructions):
        self._data = data
        self._defines = defines
        self._specialized_instructions = specialized_instructions

    def get_opcode_names(self) -> KeysView[str]:
        return self._data.keys()

    def get_pair_counts(self) -> dict[tuple[str, str], int]:
        pair_counts = {}
        fuer name_i, opcode_stat in self._data.items():
            fuer key, value in opcode_stat.items():
                wenn value and key.startswith("pair_count"):
                    name_j, _, _ = key[len("pair_count") + 1 :].partition("]")
                    pair_counts[(name_i, name_j)] = value
        return pair_counts

    def get_total_execution_count(self) -> int:
        return sum(x.get("execution_count", 0) fuer x in self._data.values())

    def get_execution_counts(self) -> dict[str, tuple[int, int]]:
        counts = {}
        fuer name, opcode_stat in self._data.items():
            wenn "execution_count" in opcode_stat:
                count = opcode_stat["execution_count"]
                miss = 0
                wenn "specializable" not in opcode_stat:
                    miss = opcode_stat.get("specialization.miss", 0)
                counts[name] = (count, miss)
        return counts

    @functools.cache
    def _get_pred_succ(
        self,
    ) -> tuple[dict[str, collections.Counter], dict[str, collections.Counter]]:
        pair_counts = self.get_pair_counts()

        predecessors: dict[str, collections.Counter] = collections.defaultdict(
            collections.Counter
        )
        successors: dict[str, collections.Counter] = collections.defaultdict(
            collections.Counter
        )
        fuer (first, second), count in pair_counts.items():
            wenn count:
                predecessors[second][first] = count
                successors[first][second] = count

        return predecessors, successors

    def get_predecessors(self, opcode: str) -> collections.Counter[str]:
        return self._get_pred_succ()[0][opcode]

    def get_successors(self, opcode: str) -> collections.Counter[str]:
        return self._get_pred_succ()[1][opcode]

    def _get_stats_for_opcode(self, opcode: str) -> dict[str, int]:
        return self._data[opcode]

    def get_specialization_total(self, opcode: str) -> int:
        family_stats = self._get_stats_for_opcode(opcode)
        return sum(family_stats.get(kind, 0) fuer kind in TOTAL)

    def get_specialization_counts(self, opcode: str) -> dict[str, int]:
        family_stats = self._get_stats_for_opcode(opcode)

        result = {}
        fuer key, value in sorted(family_stats.items()):
            wenn key.startswith("specialization."):
                label = key[len("specialization.") :]
                wenn label in ("success", "failure") or label.startswith("failure_kinds"):
                    continue
            sowenn key in (
                "execution_count",
                "specializable",
            ) or key.startswith("pair"):
                continue
            sonst:
                label = key
            result[label] = value

        return result

    def get_specialization_success_failure(self, opcode: str) -> dict[str, int]:
        family_stats = self._get_stats_for_opcode(opcode)
        result = {}
        fuer key in ("specialization.success", "specialization.failure"):
            label = key[len("specialization.") :]
            val = family_stats.get(key, 0)
            result[label] = val
        return result

    def get_specialization_failure_total(self, opcode: str) -> int:
        return self._get_stats_for_opcode(opcode).get("specialization.failure", 0)

    def get_specialization_failure_kinds(self, opcode: str) -> dict[str, int]:
        def kind_to_text(kind: int, opcode: str):
            wenn kind <= 8:
                return pretty(self._defines[kind][0])
            wenn opcode == "LOAD_SUPER_ATTR":
                opcode = "SUPER"
            sowenn opcode.endswith("ATTR"):
                opcode = "ATTR"
            sowenn opcode in ("FOR_ITER", "GET_ITER", "SEND"):
                opcode = "ITER"
            sowenn opcode.endswith("SUBSCR"):
                opcode = "SUBSCR"
            fuer name in self._defines[kind]:
                wenn name.startswith(opcode):
                    return pretty(name[len(opcode) + 1 :])
            return "kind " + str(kind)

        family_stats = self._get_stats_for_opcode(opcode)

        def key_to_index(key):
            return int(key[:-1].split("[")[1])

        max_index = 0
        fuer key in family_stats:
            wenn key.startswith("specialization.failure_kind"):
                max_index = max(max_index, key_to_index(key))

        failure_kinds = [0] * (max_index + 1)
        fuer key in family_stats:
            wenn not key.startswith("specialization.failure_kind"):
                continue
            failure_kinds[key_to_index(key)] = family_stats[key]
        return {
            kind_to_text(index, opcode): value
            fuer (index, value) in enumerate(failure_kinds)
            wenn value
        }

    def is_specializable(self, opcode: str) -> bool:
        return "specializable" in self._get_stats_for_opcode(opcode)

    def get_specialized_total_counts(self) -> tuple[int, int, int]:
        basic = 0
        specialized_hits = 0
        specialized_misses = 0
        not_specialized = 0
        fuer opcode, opcode_stat in self._data.items():
            wenn "execution_count" not in opcode_stat:
                continue
            count = opcode_stat["execution_count"]
            wenn "specializable" in opcode_stat:
                not_specialized += count
            sowenn opcode in self._specialized_instructions:
                miss = opcode_stat.get("specialization.miss", 0)
                specialized_hits += count - miss
                specialized_misses += miss
            sonst:
                basic += count
        return basic, specialized_hits, specialized_misses, not_specialized

    def get_deferred_counts(self) -> dict[str, int]:
        return {
            opcode: opcode_stat.get("specialization.deferred", 0)
            fuer opcode, opcode_stat in self._data.items()
            wenn opcode != "RESUME"
        }

    def get_misses_counts(self) -> dict[str, int]:
        return {
            opcode: opcode_stat.get("specialization.miss", 0)
            fuer opcode, opcode_stat in self._data.items()
            wenn not self.is_specializable(opcode)
        }

    def get_opcode_counts(self) -> dict[str, int]:
        counts = {}
        fuer opcode, entry in self._data.items():
            count = entry.get("count", 0)
            wenn count:
                counts[opcode] = count
        return counts


klasse Stats:
    def __init__(self, data: RawData):
        self._data = data

    def get(self, key: str) -> int:
        return self._data.get(key, 0)

    @functools.cache
    def get_opcode_stats(self, prefix: str) -> OpcodeStats:
        opcode_stats = collections.defaultdict[str, dict](dict)
        fuer key, value in self._data.items():
            wenn not key.startswith(prefix):
                continue
            name, _, rest = key[len(prefix) + 1 :].partition("]")
            opcode_stats[name][rest.strip(".")] = value
        return OpcodeStats(
            opcode_stats,
            self._data["_defines"],
            self._data["_specialized_instructions"],
        )

    def get_call_stats(self) -> dict[str, int]:
        defines = self._data["_stats_defines"]
        result = {}
        fuer key, value in sorted(self._data.items()):
            wenn "Calls to" in key:
                result[key] = value
            sowenn key.startswith("Calls "):
                name, index = key[:-1].split("[")
                label = f"{name} ({pretty(defines[int(index)][0])})"
                result[label] = value

        fuer key, value in sorted(self._data.items()):
            wenn key.startswith("Frame"):
                result[key] = value

        return result

    def get_object_stats(self) -> dict[str, tuple[int, int]]:
        total_materializations = self._data.get("Object inline values", 0)
        total_allocations = self._data.get("Object allocations", 0) + self._data.get(
            "Object allocations von freelist", 0
        )
        total_increfs = (
            self._data.get("Object interpreter mortal increfs", 0) +
            self._data.get("Object mortal increfs", 0) +
            self._data.get("Object interpreter immortal increfs", 0) +
            self._data.get("Object immortal increfs", 0)
        )
        total_decrefs = (
            self._data.get("Object interpreter mortal decrefs", 0) +
            self._data.get("Object mortal decrefs", 0) +
            self._data.get("Object interpreter immortal decrefs", 0) +
            self._data.get("Object immortal decrefs", 0)
        )

        result = {}
        fuer key, value in self._data.items():
            wenn key.startswith("Object"):
                wenn "materialize" in key:
                    den = total_materializations
                sowenn "allocations" in key:
                    den = total_allocations
                sowenn "increfs" in key:
                    den = total_increfs
                sowenn "decrefs" in key:
                    den = total_decrefs
                sonst:
                    den = Nichts
                label = key[6:].strip()
                label = label[0].upper() + label[1:]
                result[label] = (value, den)
        return result

    def get_gc_stats(self) -> list[dict[str, int]]:
        gc_stats: list[dict[str, int]] = []
        fuer key, value in self._data.items():
            wenn not key.startswith("GC"):
                continue
            n, _, rest = key[3:].partition("]")
            name = rest.strip()
            gen_n = int(n)
            while len(gc_stats) <= gen_n:
                gc_stats.append({})
            gc_stats[gen_n][name] = value
        return gc_stats

    def get_optimization_stats(self) -> dict[str, tuple[int, int | Nichts]]:
        wenn "Optimization attempts" not in self._data:
            return {}

        attempts = self._data["Optimization attempts"]
        created = self._data["Optimization traces created"]
        executed = self._data["Optimization traces executed"]
        uops = self._data["Optimization uops executed"]
        trace_stack_overflow = self._data["Optimization trace stack overflow"]
        trace_stack_underflow = self._data["Optimization trace stack underflow"]
        trace_too_long = self._data["Optimization trace too long"]
        trace_too_short = self._data["Optimization trace too short"]
        inner_loop = self._data["Optimization inner loop"]
        recursive_call = self._data["Optimization recursive call"]
        low_confidence = self._data["Optimization low confidence"]
        unknown_callee = self._data["Optimization unknown callee"]
        executors_invalidated = self._data["Executors invalidated"]

        return {
            Doc(
                "Optimization attempts",
                "The number of times a potential trace is identified.  Specifically, this "
                "occurs in the JUMP BACKWARD instruction when the counter reaches a "
                "threshold.",
            ): (attempts, Nichts),
            Doc(
                "Traces created", "The number of traces that were successfully created."
            ): (created, attempts),
            Doc(
                "Trace stack overflow",
                "A trace is truncated because it would require more than 5 stack frames.",
            ): (trace_stack_overflow, attempts),
            Doc(
                "Trace stack underflow",
                "A potential trace is abandoned because it pops more frames than it pushes.",
            ): (trace_stack_underflow, attempts),
            Doc(
                "Trace too long",
                "A trace is truncated because it is longer than the instruction buffer.",
            ): (trace_too_long, attempts),
            Doc(
                "Trace too short",
                "A potential trace is abandoned because it is too short.",
            ): (trace_too_short, attempts),
            Doc(
                "Inner loop found", "A trace is truncated because it has an inner loop"
            ): (inner_loop, attempts),
            Doc(
                "Recursive call",
                "A trace is truncated because it has a recursive call.",
            ): (recursive_call, attempts),
            Doc(
                "Low confidence",
                "A trace is abandoned because the likelihood of the jump to top being taken "
                "is too low.",
            ): (low_confidence, attempts),
            Doc(
                "Unknown callee",
                "A trace is abandoned because the target of a call is unknown.",
            ): (unknown_callee, attempts),
            Doc(
                "Executors invalidated",
                "The number of executors that were invalidated due to watched "
                "dictionary changes.",
            ): (executors_invalidated, created),
            Doc("Traces executed", "The number of traces that were executed"): (
                executed,
                Nichts,
            ),
            Doc(
                "Uops executed",
                "The total number of uops (micro-operations) that were executed",
            ): (
                uops,
                executed,
            ),
        }

    def get_optimizer_stats(self) -> dict[str, tuple[int, int | Nichts]]:
        attempts = self._data["Optimization optimizer attempts"]
        successes = self._data["Optimization optimizer successes"]
        no_memory = self._data["Optimization optimizer failure no memory"]
        builtins_changed = self._data["Optimizer remove globals builtins changed"]
        incorrect_keys = self._data["Optimizer remove globals incorrect keys"]

        return {
            Doc(
                "Optimizer attempts",
                "The number of times the trace optimizer (_Py_uop_analyze_and_optimize) was run.",
            ): (attempts, Nichts),
            Doc(
                "Optimizer successes",
                "The number of traces that were successfully optimized.",
            ): (successes, attempts),
            Doc(
                "Optimizer no memory",
                "The number of optimizations that failed due to no memory.",
            ): (no_memory, attempts),
            Doc(
                "Remove globals builtins changed",
                "The builtins changed during optimization",
            ): (builtins_changed, attempts),
            Doc(
                "Remove globals incorrect keys",
                "The keys in the globals dictionary aren't what was expected",
            ): (incorrect_keys, attempts),
        }

    def get_jit_memory_stats(self) -> dict[Doc, tuple[int, int | Nichts]]:
        jit_total_memory_size = self._data["JIT total memory size"]
        jit_code_size = self._data["JIT code size"]
        jit_trampoline_size = self._data["JIT trampoline size"]
        jit_data_size = self._data["JIT data size"]
        jit_padding_size = self._data["JIT padding size"]
        jit_freed_memory_size = self._data["JIT freed memory size"]

        return {
            Doc(
                "Total memory size",
                "The total size of the memory allocated fuer the JIT traces",
            ): (jit_total_memory_size, Nichts),
            Doc(
                "Code size",
                "The size of the memory allocated fuer the code of the JIT traces",
            ): (jit_code_size, jit_total_memory_size),
            Doc(
                "Trampoline size",
                "The size of the memory allocated fuer the trampolines of the JIT traces",
            ): (jit_trampoline_size, jit_total_memory_size),
            Doc(
                "Data size",
                "The size of the memory allocated fuer the data of the JIT traces",
            ): (jit_data_size, jit_total_memory_size),
            Doc(
                "Padding size",
                "The size of the memory allocated fuer the padding of the JIT traces",
            ): (jit_padding_size, jit_total_memory_size),
            Doc(
                "Freed memory size",
                "The size of the memory freed von the JIT traces",
            ): (jit_freed_memory_size, jit_total_memory_size),
        }

    def get_histogram(self, prefix: str) -> list[tuple[int, int]]:
        rows = []
        fuer k, v in self._data.items():
            match = re.match(f"{prefix}\\[([0-9]+)\\]", k)
            wenn match is not Nichts:
                entry = int(match.groups()[0])
                rows.append((entry, v))
        rows.sort()
        return rows

    def get_rare_events(self) -> list[tuple[str, int]]:
        prefix = "Rare event "
        return [
            (key[len(prefix) + 1 : -1].replace("_", " "), val)
            fuer key, val in self._data.items()
            wenn key.startswith(prefix)
        ]


klasse JoinMode(enum.Enum):
    # Join using the first column als a key
    SIMPLE = 0
    # Join using the first column als a key, and indicate the change in the
    # second column of each input table als a new column
    CHANGE = 1
    # Join using the first column als a key, indicating the change in the second
    # column of each input table als a new column, and omit all other columns
    CHANGE_ONE_COLUMN = 2
    # Join using the first column als a key, and indicate the change als a new
    # column, but don't sort by the amount of change.
    CHANGE_NO_SORT = 3


klasse Table:
    """
    A Table defines how to convert a set of Stats into a specific set of rows
    displaying some aspect of the data.
    """

    def __init__(
        self,
        column_names: Columns,
        calc_rows: RowCalculator,
        join_mode: JoinMode = JoinMode.SIMPLE,
    ):
        self.columns = column_names
        self.calc_rows = calc_rows
        self.join_mode = join_mode

    def join_row(self, key: str, row_a: tuple, row_b: tuple) -> tuple:
        match self.join_mode:
            case JoinMode.SIMPLE:
                return (key, *row_a, *row_b)
            case JoinMode.CHANGE | JoinMode.CHANGE_NO_SORT:
                return (key, *row_a, *row_b, DiffRatio(row_a[0], row_b[0]))
            case JoinMode.CHANGE_ONE_COLUMN:
                return (key, row_a[0], row_b[0], DiffRatio(row_a[0], row_b[0]))

    def join_columns(self, columns: Columns) -> Columns:
        match self.join_mode:
            case JoinMode.SIMPLE:
                return (
                    columns[0],
                    *("Base " + x fuer x in columns[1:]),
                    *("Head " + x fuer x in columns[1:]),
                )
            case JoinMode.CHANGE | JoinMode.CHANGE_NO_SORT:
                return (
                    columns[0],
                    *("Base " + x fuer x in columns[1:]),
                    *("Head " + x fuer x in columns[1:]),
                ) + ("Change:",)
            case JoinMode.CHANGE_ONE_COLUMN:
                return (
                    columns[0],
                    "Base " + columns[1],
                    "Head " + columns[1],
                    "Change:",
                )

    def join_tables(self, rows_a: Rows, rows_b: Rows) -> tuple[Columns, Rows]:
        ncols = len(self.columns)

        default = ("",) * (ncols - 1)
        data_a = {x[0]: x[1:] fuer x in rows_a}
        data_b = {x[0]: x[1:] fuer x in rows_b}

        wenn len(data_a) != len(rows_a) or len(data_b) != len(rows_b):
            raise ValueError("Duplicate keys")

        # To preserve ordering, use A's keys als is and then add any in B that
        # aren't in A
        keys = list(data_a.keys()) + [k fuer k in data_b.keys() wenn k not in data_a]
        rows = [
            self.join_row(k, data_a.get(k, default), data_b.get(k, default))
            fuer k in keys
        ]
        wenn self.join_mode in (JoinMode.CHANGE, JoinMode.CHANGE_ONE_COLUMN):
            rows.sort(key=lambda row: abs(float(row[-1])), reverse=Wahr)

        columns = self.join_columns(self.columns)
        return columns, rows

    def get_table(
        self, base_stats: Stats, head_stats: Stats | Nichts = Nichts
    ) -> tuple[Columns, Rows]:
        wenn head_stats is Nichts:
            rows = self.calc_rows(base_stats)
            return self.columns, rows
        sonst:
            rows_a = self.calc_rows(base_stats)
            rows_b = self.calc_rows(head_stats)
            cols, rows = self.join_tables(rows_a, rows_b)
            return cols, rows


klasse Section:
    """
    A Section defines a section of the output document.
    """

    def __init__(
        self,
        title: str = "",
        summary: str = "",
        part_iter=Nichts,
        *,
        comparative: bool = Wahr,
        doc: str = "",
    ):
        self.title = title
        wenn not summary:
            self.summary = title.lower()
        sonst:
            self.summary = summary
        self.doc = textwrap.dedent(doc)
        wenn part_iter is Nichts:
            part_iter = []
        wenn isinstance(part_iter, list):

            def iter_parts(base_stats: Stats, head_stats: Stats | Nichts):
                yield von part_iter

            self.part_iter = iter_parts
        sonst:
            self.part_iter = part_iter
        self.comparative = comparative


def calc_execution_count_table(prefix: str) -> RowCalculator:
    def calc(stats: Stats) -> Rows:
        opcode_stats = stats.get_opcode_stats(prefix)
        counts = opcode_stats.get_execution_counts()
        total = opcode_stats.get_total_execution_count()
        cumulative = 0
        rows: Rows = []
        fuer opcode, (count, miss) in sorted(
            counts.items(), key=itemgetter(1), reverse=Wahr
        ):
            cumulative += count
            wenn miss:
                miss_val = Ratio(miss, count)
            sonst:
                miss_val = Nichts
            rows.append(
                (
                    opcode,
                    Count(count),
                    Ratio(count, total),
                    Ratio(cumulative, total),
                    miss_val,
                )
            )
        return rows

    return calc


def execution_count_section() -> Section:
    return Section(
        "Execution counts",
        "Execution counts fuer Tier 1 instructions.",
        [
            Table(
                ("Name", "Count:", "Self:", "Cumulative:", "Miss ratio:"),
                calc_execution_count_table("opcode"),
                join_mode=JoinMode.CHANGE_ONE_COLUMN,
            )
        ],
        doc="""
        The "miss ratio" column shows the percentage of times the instruction
        executed that it deoptimized. When this happens, the base unspecialized
        instruction is not counted.
        """,
    )


def pair_count_section(prefix: str, title=Nichts) -> Section:
    def calc_pair_count_table(stats: Stats) -> Rows:
        opcode_stats = stats.get_opcode_stats(prefix)
        pair_counts = opcode_stats.get_pair_counts()
        total = opcode_stats.get_total_execution_count()

        cumulative = 0
        rows: Rows = []
        fuer (opcode_i, opcode_j), count in itertools.islice(
            sorted(pair_counts.items(), key=itemgetter(1), reverse=Wahr), 100
        ):
            cumulative += count
            rows.append(
                (
                    f"{opcode_i} {opcode_j}",
                    Count(count),
                    Ratio(count, total),
                    Ratio(cumulative, total),
                )
            )
        return rows

    return Section(
        "Pair counts",
        f"Pair counts fuer top 100 {title wenn title sonst prefix} pairs",
        [
            Table(
                ("Pair", "Count:", "Self:", "Cumulative:"),
                calc_pair_count_table,
            )
        ],
        comparative=Falsch,
        doc="""
        Pairs of specialized operations that deoptimize and are then followed by
        the corresponding unspecialized instruction are not counted als pairs.
        """,
    )


def pre_succ_pairs_section() -> Section:
    def iter_pre_succ_pairs_tables(base_stats: Stats, head_stats: Stats | Nichts = Nichts):
        assert head_stats is Nichts

        opcode_stats = base_stats.get_opcode_stats("opcode")

        fuer opcode in opcode_stats.get_opcode_names():
            predecessors = opcode_stats.get_predecessors(opcode)
            successors = opcode_stats.get_successors(opcode)
            predecessors_total = predecessors.total()
            successors_total = successors.total()
            wenn predecessors_total == 0 and successors_total == 0:
                continue
            pred_rows = [
                (pred, Count(count), Ratio(count, predecessors_total))
                fuer (pred, count) in predecessors.most_common(5)
            ]
            succ_rows = [
                (succ, Count(count), Ratio(count, successors_total))
                fuer (succ, count) in successors.most_common(5)
            ]

            yield Section(
                opcode,
                f"Successors and predecessors fuer {opcode}",
                [
                    Table(
                        ("Predecessors", "Count:", "Percentage:"),
                        lambda *_: pred_rows,  # type: ignore
                    ),
                    Table(
                        ("Successors", "Count:", "Percentage:"),
                        lambda *_: succ_rows,  # type: ignore
                    ),
                ],
            )

    return Section(
        "Predecessor/Successor Pairs",
        "Top 5 predecessors and successors of each Tier 1 opcode.",
        iter_pre_succ_pairs_tables,
        comparative=Falsch,
        doc="""
        This does not include the unspecialized instructions that occur after a
        specialized instruction deoptimizes.
        """,
    )


def specialization_section() -> Section:
    def calc_specialization_table(opcode: str) -> RowCalculator:
        def calc(stats: Stats) -> Rows:
            DOCS = {
                "deferred": 'Lists the number of "deferred" (i.e. not specialized) instructions executed.',
                "hit": "Specialized instructions that complete.",
                "miss": "Specialized instructions that deopt.",
                "deopt": "Specialized instructions that deopt.",
            }

            opcode_stats = stats.get_opcode_stats("opcode")
            total = opcode_stats.get_specialization_total(opcode)
            specialization_counts = opcode_stats.get_specialization_counts(opcode)

            return [
                (
                    Doc(label, DOCS[label]),
                    Count(count),
                    Ratio(count, total),
                )
                fuer label, count in specialization_counts.items()
            ]

        return calc

    def calc_specialization_success_failure_table(name: str) -> RowCalculator:
        def calc(stats: Stats) -> Rows:
            values = stats.get_opcode_stats(
                "opcode"
            ).get_specialization_success_failure(name)
            total = sum(values.values())
            wenn total:
                return [
                    (label.capitalize(), Count(val), Ratio(val, total))
                    fuer label, val in values.items()
                ]
            sonst:
                return []

        return calc

    def calc_specialization_failure_kind_table(name: str) -> RowCalculator:
        def calc(stats: Stats) -> Rows:
            opcode_stats = stats.get_opcode_stats("opcode")
            failures = opcode_stats.get_specialization_failure_kinds(name)
            total = opcode_stats.get_specialization_failure_total(name)

            return sorted(
                [
                    (label, Count(value), Ratio(value, total))
                    fuer label, value in failures.items()
                    wenn value
                ],
                key=itemgetter(1),
                reverse=Wahr,
            )

        return calc

    def iter_specialization_tables(base_stats: Stats, head_stats: Stats | Nichts = Nichts):
        opcode_base_stats = base_stats.get_opcode_stats("opcode")
        names = opcode_base_stats.get_opcode_names()
        wenn head_stats is not Nichts:
            opcode_head_stats = head_stats.get_opcode_stats("opcode")
            names &= opcode_head_stats.get_opcode_names()  # type: ignore
        sonst:
            opcode_head_stats = Nichts

        fuer opcode in sorted(names):
            wenn not opcode_base_stats.is_specializable(opcode):
                continue
            wenn opcode_base_stats.get_specialization_total(opcode) == 0 and (
                opcode_head_stats is Nichts
                or opcode_head_stats.get_specialization_total(opcode) == 0
            ):
                continue
            yield Section(
                opcode,
                f"specialization stats fuer {opcode} family",
                [
                    Table(
                        ("Kind", "Count:", "Ratio:"),
                        calc_specialization_table(opcode),
                        JoinMode.CHANGE,
                    ),
                    Table(
                        ("Success", "Count:", "Ratio:"),
                        calc_specialization_success_failure_table(opcode),
                        JoinMode.CHANGE,
                    ),
                    Table(
                        ("Failure kind", "Count:", "Ratio:"),
                        calc_specialization_failure_kind_table(opcode),
                        JoinMode.CHANGE,
                    ),
                ],
            )

    return Section(
        "Specialization stats",
        "Specialization stats by family",
        iter_specialization_tables,
    )


def specialization_effectiveness_section() -> Section:
    def calc_specialization_effectiveness_table(stats: Stats) -> Rows:
        opcode_stats = stats.get_opcode_stats("opcode")
        total = opcode_stats.get_total_execution_count()

        (
            basic,
            specialized_hits,
            specialized_misses,
            not_specialized,
        ) = opcode_stats.get_specialized_total_counts()

        return [
            (
                Doc(
                    "Basic",
                    "Instructions that are not and cannot be specialized, e.g. `LOAD_FAST`.",
                ),
                Count(basic),
                Ratio(basic, total),
            ),
            (
                Doc(
                    "Not specialized",
                    "Instructions that could be specialized but aren't, e.g. `LOAD_ATTR`, `BINARY_SLICE`.",
                ),
                Count(not_specialized),
                Ratio(not_specialized, total),
            ),
            (
                Doc(
                    "Specialized hits",
                    "Specialized instructions, e.g. `LOAD_ATTR_MODULE` that complete.",
                ),
                Count(specialized_hits),
                Ratio(specialized_hits, total),
            ),
            (
                Doc(
                    "Specialized misses",
                    "Specialized instructions, e.g. `LOAD_ATTR_MODULE` that deopt.",
                ),
                Count(specialized_misses),
                Ratio(specialized_misses, total),
            ),
        ]

    def calc_deferred_by_table(stats: Stats) -> Rows:
        opcode_stats = stats.get_opcode_stats("opcode")
        deferred_counts = opcode_stats.get_deferred_counts()
        total = sum(deferred_counts.values())
        wenn total == 0:
            return []

        return [
            (name, Count(value), Ratio(value, total))
            fuer name, value in sorted(
                deferred_counts.items(), key=itemgetter(1), reverse=Wahr
            )[:10]
        ]

    def calc_misses_by_table(stats: Stats) -> Rows:
        opcode_stats = stats.get_opcode_stats("opcode")
        misses_counts = opcode_stats.get_misses_counts()
        total = sum(misses_counts.values())
        wenn total == 0:
            return []

        return [
            (name, Count(value), Ratio(value, total))
            fuer name, value in sorted(
                misses_counts.items(), key=itemgetter(1), reverse=Wahr
            )[:10]
        ]

    return Section(
        "Specialization effectiveness",
        "",
        [
            Table(
                ("Instructions", "Count:", "Ratio:"),
                calc_specialization_effectiveness_table,
                JoinMode.CHANGE,
            ),
            Section(
                "Deferred by instruction",
                "Breakdown of deferred (not specialized) instruction counts by family",
                [
                    Table(
                        ("Name", "Count:", "Ratio:"),
                        calc_deferred_by_table,
                        JoinMode.CHANGE,
                    )
                ],
            ),
            Section(
                "Misses by instruction",
                "Breakdown of misses (specialized deopts) instruction counts by family",
                [
                    Table(
                        ("Name", "Count:", "Ratio:"),
                        calc_misses_by_table,
                        JoinMode.CHANGE,
                    )
                ],
            ),
        ],
        doc="""
        All entries are execution counts. Should add up to the total number of
        Tier 1 instructions executed.
        """,
    )


def call_stats_section() -> Section:
    def calc_call_stats_table(stats: Stats) -> Rows:
        call_stats = stats.get_call_stats()
        total = sum(v fuer k, v in call_stats.items() wenn "Calls to" in k)
        return [
            (key, Count(value), Ratio(value, total))
            fuer key, value in call_stats.items()
        ]

    return Section(
        "Call stats",
        "Inlined calls and frame stats",
        [
            Table(
                ("", "Count:", "Ratio:"),
                calc_call_stats_table,
                JoinMode.CHANGE,
            )
        ],
        doc="""
        This shows what fraction of calls to Python functions are inlined (i.e.
        not having a call at the C level) and fuer those that are not, where the
        call comes from.  The various categories overlap.

        Also includes the count of frame objects created.
        """,
    )


def object_stats_section() -> Section:
    def calc_object_stats_table(stats: Stats) -> Rows:
        object_stats = stats.get_object_stats()
        return [
            (label, Count(value), Ratio(value, den))
            fuer label, (value, den) in object_stats.items()
        ]

    return Section(
        "Object stats",
        "Allocations, frees and dict materializatons",
        [
            Table(
                ("", "Count:", "Ratio:"),
                calc_object_stats_table,
                JoinMode.CHANGE,
            )
        ],
        doc="""
        Below, "allocations" means "allocations that are not von a freelist".
        Total allocations = "Allocations von freelist" + "Allocations".

        "Inline values" is the number of values arrays inlined into objects.

        The cache hit/miss numbers are fuer the MRO cache, split into dunder and
        other names.
        """,
    )


def gc_stats_section() -> Section:
    def calc_gc_stats(stats: Stats) -> Rows:
        gc_stats = stats.get_gc_stats()

        return [
            (
                Count(i),
                Count(gen["collections"]),
                Count(gen["objects collected"]),
                Count(gen["object visits"]),
                Count(gen["objects reachable von roots"]),
                Count(gen["objects not reachable von roots"]),
            )
            fuer (i, gen) in enumerate(gc_stats)
        ]

    return Section(
        "GC stats",
        "GC collections and effectiveness",
        [
            Table(
                ("Generation:", "Collections:", "Objects collected:", "Object visits:",
                 "Reachable von roots:", "Not reachable von roots:"),
                calc_gc_stats,
            )
        ],
        doc="""
        Collected/visits gives some measure of efficiency.
        """,
    )


def optimization_section() -> Section:
    def calc_optimization_table(stats: Stats) -> Rows:
        optimization_stats = stats.get_optimization_stats()

        return [
            (
                label,
                Count(value),
                Ratio(value, den, percentage=label != "Uops executed"),
            )
            fuer label, (value, den) in optimization_stats.items()
        ]

    def calc_optimizer_table(stats: Stats) -> Rows:
        optimizer_stats = stats.get_optimizer_stats()

        return [
            (label, Count(value), Ratio(value, den))
            fuer label, (value, den) in optimizer_stats.items()
        ]

    def calc_jit_memory_table(stats: Stats) -> Rows:
        jit_memory_stats = stats.get_jit_memory_stats()

        return [
            (
                label,
                Count(value),
                Ratio(value, den, percentage=label != "Total memory size"),
            )
            fuer label, (value, den) in jit_memory_stats.items()
        ]

    def calc_histogram_table(key: str, den: str | Nichts = Nichts) -> RowCalculator:
        def calc(stats: Stats) -> Rows:
            histogram = stats.get_histogram(key)

            wenn den:
                denominator = stats.get(den)
            sonst:
                denominator = 0
                fuer _, v in histogram:
                    denominator += v

            rows: Rows = []
            fuer k, v in histogram:
                rows.append(
                    (
                        f"<= {k:,d}",
                        Count(v),
                        Ratio(v, denominator),
                    )
                )
            # Don't include any leading and trailing zero entries
            start = 0
            end = len(rows) - 1

            while start <= end:
                wenn rows[start][1] == 0:
                    start += 1
                sowenn rows[end][1] == 0:
                    end -= 1
                sonst:
                    break

            return rows[start:end+1]

        return calc

    def calc_unsupported_opcodes_table(stats: Stats) -> Rows:
        unsupported_opcodes = stats.get_opcode_stats("unsupported_opcode")
        return sorted(
            [
                (opcode, Count(count))
                fuer opcode, count in unsupported_opcodes.get_opcode_counts().items()
            ],
            key=itemgetter(1),
            reverse=Wahr,
        )

    def calc_error_in_opcodes_table(stats: Stats) -> Rows:
        error_in_opcodes = stats.get_opcode_stats("error_in_opcode")
        return sorted(
            [
                (opcode, Count(count))
                fuer opcode, count in error_in_opcodes.get_opcode_counts().items()
            ],
            key=itemgetter(1),
            reverse=Wahr,
        )

    def iter_optimization_tables(base_stats: Stats, head_stats: Stats | Nichts = Nichts):
        wenn not base_stats.get_optimization_stats() or (
            head_stats is not Nichts and not head_stats.get_optimization_stats()
        ):
            return

        yield Table(("", "Count:", "Ratio:"), calc_optimization_table, JoinMode.CHANGE)
        yield Table(("", "Count:", "Ratio:"), calc_optimizer_table, JoinMode.CHANGE)
        yield Section(
            "JIT memory stats",
            "JIT memory stats",
            [
                Table(
                    ("", "Size (bytes):", "Ratio:"),
                    calc_jit_memory_table,
                    JoinMode.CHANGE
                )
            ],
        )
        yield Section(
            "JIT trace total memory histogram",
            "JIT trace total memory histogram",
            [
                Table(
                    ("Size (bytes)", "Count", "Ratio:"),
                    calc_histogram_table("Trace total memory size"),
                    JoinMode.CHANGE_NO_SORT,
                )
            ],
        )
        fuer name, den in [
            ("Trace length", "Optimization traces created"),
            ("Optimized trace length", "Optimization traces created"),
            ("Trace run length", "Optimization traces executed"),
        ]:
            yield Section(
                f"{name} histogram",
                "",
                [
                    Table(
                        ("Range", "Count:", "Ratio:"),
                        calc_histogram_table(name, den),
                        JoinMode.CHANGE_NO_SORT,
                    )
                ],
            )
        yield Section(
            "Uop execution stats",
            "",
            [
                Table(
                    ("Name", "Count:", "Self:", "Cumulative:", "Miss ratio:"),
                    calc_execution_count_table("uops"),
                    JoinMode.CHANGE_ONE_COLUMN,
                )
            ],
        )
        yield pair_count_section(prefix="uop", title="Non-JIT uop")
        yield Section(
            "Unsupported opcodes",
            "",
            [
                Table(
                    ("Opcode", "Count:"),
                    calc_unsupported_opcodes_table,
                    JoinMode.CHANGE,
                )
            ],
        )
        yield Section(
            "Optimizer errored out mit opcode",
            "Optimization stopped after encountering this opcode",
            [Table(("Opcode", "Count:"), calc_error_in_opcodes_table, JoinMode.CHANGE)],
        )

    return Section(
        "Optimization (Tier 2) stats",
        "statistics about the Tier 2 optimizer",
        iter_optimization_tables,
    )


def rare_event_section() -> Section:
    def calc_rare_event_table(stats: Stats) -> Table:
        DOCS = {
            "set class": "Setting an object's class, `obj.__class__ = ...`",
            "set bases": "Setting the bases of a class, `cls.__bases__ = ...`",
            "set eval frame func": (
                "Setting the PEP 523 frame eval function "
                "`_PyInterpreterState_SetFrameEvalFunc()`"
            ),
            "builtin dict": "Modifying the builtins, `__builtins__.__dict__[var] = ...`",
            "func modification": "Modifying a function, e.g. `func.__defaults__ = ...`, etc.",
            "watched dict modification": "A watched dict has been modified",
            "watched globals modification": "A watched `globals()` dict has been modified",
        }
        return [(Doc(x, DOCS[x]), Count(y)) fuer x, y in stats.get_rare_events()]

    return Section(
        "Rare events",
        "Counts of rare/unlikely events",
        [Table(("Event", "Count:"), calc_rare_event_table, JoinMode.CHANGE)],
    )


def meta_stats_section() -> Section:
    def calc_rows(stats: Stats) -> Rows:
        return [("Number of data files", Count(stats.get("__nfiles__")))]

    return Section(
        "Meta stats",
        "Meta statistics",
        [Table(("", "Count:"), calc_rows, JoinMode.CHANGE)],
    )


LAYOUT = [
    execution_count_section(),
    pair_count_section("opcode"),
    pre_succ_pairs_section(),
    specialization_section(),
    specialization_effectiveness_section(),
    call_stats_section(),
    object_stats_section(),
    gc_stats_section(),
    optimization_section(),
    rare_event_section(),
    meta_stats_section(),
]


def output_markdown(
    out: TextIO,
    obj: Section | Table | list,
    base_stats: Stats,
    head_stats: Stats | Nichts = Nichts,
    level: int = 2,
) -> Nichts:
    def to_markdown(x):
        wenn hasattr(x, "markdown"):
            return x.markdown()
        sowenn isinstance(x, str):
            return x
        sowenn x is Nichts:
            return ""
        sonst:
            raise TypeError(f"Can't convert {x} to markdown")

    match obj:
        case Section():
            wenn obj.title:
                drucke("#" * level, obj.title, file=out)
                drucke(file=out)
                drucke("<details>", file=out)
                drucke("<summary>", obj.summary, "</summary>", file=out)
                drucke(file=out)
            wenn obj.doc:
                drucke(obj.doc, file=out)

            wenn head_stats is not Nichts and obj.comparative is Falsch:
                drucke("Not included in comparative output.\n")
            sonst:
                fuer part in obj.part_iter(base_stats, head_stats):
                    output_markdown(out, part, base_stats, head_stats, level=level + 1)
            drucke(file=out)
            wenn obj.title:
                drucke("</details>", file=out)
                drucke(file=out)

        case Table():
            header, rows = obj.get_table(base_stats, head_stats)
            wenn len(rows) == 0:
                return

            alignments = []
            fuer item in header:
                wenn item.endswith(":"):
                    alignments.append("right")
                sonst:
                    alignments.append("left")

            drucke("<table>", file=out)
            drucke("<thead>", file=out)
            drucke("<tr>", file=out)
            fuer item, align in zip(header, alignments):
                wenn item.endswith(":"):
                    item = item[:-1]
                drucke(f'<th align="{align}">{item}</th>', file=out)
            drucke("</tr>", file=out)
            drucke("</thead>", file=out)

            drucke("<tbody>", file=out)
            fuer row in rows:
                wenn len(row) != len(header):
                    raise ValueError(
                        "Wrong number of elements in row '" + str(row) + "'"
                    )
                drucke("<tr>", file=out)
                fuer col, align in zip(row, alignments):
                    drucke(f'<td align="{align}">{to_markdown(col)}</td>', file=out)
                drucke("</tr>", file=out)
            drucke("</tbody>", file=out)

            drucke("</table>", file=out)
            drucke(file=out)

        case list():
            fuer part in obj:
                output_markdown(out, part, base_stats, head_stats, level=level)

            drucke("---", file=out)
            drucke("Stats gathered on:", date.today(), file=out)


def output_stats(inputs: list[Path], json_output=str | Nichts):
    match len(inputs):
        case 1:
            data = load_raw_data(Path(inputs[0]))
            wenn json_output is not Nichts:
                mit open(json_output, "w", encoding="utf-8") als f:
                    save_raw_data(data, f)  # type: ignore
            stats = Stats(data)
            output_markdown(sys.stdout, LAYOUT, stats)
        case 2:
            wenn json_output is not Nichts:
                raise ValueError(
                    "Can not output to JSON when there are multiple inputs"
                )
            base_data = load_raw_data(Path(inputs[0]))
            head_data = load_raw_data(Path(inputs[1]))
            base_stats = Stats(base_data)
            head_stats = Stats(head_data)
            output_markdown(sys.stdout, LAYOUT, base_stats, head_stats)


def main():
    parser = argparse.ArgumentParser(description="Summarize pystats results")

    parser.add_argument(
        "inputs",
        nargs="*",
        type=str,
        default=[DEFAULT_DIR],
        help=f"""
        Input source(s).
        For each entry, wenn a .json file, the output provided by --json-output von a previous run;
        wenn a directory, a directory containing raw pystats .txt files.
        If one source is provided, its stats are printed.
        If two sources are provided, comparative stats are printed.
        Default is {DEFAULT_DIR}.
        """,
    )

    parser.add_argument(
        "--json-output",
        nargs="?",
        help="Output complete raw results to the given JSON file.",
    )

    args = parser.parse_args()

    wenn len(args.inputs) > 2:
        raise ValueError("0-2 arguments may be provided.")

    output_stats(args.inputs, json_output=args.json_output)


wenn __name__ == "__main__":
    main()
