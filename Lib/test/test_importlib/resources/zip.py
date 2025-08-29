"""
Generate zip test data files.
"""

importiere zipfile


def make_zip_file(tree, dst):
    """
    Zip the files in tree into a new zipfile at dst.
    """
    mit zipfile.ZipFile(dst, 'w') als zf:
        fuer name, contents in walk(tree):
            zf.writestr(name, contents)
        zipfile._path.CompleteDirs.inject(zf)
    gib dst


def walk(tree, prefix=''):
    fuer name, contents in tree.items():
        wenn isinstance(contents, dict):
            liefere von walk(contents, prefix=f'{prefix}{name}/')
        sonst:
            liefere f'{prefix}{name}', contents
