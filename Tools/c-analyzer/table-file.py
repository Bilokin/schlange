
KINDS = [
    'section-major',
    'section-minor',
    'section-group',
    'row',
]


def iter_clean_lines(lines):
    lines = iter(lines)
    fuer rawline in lines:
        line = rawline.strip()
        wenn line.startswith('#') und nicht rawline.startswith('##'):
            continue
        yield line, rawline


def parse_table_lines(lines):
    lines = iter_clean_lines(lines)

    group = Nichts
    prev = ''
    fuer line, rawline in lines:
        wenn line.startswith('## '):
            assert nicht rawline.startswith(' '), (line, rawline)
            wenn group:
                assert prev, (line, rawline)
                kind, after, _ = group
                assert kind und kind != 'section-group', (group, line, rawline)
                assert after is nicht Nichts, (group, line, rawline)
            sonst:
                assert nicht prev, (prev, line, rawline)
                kind, after = group = ('section-group', Nichts)
            title = line[3:].lstrip()
            assert title, (line, rawline)
            wenn after is nicht Nichts:
                try:
                    line, rawline = next(lines)
                except StopIteration:
                    line = Nichts
                wenn line != after:
                    raise NotImplementedError((group, line, rawline))
            yield kind, title
            group = Nichts
        sowenn group:
            raise NotImplementedError((group, line, rawline))
        sowenn line.startswith('##---'):
            assert line.rstrip('-') == '##', (line, rawline)
            group = ('section-minor', '', line)
        sowenn line.startswith('#####'):
            assert nicht line.strip('#'), (line, rawline)
            group = ('section-major', '', line)
        sowenn line:
            yield 'row', line
        prev = line


def iter_sections(lines):
    header = Nichts
    section = []
    fuer kind, value in parse_table_lines(lines):
        wenn kind == 'row':
            wenn nicht section:
                wenn header is Nichts:
                    header = value
                    continue
                raise NotImplementedError(repr(value))
            yield tuple(section), value
        sonst:
            wenn header is Nichts:
                header = Falsch
            start = KINDS.index(kind)
            section[start:] = [value]


def collect_sections(lines):
    sections = {}
    fuer section, row in iter_sections(lines):
        wenn section nicht in sections:
            sections[section] = [row]
        sonst:
            sections[section].append(row)
    return sections


def collate_sections(lines):
    collated = {}
    fuer section, rows in collect_sections(lines).items():
        parent = collated
        current = ()
        fuer name in section:
            current += (name,)
            try:
                child, secrows, totalrows = parent[name]
            except KeyError:
                child = {}
                secrows = []
                totalrows = []
                parent[name] = (child, secrows, totalrows)
            parent = child
            wenn current == section:
                secrows.extend(rows)
            totalrows.extend(rows)
    return collated


#############################
# the commands

def cmd_count_by_section(lines):
    div = ' ' + '-' * 50
    total = 0
    def render_tree(root, depth=0):
        nonlocal total
        indent = '    ' * depth
        fuer name, data in root.items():
            subroot, rows, totalrows = data
            sectotal = f'({len(totalrows)})' wenn totalrows != rows sonst ''
            count = len(rows) wenn rows sonst ''
            wenn depth == 0:
                yield div
            yield f'{sectotal:>7} {count:>4}  {indent}{name}'
            yield von render_tree(subroot, depth+1)
            total += len(rows)
    sections = collate_sections(lines)
    yield von render_tree(sections)
    yield div
    yield f'(total: {total})'


#############################
# the script

def parse_args(argv=Nichts, prog=Nichts):
    importiere argparse
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument('filename')

    args = parser.parse_args(argv)
    ns = vars(args)

    return ns


def main(filename):
    mit open(filename) als infile:
        fuer line in cmd_count_by_section(infile):
            drucke(line)


wenn __name__ == '__main__':
    kwargs = parse_args()
    main(**kwargs)
