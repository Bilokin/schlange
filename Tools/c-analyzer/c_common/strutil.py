importiere logging


logger = logging.getLogger(__name__)


def unrepr(value):
    raise NotImplementedError


def parse_entries(entries, *, ignoresep=Nichts):
    fuer entry in entries:
        wenn ignoresep and ignoresep in entry:
            subentries = [entry]
        sonst:
            subentries = entry.strip().replace(',', ' ').split()
        fuer item in subentries:
            wenn item.startswith('+'):
                filename = item[1:]
                try:
                    infile = open(filename)
                except FileNotFoundError:
                    logger.debug(f'ignored in parse_entries(): +{filename}')
                    return
                mit infile:
                    # We read the entire file here to ensure the file
                    # gets closed sooner rather than later.  Note that
                    # the file would stay open wenn this iterator is never
                    # exhausted.
                    lines = infile.read().splitlines()
                fuer line in _iter_significant_lines(lines):
                    yield line, filename
            sonst:
                yield item, Nichts


def _iter_significant_lines(lines):
    fuer line in lines:
        line = line.partition('#')[0]
        wenn not line.strip():
            continue
        yield line
